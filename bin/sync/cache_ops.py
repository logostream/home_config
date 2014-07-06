import os.path as _path;
import common_def as _common;
import functools as _func;
import data_ops as _data;
import os;

class CommitCheckReport(object):
	def __init__(self, cache_path, err_level=_common.LOGLEVEL_INFO, err_desc=None, origin_status=None, actions=None):
		self.cache_path = cache_path;
		self.err_level = err_level;
		self.err_desc = err_desc;
		self.origin_status = origin_status;
		self.actions = actions if not actions is None else [];
		return;

	@property
	def origin_status_desc(self):
		return _common.get_status_desc(self.origin_status);
	pass;

# check current file status in cache
# here is the prossible list of status:
#     * None -- exception happens;
#     * null -- only happens to cache_path as directory, when test_untracked==True, it means it has multiple status on files/folders in it, when test_untracked==False, it means it is whether null or untracted;
#     * clean -- a link point to entry in data, with aligned path, no entry in git;
#     * conflict -- file is not a link, but has corresponding doc entry in data. File may miss in cache;
#     * dirty -- has corresponding entry in git, dirty is not detected in this method, and will treat independently;
#     * renamed -- a link point to entry in data, but path not aligened;
#     * miss -- file not exists in cache, (and may also miss in data and git);
#     * delay -- a non-link which manually taged in cache as an entry delay for sync
#     * ready -- a non-link which manually taged in cache as an entry ready for sync
#     * partial -- only happens when test_partial=True, means it is just a part of a doc entry in cache/git/doc
#     * untracted -- a file is untracted iff it haven't any above known status, a direct is untracted iff all its child are untracted. A folder can be determined as untracked only when test_untracked=True is specifed and recursive check is performed, if not it just return status null
# here is a list of possible combination of status, which is checked by status_corrupted():
#     * clean + miss + partial -- ancestor clean, but file miss
#     * clean + partial -- partial clean, rest part of entry may not clean
#     * conflict + miss -- maltag, will return None, means the file tagged as 'c' but miss in cache, caused by conflict then rename. The flags couldn't imply a case that the overriding file is part of doc-entry, because it won't lead to a miss.
#     * conflict + miss + partial -- means (partial conflict) + miss, for the case the ancestor itself miss (means ancestor tagged as 'c' but miss in cache, maltag), we will return None as error, for miss co-existing with partial conflict, it only means the file miss both in cache and data.
#     * conflict + partial -- partial conflict, means the file not overriding in cache, but the checking file belongs to a part of existing doc entry (we should check in data here). ! we consider it a complete conflict if there already exist a counterpart in data, even if it just a part of one existing doc entry.
#     * renamed + miss + partial -- ancestor renamed, but file miss
#     * renamed + partial -- partial renamed
#     * delay + miss + partial -- ancestor delay, but file miss
#     * delay + partial -- partial delay
#     * ready + miss -- maltag, will return None, means the file tagged as 'r' but miss in cache
#     * ready + miss + partial -- means (partial ready) + miss, for the case ancestor miss we (condiser it as maltag) will return None as error
#     * ready + partial -- partial ready
# following combination is impossible (not expected to appear in return):
#     * None + <any>
#     * null + <any>
#     * untracked + <any>
#     * partial (alone) -- should with one of (clean | conflict | renamed | delay)
#     * clean + (conflict | renamed | delay | ready)
#     * conflict + (renamed | delay | ready) -- conflict with rename will finally cause conflict + miss
#     * renamed + (delay | ready)
#     * delay + ready
#     * miss + (delay | renamed | clean) (without partial)
def status_check(cache_path, test_partial=True, test_untracked=True):
	cache_path = _path.normpath(cache_path);
	status_flags = _common.STATEFLAG_NULL;

	if not _common.isancestor(_common.REPO_CACHE_PATH, cache_path):
		_common.logerr('invalid path');
		return (None, None);

	if not _path.exists(cache_path):
		if _path.lexists(cache_path):
			_common.logerr('dead link');
			return (None, None);
		status_flags |= _common.STATEFLAG_MISS;

	link_ancestor=None;
	conflict_ancestor=None;
	delay_ancestor=None;
	ready_ancestor=None;
	ancestor = cache_path;
	while len(ancestor) > len(_common.REPO_CACHE_PATH):
		if _path.islink(ancestor):
			if link_ancestor:
				_common.logerr('multi-link redirection');
				return (None, None);
			link_ancestor = ancestor;
		if _common.gettag(ancestor) == 'c': # here we just rely on 'c' tag, we don't check it by test if corresponding data_path has tag 'e', which should be the work in aggregation check
			if conflict_ancestor:
				_common.logerr('multi-partial-conflict');
				return (None, None);
			conflict_ancestor = ancestor;
		if _common.gettag(ancestor) == 'd':
			if delay_ancestor:
				_common.logerr('multi-partial-delay');
				return (None, None);
			delay_ancestor = ancestor;
		if _common.gettag(ancestor) == 'r':
			if ready_ancestor:
				_common.logerr('multi-partial-ready');
				return (None, None);
			ready_ancestor = ancestor;
		if test_partial:
			ancestor = _path.dirname(ancestor); # continue with parent
		else:
			break; # only test cache_path alone and stop
	if (not link_ancestor is None) + (not conflict_ancestor is None) + (not delay_ancestor is None) > 1:
		_common.logerr('multi-partial status');
		return (None, None);

	if conflict_ancestor:
		data_ancestor = get_data_path(conflict_ancestor);
		if _path.isdir(data_ancestor) and _common.gettag(data_ancestor) != 'e':
			_common.logerr('link is not a tracked doc entry in data');
		if not _path.exists(conflict_ancestor):
			_common.logerr('maltag: the file tagged as \'c\' not exists');
			return (None, conflict_ancestor);
		if not _path.exists(data_ancestor):
			# todo: more restrict detection
			_common.logerr('malconflict: data cache entry unmatched');
			return (None, conflict_ancestor);
		status_flags |= _common.STATEFLAG_CONFLICT;
		if conflict_ancestor != cache_path: # we should review the existing of file in data
			status_flags |= _common.STATEFLAG_PARTIAL;
			data_path = get_data_path(cache_path);
			if _path.exists(data_path): # we don't consider it is a miss if the data counterpart got hidden by conflict ancestor
				status_flags &= ~_common.STATEFLAG_MISS;
				if _path.exists(cache_path):
					status_flags &= ~_common.STATEFLAG_PARTIAL;

	if ready_ancestor:
		if not _path.exists(ready_ancestor):
			_common.logerr('maltag: the file tagged as \'r\' not exists');
			return (None, ready_ancestor);
		status_flags |= _common.STATEFLAG_READY;
		if ready_ancestor != cache_path: # we should review the existing of file in data
			status_flags |= _common.STATEFLAG_PARTIAL;

	if delay_ancestor:
		status_flags |= _common.STATEFLAG_DELAY;
		if delay_ancestor != cache_path:
			status_flags |= _common.STATEFLAG_PARTIAL;

	if link_ancestor:
		data_ancestor = _path.realpath(link_ancestor);
		if not _common.isancestor(_common.REPO_DATA_PATH, data_ancestor):
			_common.logerr('link outof scope');
			return (None, link_ancestor);
		if _path.isdir(data_ancestor) and _common.gettag(data_ancestor) != 'e':
			_common.logerr('link is not a tracked doc entry in data');
			return (None, link_ancestor);
		if _path.relpath(link_ancestor, _common.REPO_CACHE_PATH) == _path.relpath(data_ancestor, _common.REPO_DATA_PATH):
			status_flags |= _common.STATEFLAG_CLEAN;
		else:
			status_flags |= _common.STATEFLAG_RENAMED;
		if link_ancestor != cache_path:
			status_flags |= _common.STATEFLAG_PARTIAL;
	
	if status_flags == _common.STATEFLAG_NULL:
		if _path.isfile(cache_path):
			status_flags |= _common.STATEFLAG_UNTRACTED;
		elif _path.isdir(cache_path) and test_untracked: # try to test untract recursively
			all_untracked = True;
			for subname in os.listdir(cache_path):
				subpath = _path.join(cache_path, subname);
				if not status_check(subpath, test_partial=False, test_untracked=True
						)[0] == _common.STATEFLAG_UNTRACTED:
					# disable test_partial because we have already tested all ancestors if we want
					all_untracked = False;
					break;
			if all_untracked:
				status_flags |= _common.STATEFLAG_UNTRACTED;

	assert not (status_flags & _common.STATEFLAG_DIRTY);
	return status_flags, link_ancestor or conflict_ancestor or delay_ancestor or ready_ancestor;

