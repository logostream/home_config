#!/usr/bin/python
# coding=ascii

# TODO (style): imports order
import argparse as _arg
import os
import os.path as _path
import yaml as _yaml
import sys
import datetime as _dt
import collections as _col
import subprocess as _sp
import tempfile as _tf
import re
import urllib2 as _url
import urlparse as _urlp
import difflib as _diff
import base64 as _b64
import uuid as _uuid

# TODO (p1): _check_health after dryrun
# TODO (style): comments
# TODO (p2): add tag web-only, ignore for map? (no, to explain)
# TODO (p3): ? cleanup orphan files, orphan file only happens when mannual edit the file date, or
#            uuid
# TODO (p1, obsolete): comand for rename file, name are free of change now
#+ manually for non-auto downloadable file. (mv, deplicate mode)
#+ TODO (p1): readlink/map fall back to web option
#+ TODO (p2): readlink/map follow successor option (now just warn on deprecation)
# TODO (p0, cc): add uuid, and successor:
#+ * uuid for linkfile (free from rename)
#+ * uuid for internal save (free from rename)
#+ * uuid for internal refering
#+ * check uuid-successor health
#+ * provide map, ln, cp, update by uuid
#+ * TODO (p2): print entry, print uuid in less verbose mode
#* * some ut maybe uuid aware, some may not (minial principle)
#+ ! uuid should independent, unique, unchange, can be delete but not recommended,
#+ generating can retry


_HOME = os.environ['HOME']
_LINKHUB_PATH = _path.join(_HOME, 'linkhub')
# todo: archived link
_LINKMAP_PATH = _path.join(_LINKHUB_PATH, 'linkmap.yaml')
_FLAGS_dry_run = True
_TEMP_DIR_PREFIX = 'linktmp'
# _DATE_ENTRY_FORMAT= '%Y-%m-%d' # yaml format/parse datimetime.date like this by default
_DATE_DIR_FORMAT = '%Y%m%d'

# mode
_MODE_EQUALS = 'equals'
_MODE_CONTAINS = 'contains'
_MODE_REGEX = 'regex'

# tags
_TAG_DEPRECATED = 'deprecated'
_TAG_AUTO = 'auto' # automatically downloadable

# Entry properties
# The data model of linkmap: uuid as primary key featured unchangibility, (name, url) as
#+ secondary key featured readability, uuid can be view as internal id used within linkhub and link
#+ files, while (name, url) can be view as readable "id" among non-deprecated entries
# uuid used for refering in linkmap, saved file name in linkhub, link file. the purpose is to have
#+ a unchanged (independent from name, url etc.), unique, compact property.
_KEY_UUID = 'uuid'
_KEY_NAME = 'name' # also used in rawlink
_KEY_URL = 'url' # also used in rawlink
_KEY_DATE = 'date'
_KEY_TAGS = 'tags'
# Optional entry properties
_KEY_COMMENT = 'comment'
_KEY_ALT_URLS = 'alt_urls'
_KEY_SUCCESSOR = 'successor'
# rawlink optional properties
_KEY_AUTO = 'auto'


# ops
# not suppose to be a general search tool, because one can search for linkmap file directly.
def _find(name, url, match_mode, case_sensitive, include_alt_urls, include_deprecated):
	# TODO(p1): support search for id. right now, use command `map` instead
	assert name is not None or url is not None
	candidates = sorted([entry for entry in _linkmap if
				(include_deprecated or not _tagged_as(entry, _TAG_DEPRECATED))
				and (name is None or _match(entry[_KEY_NAME], name, match_mode, case_sensitive))
				and (url is None or _match(entry[_KEY_URL], url, match_mode, case_sensitive)
					or (include_alt_urls
						and _KEY_ALT_URLS in entry
						and _match_any(entry[_KEY_ALT_URLS], url, match_mode, case_sensitive)))],
			key=_get_date, reverse=True)

	_info('Matched entries:')
	for candidate in candidates:
		_print_entry(sys.stdout, candidate)
		print # empty line
	return 0

