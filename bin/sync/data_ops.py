import os.path as _path;
import os;
import common_def as _common;

def get_entries(root_path):
	assert not _path.islink(root_path);
	if _common.gettag(root_path) == 'd':
		return [];

	if _path.isfile(root_path) or _common.gettag(root_path) == 'e':
		return [root_path];

	entry_list = [];
	for subname in os.listdir(root_path):
		subpath = _path.join(root_path, subname);
		entry_list.extend(get_entries(subpath));
	return entry_list;

def get_cache_path(data_path):
	assert _common.isancestor(_common.REPO_DATA_PATH, data_path);
	return _path.normpath(_path.join(_common.REPO_CACHE_PATH, _path.relpath(data_path, _common.REPO_DATA_PATH)));

def entryfile_sync(data_path):
	entry_list = get_entries(data_path);
	for entry in entry_list:
		if not _common.isactive_entry(entry):
			_common.add_entry(entry);

	def enum_func(path, entry):
		if not _path.exists(path):
			_common.discard_entry(path);
		return;

	_common.enum_active_entries(enum_func);
	return;

def entryfile_update(rawlog):
	rename_map = {};
	for log in rawlog:
		if log.level != _common.LOGLEVEL_INFO:
			continue;
		if log.op_name != 'log_rename':
			continue;
		assert 'src' in log.details;
		assert 'dest' in log.details;
		rename_map[log.details['src']] = log.details['dest'];
	_common.rename_entry(rename_map);
	return;
