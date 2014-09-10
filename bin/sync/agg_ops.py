import common_def as _common;
import re;
import cache_ops as _cache;
import functools as _func;
import data_ops as _data;
import os;
import os.path as _path;
# terms:
#     * agg_path: aggreation target path

class ConflictCheckReport(object):
	def __init__(self, agg_path, err_level=_common.LOGLEVEL_INFO, err_desc=None, origin_status=None, target_status=None, actions=None):
		self.agg_path = agg_path;
		self.err_level = err_level;
		self.err_desc = err_desc;
		self.origin_status = origin_status;
		self.target_status = target_status;
		self.actions = actions;
		return;

	@property
	def origin_status_desc(self):
		return _common.get_status_desc(self.origin_status);

	@property
	def target_status_desc(self):
		return _common.get_status_desc(self.target_status);
	pass;

# check if aggregate will cause save conflict, or unsafe conflict
# unsafe conflict include:
#     * partial conflict -- WARN
#     * conflict with renamed -- ERR
#     * conflict with conflicted -- WARN
# agg_path has the form: _common.REPO_AGGSRC_PATH/${agg_subfolder}/${agg_relpath}
# notice that, aggregation is regular-file based.
def conflict_check(agg_path):
	agg_path = _path.normpath(agg_path);
	if not _common.isancestor(_common.REPO_AGGSRC_PATH, agg_path):
		_common.logerr('invalid path format');
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='path should under _common.REPO_AGGSRC_PATH');
	cache_path = get_agg_targetpath(agg_path);
	if _path.isdir(_path.realpath(cache_path)):
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='can\'t override folder by regular file');
	cache_status, cache_ancestor = _cache.status_check(cache_path);
	if cache_status is None:
		_common.logerr('corrupted cache status (None), need manually check');
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='corrupted cache status (None)');
	
	assert not (cache_status & _common.STATEFLAG_NULL);
	assert cache_status != _common.STATEFLAG_PARTIAL;
	assert bool(cache_status & _common.STATEFLAG_PARTIAL) == bool(not cache_ancestor is None and cache_ancestor != cache_path) or (cache_status & _common.STATEFLAG_CONFLICT);

	if _cache.is_status_corrupted(cache_status):
		_common.logerr('corrupted status, need manually check');
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='corrupted cache status',
				origin_status=cache_status);

	if cache_status == _common.STATEFLAG_CLEAN:
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=_common.STATEFLAG_CONFLICT, actions=[
					_func.partial(_common.tagfile_op, path=cache_path, tag='c'),
					_func.partial(_common.rmlink_op, link_path=cache_path),
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == _common.STATEFLAG_CONFLICT:
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=_common.STATEFLAG_CONFLICT, actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == _common.STATEFLAG_RENAMED:
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='agg may cause: miss and malconflict');

	if cache_status == _common.STATEFLAG_MISS:
		data_path = _cache.get_data_path(cache_path);
		assert _common.isancestor(_common.REPO_DATA_PATH, data_path);
		data_ancestor = data_path;
		is_malassoc = False;
		while len(data_ancestor) > len(_common.REPO_DATA_PATH):
			if _common.gettag(data_ancestor) in ['e', 'd']:
				is_malassoc = True;
				break;
			data_ancestor = _path.dirname(data_ancestor);
		if is_malassoc:
			return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='agg may cause: malassociate', origin_status=cache_status, target_status=_common.STATEFLAG_CONFLICT);
		else:
			return ConflictCheckReport(agg_path, origin_status=cache_status,
					target_status=_common.STATEFLAG_UNTRACTED, actions=[
						_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
						_func.partial(_common.rmfile_op, path=agg_path),
					]);

	if cache_status == _common.STATEFLAG_DELAY:
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=_common.STATEFLAG_DELAY, actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == _common.STATEFLAG_READY:
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=_common.STATEFLAG_READY, actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == cache_status == _common.STATEFLAG_UNTRACTED:
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=_common.STATEFLAG_UNTRACTED, actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_CLEAN | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.tagfile_op, path=cache_ancestor, tag='c'),
					_func.partial(_common.rmlink_op, link_path=cache_ancestor),
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_CLEAN | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.tagfile_op, path=cache_ancestor, tag='c'),
					_func.partial(_common.rmlink_op, link_path=cache_ancestor),
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_CONFLICT | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_CONFLICT | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_RENAMED | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='agg may cause: miss and malconflict');

	if cache_status == (_common.STATEFLAG_RENAMED | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, err_level=_common.LOGLEVEL_ERR, err_desc='agg may cause: miss and malconflict');

	if cache_status == (_common.STATEFLAG_DELAY | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_DELAY | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_DELAY | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_DELAY | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_READY | _common.STATEFLAG_MISS | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_READY | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.addfile_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	if cache_status == (_common.STATEFLAG_READY | _common.STATEFLAG_PARTIAL):
		return ConflictCheckReport(agg_path, origin_status=cache_status,
				target_status=(_common.STATEFLAG_READY | _common.STATEFLAG_PARTIAL),
				actions=[
					_func.partial(_common.override_op, src=agg_path, dest=cache_path),
					_func.partial(_common.rmfile_op, path=agg_path),
				]);

	assert False;
	return None;

def conflict_scan_check(root_path):
	conflict_list = [];
	for dirpath, dirnames, filenames in os.walk(root_path):
		for name in filenames:
			path = _path.join(dirpath, name);
			assert not _path.islink(path);
			assert _path.isfile(path);
			conflict_list.append(conflict_check(path));
	return conflict_list;

# return a list of files with same agg_path
def multiconflict_check(cache_path):
	# todo
	src_folders = [];
	for agg_path, src_folder in get_agg_srcpath(cache_path):
		if _path.exists(agg_path):
			src_folders.append(src_folder);
	return src_folders;

# recursively scan for specified directory to check for multiple conflict
# return a list of files which have multiple conflict
def multiconflict_scan_check(root_path):
	multiconflict_map = {};
	for dirpath, dirnames, filenames in os.walk(root_path):
		for filename in filenames:
			path = _path.join(dirpath, filename);
			assert not _path.islink(path);
			assert _path.isfile(path);
			cache_path = get_agg_targetpath(path);
			if not cache_path in multiconflict_map:
				multiconflict_map[cache_path] = [];
			multiconflict_map[cache_path].append(get_srcfolder(path));
	multiconflict_map = dict([(path, src_list)
		for path, src_list in multiconflict_map.iteritems() if len(src_list) != 1]);
	return multiconflict_map;

def aggregate_update(root_path, logonly=True):
	rawlog = [];
	conflict_list = [];

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'multiconflict_scan_check',
					'root_path' : root_path,
				}));
	multiconflict_map = multiconflict_scan_check(root_path);
	if multiconflict_map:
		for path, src_folders in multiconflict_map.iteritems():
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'multiconflict_scan_check', {
							'path' : path,
							'src_folders' : src_folders,
						}));
		return rawlog;

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'malassociate_scan_check',
					'cache_root' : _common.REPO_CACHE_PATH,
				}));
	malassociate_list = _cache.malassociate_scan_check(_common.REPO_CACHE_PATH, _common.REPO_DATA_PATH);

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'malconflict_scan_check',
					'cache_root' : _common.REPO_CACHE_PATH,
				}));
	malconflict_list = _cache.malconflict_scan_check(_common.REPO_CACHE_PATH);
	if malassociate_list or malconflict_list:
		for path in malassociate_list:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'malassociate_scan_check', {
							'path' : path,
						}));

		for path in malconflict_list:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'malconflict_scan_check', {
							'path' : path,
						}));
		return rawlog;

	for subname in os.listdir(root_path):
		subpath = _path.join(root_path, subname);
		if _path.isdir(subpath):
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
							'step' : 'conflict_scan_check',
							'root_path' : root_path,
						}));
			conflict_list.extend(conflict_scan_check(subpath));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	
	# merge operation
	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'merge ops',
					'root_path' : root_path,
				}));
	haserr = False;
	tagfile_ops = {}; # key: path
	addfile_ops = {}; # key: dest
	override_ops = {}; # key: dest
	rmlink_ops = {}; # key: path
	rmfile_ops = {}; # key: path
	for report in conflict_list:
		if report.err_level == _common.LOGLEVEL_ERR:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'conflict_scan_check', {
							'agg_path' : report.agg_path,
							'err_desc' : report.err_desc,
						}));
			haserr = True;
			break;

		if report.err_level == _common.LOGLEVEL_WARN:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'conflict_scan_check', {
							'agg_path' : report.agg_path,
							'warn_desc' : report.err_desc,
							'origin_status' : report.origin_status_desc,
							'target_status' : report.target_status_desc,
							'actions' : map(_common.get_bareopname, report.actions),
						}));
			# we won't stop on warning
		else:
			assert report.err_level == _common.LOGLEVEL_INFO;
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'conflict_scan_check', {
							'agg_path' : report.agg_path,
							'info_desc' : report.err_desc, # may be None
							'origin_status' : report.origin_status_desc,
							'target_status' : report.target_status_desc,
							'actions' : map(_common.get_bareopname, report.actions),
						}));

		for op in report.actions:
			if _common.get_bareop(op) == _common.tagfile_op:
				path, tag = op.keywords['path'], op.keywords['tag'];
				key = path;
				if key in tagfile_ops:
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'aggregate_update', {
									'warn_desc' : 'duplicated path tobe tagged',
									'path' : path,
									'tag' : tag,
								}));
				tagfile_ops[key] = op;
			if _common.get_bareop(op) == _common.addfile_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				key = dest;
				assert _common.isancestor(_common.REPO_AGGSRC_PATH, src);
				assert _common.isancestor(_common.REPO_CACHE_PATH, dest);
				if key in addfile_ops:
					assert False;
				addfile_ops[key] = op;
			if _common.get_bareop(op) == _common.override_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				assert _common.isancestor(_common.REPO_AGGSRC_PATH, src);
				assert _common.isancestor(_common.REPO_CACHE_PATH, dest);
				key = dest;
				if key in override_ops:
					assert False;
				override_ops[key] = op;
			if _common.get_bareop(op) == _common.rmlink_op:
				key = link_path = op.keywords['link_path'];
				assert _common.isancestor(_common.REPO_CACHE_PATH, link_path);
				if key in rmlink_ops:
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'aggregate_update', {
									'warn_desc' : 'duplicated link tobe removed',
									'link_path' : link_path,
								}));
				rmlink_ops[key] = op;
			if _common.get_bareop(op) == _common.rmfile_op:
				key = path = op.keywords['path'];
				assert _common.isancestor(_common.REPO_AGGSRC_PATH, path);
				assert not key in rmfile_ops;
				rmfile_ops[key] = op;
	if haserr:
		return rawlog;

	if not logonly:
		_common.incfile_init();

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'execute ops',
					'root_path' : root_path,
				}));
	for ops in [
					rmlink_ops, addfile_ops, override_ops,
					tagfile_ops, rmfile_ops,
				]:
		for op in ops.values():
			rawlog.extend(op(logonly=logonly));
			if rawlog[-1].level == _common.LOGLEVEL_ERR:
				return rawlog;

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'aggregate_update', {
					'step' : 'post check',
					'cache_root' : _common.REPO_CACHE_PATH,
				}));
	if not logonly:
		# check after updating
		malassociate_list = _cache.malassociate_scan_check(_common.REPO_CACHE_PATH, _common.REPO_DATA_PATH);
		malconflict_list = _cache.malconflict_scan_check(_common.REPO_CACHE_PATH);
		if malassociate_list or malconflict_list:
			for path in malassociate_list:
				rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'malassociate_scan_check', {
								'path' : path,
							}));

			for path in malconflict_list:
				rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'malconflict_scan_check', {
								'path' : path,
							}));
		rawlog.extend(_common.incfile_check());
	return rawlog;

def get_agg_targetpath(agg_path):
	assert _common.isancestor(_common.REPO_AGGSRC_PATH, agg_path);
	return _path.normpath(_path.join(_common.REPO_CACHE_PATH, get_agg_relpath(agg_path)));

g_agg_ptn = re.compile('[^/]+'); # it miss a rare case here -- '\\/'
def get_agg_relpath(agg_path):
	assert _common.isancestor(_common.REPO_AGGSRC_PATH, agg_path);
	agg_relpath = _path.relpath(agg_path, _common.REPO_AGGSRC_PATH);
	assert agg_relpath != '.';
	agg_subfolder = g_agg_ptn.match(agg_relpath).group(0);
	return _path.relpath(agg_relpath, agg_subfolder);

def get_srcfolder(agg_path):
	assert _common.isancestor(_common.REPO_AGGSRC_PATH, agg_path);
	agg_relpath = _path.relpath(agg_path, _common.REPO_AGGSRC_PATH);
	assert agg_relpath != '.';
	agg_subfolder = g_agg_ptn.match(agg_relpath).group(0);
	return agg_subfolder;