def _load_rawlinks(rawlinks_yaml_path, override):
	downloads = []
	with open(rawlinks_yaml_path, 'r') as rawlinks_yaml_file:
		rawlinks_yaml = ''.join(rawlinks_yaml_file.readlines())
		rawlinks = _yaml.load(rawlinks_yaml)

		for rawlink in rawlinks:
			if _KEY_NAME not in rawlink:
				name = _name_from_url(rawlink[_KEY_URL])
				if name:
					_info('Inferred name from url: %s.', name)
				else:
					_error('Inferred name is empty.')
					continue
				rawlink[_KEY_NAME] = name

			candidates = _map_to_candidates(_linkmap,
					name=rawlink[_KEY_NAME], url=rawlink[_KEY_URL], check_unique=False)
			if candidates and candidates[0][_KEY_DATE] == _today():
				_warn('Links alread added into linkmap, use existing one:')
				_print_entry(sys.stderr, candidates[0])
				entry = candidates[0]
			else:
				if candidates:
					_warn('Exists another entry with same name and url:')
					_print_entry(sys.stderr, candidates[0])
				entry = _new_entry(rawlink, _linkmap_table)
				_info('New entry:')
				_print_entry(sys.stderr, entry)
				_info()
				_linkmap.append(entry)

			local_path = _to_local_path(entry)
			if _tagged_as(entry, _TAG_AUTO) and (override or not _path.exists(local_path)):
				downloads.append(entry)
			elif not _path.exists(local_path):
				_warn('Local file %s dosen\'t exist, need to download manually.', local_path)

		_diff_linkmap(_linkmap, _linkmap_yaml)
		_export_linkmap(_linkmap, _FLAGS_dry_run)
		
		# Put download in the final stage to prevent generating orphan file
		for entry in downloads:
			_download_file(entry[_KEY_URL], _to_local_path(entry), _FLAGS_dry_run)
	return 0

def _map_to_local(uuid=None, name=None, url=None, check=False):
	candidate = _map_to_candidates(_linkmap, _linkmap_table, uuid, name, url)[0]
	_print_entry(sys.stderr, candidate)

	local_path = _to_local_path(candidate)
	if check:
		assert _path.exists(local_path)
	print local_path
	return 0

def _make_link(uuid, name, url, dest_path):
	# TODO (p1): support dest_dir, using default name
	candidate = _map_to_candidates(_linkmap, _linkmap_table, uuid, name, url)[0]
	_info('Make link for entry:')
	_print_entry(sys.stderr, candidate)

	link_yaml = _build_link_yaml(candidate)
	_save_to_file(link_yaml, dest_path, _FLAGS_dry_run)
	return 0

def _read_link(link_path, check):
	# TODO (p3): get url mode
	with open(link_path, 'r') as link_file:
		link_yaml = ''.join(link_file.readlines())
		link = _yaml.load(link_yaml)
		uuid = link[_KEY_UUID]
		_info('Link uuid: %s.', uuid)
		return _map_to_local(uuid=uuid, check=check)

def _make_copy(uuid, name, url, dest_path):
	# TODO (p1): support dest_dir, using default name
	candidate = _map_to_candidates(_linkmap, _linkmap_table, uuid, name, url)[0]
	_info('Make copy for entry:')
	_print_entry(sys.stderr, candidate)

	local_path = _to_local_path(candidate)
	_copy_file(local_path, dest_path, _FLAGS_dry_run)
	return 0

def _update_from_url(uuid, name, url):
	candidate = _map_to_candidates(_linkmap, _linkmap_table, uuid, name, url)[0]
	_print_entry(sys.stderr, candidate)

	if not _tagged_as(candidate, _TAG_AUTO):
		_error('Not automatically downloadable.')
		return 1

	local_path = _to_local_path(candidate)
	if not _path.exists(local_path):
		_warn('Original local file not exists.')

	_download_file(candidate[_KEY_URL], local_path, _FLAGS_dry_run)
	return 0