# check the invalid combination which is described in status_check()
def is_status_corrupted(status_flags):
	# no bad state except None will be returned temporary
	return status_flags is None;

def coverage_scan_check(cache_root, data_root):
	assert _common.isancestor(_common.REPO_CACHE_PATH, cache_root);
	assert _common.isancestor(_common.REPO_DATA_PATH, data_root);
	entry_list = _data.get_entries(data_root);
	miss_set = set(entry_list);
	hit_map = {}; # key: data entry, value: cache entry list
	def coverage_eliminate(cache_path):
		status = status_check(cache_path, test_partial=False, test_untracked=False)[0];
		assert not status is None;
		assert not (_common.STATEFLAG_MISS & status);
		assert not (_common.STATEFLAG_PARTIAL & status);
		data_path = None;
		if status & _common.STATEFLAG_CLEAN or status & _common.STATEFLAG_RENAMED:
			data_path = _path.realpath(cache_path);
		else:
			assert not _path.islink(cache_path);
		if status & _common.STATEFLAG_CONFLICT:
			data_path = get_data_path(cache_path);
		if not data_path is None:
			miss_set.remove(data_path);
			if not data_path in hit_map:
				hit_map[data_path] = [];
			hit_map[data_path].append(cache_path);
		if status == _common.STATEFLAG_NULL:
			for subname in os.listdir(cache_path):
				subpath = _path.join(cache_path, subname);
				coverage_eliminate(subpath);
		return;
	coverage_eliminate(cache_root);
	return miss_set, hit_map;

