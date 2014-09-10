import common_def as _common;
import os.path as _path;
import functools as _func;

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

def commit_update(root_path, logonly=True):
	_common.gitmap_check();
	addfile_ops = {}; # key git_path, data_path
	rmfile_ops = {};
	rawlog = [];
	assert _common.isancestor(_common.REPO_GIT_PATH, root_path);

	if not logonly:
		_common.incfile_init();

	for git_path, data_path in _common.get_iter_gitmap():
		if not _common.isancestor(root_path, git_path):
			continue;
		assert not git_path in addfile_ops;
		assert not data_path in rmfile_ops;
		rawlog.append(_common.LogEntry(level=_common.LOGLEVEL_WARN if _path.isdir(git_path) else _common.LOGLEVEL_INFO, op_name='git_commit_update', details={
					'git_path' : git_path,
					'data_path' : data_path,
					'override_type' : 'dir' if _path.isdir(git_path) else 'single_file',
					}));
		addfile_ops[git_path] = _func.partial(_common.addfile_op, git_path, data_path);
		rmfile_ops[git_path] = _func.partial(_common.rmfile_op, data_path);
	for ops in [rmfile_ops, addfile_ops]:
		for op in ops.values():
			rawlog.extend(op(logonly=logonly));
			if rawlog[-1].level == _common.LOGLEVEL_ERR:
				return rawlog;

	if not logonly:
		_common.gitmap_check(); # ensure noth lost
		_common.incfile_check();
	return rawlog;