def _update_from_local(uuid, name, url, local_source):
	assert _path.exists(local_source)

	candidate = _map_to_candidates(_linkmap, _linkmap_table, uuid, name, url)[0]
	_print_entry(sys.stderr, candidate)

	if not _tagged_as(candidate, _TAG_AUTO):
		_warn('This file can be download from url.')

	local_path = _to_local_path(candidate)
	if not _path.exists(local_path):
		_warn('Original local file not exists.')

	_copy_file(local_source, local_path, _FLAGS_dry_run)
	return 0

def _deprecate_duplicates(name, url):
	candidates = _map_to_candidates(_linkmap, name=name, url=url, check_unique=False)

	if not candidates:
		_warn('No matched enties.')
		return

	latest, candidates = candidates[0], candidates[1:]
	_info('Latest match:')
	_print_entry(sys.stderr, latest)
	_info()

	if not candidates:
		_warn('No candidates to deprecate.')
		return
	
	_info('Deprecating candidates:')
	for candidate in candidates:
		_print_entry(sys.stderr, candidate)
		_info()
		_tag_as(candidate, _TAG_DEPRECATED)
		assert _KEY_SUCCESSOR not in candidate
		candidate[_KEY_SUCCESSOR] = latest[_KEY_UUID]

	_diff_linkmap(_linkmap, _linkmap_yaml)
	_export_linkmap(_linkmap, _FLAGS_dry_run)
	return

def _clean_deprecated():
	candidates = [entry for entry in _linkmap if _tagged_as(entry, _TAG_DEPRECATED)
			and _path.exists(_to_local_path(entry))]

	if not candidates:
		_warn('No matched enties.')
		return

	_info('Removing deprecated files:')
	for candidate in candidates:
		_print_entry(sys.stderr, candidate)
		_remove_file(_to_local_path(candidate), _FLAGS_dry_run)
		_info()
	return

def _check_health():
	healthy = _check_no_duplicates(_linkmap)
	healthy &= _check_list_order(_linkmap)
	healthy &= _check_local_files(_linkmap)
	healthy &= _check_successor(_linkmap, _linkmap_table)
	print 'Healthy.' if healthy else 'See logs for potential problems.'
	return 0 if healthy else 1


# support functions
def _map_to_candidates(linkmap=None, linkmap_table=None, uuid=None, name=None, url=None,
		check_unique=True):
	assert uuid is not None or name is not None or url is not None

	if uuid is not None:
		if name is not None or url is not None:
			_warn('Ignores name or url when uuid is given.')
		return [linkmap_table[uuid]]

	candidates = sorted([entry for entry in linkmap if not _tagged_as(entry, _TAG_DEPRECATED)
				and (name is None or entry[_KEY_NAME] == name)
				and (url is None or entry[_KEY_URL] == url)],
			key=_get_date, reverse=True)

	if check_unique:
		assert candidates
		if len(candidates) > 1:
			_warn('Found %d candidates.', len(candidates))
	return candidates

def _build_link_yaml(entry):
	return 'uuid: %s\n' % (entry[_KEY_UUID])

