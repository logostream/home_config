#!/usr/bin/python
# coding=utf-8

# TODO (style): import order
import sys
import datetime as _dt
import inspect as _isp
import linkhub as _lhub
import mock
import re
import yaml as _yaml
import unittest as _ut
import collections as _col
import os.path as _path

from mock import patch

# TODO (styles): return, <= 80 chars perline, indent

class _LinkhubTests(_ut.TestCase):
	# test _map_to_candidates
	def test_map_to_candidates_uuid(self):
		matched = {
			'uU_a' : {'uuid' : 'uU_a', 'date' : _dt.date(2012, 1, 2)},
		}
		unmatched = {
			'uU_ab' : {'uuid' : 'uU_ab'},
			'_uU_a' : {'uuid' : '_uU_a'}
		}

		self.assertEqual(matched.values(), _lhub._map_to_candidates(
					linkmap_table=dict(matched.items() + unmatched.items()),
					uuid='uU_a', check_unique=False))
		return

	def test_map_to_candidates_name(self):
		matched = [
			{'name' : 'a', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'a', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'c'}, {'name' : 'd'}
		]

		self.assertEqual(matched, _lhub._map_to_candidates(
					matched + unmatched, name='a', check_unique=False))
		return

	def test_map_to_candidates_url(self):
		matched = [
			{'url' : 'a', 'date' : _dt.date(2012, 1, 2)},
			{'url' : 'a', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'c'}, {'url' : 'd'}
		]

		self.assertEqual(matched, _lhub._map_to_candidates(
					matched + unmatched, url='a', check_unique=False))
		return

	def test_map_to_candidates_name_url(self):
		matched = [
			{'name' : 'a', 'url' : 'b', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'a', 'url' : 'b', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'b', 'url' : 'b'},
			{'name' : 'a', 'url' : 'a'},
			{'name' : 'b', 'url' : 'a'},
			{'name' : 'aa', 'url' : 'b'},
			{'name' : 'x', 'url' : 'y'},
		]

		self.assertEqual(matched, _lhub._map_to_candidates(
					matched + unmatched, name='a', url='b', check_unique=False))
		return

	def test_map_to_candidates_sort(self):
		matched = [
			{'name' : 'a', 'date' : _dt.date(2012, 1, 1)},
			{'name' : 'a', 'date' : _dt.date(2012, 1, 2)},
		]
		expected = [
			{'name' : 'a', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'a', 'date' : _dt.date(2012, 1, 1)},
		]

		self.assertEqual(expected, _lhub._map_to_candidates(
					matched, name='a', check_unique=False))
		return

	def test_map_to_candidates_deprecated(self):
		matched = [
			{'name' : 'a', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'a', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'a', 'tags' : ['deprecated']},
		]

		self.assertEqual(matched, _lhub._map_to_candidates(
					matched + unmatched, name='a', check_unique=False))
		return

	@patch('linkhub._warn')
	def test_map_to_candidates_check_unique(self, warn_mock):
		matched = [
			{'name' : 'a', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'a', 'date' : _dt.date(2012, 1, 1)},
		]

		self.assertEqual([matched[0]], _lhub._map_to_candidates(
					[matched[0]], name='a', check_unique=True))

		try:
			_lhub._map_to_candidates(matched, name='b', check_unique=True)
			raise RuntimeError('Expected AssertionError not happened.')
		except AssertionError:
			pass # expected

		_lhub._map_to_candidates(matched, name='a', check_unique=True)
		self.assertEqual(mock.call('Found %d candidates.', 2), warn_mock.call_args)
		return


	# test _build_link_yaml()
	def test_build_link_yaml(self):
		self.assertEqual('uuid: uU_a\n',
				_lhub._build_link_yaml({'uuid' : 'uU_a', 'name' : 'foo', 'url' : 'bar'}))
		return


	# test _check_no_duplicates():
	def test_check_no_duplicates(self):
		self.assertFalse(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_a', 'name' : 'c', 'url' : 'd'},
				]))

		self.assertFalse(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_b', 'name' : 'a', 'url' : 'c'},
				]))

		self.assertFalse(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'b', 'url' : 'a'},
				{'uuid' : 'uU_b', 'name' : 'c', 'url' : 'a'},
				]))

		self.assertFalse(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_b', 'name' : 'a', 'url' : 'b'},
				]))

		self.assertTrue(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_b', 'name' : 'c', 'url' : 'd'},
				]))
		return

	def test_check_no_duplicates_deprecated(self):
		self.assertFalse(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_a', 'name' : 'c', 'url' : 'd', 'tags' : ['depredated']},
				]))

		self.assertTrue(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_b', 'name' : 'a', 'url' : 'b', 'tags' : ['deprecated']},
				]))

		self.assertTrue(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'b', 'url' : 'a'},
				{'uuid' : 'uU_b', 'name' : 'c', 'url' : 'a', 'tags' : ['deprecated']},
				]))

		self.assertTrue(_lhub._check_no_duplicates([
				{'uuid' : 'uU_a', 'name' : 'a', 'url' : 'b'},
				{'uuid' : 'uU_b', 'name' : 'a', 'url' : 'b', 'tags' : ['deprecated']},
				]))
		return


	# test _check_list_order
	def test_check_list_order(self):
		self.assertTrue(_lhub._check_list_order([]))

		self.assertTrue(_lhub._check_list_order([
				{'date' : _dt.date(2012, 1, 1)},
				{'date' : _dt.date(2012, 1, 1)},
				{'date' : _dt.date(2012, 1, 2)},
				{'date' : _dt.date(2012, 1, 2)},
				]))

		self.assertFalse(_lhub._check_list_order([
				{'date' : _dt.date(2012, 1, 1)},
				{'date' : _dt.date(2012, 1, 2)},
				{'date' : _dt.date(2012, 1, 1)},
				]))
		return


	# test _check_local_files()
	@patch('os.path.exists')
	def test_check_local_files(self, exists_mock):
		exists_mock.side_effect = lambda(path): path.find('/uU_exists') >= 0

		self.assertTrue(_lhub._check_local_files([
				{'uuid' : 'uU_exists_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'tags' : ['deprecated']}
				]))

		self.assertFalse(_lhub._check_local_files([
				{'uuid' : 'uU_exists_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today()}
				]))

		self.assertFalse(_lhub._check_local_files([
				{'uuid' : 'uU_exists_a', 'date' : _dt.date.today(), 'tags' : ['deprecated']},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'tags' : ['deprecated']}
				]))

		self.assertFalse(_lhub._check_local_files([
				{'uuid' : 'uU_exists_a', 'date' : _dt.date.today(), 'tags' : ['deprecated']},
				{'uuid' : 'uU_b', 'date' : _dt.date.today()}
				]))
		return


	# test _check_successor()
	@patch('os.path.exists')
	def test_check_successor(self, exists_mock):
		self._load_context([
				{'uuid' : 'uU_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'tags' : ['deprecated']}
				])
		self.assertFalse(_lhub._check_successor(_lhub._linkmap, _lhub._linkmap_table))

		self._load_context([
				{'uuid' : 'uU_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'successor' : 'uU_a'}
				])
		self.assertFalse(_lhub._check_successor(_lhub._linkmap, _lhub._linkmap_table))

		self._load_context([
				{'uuid' : 'uU_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'tags' : ['deprecated'], 'successor' : 'uU_c'}
				])
		self.assertFalse(_lhub._check_successor(_lhub._linkmap, _lhub._linkmap_table))

		self._load_context([
				{'uuid' : 'uU_a', 'date' : _dt.date.today()},
				{'uuid' : 'uU_b', 'date' : _dt.date.today(), 'tags' : ['deprecated'], 'successor' : 'uU_a'}
				])
		self.assertTrue(_lhub._check_successor(_lhub._linkmap, _lhub._linkmap_table))
		return


	# test _load_linkmap()
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_linkmap_unicode(self, exists_mock, open_mock):
		yaml = """- uuid: uU_a
  name: Article Name
  url: http://article/url
  date: 2012-01-12
  tags: [deprecated, auto]
  comment: |-
    test the string
  alt_urls:
  - alternative url 1
  - alternative url 2

- uuid: uU_b
  name: Image Name
  url: http://image/url
  date: 2012-03-22
  tags: null

# Unicode test
- uuid: uU_c
  name: 中文
  url: http://www.example.com/path?key=value#foo
  date: 2012-03-23
  tags: # Same as null
  comment: |-
    道可道，非常道
"""
		self._mock_read_yaml_file(_lhub._LINKMAP_PATH, yaml, exists_mock, open_mock)

		linkmap, linkmap_table, linkmap_yaml = _lhub._load_linkmap()

		# Verify parsed object
		self.assertEqual(linkmap_yaml, yaml)
		self.assertEqual(linkmap[0]['uuid'], 'uU_a')
		self.assertEqual(linkmap[0]['name'], 'Article Name')
		self.assertEqual(linkmap[0]['url'], 'http://article/url')
		self.assertEqual(linkmap[0]['date'], _dt.date(2012, 01, 12))
		self.assertEqual(linkmap[0]['tags'], ['deprecated', 'auto'])
		self.assertEqual(linkmap[0]['comment'], u'test the string')
		self.assertEqual(linkmap[0]['alt_urls'], ['alternative url 1', 'alternative url 2'])

		self.assertEqual(linkmap[1]['uuid'], 'uU_b')
		self.assertEqual(linkmap[1]['name'], 'Image Name')
		self.assertEqual(linkmap[1]['url'], 'http://image/url')
		self.assertEqual(linkmap[1]['date'], _dt.date(2012, 03, 22))
		self.assertEqual(linkmap[1]['tags'], None)

		self.assertEqual(linkmap[2]['uuid'], 'uU_c')
		self.assertEqual(linkmap[2]['name'], u'中文')
		self.assertEqual(linkmap[2]['url'], 'http://www.example.com/path?key=value#foo')
		self.assertEqual(linkmap[2]['date'], _dt.date(2012, 03, 23))
		self.assertEqual(linkmap[2]['tags'], None)
		self.assertEqual(linkmap[2]['comment'], u'道可道，非常道')

		assert linkmap_table == {
			'uU_a': linkmap[0],
			'uU_b': linkmap[1],
			'uU_c': linkmap[2],
		}
		return

	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_linkmap_empty(self, exists_mock, open_mock):
		self._mock_read_yaml_file(_lhub._LINKMAP_PATH, '', exists_mock, open_mock)
		self.assertEqual(([], {}, ''), _lhub._load_linkmap())
		return


	# test _diff_linkmap()
	@patch('linkhub._info')
	def test_diff_linkmap_unicode(self, info_mock):
		linkmap_yaml = """- uuid: uU_a
  name: foo
  url: http://foo.com
  date: 2012-01-12
  tags: [deprecated, auto]
  comment: |-
    test the string
  alt_urls:
  - alternative url 1
  - alternative url 2
"""
		expected_info_calls = [
			mock.call('Diff linkmap.'),
			mock.call('%s', '--- before.yaml'),
			mock.call('%s', '+++ after.yaml'),
			mock.call('%s', '@@ -1,10 +1,10 @@'),
			mock.call('%s', ' - uuid: uU_a'),
			mock.call('%s', '-  name: foo'),
			mock.call('%s', '+  name: bar'),
			mock.call('%s', '   url: http://foo.com'),
			mock.call('%s', '   date: 2012-01-12'),
			mock.call('%s', '   tags: [deprecated, auto]'),
			mock.call('%s', '   comment: |-'),
			mock.call('%s', '-    test the string'),
			mock.call('%s', '+    test the string have 中文'),
			mock.call('%s', '   alt_urls:'),
			mock.call('%s', '   - alternative url 1'),
			mock.call('%s', '   - alternative url 2'),
		]

		linkmap = self._linkmap_from_str(linkmap_yaml)
		linkmap[0]['name'] = 'bar'
		linkmap[0]['comment'] += u' have 中文'

		_lhub._diff_linkmap(linkmap, linkmap_yaml)

		# verify
		self._verify_info_calls(info_mock, expected_info_calls)
		return

	@patch('linkhub._info')
	def test_diff_linkmap_nochange(self, info_mock):
		linkmap_yaml = """- uuid: uU_a
  name: foo
  url: http://foo.com
  date: 2012-01-12
  tags: [deprecated, auto]
  comment: |-
    test the string
  alt_urls:
  - alternative url 1
  - alternative url 2
"""
		expected_info_calls = [
			mock.call('Diff linkmap.'),
		]

		linkmap = self._linkmap_from_str(linkmap_yaml)
		_lhub._diff_linkmap(linkmap, linkmap_yaml)

		self._verify_info_calls(info_mock, expected_info_calls)
		return


	# test _export_linkmap()
	@patch('linkhub._save_to_file')
	def test_export_linkmap_unicode(self, save_to_file_mock):
		linkmap_yaml = """- uuid: uU_a
  name: Article Name
  url: http://article/url
  date: 2012-01-12
  tags: [deprecated, auto]
  comment: |-
    test the string
  alt_urls:
  - alternative url 1
  - alternative url 2

- uuid: uU_b
  name: Image Name
  url: http://image/url
  date: 2012-03-22
  tags: null

- uuid: uU_c
  name: 中文
  url: http://www.example.com/path?key=value#foo
  date: 2012-03-23
  tags: null
  comment: |-
    道可道，非常道
"""
		linkmap = self._linkmap_from_str(linkmap_yaml)
		_lhub._export_linkmap(linkmap, True)

		self.assertEqual(save_to_file_mock.call_args, mock.call(linkmap_yaml, _lhub._LINKMAP_PATH, True))


	# test _format_linkmap()
	def test_format_linkmap_entries_style(self):
		same_value = _dt.date(2016, 02, 28) # test not aliases
		linkmap = [
			_col.OrderedDict({'foo': same_value}), 
			_col.OrderedDict({'bar': same_value}),
			_col.OrderedDict({'baz': same_value}),
		]
		expected = '- foo: 2016-02-28\n\n- bar: 2016-02-28\n\n- baz: 2016-02-28\n'
		self.assertEqual(expected, _lhub._format_linkmap(linkmap))
		return

	def test_format_linkmap_roundtrip(self):
		# Covers cases of 'comment' style, 'alt_urls' style, long url, unicode, ordered dict
		linkmap_yaml = """- uuid: uU_a
  name: Article Name
  url: http://article/url
  date: 2012-01-12
  tags: [deprecated, auto]
  comment: |-
    test the string
  alt_urls:
  - alternative url 1
  - alternative url 2

- uuid: uU_b
  name: Image Name
  url: http://image/url?looooooooooooooooooooooooooooooooooooong=hashSDSVAEREWCWA#@#REWCAW2323tgerWEswe@#@FCWSVRHYERYH%^TR$4rq34
  date: 2012-03-22
  tags: null

- uuid: uU_c
  name: 中文
  url: http://www.example.com/path?key=value#foo
  date: 2012-03-23
  tags: null
  comment: |-
    道可道，非常道
"""
		linkmap = self._linkmap_from_str(linkmap_yaml)

		self.assertEqual(linkmap_yaml, _lhub._format_linkmap(linkmap))
		return


	# test _save_to_file()
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_save_to_file(self, exists_mock, open_mock):
		file_mock = self._mock_write_file('/path/of/save.txt', exists_mock, open_mock)

		_lhub._save_to_file('Wikipedia\n维基百科', '/path/of/save.txt', False)

		self.assertEqual(file_mock.write.call_args, mock.call('Wikipedia\n维基百科'))
		return

	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_save_to_file_override(self, exists_mock, open_mock):
		file_mock = self._mock_write_file('/path/of/save.txt', exists_mock, open_mock,
				exists_mode='file')

		_lhub._save_to_file('Wikipedia\n维基百科', '/path/of/save.txt', False)

		self.assertEqual(file_mock.write.call_args, mock.call('Wikipedia\n维基百科'))
		return

	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_save_to_file_no_dir(self, exists_mock, open_mock):
		file_mock = self._mock_write_file('/path/of/save.txt', exists_mock, open_mock,
				exists_mode='no_dir')

		try:
			_lhub._save_to_file('Wikipedia\n维基百科', '/path/of/save.txt', False)
			raise RuntimeError('Expected AssertionError not happened.')
		except AssertionError:
			pass # expected
		return

	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_save_to_file_to_pwd(self, exists_mock, open_mock):
		file_mock = self._mock_write_file('save.txt', exists_mock, open_mock)

		_lhub._save_to_file('Wikipedia\n维基百科', 'save.txt', False)

		self.assertEqual(file_mock.write.call_args, mock.call('Wikipedia\n维基百科'))
		return


	# test _copy_file()
	# TODO (p2): add case for dir_name == ''
	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_copy_file(self, exists_mock, call_mock):
		exists_mock.return_value = True

		_lhub._copy_file('src/file', 'dest/file', False)

		self.assertEqual(call_mock.call_args_list, [mock.call(['cp', 'src/file', 'dest/file'])])
		return

	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_copy_file_dry_run(self, exists_mock, call_mock):
		exists_mock.return_value = True

		_lhub._copy_file('src/file', 'dest/file', True)

		self.assertEqual(call_mock.call_args_list, [])
		return

	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_copy_file_to_pwd(self, exists_mock, call_mock):
		exists_mock.return_value = True

		_lhub._copy_file('src/file', 'dest_file', False)

		self.assertEqual(call_mock.call_args_list, [mock.call(['cp', 'src/file', 'dest_file'])])
		return


	# test _remove_file()
	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_remove_file(self, exists_mock, call_mock):
		exists_mock.return_value = True

		_lhub._remove_file('to/delete', False)

		self.assertEqual(call_mock.call_args_list, [mock.call(['rm', 'to/delete'])])
		return

	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_copy_file_dry_run(self, exists_mock, call_mock):
		exists_mock.return_value = True

		_lhub._remove_file('to/delete', True)

		self.assertEqual(call_mock.call_args_list, [])
		return


	# test _download_file()
	# TODO (p2): add case for dir_name == ''
	@patch('tempfile.mkdtemp')
	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_download_file_local_not_exists(self, exists_mock, call_mock, mkdtemp_mock):
		exists_mock.return_value = False
		mkdtemp_mock.return_value = '/tmp/linktmp123'

		_lhub._download_file('http://download.com', '/home/local/path', False)

		self.assertEqual(_lhub._TEMP_DIR_PREFIX, 'linktmp')
		self.assertEqual(mkdtemp_mock.call_args_list, [mock.call('linktmp')])
		self.assertEqual(call_mock.call_args_list, [
				mock.call(['mkdir', '-p', '/home/local']),
				mock.call(['wget', '-O', '/tmp/linktmp123/downloading', 'http://download.com']),
				mock.call(['mv', '/tmp/linktmp123/downloading', '/home/local/path']),
				mock.call(['rmdir', '/tmp/linktmp123']),
				])
		return

	@patch('tempfile.mkdtemp')
	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_download_file_local_exists(self, exists_mock, call_mock, mkdtemp_mock):
		exists_mock.return_value = True
		mkdtemp_mock.return_value = '/tmp/linktmp123'

		_lhub._download_file('http://download.com', '/home/local/path', False)

		self.assertEqual(_lhub._TEMP_DIR_PREFIX, 'linktmp')
		self.assertEqual(mkdtemp_mock.call_args_list, [mock.call('linktmp')])
		self.assertEqual(call_mock.call_args_list, [
				mock.call(['wget', '-O', '/tmp/linktmp123/downloading', 'http://download.com']),
				mock.call(['mv', '/tmp/linktmp123/downloading', '/home/local/path']),
				mock.call(['rmdir', '/tmp/linktmp123']),
				])
		return

	@patch('tempfile.mkdtemp')
	@patch('subprocess.call')
	@patch('os.path.exists')
	def test_download_file_dry_run(self, exists_mock, call_mock, mkdtemp_mock):
		exists_mock.return_value = False

		_lhub._download_file('http://download.com', 'local/path', True)

		self.assertEqual(mkdtemp_mock.call_args_list, [])
		self.assertEqual(call_mock.call_args_list, [])
		return


	# test _name_from_url()
	def test_name_from_url(self):
		# none
		self.assertTrue(_lhub._name_from_url('http://foo/') == '')

		# simple
		self.assertEqual(_lhub._name_from_url('http://foo/bar'), 'bar')

		# params
		self.assertEqual(_lhub._name_from_url('http://foo/bar?params'), 'bar')

		# anchor
		self.assertEqual(_lhub._name_from_url('http://foo/bar#title'), 'bar')

		# unquote url encoding
		self.assertEqual(_lhub._name_from_url('http://foo/%E9%9D%9E%E5%B8%B8%E9%81%93'), '非常道')
		return


	# test _match()
	def test_match_equals(self):
		self.assertTrue(_lhub._match('abcabc', 'abcabc', _lhub._MODE_EQUALS, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abc', _lhub._MODE_EQUALS, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abc.', _lhub._MODE_EQUALS, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abcd', _lhub._MODE_EQUALS, case_sensitive=True))
		return

	def test_match_contains(self):
		self.assertTrue(_lhub._match('abcabc', 'abcabc', _lhub._MODE_CONTAINS, case_sensitive=True))
		self.assertTrue(_lhub._match('abcabc', 'abc', _lhub._MODE_CONTAINS, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abc.', _lhub._MODE_CONTAINS, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abcd', _lhub._MODE_CONTAINS, case_sensitive=True))
		return

	def test_match_regex(self):
		self.assertTrue(_lhub._match('abcabc', 'abcabc', _lhub._MODE_REGEX, case_sensitive=True))
		self.assertTrue(_lhub._match('abcabc', 'abc', _lhub._MODE_REGEX, case_sensitive=True))
		self.assertTrue(_lhub._match('abcabc', '.ca.', _lhub._MODE_REGEX, case_sensitive=True))
		self.assertFalse(_lhub._match('abcabc', 'abcd', _lhub._MODE_REGEX, case_sensitive=True))
		return

	def test_match_equals_case_sensitive(self):
		self.assertTrue(_lhub._match('ABc', 'abC', _lhub._MODE_EQUALS, case_sensitive=False))
		self.assertFalse(_lhub._match('ABc', 'abC', _lhub._MODE_EQUALS, case_sensitive=True))
		return

	def test_match_contains_case_sensitive(self):
		self.assertTrue(_lhub._match('ABc', 'abC', _lhub._MODE_CONTAINS, case_sensitive=False))
		self.assertFalse(_lhub._match('ABc', 'abC', _lhub._MODE_CONTAINS, case_sensitive=True))
		return

	def test_match_regex_case_sensitive(self):
		self.assertTrue(_lhub._match('ABc', 'abC', _lhub._MODE_REGEX, case_sensitive=False))
		self.assertFalse(_lhub._match('ABc', 'abC', _lhub._MODE_REGEX, case_sensitive=True))
		return


	# test _match_any()
	def test_match_any(self):
		self.assertTrue(_lhub._match_any(['a', 'b', 'c'], 'a', _lhub._MODE_EQUALS,
					case_sensitive=True))
		self.assertFalse(_lhub._match_any(['a', 'b', 'c'], 'd', _lhub._MODE_EQUALS,
					case_sensitive=True))

		self.assertTrue(_lhub._match_any(['aa', 'bb', 'cc'], 'b', _lhub._MODE_CONTAINS,
					case_sensitive=True))
		self.assertFalse(_lhub._match_any(['aa', 'bb', 'cc'], 'd', _lhub._MODE_CONTAINS,
					case_sensitive=True))

		self.assertTrue(_lhub._match_any(['aa', 'bb', 'cc'], '[cd]', _lhub._MODE_REGEX,
					case_sensitive=True))
		self.assertFalse(_lhub._match_any(['aa', 'bb', 'cc'], '[ed]', _lhub._MODE_REGEX,
					case_sensitive=True))
		return

	def test_match_any_case_sensitive(self):
		self.assertTrue(_lhub._match_any(['a', 'b', 'c'], 'A', _lhub._MODE_EQUALS,
					case_sensitive=False))
		self.assertFalse(_lhub._match_any(['a', 'b', 'c'], 'A', _lhub._MODE_EQUALS,
					case_sensitive=True))
		self.assertFalse(_lhub._match_any(['a', 'b', 'c'], 'D', _lhub._MODE_EQUALS,
					case_sensitive=False))


	# test _duplicated_keys()
	def test_duplicated_keys(self):
		self.assertEqual(set(_lhub._duplicated_keys([
					('a', 1),
					('b', 2),
					('c', 3),
					('d', 4),
					('a', 5),
					('c', 6),
					('c', 6),
					('b', 2),
					('e', 1),
				])), set(['a', 'b', 'c']))
		return


	# test _to_local_path()
	def test_to_local_path(self):
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		self.assertEqual('/home/stream/linkhub/20120123/uU_a', _lhub._to_local_path({
					'uuid' : 'uU_a',
					'name' : 'article',
					'date' : _dt.date(2012, 01, 23)
				}))
		return


	# test _get_date()
	def test_get_date(self):
		self.assertEqual(_dt.date(2012, 01, 23), _lhub._get_date({
					'uuid' : 'uU_a',
					'name' : 'article',
					'date' : _dt.date(2012, 01, 23)
				}))
		return


	# test _tagged_as()
	def test_tagged_as(self):
		self.assertTrue(_lhub._tagged_as({'tags' : ['a', 'b', 'c']}, 'a'))
		self.assertTrue(_lhub._tagged_as({'tags' : ['a', 'b', 'c']}, 'c'))
		self.assertTrue(not _lhub._tagged_as({'tags' : ['a', 'b', 'c']}, 'd'))
		return


	# test _tagg_as()
	def test_tag_as(self):
		entry = {'tags': []}
		_lhub._tag_as(entry, 'a')
		_lhub._tag_as(entry, 'b')
		_lhub._tag_as(entry, 'c')
		_lhub._tag_as(entry, 'a')
		self.assertEqual(['a', 'b', 'c'], entry['tags'])
		return


	# test _new_entry()
	@patch('linkhub._genereate_uuid')
	def test_new_entry(self, generate_uuid_mock):
		generate_uuid_mock.return_value = 'uU_a'
		self.assertEqual(_col.OrderedDict([
					('uuid', 'uU_a'),
					('name', 'foo'),
					('url', 'http://bar'),
					('date', _dt.date.today()),
					('tags', None),
				]), _lhub._new_entry({
					'name' : 'foo',
					'url' : 'http://bar'
				}, {}))
		return

	@patch('linkhub._genereate_uuid')
	def test_new_entry_auto(self, generate_uuid_mock):
		generate_uuid_mock.return_value = 'uU_a'
		self.assertEqual(_col.OrderedDict([
					('uuid', 'uU_a'),
					('name', 'foo'),
					('url', 'http://bar'),
					('date', _dt.date.today()),
					('tags', ['auto']),
				]), _lhub._new_entry({
					'name' : 'foo',
					'url' : 'http://bar',
					'auto' : None
				}, {}))
		return


	# test _find()
	@patch('linkhub._print_entry')
	def test_find_name(self, print_entry_mock):
		matched = [
			{'name' : 'faf', 'date' : _dt.date(2012, 1, 3)},
			{'name' : 'ca', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'xc'}, {'name' : 'cxy'}, {'name' : 'dbd'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_name_case_sensitive(self, print_entry_mock):
		matched = [
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'ABC'}, {'name' : 'EFG'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_name_case_insensitive(self, print_entry_mock):
		matched = [
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'ABC', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'EFG'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=False, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_url(self, print_entry_mock):
		matched = [
			{'url' : 'faf', 'date' : _dt.date(2012, 1, 3)},
			{'url' : 'ca', 'date' : _dt.date(2012, 1, 2)},
			{'url' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'xc'}, {'url' : 'cxy'}, {'url' : 'dbd'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_url_case_sensitive(self, print_entry_mock):
		matched = [
			{'url' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'ABC'}, {'url' : 'EFG'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_url_case_insensitive(self, print_entry_mock):
		matched = [
			{'url' : 'abc', 'date' : _dt.date(2012, 1, 2)},
			{'url' : 'ABC', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'EFG'}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=False, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_name_url(self, print_entry_mock):
		matched = [
			{'name' : 'ca', 'url' : 'fb', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'abc', 'url' : 'bcd', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'abc', 'url' : 'acd'}, {'name' : 'cb', 'url' : 'fb'},
			{'name' : 'bd', 'url' : 'aa'}, {'name' : 'xy', 'url' : 'zz'},
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find('a', 'b', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_alt_urls(self, print_entry_mock):
		matched = [
			{'url' : 'xy', 'alt_urls' : ['ab', 'cd'], 'date' : _dt.date(2012, 1, 2)},
			{'url' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'xc'}, {'url' : 'cxy', 'alt_urls' : ['bb', 'dd']}
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=True,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_alt_urls_case_sensitive(self, print_entry_mock):
		matched = [
			{'url' : 'cd', 'alt_urls' : ['ab'], 'date' : _dt.date(2012, 1, 2)},
		]
		unmatched = [
			{'url' : 'cd', 'alt_urls' : ['AB']},
			{'url' : 'cd', 'alt_urls' : ['EF']},
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=True,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_alt_urls_case_insensitive(self, print_entry_mock):
		matched = [
			{'url' : 'cd', 'alt_urls' : ['ab'], 'date' : _dt.date(2012, 1, 2)},
			{'url' : 'cd', 'alt_urls' : ['AB'], 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'url' : 'cd', 'alt_urls' : ['EF']},
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find(None, 'a', _lhub._MODE_CONTAINS, case_sensitive=False, include_alt_urls=True,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_name_alt_urls(self, print_entry_mock):
		matched = [
			{'name' : 'cda', 'url' : '', 'alt_urls' : ['ab', 'cd'], 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'aa', 'url' : '', 'alt_urls' : ['bb', 'c'], 'date' : _dt.date(2012, 1, 1)},
		]
		unmatched = [
			{'name' : 'bb', 'url' : '', 'alt_urls' : ['aa', 'c']},
			{'name' : 'bb', 'url' : '', 'alt_urls' : ['bb', 'cd']},
			{'name' : 'aa', 'url' : '', 'alt_urls' : ['aa', 'cd']},
		]
		self._load_context(linkmap=(matched + unmatched), load_linkmap_table=False)

		_lhub._find('a', 'b', _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=True,
				include_deprecated=False)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)
		return

	@patch('linkhub._print_entry')
	def test_find_deprecate(self, print_entry_mock):
		matched = [
			{'name' : 'faf', 'date' : _dt.date(2012, 1, 3)},
			{'name' : 'ca', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		deprecated = [
			{'name' : 'abc', 'tags' : ['deprecated'], 'date' : _dt.date(2012, 1, 4)}
		]
		unmatched = [
			{'name' : 'xc'}, {'name' : 'cxy', 'tags' : ['deprecated']}
		]
		self._load_context(linkmap=(matched + deprecated + unmatched), load_linkmap_table=False)

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=False)
		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, matched)

		print_entry_mock.reset_mock()

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=True)
		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, deprecated + matched)
		return

	@patch('linkhub._print_entry')
	def test_find_sort(self, print_entry_mock):
		matched = [
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 1)},
			{'name' : 'ca', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'faf', 'date' : _dt.date(2012, 1, 3)},
		]
		expected = [
			{'name' : 'faf', 'date' : _dt.date(2012, 1, 3)},
			{'name' : 'ca', 'date' : _dt.date(2012, 1, 2)},
			{'name' : 'abc', 'date' : _dt.date(2012, 1, 1)},
		]
		self._load_context(linkmap=(matched), load_linkmap_table=False)

		_lhub._find('a', None, _lhub._MODE_CONTAINS, case_sensitive=True, include_alt_urls=False,
				include_deprecated=True)

		self._verify_print_entry_outputs(print_entry_mock, sys.stdout, expected)
		return


	# test _load_rawlinks()
	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_a', 'uU_b', 'uU_c'])
		rawlinks_yaml = """- name: foo
  url: http://foo
  auto:

- name: bar
  url: http://bar

- name: baz
  url: http://baz
  auto:
"""
		linkmap_yaml_before = ''
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [auto]

- uuid: uU_b
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: null

- uuid: uU_c
  name: baz
  url: http://baz
  date: 2012-12-01
  tags: [auto]
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			mock.call('http://foo', '/home/stream/linkhub/20121201/uU_a', True),
			mock.call('http://baz', '/home/stream/linkhub/20121201/uU_c', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', False)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return

	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks_miss_name(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_a', 'uU_b'])
		rawlinks_yaml = """- url: http://go/foo
  auto:

- url: http://go/bar
"""
		linkmap_yaml_before = ''
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://go/foo
  date: 2012-12-01
  tags: [auto]

- uuid: uU_b
  name: bar
  url: http://go/bar
  date: 2012-12-01
  tags: null
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			mock.call('http://go/foo', '/home/stream/linkhub/20121201/uU_a', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', False)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return

	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks_no_duplicate(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_a', 'uU_b'])
		rawlinks_yaml = """- name: foo
  url: http://foo
  auto:

- name: bar
  url: http://bar
"""
		linkmap_yaml_before = """- uuid: uU_0
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [deprecated]
"""
		linkmap_yaml_after = """- uuid: uU_0
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [deprecated]

- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [auto]

- uuid: uU_b
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: null
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			mock.call('http://foo', '/home/stream/linkhub/20121201/uU_a', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', False)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return

	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks_duplicate(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_a'])
		rawlinks_yaml = """- name: foo
  url: http://foo

- name: bar
  url: http://bar
  auto:
"""
		linkmap_yaml_before = """- uuid: uU_0
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [auto]
"""
		linkmap_yaml_after = """- uuid: uU_0
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [auto]

- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: null
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			# Will still try downloading the file
			mock.call('http://bar', '/home/stream/linkhub/20121201/uU_0', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', False)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return

	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks_not_override(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_exists_a', 'uU_b'])
		rawlinks_yaml = """- name: foo
  url: http://foo
  auto:

- name: bar
  url: http://bar
  auto:
"""
		linkmap_yaml_before = ''
		linkmap_yaml_after = """- uuid: uU_exists_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [auto]

- uuid: uU_b
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [auto]
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			mock.call('http://bar', '/home/stream/linkhub/20121201/uU_b', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		exists_mock.side_effect = lambda(path): path.find('uU_exists') >= 0
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', False)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return

	@patch('linkhub._genereate_uuid')
	@patch('linkhub._today')
	@patch('linkhub._download_file')
	@patch('linkhub._export_linkmap')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_load_rawlinks_override(
			self, exists_mock, open_mock, export_linkmap_mock, download_file_mock, today_mock,
			generate_uuid_mock):
		generate_uuid_mock.side_effect = iter(['uU_exists_a', 'uU_b'])
		rawlinks_yaml = """- name: foo
  url: http://foo
  auto:

- name: bar
  url: http://bar
  auto:
"""
		linkmap_yaml_before = ''
		linkmap_yaml_after = """- uuid: uU_exists_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [auto]

- uuid: uU_b
  name: bar
  url: http://bar
  date: 2012-12-01
  tags: [auto]
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			# Will still try downloading the file
			mock.call('http://foo', '/home/stream/linkhub/20121201/uU_exists_a', True),
			mock.call('http://bar', '/home/stream/linkhub/20121201/uU_b', True),
		]
		today_mock.return_value = _dt.date(2012, 12, 1)
		exists_mock.side_effect = lambda(path): path.find('uU_exists') >= 0
		self._mock_read_yaml_file('/path/of/rawlinks.yaml', rawlinks_yaml, exists_mock, open_mock)
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._load_rawlinks('/path/of/rawlinks.yaml', True)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		self._verify_download_file_calls(download_file_mock, expected_calls)
		return


	# test _map_to_local()
	@patch('linkhub._to_local_path')
	@patch('os.path.exists')
	def test_map_to_local_not_check(self, exists_mock, to_local_path_mock):
		candidate = {'uuid' : 'uU_a'}
		self._load_context(linkmap=[candidate])
		exists_mock.return_value = True

		_lhub._map_to_local(uuid='uU_a', check=False)

		self.assertTrue(to_local_path_mock.call_args, mock.call(candidate))
		exists_mock.assert_not_called()
		return

	@patch('linkhub._to_local_path')
	@patch('os.path.exists')
	def test_map_to_local_check(self, exists_mock, to_local_path_mock):
		candidate = {'uuid' : 'uU_a'}
		self._load_context(linkmap=[candidate])
		exists_mock.return_value = True
		to_local_path_mock.return_value = '/mock/local/path'

		_lhub._map_to_local(uuid='uU_a', check=True)

		self.assertTrue(to_local_path_mock.call_args, mock.call(candidate))
		exists_mock.assert_any_call('/mock/local/path')
		return


	# test _make_link()
	@patch('linkhub._save_to_file')
	def test_make_link(self, save_to_file_mock):
		candidate = {'uuid' : 'uU_a'}
		self._load_context(linkmap=[candidate])

		_lhub._make_link('uU_a', None, None, '/dest/path')

		self.assertTrue(save_to_file_mock.call_args, mock.call(
					'uuid: uU_a\n', '/dest/path', True))
		return


	# test _read_link()
	@patch('linkhub._map_to_local')
	@patch('__builtin__.open')
	@patch('os.path.exists')
	def test_read_link(self, exists_mock, open_mock, map_to_local_mock):
		link_yaml = """uuid: uU_a\n"""
		self._mock_read_yaml_file('/path/to/link.ln', link_yaml, exists_mock, open_mock)

		_lhub._read_link('/path/to/link.ln', True)

		self.assertEqual(map_to_local_mock.call_args, mock.call(uuid='uU_a', check=True))
		return


	# test _make_copy()
	@patch('linkhub._copy_file')
	def test_make_copy(self, make_copy_mock):
		candidate = {'uuid' : 'uU_a', 'date' : _dt.date(2012, 1, 3)}
		self._load_context(linkmap=[candidate])

		_lhub._make_copy('uU_a', None, None, '/dest/path')

		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		self.assertEqual(make_copy_mock.call_args, mock.call(
					'/home/stream/linkhub/20120103/uU_a', '/dest/path', True))
		return


	# test _update_from_url()
	@patch('linkhub._download_file')
	def test_update_from_url_auto(self, download_file_mock):
		candidate = {
			'uuid' : 'uU_a',
			'url' : 'http://foo',
			'date' : _dt.date(2012, 1, 3),
		}
		self._load_context(linkmap=[candidate])

		self.assertEqual(0, _lhub._update_from_url('uU_a', None, None))

		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		self.assertEqual(download_file_mock.call_args, mock.call(
					'http://foo', '/home/stream/linkhub/20120103/uU_a', True))
		return

	@patch('linkhub._download_file')
	def test_update_from_url_not_auto(self, download_file_mock):
		candidate = {
			'uuid' : 'uU_a',
			'url' : 'http://foo',
			'date' : _dt.date(2012, 1, 3),
		}
		self._load_context(linkmap=[candidate])

		self.assertEqual(1, _lhub._update_from_url('uU_a', None, None))

		download_file_mock.assert_not_called()
		return

	# test _update_from_local()
	@patch('linkhub._copy_file')
	@patch('os.path.exists')
	def test_update_from_url_auto(self, exists_mock, copy_file_mock):
		candidate = {
			'uuid' : 'uU_a',
			'url' : 'http://foo',
			'date' : _dt.date(2012, 1, 3),
		}
		self._load_context(linkmap=[candidate])
		exists_mock.return_value = True

		self.assertEqual(0, _lhub._update_from_local('uU_a', None, None, '/local/source/path'))

		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		self.assertEqual(copy_file_mock.call_args, mock.call(
					'/local/source/path', '/home/stream/linkhub/20120103/uU_a', True))
		return


	# test _deprecate_duplicates()
	@patch('linkhub._export_linkmap')
	def test_deprecate_duplicates_name(self, export_linkmap_mock):
		linkmap_yaml_before = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: null

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: null

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated]
  successor: uU_d

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: [deprecated]
  successor: uU_d

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: null

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._deprecate_duplicates('foo', None)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)

	@patch('linkhub._export_linkmap')
	def test_deprecate_duplicates_url(self, export_linkmap_mock):
		linkmap_yaml_before = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: null

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: null

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated]
  successor: uU_d

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: [deprecated]
  successor: uU_d

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._deprecate_duplicates(None, 'http://foo')

		self._verify_linkmap_by_yaml(linkmap_yaml_after)

	@patch('linkhub._export_linkmap')
	def test_deprecate_duplicates_name_url(self, export_linkmap_mock):
		linkmap_yaml_before = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: null

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: null

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated]
  successor: uU_d

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: bar
  url: http://foo
  date: 2012-12-03
  tags: null

- uuid: uU_d
  name: foo
  url: http://foo
  date: 2012-12-04
  tags: null

- uuid: uU_e
  name: bar
  url: http://bar
  date: 2012-12-05
  tags: null
"""
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._deprecate_duplicates('foo', 'http://foo')

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		return

	@patch('linkhub._export_linkmap')
	def test_deprecate_duplicates_deprecated(self, export_linkmap_mock):
		linkmap_yaml_before = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated, auto]
  successor: uU_b

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: null

- uuid: uU_c
  name: foo
  url: http://baz
  date: 2012-12-03
  tags: null
"""
		linkmap_yaml_after = """- uuid: uU_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated, auto]
  successor: uU_b

- uuid: uU_b
  name: foo
  url: http://bar
  date: 2012-12-02
  tags: [deprecated]
  successor: uU_c

- uuid: uU_c
  name: foo
  url: http://baz
  date: 2012-12-03
  tags: null
"""
		self._load_context(linkmap_yaml=linkmap_yaml_before)

		_lhub._deprecate_duplicates('foo', None)

		self._verify_linkmap_by_yaml(linkmap_yaml_after)
		return


	# test _clean_deprecated()
	@patch('linkhub._remove_file')
	@patch('os.path.exists')
	def test_clean_deprecated(self, exists_mock, remove_file_mock):
		linkmap_yaml = """- uuid: uU_exists_a
  name: foo
  url: http://foo
  date: 2012-12-01
  tags: [deprecated, auto]

- uuid: uU_b
  name: bar
  url: http://bar
  date: 2012-12-02
  tags: [deprecated]

- uuid: uU_c
  name: baz
  url: http://baz
  date: 2012-12-03
  tags: null

- uuid: uU_exists_d
  name: bac
  url: http://bac
  date: 2012-12-04
  tags: [deprecated]
"""
		self.assertEqual(_lhub._LINKHUB_PATH, '/home/stream/linkhub')
		expected_calls = [
			mock.call('/home/stream/linkhub/20121201/uU_exists_a', True),
			mock.call('/home/stream/linkhub/20121204/uU_exists_d', True),
		]
		exists_mock.side_effect = lambda(path): path.find('uU_exists') >= 0
		self._load_context(linkmap_yaml=linkmap_yaml)

		_lhub._clean_deprecated()

		self._verify_remove_file_calls(remove_file_mock, expected_calls)
		return


	# test _check_health()
	# TODO (p2): add cases


	# test utilities
	def _linkmap_from_str(self, yaml):
		linkmap = _yaml.load(yaml)
		return linkmap if linkmap is not None else []

	def _load_context(self, linkmap=None, linkmap_yaml=None, load_linkmap_table=True):
		# TODO: mock _linkmap_table
		self.assertTrue(linkmap is not None or linkmap_yaml is not None)
		_lhub._FLAGS_dry_run = True
		if linkmap is not None:
			_lhub._linkmap_yaml = _lhub._format_linkmap(linkmap)
			_lhub._linkmap = linkmap
		if linkmap_yaml is not None:
			_lhub._linkmap_yaml = linkmap_yaml
			_lhub._linkmap = self._linkmap_from_str(linkmap_yaml)
		if load_linkmap_table:
			_lhub._linkmap_table = {entry[_lhub._KEY_UUID]: entry for entry in _lhub._linkmap}
		return

	def _mock_read_yaml_file(self, path, yaml, exists_mock, open_mock):
		self._add_exists_path_to_mock(exists_mock, path)
		file_mock = mock.MagicMock()
		file_mock.__enter__.return_value = file_mock
		file_mock.__exit__.return_value = None
		if yaml:
			assert yaml[-1] == '\n' # Simply assume all file contains tailing eol
			file_mock.readlines.return_value = [line + '\n' for line in yaml[:-1].split('\n')]
		else:
			file_mock.readlines.return_value = []
		open_mock.return_value = file_mock
		return

	def _mock_write_file(self, path, exists_mock, open_mock, exists_mode='dir'):
		# exists_mode includes: dir (parent dir exists), file (both file and parent dir exists),
		# no_dir (even parent not exists)
		assert exists_mode in ['file', 'dir', 'no_dir']
		exists_mock.side_effect = lambda(p): False
		if exists_mode == 'file' or exists_mode == 'dir':
			self._add_exists_path_to_mock(exists_mock, _path.dirname(path))
		if exists_mode == 'file':
			self._add_exists_path_to_mock(exists_mock, path)
		file_mock = mock.MagicMock()
		file_mock.__enter__.return_value = file_mock
		file_mock.__exit__.return_value = None
		open_mock.return_value = file_mock
		return file_mock  # To verify the writing args

	def _verify_info_calls(self, info_mock, expected_calls):
		_info('Expected: %s', expected_calls)
		_info('Actual: %s', info_mock.call_args_list)

		self.assertEqual(len(expected_calls), len(info_mock.call_args_list))
		for call, expected_call in zip(info_mock.call_args_list, expected_calls):
			self.assertEqual(expected_call, call)
		return

	def _verify_print_entry_outputs(self, print_entry_mock, fd, expected_entries):
		_info('Expected: %s', expected_entries)
		_info('Actual: %s', print_entry_mock.call_args_list)

		self.assertEqual(len(expected_entries), len(print_entry_mock.call_args_list))
		for call_args, entry in zip(print_entry_mock.call_args_list, expected_entries):
			self.assertEqual(mock.call(fd, entry), call_args)
		return

	def _verify_download_file_calls(self, download_file_mock, expected_calls):
		_info('Expected: %s', expected_calls)
		_info('Actual: %s', download_file_mock.call_args_list)

		self.assertEqual(len(expected_calls), len(download_file_mock.call_args_list))
		for call_args, expected_call_args in zip(download_file_mock.call_args_list, expected_calls):
			self.assertEqual(expected_call_args, call_args)
		return

	def _verify_remove_file_calls(self, remove_file_mock, expected_calls):
		_info('Expected: %s', expected_calls)
		_info('Actual: %s', remove_file_mock.call_args_list)

		self.assertEqual(len(expected_calls), len(remove_file_mock.call_args_list))
		for call_args, expected_call_args in zip(remove_file_mock.call_args_list, expected_calls):
			self.assertEqual(expected_call_args, call_args)
		return

	def _verify_linkmap_by_yaml(self, expected_yaml, linkmap=None):
		if linkmap == None:
			linkmap = _lhub._linkmap
		self.assertEqual(expected_yaml, _lhub._format_linkmap(linkmap))

	def _add_exists_path_to_mock(self, exists_mock, path):
		fun = lambda(p): False
		if exists_mock.side_effect is not None:
			fun = exists_mock.side_effect
		def wrapper(p):
			return path == p or fun(p)
		exists_mock.side_effect = wrapper
		return

def _info(msg, args):
	print >> sys.stderr, msg % args

if __name__ == '__main__':
	_ut.main(failfast=True)
