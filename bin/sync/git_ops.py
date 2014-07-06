import common_def as _common;

def gitmap_update(rawlog):
	rename_map = {};
	for log in rawlog:
		if log.level != _common.LOGLEVEL_INFO:
			continue;
		if log.op_name != 'log_rename':
			continue;
		assert 'src' in log.details;
		assert 'dest' in log.details;
		rename_map[log.details['src']] = log.details['dest'];
	_common.gitmap_remap(rename_map);
	return;