def _check_no_duplicates(linkmap):
	duplicates_by_uuid = _duplicated_keys([(entry[_KEY_UUID], entry) for entry in linkmap])
	duplicates_by_id = _duplicated_keys([((entry[_KEY_NAME], entry[_KEY_URL]), entry)
			for entry in linkmap if not _tagged_as(entry, _TAG_DEPRECATED)])
	duplicates_by_name = _duplicated_keys([(entry[_KEY_NAME], entry) for entry in linkmap
			if not _tagged_as(entry, _TAG_DEPRECATED)])
	duplicates_by_url = _duplicated_keys([(entry[_KEY_URL], entry) for entry in linkmap
			if not _tagged_as(entry, _TAG_DEPRECATED)])

	if duplicates_by_uuid:
		_error('Found duplicated uuid:')
		for uuid in duplicates_by_uuid:
			_warn(uuid)
		_warn('')

	if duplicates_by_id:
		_warn('Found duplicated ids (name, url):')
		for name, url in duplicates_by_id:
			_warn('[%s]: %s', name, url)
		_warn('')

	if duplicates_by_name:
		_warn('Found duplicated names:')
		for name in duplicates_by_name:
			_warn(name)
		_warn('')

	if duplicates_by_url:
		_warn('Found duplicated url:')
		for url in duplicates_by_url:
			_warn(url)
		_warn('')
	return (not duplicates_by_uuid and not duplicates_by_id
			and not duplicates_by_name and not duplicates_by_url)

def _check_list_order(linkmap):
	max_date = None
	for entry in linkmap:
		date = _get_date(entry)
		if max_date is not None and max_date > date:
			_warn('Entries not in ascending order by date. First wrong placed entry:')
			_print_entry(sys.stderr, entry)
			return False
		max_date = date
	return True

def _check_local_files(linkmap):
	undownloaded = [entry for entry in linkmap if not _path.exists(_to_local_path(entry))
			and not _tagged_as(entry, _TAG_DEPRECATED)]
	uncleaned = [entry for entry in linkmap if _path.exists(_to_local_path(entry))
			and _tagged_as(entry, _TAG_DEPRECATED)]

	if undownloaded:
		_warn('Found non-deprecated entries with no local file:')
		for entry in undownloaded:
			_print_entry(sys.stderr, entry, print_local_path=False)
			_info()

	if uncleaned:
		_warn('Found deprecated entries with undeleted local file:')
		for entry in uncleaned:
			_print_entry(sys.stderr, entry)
			_info()
	return not undownloaded and not uncleaned

def _check_successor(linkmap, linkmap_table):
	# TODO (p5): cycular checking
	no_successor = []
	non_deprecated = []
	invalid_successor = []
	for entry in linkmap:
		deprecated = _tagged_as(entry, _TAG_DEPRECATED)
		has_successor = _KEY_SUCCESSOR in entry
		if deprecated != has_successor:
			if deprecated:
				no_successor.append(entry)
			else:
				non_deprecated.append(entry)
		if has_successor and entry[_KEY_SUCCESSOR] not in linkmap_table:
			invalid_successor.append(entry)
	if no_successor:
		_warn('Found deprecated entries with no successor:')
		for entry in no_successor:
			_print_entry(sys.stderr, entry, print_local_path=False)
			_info()

	if non_deprecated:
		_warn('Found non-deprecated entries has successor:')
		for entry in non_deprecated:
			_print_entry(sys.stderr, entry, print_local_path=False)
			_info()

	if invalid_successor:
		_warn('Found invalid successor:')
		for entry in invalid_successor:
			_print_entry(sys.stderr, entry, print_local_path=False)
			_info()
	return not no_successor and not non_deprecated and not invalid_successor


# linkmap utilities
def _load_linkmap():
	assert _path.exists(_LINKMAP_PATH)
	with open(_LINKMAP_PATH, 'r') as linkmap_yaml_file:
		linkmap_yaml = ''.join(linkmap_yaml_file.readlines())
		linkmap = _yaml.load(linkmap_yaml)
		if linkmap is None:
			_warn('Current linkmap is empty.')
			linkmap = []
		linkmap_table = {entry[_KEY_UUID]: entry for entry in linkmap}
		if len(linkmap_table) != len(linkmap):
			_warn('Has duplicate keys in linkmap.')
		return linkmap, linkmap_table, linkmap_yaml