def malassociate_scan_check(cache_root, data_root):
	# caused by delete/rename from the path sometime, then agg/rename to the path
	miss_set, hit_map = coverage_scan_check(cache_root, data_root);
	malassoc_map = {};
	for data_path in miss_set:
		cache_path = _data.get_cache_path(data_path);
		if _path.exists(cache_path):
			if not data_path in malassoc_map:
				malassoc_map[data_path] = [];
			malassoc_map[data_path] = cache_path;
	for data_path, cache_list in hit_map.iteritems():
		if len(cache_list) > 1:
			if not data_path in malassoc_map:
				malassoc_map[data_path] = [];
			malassoc_map.extend(cache_list);
	return malassoc_map;

def malconflict_scan_check(cache_root):
	malconflict_list = [];
	for cache_path in _common.get_tag_pathlist('c'):
		assert _common.isancestor(_common.REPO_CACHE_PATH, cache_path);
		if not _common.isancestor(cache_root, cache_path):
			continue;
		if not _path.exists(cache_path):
			logerr('malconflict: %s -- not exists' % cache_path);
			malconflict_list.append(cache_path);
		data_path = get_data_path(cache_path);
		if not _path.exists(data_path):
			logerr('malconflict: %s -- data counterpart not exists' % cache_path);
			malconflict_list.append(cache_path);
		if _path.isdir(data_path) and _common.gettag(data_path) != 'e':
			logerr('malconflict: %s -- data counterpart not an entry' % cache_path);
			malconflict_list.append(cache_path);
		if _path.isfile(cache_path) != _path.isfile(data_path):
			logerr('malconflict: %s -- unconsistent type' % cache_path);
			malconflict_list.append(cache_path);
	return malconflict_list;

# use to have a thorough status check, unlike commit_check with just stop on an determined status
def malstatus_scan_check(cache_root):
	malstatus_list = [];
	for dirpath, dirnames, filenames in os.walk(cache_root):
		for name in dirnames + filenames:
			path = _path.join(dirpath, name);
			if status_check(path, test_partial=True, test_untracked=False)[0] is None:
				malstatus_list.append(path);
	return malstatus_list;

