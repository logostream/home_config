import common_def as _common;
import agg_ops as _agg;
import cache_ops as _cache;
import os;
import os.path as _path;

def agg_test():
	_common.loadtags();
	_common.LogEntry.open_realtime_log();
	rawlog = _cache.restore_miss_update(logonly=False);
	_common.LogEntry.close_realtime_log();
	logpath = '/home/stream/tmp/test.log';
	if _path.exists(logpath):
		os.remove(logpath);
	_common.dumplog(rawlog, logpath=logpath, warnpath=logpath, errpath=logpath);
	_common.dumptags();
	return;

if __name__ == '__main__':
	agg_test();