def _diff_linkmap(linkmap, linkmap_yaml):
	# differ the original yaml text with current yaml object to see the changes
	_info('Diff linkmap.')

	new_linkmap_yaml = _format_linkmap(linkmap)
	for line in _diff.unified_diff(linkmap_yaml.split('\n'), new_linkmap_yaml.split('\n'),
			fromfile='before.yaml', tofile='after.yaml'):
		_info('%s', line.rstrip('\n'))
	return

def _export_linkmap(linkmap, dry_run):
	_info('Exporting linkmap.')

	new_linkmap_yaml = _format_linkmap(linkmap)
	_save_to_file(new_linkmap_yaml, _LINKMAP_PATH, dry_run)
	return


# linkmap formatter
DEFAULT_MAPPING_TAG = _yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
DEFAULT_SEQUENCE_TAG = _yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG
DEFAULT_SCALAR_TAG = _yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG

def _format_linkmap(linkmap):
	if not linkmap:
		_warn('Current linkmap is empty.')
		return ''

	# Supposed each map in linkmap is already OrderedMap, which is backed by
	# ordered_dict_representer() and _new_entry()
	for entry in linkmap:
		if _KEY_COMMENT in entry:
			entry[_KEY_COMMENT] = _LiteralUnicode(entry[_KEY_COMMENT])
		if _KEY_ALT_URLS in entry:
			entry[_KEY_ALT_URLS] = _BlockSeq(entry[_KEY_ALT_URLS])
	linkmap_yaml = _yaml.dump(linkmap, allow_unicode=True)
	return linkmap_yaml.replace('\n-', '\n\n-')

class _BlockSeq(list):
	pass

class _LiteralUnicode(unicode):
	pass

def ordered_dict_representer(dumper, data):
	return dumper.represent_mapping(DEFAULT_MAPPING_TAG, data.iteritems(), flow_style=False)

def ordered_dict_constructor(loader, node):
	return _col.OrderedDict(loader.construct_pairs(node))

def block_seq_representer(dumper, data):
	return dumper.represent_sequence(DEFAULT_SEQUENCE_TAG, data, flow_style=False)

def literal_unicode_representer(dumper, data):
	return dumper.represent_scalar(DEFAULT_SCALAR_TAG, data, style='|')

_yaml.Dumper.ignore_aliases = lambda *args : True # Disable aliases
_yaml.add_representer(_col.OrderedDict, ordered_dict_representer)
_yaml.add_constructor(DEFAULT_MAPPING_TAG, ordered_dict_constructor)
_yaml.add_representer(_BlockSeq, block_seq_representer)
_yaml.add_representer(_LiteralUnicode, literal_unicode_representer)


# file utilities
def _save_to_file(text, dest_path, dry_run):
	_info('Saving file to %s.', dest_path)

	dest_dir = _path.dirname(dest_path)
	if len(dest_dir) and not _path.exists(dest_dir):
		_error('Destination folder %s not exists.', dest_dir)
		assert False
	if _path.exists(dest_path):
		_warn('Destination %s already exists.', dest_path)

	if not dry_run:
		with open(dest_path, 'w') as dest_file:
			dest_file.write(text)
		_info('Done.')
	else:
		_info('Dry run mode.')
	return

def _copy_file(src_path, dest_path, dry_run):
	_info('Copying file from %s to %s.', src_path, dest_path)

	assert _path.exists(src_path)

	dest_dir = _path.dirname(dest_path)
	if len(dest_dir) and not _path.exists(dest_dir):
		_warn('Destination folder %s not exists.', dest_dir)
	if _path.exists(dest_path):
		_warn('Destination %s already exists.', dest_path)

	if not dry_run:
		_sp.call(['cp', src_path, dest_path])
		_info('Done.')
	else:
		_info('Dry run mode.')
	return

def _remove_file(path, dry_run):
	_info('Removing file %s.', path)
	assert _path.exists(path)

	if not dry_run:
		_sp.call(['rm', path])
		_info('Done.')
	else:
		_info('Dry run mode.')
	return