def commit_scan_check(root_path):
	commit_list=[];
	untracted_set=set();
	rename_map={};
	def commit_scan(cache_path):
		status, ancestor = status_check(cache_path, test_partial=True, test_untracked=False);

		if status is None:
			_common.logerr('corrupted cache status (None), need manually check');
			commit_list.append(CommitCheckReport(cache_path, err_level=_common.LOGLEVEL_ERR, err_desc='corrupted cache status (None)'));
		
		if is_status_corrupted(status):
			_common.logerr('corrupted status, need manually check');
			commit_list.append(CommitCheckReport(cache_path, err_level=_common.LOGLEVEL_ERR, err_desc='corrupted cache status',
					origin_status=status));

		assert not (_common.STATEFLAG_MISS & status);
		diginto = False;
		untracted = False;
		if status == _common.STATEFLAG_NULL:
			untracted = True;
			diginto = True;
		if status & _common.STATEFLAG_UNTRACTED:
			assert status == _common.STATEFLAG_UNTRACTED;
			untracted = True;
			assert diginto == False;
			commit_list.append(CommitCheckReport(cache_path, err_desc='no action', origin_status=status));
		if status & _common.STATEFLAG_CLEAN:
			assert status == _common.STATEFLAG_CLEAN;
			assert untracted == False;
			assert diginto == False;
			commit_list.append(CommitCheckReport(cache_path, err_desc='no action', origin_status=status));
		if status & _common.STATEFLAG_CONFLICT:
			# todo: check doc entry
			assert untracted == False;
			assert not ancestor is None;
			data_path = get_data_path(cache_path);
			data_ancestor = get_data_path(ancestor);
			if _path.isfile(cache_path):
				assert diginto == False;
				if status & _common.STATEFLAG_PARTIAL:
					commit_list.append(CommitCheckReport(cache_path, err_desc='new file', origin_status=status, actions=[
									_func.partial(_common.addfile_op, src=cache_path, dest=data_path),
									_func.partial(_common.rmfile_op, path=cache_path),
									_func.partial(_common.untag_op, path=ancestor, origin_tag='c'),
									_func.partial(_common.restorelink_op, src=data_ancestor, dest=ancestor),
								]));
				else:
					commit_list.append(CommitCheckReport(cache_path, origin_status=status, actions=[
									_func.partial(_common.override_op, src=cache_path, dest=data_path),
									_func.partial(_common.rmfile_op, path=cache_path),
									_func.partial(_common.untag_op, path=ancestor, origin_tag='c'),
									_func.partial(_common.restorelink_op, src=data_ancestor, dest=ancestor),
								]));
			else:
				diginto = True;
		if status & _common.STATEFLAG_RENAMED:
			# todo: check doc entry
			assert untracted == False;
			assert diginto == False;
			assert status == _common.STATEFLAG_RENAMED;
			data_path = _path.realpath(cache_path);
			assert _path.exists(data_path);
			new_data_path = get_data_path(cache_path);
			actions = [];
			assert not data_path in rename_map;
			rename_map[data_path] = new_data_path;
			if _path.isdir(data_path):
				actions.extend([
							_func.partial(_common.untag_op, path=data_path, origin_tag='e'),
							_func.partial(_common.tagfile_op, path=new_data_path, tag='e'),
						]);
			commit_list.append(CommitCheckReport(cache_path, err_desc='override', origin_status=status, actions=actions + [
							_func.partial(_common.rmlink_op, link_path=cache_path),
							_func.partial(_common.mv_batch_op, src=data_path, dest=new_data_path),
							_func.partial(_common.restorelink_op, src=new_data_path, dest=cache_path),
						]));
		if status & _common.STATEFLAG_DELAY:
			assert untracted == False;
			assert diginto == False;
			assert status == _common.STATEFLAG_DELAY;
			commit_list.append(CommitCheckReport(cache_path, err_desc='no action', origin_status=status));
		if status & _common.STATEFLAG_READY:
			assert untracted == False;
			assert diginto == False;
			assert status == _common.STATEFLAG_READY;
			data_path = get_data_path(cache_path);
			actions = [];
			if _path.isdir(cache_path):
				actions.append(
							_func.partial(_common.tagfile_op, path=data_path, tag='e')
						);
			commit_list.append(CommitCheckReport(cache_path, err_desc='new file', origin_status=status, actions=actions + [
							_func.partial(_common.addfile_op, src=cache_path, dest=data_path),
							_func.partial(_common.untag_op, path=cache_path, origin_tag='r'),
							_func.partial(_common.rmfile_op, path=cache_path),
							_func.partial(_common.restorelink_op, src=data_path, dest=cache_path),
						]));
		if untracted:
			untracted_set.add(cache_path);
		else: # remove any ancestors in untracted_set
			untracted_ancestor = _path.dirname(cache_path);
			while untracted_ancestor in untracted_set:
				untracted_set.remove(untracted_ancestor);
				untracted_ancestor = _path.dirname(untracted_ancestor);
		if diginto:
			for subname in os.listdir(cache_path):
				subpath = _path.join(cache_path, subname);
				commit_scan(subpath);
	commit_scan(root_path);
	untracted_list = [];
	for path in untracted_set:
		if not _path.dirname(path) in untracted_set:
			untracted_list.append(path);
	return commit_list, untracted_list, rename_map;

