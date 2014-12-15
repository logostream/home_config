import common_def as _common;
import agg_ops as _agg;
import os;
import os.path as _path;
import subprocess as _sp;
import functools as _func;
import cache_ops as _cache;
import data_ops as _data;
import git_ops as _git;

TESTCASES_HOME = '/home/stream/tmp/testcases';
g_pathenv = None;

def push_pathenv():
	global g_pathenv;
	if g_pathenv is None:
		g_pathenv = os.environ['PATH'];
		os.environ['PATH']+=':' + _path.dirname(_common.__file__);
	return;

def pop_pathenv():
	global g_pathenv;
	if not g_pathenv is None:
		os.environ['PATH'] = g_pathenv;
	return;

def common_testpath_set(test_home):
	test_root = _path.join(test_home, 'root');
	_common.commonpath_set(test_root);
	_common.REALTIME_LOGPATH = _path.join(test_home, 'realtime.log');
	return;

def basic_verify(expected_root, got_root, rawlog):
	for logentry in rawlog:
		assert logentry.level != _common.LOGLEVEL_ERR;
	output = _sp.check_output(['rsync', '-rlpgoDvnc', '--checksum', '--delete', '--exclude', '/cache/tagged*', '--exclude', '/cache/gitmap.log*', _path.join(expected_root, ''), _path.join(got_root, '')]);
	if len(output.splitlines()) != 4:
		print output;
		raise RuntimeError('basic_verify failed');
	for fconfig in ['cache/tagged', 'cache/tagged.new', 'cache/gitmap.log', 'cache/gitmap.log.new']:
		output = _sp.check_output(['sort_diff.sh', _path.join(expected_root, fconfig), _path.join(got_root, fconfig), '-u']);
		if len(output) > 0:
			raise RuntimeError('basic_verify failed');
	return;

def run_test(test_name, test_func, verify_func, logonly=True):
	test_home = _path.join(TESTCASES_HOME, test_name);
	test_before = _path.join(test_home, 'before');
	test_after = _path.join(test_home, 'after');
	test_root = _path.join(test_home, 'root');
	common_testpath_set(test_home);

	_sp.check_output(['rm', '-r', test_root]);
	_sp.check_output(['cp', '-r', test_before, test_root]);

	_common.LogEntry.open_realtime_log();
	_common.loadtags();
	_common.gitmap_load();
	_common.gitmap_check();
	rawlog = test_func(logonly=logonly);
	if not logonly:
		_git.gitmap_update(rawlog);
	_common.gitmap_check();
	_common.gitmap_dump();
	_common.dumptags();
	_common.LogEntry.close_realtime_log();

	if not logonly:
		verify_func(test_after, test_root, rawlog);
	return rawlog;

def agg_test(logonly):
	return _agg.aggregate_update(_common.REPO_AGGSRC_PATH, logonly);

def restore_miss_test(logonly):
	return _cache.restore_miss_update(_common.REPO_CACHE_PATH, _common.REPO_DATA_PATH, logonly);

def commit_test(logonly):
	return _cache.commit_update(_common.REPO_CACHE_PATH, logonly);

def entryfile_sync_test(logonly):
	_common.load_entryfile();
	_data.entryfile_sync(_common.REPO_DATA_PATH);
	_common.dump_entryfile();
	return [];

def entryfile_update_test(logonly):
	_common.load_entryfile();
	_data.entryfile_sync(_common.REPO_DATA_PATH);
	rawlog = _cache.commit_update(_common.REPO_CACHE_PATH, logonly);
	_data.entryfile_update(rawlog);
	_common.dump_entryfile();
	return rawlog;

