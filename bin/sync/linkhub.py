#!/usr/bin/python
# coding=ascii

# TODO: imports order
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
_KEY_NAME = 'name' # also used in rawlink
_KEY_URL = 'url' # also used in rawlink
_KEY_DATE = 'date'
_KEY_TAGS = 'tags'
# Optional entry properties
_KEY_COMMENT = 'comment'
_KEY_ALT_URLS = 'alt_urls'
# rawlink optional properties
_KEY_AUTO = 'auto'

# TODO: ? cleanup orphan files
# TODO: all properties have constant


# ops
# not suppose to be a general search tool, because one can search for linkmap file directly.
def _find(name, url, match_mode, include_alt_urls, include_deprecated):
	assert name is not None or url is not None
	candidates = sorted([entry for entry in _linkmap if
				(include_deprecated or not _tagged_as(entry, _TAG_DEPRECATED))
				and (name is None or _match(entry[_KEY_NAME], name, match_mode))
				and (url is None or _match(entry[_KEY_URL], url, match_mode)
					or (include_alt_urls
						and _KEY_ALT_URLS in entry
						and _match_any(entry[_KEY_ALT_URLS], url, match_mode)))],
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
				filename = _filename_from_url(rawlink[_KEY_URL])
				if filename:
					_warn('Infer filename from url: %s.', filename)
				else:
					_error('Infered filename is empty.')
					continue
				rawlink[_KEY_NAME] = filename

			candidates = _map_to_candidates(
					_linkmap, rawlink[_KEY_NAME], rawlink[_KEY_URL], check_unique=False)
			if candidates and candidates[0].date == _today():
				_info('Links alread added into linkmap, ignore current one.')
				entry = candidates[0]
			else:
				entry = _new_entry(rawlink)
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

def _map_to_local(name, url):
	candidate = _map_to_candidates(_linkmap, name, url)[0]
	_print_entry(sys.stderr, candidate)

	local_path = _to_local_path(candidate)
	assert _path.exists(local_path)
	print local_path
	return 0

def _make_link(name, url, dest_path):
	candidate = _map_to_candidates(_linkmap, name, url)[0]
	_info('Make link for entry:')
	_print_entry(sys.stderr, candidate)

	link_yaml = _build_link_yaml(name, url)
	_save_to_file(link_yaml, dest_path, _FLAGS_dry_run)
	return 0

def _make_copy(name, url, dest_path):
	candidate = _map_to_candidates(_linkmap, name, url)[0]
	_info('Make copy for entry:')
	_print_entry(sys.stderr, candidate)

	local_path = _to_local_path(candidate)
	_copy_to_file(local_path, dest_path, _FLAGS_dry_run)
	return 0

def _update_local(name, url):
	candidate = _map_to_candidates(_linkmap, name, url)[0]
	_print_entry(sys.stderr, candidate)

	if not _tagged_as(candidate, _TAG_AUTO):
		_error('Not automatically downloadable.')
		return 1

	local_path = _to_local_path(candidate)
	if not _path.exists(local_path):
		_warn('Original local file not exists.')

	_download_file(candidate.url, local_path, _FLAGS_dry_run)
	return 0

def _deprecate_duplicates(name, url):
	assert name is not None or url is not None
	candidates = _map_to_candidates(_linkmap, name, url, check_unique=False)

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

	_diff_linkmap(_linkmap, _linkmap_yaml)
	_export_linkmap(_linkmap, _FLAGS_dry_run)
	return

def _clean_deprecated():
	latest = None
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
	print 'Healty.' if healty else 'See logs for potential problems.'
	return 0 if healthy else 1


# support functions
def _map_to_candidates(linkmap, name, url, check_unique=True):
	assert name is not None or url is not None
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
	return 'name: %s\nurl: %s' % (entry[_KEY_NAME], entry[_KEY_URL])

def _check_no_duplicates(linkmap):
	duplicates_by_id = _duplicated_keys([((entry[_KEY_NAME], entry[_KEY_URL]), entry)
			for entry in linkmap if not _tagged_as(entry, _TAG_DEPRECATED)])
	duplicates_by_name = _duplicated_keys([(entry[_KEY_NAME], entry) for entry in linkmap
			if not _tagged_as(entry, _TAG_DEPRECATED)])
	duplicates_by_url = _duplicated_keys([(entry[_KEY_URL], entry) for entry in linkmap
			if not _tagged_as(entry, _TAG_DEPRECATED)])

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
	return not duplicates_by_id and not duplicates_by_name and not duplicates_by_url

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


# linkmap utilities
def _load_linkmap():
	assert _path.exists(_LINKMAP_PATH)
	with open(_LINKMAP_PATH, 'r') as linkmap_yaml_file:
		linkmap_yaml = ''.join(linkmap_yaml_file.readlines())
		linkmap = _yaml.load(linkmap_yaml)
		if linkmap is None:
			_warn('Current linkmap is empty.')
			linkmap = []
		return linkmap, linkmap_yaml

def _diff_linkmap(linkmap, linkmap_yaml):
	# differ the original yaml text with current yaml object to see the changes
	new_linkmap_yaml = _format_linkmap(linkmap)
	for line in _diff.unified_diff(linkmap_yaml.split('\n'), new_linkmap_yaml.split('\n'),
			fromfile='before.yaml', tofile='after.yaml'):
		_info(line.rstrip('\n'))
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

	if not _path.exists(_path.dirname(dest_path)):
		_error('Destination folder %s not exists.', _path.dirname(dest_path))
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

def _copy_to_file(src_path, dest_path, dry_run):
	_info('Copying file from %s to %s.', src_path, dest_path)

	assert _path.exists(src_path)
	if not _path.exists(_path.dirname(dest_path)):
		_warn('Destination folder %s not exists.', dest_path)
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
	if not _path.exists(local_dir):
		if not dry_run:
			_warn('Creating Local dir %s.', local_dir)
			_sp.call(['mkdir', '-p', local_dir])
		else:
			_warn('Local dir %s not exists.', local_dir)

	if not dry_run:
		tmp_dir = _tf.mkdtemp(_TEMP_DIR_PREFIX)
		tmp_path = _path.join(tmp_dir, 'downloading')
		_info('Downloading to tmp file %s.', tmp_path)
		_sp.call(['wget', '-o', tmp_path, url])
		_sp.call(['mv', tmp_path, local_path])
		_sp.call(['rmdir', tmp_dir])
		_info('Done.')
	else:
		_info('Dry run mode.')
	return


# common utilities
def _today():
	return _dt.date.today()

def _filename_from_url(url):
	_info('Infer file name from url: %s.', url)
	path = _urlp.urlsplit(url).path
	filename = _path.basename(path)
	_info('Raw file name: %s.', filename)
	filename = _url.unquote(filename)
	_info('Unquoted file name: %s.', filename)
	# TDOD: https://github.com/django/django/blob/master/django/utils/text.py
	_info('Sanitized file name: %s.', filename)
	return filename

def _match(text, keyword, match_mode):
	if match_mode == _MODE_EQUALS:
		return text == keyword
	if match_mode == _MODE_CONTAINS:
		return text.find(keyword) >= 0
	if match_mode == _MODE_REGEX:
		return re.match(keyword, text)
	_error('Not a valid match_mode: %s.', match_mode)
	assert False

def _match_any(text_list, keyword, match_mode):
	for text in text_list:
		if _match(text, keyword, match_mode):
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
			entry[_KEY_NAME])