def _download_file(url, local_path, dry_run):
	_info('Downloading resource from %s to %s.', url, local_path)

	local_dir = _path.dirname(local_path)
	if len(local_dir) and not _path.exists(local_dir):
		if not dry_run:
			_warn('Creating Local dir %s.', local_dir)
			_sp.call(['mkdir', '-p', local_dir])
		else:
			_warn('Local dir %s not exists.', local_dir)

	if not dry_run:
		tmp_dir = _tf.mkdtemp(_TEMP_DIR_PREFIX)
		tmp_path = _path.join(tmp_dir, 'downloading')
		_info('Downloading to tmp file %s.', tmp_path)
		_sp.call(['wget', '-O', tmp_path, url])
		_sp.call(['mv', tmp_path, local_path])
		_sp.call(['rmdir', tmp_dir])
		_info('Done.')
	else:
		_info('Dry run mode.')
	return


# common utilities
def _genereate_uuid(linkmap_table):
	# TODO (p3): ut
	# Add retries to ensure no exception happend in no-dry_run mode
	for i in range(10):
		uuid = _b64.urlsafe_b64encode(_uuid.uuid4().bytes).rstrip('=\n')
		if uuid not in linkmap_table:
			return uuid
		_warn('Failed to generate unique uuid for %d times.' % (i + 1))
	assert False

def _today():
	return _dt.date.today()

def _name_from_url(url):
	_info('Infer name from url: %s.', url)
	path = _urlp.urlsplit(url).path
	name = _path.basename(path)
	_info('Raw name: %s.', name)
	name = _url.unquote(name)
	_info('Unquoted name: %s.', name)
	# TODO (p2): https://github.com/django/django/blob/master/django/utils/text.py
	_info('Sanitized name: %s.', name)
	return name

def _match(text, keyword, match_mode, case_sensitive):
	# TODO (p3): _match used for any commands with --name
	if match_mode == _MODE_EQUALS:
		return text == keyword if case_sensitive else text.lower() == keyword.lower()
	if match_mode == _MODE_CONTAINS:
		return (text.find(keyword) >= 0 if case_sensitive
				else text.lower().find(keyword.lower()) >= 0)
	if match_mode == _MODE_REGEX:
		return re.search(keyword, text, 0 if case_sensitive else re.IGNORECASE)
	_error('Not a valid match_mode: %s.', match_mode)
	assert False

def _match_any(text_list, keyword, match_mode, case_sensitive):
	for text in text_list:
		if _match(text, keyword, match_mode, case_sensitive):
			return True
	return False

def _duplicated_keys(pairs):
	dd = _col.defaultdict(list)
	for k, v in pairs:
		dd[k].append(v)
	return [k for k, v in dd.items() if len(v) > 1]


# entry utilities
def _to_local_path(entry):
	return '%s/%s/%s' % (
			_LINKHUB_PATH, _dt.datetime.strftime(_get_date(entry), _DATE_DIR_FORMAT),
			entry[_KEY_UUID])

def _get_date(entry):
	return entry[_KEY_DATE]

def _tagged_as(entry, tag):
	if _KEY_TAGS not in entry:
		_warn('Entry miss "tags" property. In UT?')
		return False
	return entry[_KEY_TAGS] is not None and tag in entry[_KEY_TAGS]

def _tag_as(entry, tag):
	if entry[_KEY_TAGS] is None:
		entry[_KEY_TAGS] = []
	if _tagged_as(entry, tag):
		_warn('Entry already has tag %s: %s', tag, entry)
	else:
		entry[_KEY_TAGS].append(tag)
	return

def _new_entry(rawlink, linkmap_table):
	entry = _col.OrderedDict([
			(_KEY_UUID, _genereate_uuid(linkmap_table)),
			(_KEY_NAME, rawlink[_KEY_NAME]),
			(_KEY_URL, rawlink[_KEY_URL]),
			(_KEY_DATE, _today()),
			(_KEY_TAGS, None)])
	if _KEY_AUTO in rawlink:
		_tag_as(entry, _TAG_AUTO)
	return entry