def commit_update(root_path, logonly=True):
	rawlog = [];
	assert _common.isancestor(_common.REPO_CACHE_PATH, root_path);

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'malassociate_scan_check',
					'root_path' : root_path,
				}));
	malassociate_list = malassociate_scan_check(root_path, _common.REPO_DATA_PATH);
	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'malconflict_scan_check',
					'root_path' : root_path,
				}));
	malconflict_list = malconflict_scan_check(root_path);
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

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'commit_scan_check',
					'root_path' : root_path,
				}));
	commit_list, untracted_list, rename_map = commit_scan_check(root_path);
	if len(untracted_list):
		for path in untracted_list:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'commit_scan_check', {
							'err_desc' : 'untracted entry',
							'path' : path,
						}));
		return rawlog;
	
	for src, dest in rename_map.iteritems():
		rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'log_rename', {
						'src' : src,
						'dest' : dest,
					}));
	
	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'merge ops',
					'root_path' : root_path,
				}));
	# merge operation
	mv_batch_ops = {}; # key: src, dest
	addfile_ops = {}; # key: dest
	override_ops = {}; # key: dest
	untag_ops = {}; # key: path
	tagfile_ops = {}; # key: path
	rmlink_ops = {}; # key: path
	rmfile_ops = {}; # key: path
	restorelink_ops = {}; # key: dest
	for report in commit_list:
		if report.err_level == _common.LOGLEVEL_ERR:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'commit_scan_check', {
							'cache_path' : report.cache_path,
							'err_desc' : report.err_desc,
						}));
			return rawlog;

		if report.err_level == _common.LOGLEVEL_WARN:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'commit_scan_check', {
							'cache_path' : report.cache_path,
							'warn_desc' : report.err_desc,
							'origin_status' : report.origin_status_desc,
							'actions' : map(_common.get_bareopname, report.actions),
						}));
			# we won't stop on warning
		else:
			assert report.err_level == _common.LOGLEVEL_INFO;
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_scan_check', {
							'cache_path' : report.cache_path,
							'info_desc' : report.err_desc, # may be None
							'origin_status' : report.origin_status_desc,
							'actions' : map(_common.get_bareopname, report.actions),
						}));

		for op in report.actions:
			if _common.get_bareop(op) == _common.mv_batch_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				key = src, dest;
				assert _common.isancestor(_common.REPO_DATA_PATH, src);
				assert _common.isancestor(_common.REPO_DATA_PATH, dest);
				if key in mv_batch_ops:
					assert False;
				mv_batch_ops[key] = op;
				if len(set([src for src, dest in mv_batch_ops])) != len(mv_batch_ops):
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'commit_update', {
									'err_desc' : 'mv confliction: multiple ops have same src',
								}));
					return rawlog;
				if len(set([dest for src, dest in mv_batch_ops])) != len(mv_batch_ops):
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'commit_update', {
									'err_desc' : 'mv confliction: multiple ops have same dest',
								}));
					return rawlog;
			if _common.get_bareop(op) == _common.addfile_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				key = dest;
				assert _common.isancestor(_common.REPO_CACHE_PATH, src);
				assert _common.isancestor(_common.REPO_DATA_PATH, dest);
				if key in addfile_ops:
					assert False;
				addfile_ops[key] = op;
			if _common.get_bareop(op) == _common.override_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				key = dest;
				assert _common.isancestor(_common.REPO_CACHE_PATH, src);
				assert _common.isancestor(_common.REPO_DATA_PATH, dest);
				if key in override_ops:
					assert False;
				override_ops[key] = op;
			if _common.get_bareop(op) == _common.untag_op:
				path, origin_tag = op.keywords['path'], op.keywords['origin_tag'];
				key = path;
				if key in untag_ops:
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'commit_update', {
									'warn_desc' : 'duplicated untag',
									'path' : path,
									'origin_tag' : origin_tag,
								}));
				untag_ops[key] = op;
			if _common.get_bareop(op) == _common.tagfile_op:
				path, tag = op.keywords['path'], op.keywords['tag'];
				key = path;
				if key in tagfile_ops:
					assert False;
				tagfile_ops[key] = op;
			if _common.get_bareop(op) == _common.rmlink_op:
				key = link_path = op.keywords['link_path'];
				assert _common.isancestor(_common.REPO_CACHE_PATH, link_path);
				if key in rmlink_ops:
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'commit_update', {
									'warn_desc' : 'duplicated rmlink',
									'link_path' : link_path,
								}));
				rmlink_ops[key] = op;
			if _common.get_bareop(op) == _common.rmfile_op:
				key = path = op.keywords['path'];
				assert _common.isancestor(_common.REPO_CACHE_PATH, path);
				assert not key in rmfile_ops;
				rmfile_ops[key] = op;
			if _common.get_bareop(op) == _common.restorelink_op:
				src, dest = op.keywords['src'], op.keywords['dest'];
				assert _common.isancestor(_common.REPO_DATA_PATH, src);
				assert _common.isancestor(_common.REPO_CACHE_PATH, dest);
				key = dest;
				if key in restorelink_ops:
					rawlog.append(_common.LogEntry(_common.LOGLEVEL_WARN, 'commit_update', {
									'warn_desc' : 'duplicated entry to restorelink',
									'src' : src,
									'dest' : dest,
								}));
				restorelink_ops[key] = op;

	if not logonly:
		_common.incfile_init();

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'execute ops',
					'root_path' : root_path,
				}));
	# wish: remove repeated code
	for op in rmlink_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	rawlog.extend(_common.mv_init_op(logonly=logonly));
	if rawlog[-1].level == _common.LOGLEVEL_ERR:
		return rawlog;
	for op in mv_batch_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	rawlog.extend(_common.mv_commit_op(logonly=logonly));
	if rawlog[-1].level == _common.LOGLEVEL_ERR:
		return rawlog;
	for op in addfile_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	for op in override_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	for op in untag_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	for op in tagfile_ops.values():
		rawlog.extend(op(logonly=logonly));
	for op in rmfile_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;
	for op in restorelink_ops.values():
		rawlog.extend(op(logonly=logonly));
		if rawlog[-1].level == _common.LOGLEVEL_ERR:
			return rawlog;

	rawlog.append(_common.LogEntry(_common.LOGLEVEL_INFO, 'commit_update', {
					'step' : 'post check',
					'root_path' : root_path,
				}));
	if not logonly:
		# check after updating
		rawlog.extend(malassociate_scan_check(root_path, _common.REPO_DATA_PATH));
		rawlog.extend(malconflict_scan_check(root_path));
		_common.incfile_check();
	return rawlog;

def restore_miss_update(cache_root, data_root, logonly=True):
	rawlog = [];
	malassociate_list = malassociate_scan_check(cache_root, data_root);
	if malassociate_list:
		for path in malassociate_list:
			rawlog.append(_common.LogEntry(_common.LOGLEVEL_ERR, 'malassociate_scan_check', {
							'path' : path,
						}));
		return rawlog;
	miss_set, hit_map = coverage_scan_check(cache_root, data_root);
	for data_path in miss_set:
		cache_path = _data.get_cache_path(data_path);
		assert _common.isancestor(_common.REPO_DATA_PATH, data_path);
		assert _common.isancestor(_common.REPO_CACHE_PATH, cache_path);
		rawlog.extend(_common.restorelink_op(data_path, cache_path, logonly=logonly));
	return rawlog;

def clean_miss_update():
	# todo
	return;

def get_data_path(cache_path):
	assert _common.isancestor(_common.REPO_CACHE_PATH, cache_path);
	return _path.normpath(_path.join(_common.REPO_DATA_PATH, _path.relpath(cache_path, _common.REPO_CACHE_PATH)));
