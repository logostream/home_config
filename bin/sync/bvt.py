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

def common_testpath_set(root_path):
	_common.REPO_BASE_PATH     = root_path;
	_common.REPO_CACHE_PATH    = _path.join(_common.REPO_BASE_PATH, 'cache/docs');
	_common.REPO_AGGSRC_PATH   = _path.join(_common.REPO_BASE_PATH, 'cache/copy');
	_common.REPO_GIT_PATH      = _path.join(_common.REPO_BASE_PATH, 'cache/github');
	_common.REPO_GITMAP_PATH   = _path.join(_common.REPO_BASE_PATH, 'cache/gitmap.log');
	_common.REPO_DATA_PATH     = _path.join(_common.REPO_BASE_PATH, 'data/docs');
	_common.REPO_ARCH_PATH     = _path.join(_common.REPO_BASE_PATH, 'arch');
	_common.REPO_TAGS_PATH     = _path.join(_common.REPO_BASE_PATH, 'tagged');
	_common.REPO_TMP_PATH      = _path.join(_common.REPO_BASE_PATH, 'tmp');
	_common.REPO_ENTRYFILE_PATH = _path.join(_common.REPO_BASE_PATH, 'data/indexes/entry.log');
	return;

def basic_verify(expected_root, got_root, rawlog):
	for logentry in rawlog:
		assert logentry.level != _common.LOGLEVEL_ERR;
	output = _sp.check_output(['rsync', '-rlpgoDvnc', '--delete', '--exclude', '/tagged*', '--exclude', '/cache/gitmap.log*', _path.join(expected_root, ''), _path.join(got_root, '')]);
	if len(output.splitlines()) != 4:
		print output;
		raise RuntimeError('basic_verify failed');
	for fconfig in ['tagged', 'tagged.new', 'cache/gitmap.log', 'cache/gitmap.log.new']:
		output = _sp.check_output(['sort_diff.sh', _path.join(expected_root, fconfig), _path.join(got_root, fconfig), '-u']);
		if len(output) > 0:
			raise RuntimeError('basic_verify failed');
	return;

def run_test(test_name, test_func, verify_func, logonly=True):
	test_home = _path.join(TESTCASES_HOME, test_name);
	test_before = _path.join(test_home, 'before');
	test_after = _path.join(test_home, 'after');
	test_root = _path.join(test_home, 'root');
	common_testpath_set(test_root);
	_common.REALTIME_LOGPATH = _path.join(test_home, 'realtime.log');

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

if __name__ == '__main__':
	push_pathenv();
	run_test('agg_basic', agg_test, basic_verify, logonly=False);
	run_test('restore_miss_basic', restore_miss_test, basic_verify, logonly=False);
	run_test('agg_over_cache', agg_test, basic_verify, logonly=False);
	run_test('agg_over_conflict', agg_test, basic_verify, logonly=False);
	run_test('commit_basic', commit_test, basic_verify, logonly=False);
	run_test('commit_rename_basic', commit_test, basic_verify, logonly=False);
	run_test('entryfile_sync_basic', entryfile_sync_test, basic_verify, logonly=False);
	run_test('entryfile_update_basic', entryfile_update_test, basic_verify, logonly=False);
	run_test('commit_rename_gitmap', commit_test, basic_verify, logonly=False); # test gitmap.log only
	pop_pathenv();