def _print_entry(fd, entry, print_local_path=False):
	entry = _col.OrderedDict(entry.items())
	if print_local_path:
		entry['local_path'] = _to_local_path(entry)
	print >> fd, _format_linkmap([entry])
	return


# logging utilities
def _info(msg='', *args):
	print >> sys.stderr, msg % args
	return

def _warn(msg, *args):
	print >> sys.stderr, 'WARN: %s' % (msg % args)
	return

def _error(msg, *args):
	print >> sys.stderr, 'ERROR: %s' % (msg % args)
	return


if __name__ == '__main__':
	global _linkmap_yaml # original yaml text
	global _linkmap # parsed linkmap entries
	global _linkmap_table # dict from uuid to entries

	parser = _arg.ArgumentParser(prog='lhub')
	parser.add_argument('-n', '--dry_run', help='Dry run mode.', action='store_true')

	subparsers = parser.add_subparsers(title='action')

	# find
	parser_find = subparsers.add_parser(
			'find', help='Finds map entries by matching attributes like url, name etc.'
			+ 'listed in date decrease order.')
	parser_find.add_argument('-k', '--name', help='name')
	parser_find.add_argument('-u', '--url', help='url')
	parser_find.add_argument('-m', '--match_mode', default=_MODE_CONTAINS,
			help='Search mode: match regex, whole string, substring (default).')
	parser_find.add_argument('-c', '--case_sensitive', action='store_true',
			help='Enable case sensitive in search (case insensitive by default).')
	parser_find.add_argument('-U', '--include_alt_urls', action='store_true',
			help='Include alt_urls as the url query search for, used with -u.')
	parser_find.add_argument('-d', '--include_deprecated', action='store_true',
			help='Include deprecated entries.')
	parser_find.set_defaults(action='find'); # action=find

	# load
	parser_load = subparsers.add_parser('load', help='Load rawinks and add new enties.')
	parser_load.add_argument('rawlinks_yaml_path', metavar='PATH', help='Path of rawlinks.yaml.')
	parser_load.add_argument('-o', '--override', action='store_true',
			help='Override existing files in case of auto downloading.')
	parser_load.set_defaults(action='load'); # action=load

	# map: id -> local url
	parser_map = subparsers.add_parser('map', help='Map entry to the location of local file.')
	parser_map.add_argument('-i', '--uuid', help='uuid')
	parser_map.add_argument('-k', '--name', help='name')
	parser_map.add_argument('-u', '--url', help='url')
	parser_map.add_argument('-c', '--check', action='store_true',
			help='Need to check if local file exists.')
	# TODO(p5): more friendly return for no candidte or 2+ candidates
	parser_map.set_defaults(action='map'); # action=map

	# link: id -> destination
	parser_link = subparsers.add_parser('ln', help='Make a link file to destination.')
	parser_link.add_argument('-i', '--uuid', help='uuid')
	parser_link.add_argument('-k', '--name', help='name')
	parser_link.add_argument('-u', '--url', help='url')
	parser_link.add_argument('dest_path', metavar='DEST', help='Destination path')
	parser_link.set_defaults(action='ln'); # action=link

	# readlink: link -> destination
	parser_readlink = subparsers.add_parser('readlink', help='Make a link file to destination.')
	parser_readlink.add_argument('link_path', metavar='LINK', help='Path of link file')
	parser_readlink.add_argument('-c', '--check', action='store_true',
			help='Need to check if local file exists.')
	# TODO(p0): read url option
	parser_readlink.set_defaults(action='readlink'); # action=link

	# copy: id -> destination
	parser_copy = subparsers.add_parser('cp', help='Make a copy to destination.')
	parser_copy.add_argument('-i', '--uuid', help='uuid')
	parser_copy.add_argument('-k', '--name', help='name')
	parser_copy.add_argument('-u', '--url', help='url')
	parser_copy.add_argument('dest_path', metavar='DEST', help='Destination path.')
	parser_copy.set_defaults(action='cp'); # action=cp

	# update: re-download by id
	parser_update = subparsers.add_parser('update', help='Re-download entry.')
	parser_update.add_argument('-i', '--uuid', help='uuid')
	parser_update.add_argument('-k', '--name', help='name')
	parser_update.add_argument('-u', '--url', help='url')
	parser_update.add_argument('-l', '--local', help='Local source')
	parser_update.set_defaults(action='update'); # action=update

	# deprecate
	parser_deprecate = subparsers.add_parser('gc', help='Deprecates duplicated entries.')
	parser_deprecate.add_argument('-k', '--name', help='name')
	parser_deprecate.add_argument('-u', '--url', help='url')
	parser_deprecate.set_defaults(action='gc'); # action=deprecate

	# clean
	parser_clean = subparsers.add_parser('clean', help='Clean files of deprecated items.')
	parser_clean.set_defaults(action='clean'); # action=clean

	# check
	parser_check = subparsers.add_parser('check', help='Check health of linkhub.')
	parser_check.set_defaults(action='check'); # action=check

	args = parser.parse_args();
	_linkmap, _linkmap_table, _linkmap_yaml = _load_linkmap()
	_FLAGS_dry_run = args.dry_run
	exit_code = 0
	if args.action == 'find':
		if args.include_alt_urls and args.url is None:
			_warn('Ignores --include_alt_urls when --url not specified.')
		exit_code = _find(
				args.name, args.url, args.match_mode, args.case_sensitive,
				args.include_alt_urls, args.include_deprecated)
	elif args.action == 'load':
		# import
		exit_code = _load_rawlinks(args.rawlinks_yaml_path, args.override)
	elif args.action == 'map':
		assert args.uuid is not None or args.name is not None or args.url is not None
		if args.uuid is not None and (args.name is not None or args.url is not None):
			_warn('Ignores --name and --url when --uuid is specified')
			args.name, args.url = None, None
		exit_code = _map_to_local(args.uuid, args.name, args.url, args.check)
	elif args.action == 'ln':
		# export
		assert args.uuid is not None or args.name is not None or args.url is not None
		if args.uuid is not None and (args.name is not None or args.url is not None):
			_warn('Ignores --name and --url when --uuid is specified')
			args.name, args.url = None, None
		exit_code = _make_link(args.uuid, args.name, args.url, args.dest_path)
	elif args.action == 'readlink':
		assert args.link_path is not None
		exit_code = _read_link(args.link_path, args.check)
	elif args.action == 'cp':
		# export
		assert args.uuid is not None or args.name is not None or args.url is not None
		if args.uuid is not None and (args.name is not None or args.url is not None):
			_warn('Ignores --name and --url when --uuid is specified')
			args.name, args.url = None, None
		exit_code = _make_copy(args.uuid, args.name, args.url, args.dest_path)
	elif args.action == 'update':
		# import
		# TODO (p4): update all (repair all)
		# TODO (p3): update by date
		assert args.uuid is not None or args.name is not None or args.url is not None
		if args.uuid is not None and (args.name is not None or args.url is not None):
			_warn('Ignores --name and --url when --uuid is specified')
			args.name, args.url = None, None
		if args.local is not None:
			exit_code = _update_from_local(args.uuid, args.name, args.url, args.local)
		else:
			exit_code = _update_from_url(args.uuid, args.name, args.url)
	elif args.action == 'gc':
		assert args.name is not None or args.url is not None
		exit_code = _deprecate_duplicates(args.name, args.url)
	elif args.action == 'clean':
		exit_code = _clean_deprecated()
	elif args.action == 'check':
		exit_code = _check_health()
	# TODO (p2): add uuid generation command for manually adding
	else:
		_error('Invalid action.')
		assert False
	sys.exit(exit_code)
	pass
