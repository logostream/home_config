import common_def as _common;
import cache_ops as _cache;
import agg_ops as _agg;
import os;
import os.path as _path;

def restore_test():
	rawlog = _cache.restore_miss_update(logonly=False);
	return;

def agg_test():
	rawlog = _agg.aggregate_update(logonly=False);
	return;

def commit_test():
	rawlog = _cache.commit_update(logonly=False);
	return;

if __name__ == '__main__':
	_common.LogEntry.open_realtime_log();
	_common.loadtags();
	_common.gitmap_load();
	_common.gitmap_check();
	#restore_test();
	#agg_test();
	commit_test();
	_common.gitmap_check();
	_common.gitmap_dump();
	_common.dumptags();
	_common.LogEntry.close_realtime_log();