def _get_date(entry):
	return entry[_KEY_DATE]

def _tagged_as(entry, tag):
	if _KEY_TAGS not in entry:
		_warn('Entry miss "tags" property.')
		return False
	return entry[_KEY_TAGS] and tag in entry[_KEY_TAGS]

def _tag_as(entry, tag):
	if entry[_KEY_TAGS] is None:
		entry[_KEY_TAGS] = []
	if _tagged_as(entry, tag):
		_warn('Entry already has tag %s: %s', tag, entry)
	else:
		entry[_KEY_TAGS].append(tag)
	return

def _new_entry(rawlink):
	entry = _col.OrderedDict([
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
	global _linkmap # parsed yaml object

	parser = argparse.ArgumentParser(prog='lhub');
	parser.add_argument('-n', '--dry_run', help='Dry run mode.', action='store_true');

	subparsers = parser.add_subparsers(title='action');

	# find
	parser_find = subparsers.add_parser(
			'find', help='Finds map entries by matching attributes like url, name etc.'
			+ 'listed in date decrease order');
	parser_find.add_argument('-a', '--name', nargs=1, help='name');
	parser_find.add_argument('-u', '--url', nargs=1, help='url');
	parser_find.add_argument('-m', '--mode', nargs=1,
			help='Search mode: match regex, substring, whole string (default)');
	parser_find.set_defaults(action='find'); # action=find

	# load
	parser_load = subparsers.add_parser(
			'load', help='Load and add new enties');

	# map: id -> local url
	parser_map

	# gc
	parser_gc

	args = parser.parse_args();
	{
		'status': cachefile_status_query,
		'agg': aggregate_update,
		'cache-commit': cache_commit_update,
		'restore': cache_restore_miss_update,
		'entryfile': entryfile_sync_update,
		'git-commit': git_commit_update,
	}[args.action](args);