def cache_status_test(logonly):
	cache_path_cases = {
		'clean.log': {
			'status': _common.STATEFLAG_CLEAN,
			'ancestor': 'clean.log',
		},
		'clean.d': {
			'status': _common.STATEFLAG_CLEAN,
			'ancestor': 'clean.d',
		},
		'conflict.log': {
			'status': _common.STATEFLAG_CONFLICT,
			'ancestor': 'conflict.log',
		},
		'conflict.d': {
			'status': _common.STATEFLAG_CONFLICT,
			'ancestor': 'conflict.d',
		},
		'renamed.log': {
			'status': _common.STATEFLAG_RENAMED,
			'ancestor': 'renamed.log',
		},
		'renamed.d': {
			'status': _common.STATEFLAG_RENAMED,
			'ancestor': 'renamed.d',
		},
		'miss.log': {
			'status': _common.STATEFLAG_MISS,
			'ancestor': None,
		},
		'delay.log': {
			'status': _common.STATEFLAG_DELAY,
			'ancestor': 'delay.log',
		},
		'delay.d': {
			'status': _common.STATEFLAG_DELAY,
			'ancestor': 'delay.d',
		},
		'ready.log': {
			'status': _common.STATEFLAG_READY,
			'ancestor': 'ready.log',
		},
		'ready.d': {
			'status': _common.STATEFLAG_READY,
			'ancestor': 'ready.d',
		},
		'untracted.log': {
			'status': _common.STATEFLAG_UNTRACTED,
			'ancestor': None,
		},
		'untracted.d': {
			'status': _common.STATEFLAG_UNTRACTED,
			'ancestor': None,
		},

		'clean.d/miss.log': {
			'status': _common.STATEFLAG_CLEAN | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL,
			'ancestor': 'clean.d',
		},
		'clean.d/partial.log': {
			'status': _common.STATEFLAG_CLEAN | _common.STATEFLAG_PARTIAL,
			'ancestor': 'clean.d',
		},

		'conflict.d/miss.log': {
			'status': _common.STATEFLAG_CONFLICT | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL,
			'ancestor': 'conflict.d',
		},
		'conflict.d/partial.log': {
			'status': _common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL,
			'ancestor': 'conflict.d',
		},
		'conflict.d/new.log': {
			'status': _common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL,
			'ancestor': 'conflict.d',
		},
		'conflict.d/hit.log': {
			'status': _common.STATEFLAG_CONFLICT,
			'ancestor': 'conflict.d',
		},

		'renamed.d/miss.log': {
			'status': _common.STATEFLAG_RENAMED | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL,
			'ancestor': 'renamed.d',
		},
		'renamed.d/partial.log': {
			'status': _common.STATEFLAG_RENAMED | _common.STATEFLAG_PARTIAL,
			'ancestor': 'renamed.d',
		},

		'delay.d/miss.log': {
			'status': _common.STATEFLAG_DELAY | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL,
			'ancestor': 'delay.d',
		},
		'delay.d/partial.log': {
			'status': _common.STATEFLAG_DELAY | _common.STATEFLAG_PARTIAL,
			'ancestor': 'delay.d',
		},

		'ready.d/miss.log': {
			'status': _common.STATEFLAG_READY | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL,
			'ancestor': 'ready.d',
		},
		'ready.d/partial.log': {
			'status': _common.STATEFLAG_READY | _common.STATEFLAG_PARTIAL,
			'ancestor': 'ready.d',
		},

		'': {
			'status': _common.STATEFLAG_NULL,
			'ancestor': None,
		},
	};

	for path, expected in cache_path_cases.iteritems():
		cache_path = _path.join(_common.REPO_CACHE_PATH, path);
		status, ancestor = _cache.status_check(cache_path);
		assert status == expected['status'];
		assert ancestor == None if expected['ancestor'] is None else _path.join(_common.REPO_CACHE_PATH, expected['ancestor']);
	return [];

if __name__ == '__main__':
	push_pathenv();
	logonly = False;
	run_test('agg_basic', agg_test, basic_verify, logonly=logonly);
	run_test('restore_miss_basic', restore_miss_test, basic_verify, logonly=logonly);
	run_test('agg_over_cache', agg_test, basic_verify, logonly=logonly);
	run_test('agg_over_conflict', agg_test, basic_verify, logonly=logonly);
	run_test('commit_basic', commit_test, basic_verify, logonly=logonly);
	run_test('commit_rename_basic', commit_test, basic_verify, logonly=logonly);
	run_test('entryfile_sync_basic', entryfile_sync_test, basic_verify, logonly=logonly);
	run_test('entryfile_update_basic', entryfile_update_test, basic_verify, logonly=logonly);
	run_test('commit_rename_gitmap', commit_test, basic_verify, logonly=logonly); # test gitmap.log only
	run_test('cache_status', cache_status_test, basic_verify, logonly=logonly);
	pop_pathenv();

