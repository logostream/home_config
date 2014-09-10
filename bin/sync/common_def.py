try: import simplejson as json
except ImportError: import json
import re;
import subprocess as _sp;
import os;
import hashlib as _hash;
import base64 as _b64;
import sys;
import traceback;
import os.path as _path;

# variable represent cache status
STATEFLAG_NULL      = 0x0;
STATEFLAG_CLEAN     = 0x1 << 0;
STATEFLAG_CONFLICT  = 0x1 << 1;
STATEFLAG_DIRTY     = 0x1 << 2;
STATEFLAG_RENAMED   = 0x1 << 3;
STATEFLAG_MISS      = 0x1 << 4;
STATEFLAG_PARTIAL   = 0x1 << 5; # means file is a part of (cache|data) doc entry
STATEFLAG_DELAY     = 0x1 << 6;
STATEFLAG_READY     = 0x1 << 7;
STATEFLAG_UNTRACTED = 0x1 << 8;
STATEFLAG_LEN       = 9;
STATEFLAG_DESC      = [
	'clean', 'conflict', 'dirty', 'renamed', 'miss', 'partial', 'delay', 'ready', 'untracted'
];
assert STATEFLAG_LEN == len(STATEFLAG_DESC);

# log level
LOGLEVEL_INFO = 0;
LOGLEVEL_WARN = 1;
LOGLEVEL_ERR  = 2;

# repo config
REPO_BASE_PATH   = '/home/stream/tmp';
REPO_CACHE_PATH  = '%s/cache/docs' % REPO_BASE_PATH;
REPO_AGGSRC_PATH = '%s/cache/copy' % REPO_BASE_PATH;
REPO_GIT_PATH    = '%s/cache/github' % REPO_BASE_PATH;
REPO_GITMAP_PATH = '%s/cache/gitmap.log' % REPO_BASE_PATH;
REPO_DATA_PATH   = '%s/data/docs' % REPO_BASE_PATH;
REPO_ARCH_PATH   = '%s/arch' % REPO_BASE_PATH;
REPO_TAGS_PATH   = '/home/stream/.config/ranger/tagged';
REPO_TMP_PATH    = '%s/tmp' % REPO_BASE_PATH;
REPO_ENTRYFILE_PATH = '%s/data/indexes/entry.log' % REPO_BASE_PATH;

# realtime log
REALTIME_LOGLEVEL = LOGLEVEL_INFO # LOGLEVEL_* or None means disable
# dump to path so that you can use :$ tail -f $REALTIME_LOGPATH | grep $ptn
REALTIME_LOGPATH = '%s/realtime.log' % REPO_BASE_PATH;

class LogEntry:
	leveltab = ['info', 'warn', 'err'];
	levelmap = {'info': LOGLEVEL_INFO, 'warn': LOGLEVEL_WARN, 'err': LOGLEVEL_ERR};
	logptn = re.compile('(info|warn|err)\\s+(\\w+)\\s+(.*)');
	
	@classmethod
	def open_realtime_log(cls, clean=False):
		if clean and _path.exists(REALTIME_LOGPATH):
			os.remove(REALTIME_LOGPATH);
		cls.frealtime = open(REALTIME_LOGPATH, 'a', buffering=1);
		return;

	@classmethod
	def close_realtime_log(cls):
		cls.frealtime.close();

	def __init__(self, level, op_name, details):
		self.level = level;
		self.op_name = op_name;
		self.details = details;
		if not REALTIME_LOGLEVEL is None and REALTIME_LOGLEVEL <= level:
			self.frealtime.write('%s\n' % self.encode().encode('utf-8'));
		return;
	
	def encode(self):
		level_name = self.leveltab[self.level];
		detail_info = json.dumps(self.details, ensure_ascii=False); # make chinese char more readable
		#detail_info = re.sub('"(\\w+)"\\s*:', '\\1:', detail_info);
		# print detail_info;
		return u'%-8s%-32s%s' % (level_name, self.op_name, detail_info);
	
	@classmethod
	def decode(cls, logline):
		mth = cls.logptn.match(logline);
		logentry = cls(cls.levelmap[mth.group(1)], mth.group(2), json.loads(mth.group(3)));
		return logentry;
	pass;

# dump raw log into file
def dumplog(rawlog, logpath, warnpath, errpath):
	with open(logpath, 'a', buffering=1) as logfile: # buffering=1 means line buffered
		with open(warnpath, 'a', buffering=1) as warnfile:
			with open(errpath, 'a', buffering=1) as errfile:
				# filetab[LOGLEVEL_INFO] == logfile
				# filetab[LOGLEVEL_WARN] == warnfile
				# filetab[LOGLEVEL_ERR] == errfile
				filetab = [logfile, warnfile, errfile];
				for logentry in rawlog:
					filetab[logentry.level].write(
							'%s\n' % logentry.encode().encode('utf-8'));
	return;

# parse file into raw log entries
def parselog(logpath):
	rawlog = [];
	with open(logpath, 'r') as logfile:
		for line in logfile:
			rawlog.append(LogEntry.decode(line));
	return rawlog;

g_tagptn = re.compile('(.):(.*)');

def loadtags():
	global g_tagsmap;
	g_tagsmap={};
	with open(REPO_TAGS_PATH, 'r') as tagsfile:
		for line in tagsfile:
			mth = g_tagptn.match(line);
			if mth:
				tag, path = mth.group(1), mth.group(2);
			else:
				tag, path = '', line.rstrip(); # remove tailing '\n' from line
			assert _path.exists(path);
			if tag == 'e': # entry -- tag for dir in data
				assert _path.isdir(path) and isancestor(REPO_DATA_PATH, path);
			if tag == 'c': # conflict -- tag for files in cache
				assert isancestor(REPO_CACHE_PATH, path);
			if tag == 'r': # ready -- tag for files in cache
				assert isancestor(REPO_CACHE_PATH, path);
			if tag == 'k': # keep -- tag for dir
				assert _path.isdir(path);
				assert isancestor(REPO_DATA_PATH, path) or isancestor(REPO_CACHE_PATH, path) \
					or isancestor(REPO_AGGSRC_PATH, path);
			if tag == 'd': # delay
				assert isancestor(REPO_DATA_PATH, path) or isancestor(REPO_CACHE_PATH, path);
			g_tagsmap[path] = tag;
	return;

def dumptags():
	new_tag_path = '%s.new' % REPO_TAGS_PATH;
	with open(new_tag_path, 'w') as tagsfile:
		for path, tag in g_tagsmap.iteritems():
			if tag == '':
				tagsfile.write('%s\n' % path);
			else:
				tagsfile.write('%s:%s\n' % (tag, path));
	return;

def gettag(path):
	return g_tagsmap[path] if path in g_tagsmap else None;

def get_tag_pathlist(tag):
	pathlist = [];
	for path, tag_ in g_tagsmap.iteritems():
		if tag_ == tag:
			pathlist.append(path);
	return pathlist;

def isancestor(ancestor, path):
	return path == ancestor or path.startswith(ancestor + '/');

def logerr(err_msg):
	print >> sys.stderr, 'ERR: %s' % err_msg;
	traceback.print_stack(limit=2); # it goes to stderr by default
	return;

def get_status_desc(status_flags):
	if status_flags is None:
		return None;
	status_list = [];
	for i in xrange(STATEFLAG_LEN):
		if (1 << i) & status_flags:
			status_list.append(STATEFLAG_DESC[i]);
	status_desc = '0x%08x (%s)' %(status_flags,
			' + '.join(status_list) if len(status_list) else 'null');
	return status_desc;

def get_bareop(op):
	while hasattr(op, 'func'):
		op = op.func;
	return op;

def get_bareopname(op):
	return get_bareop(op).func_name;

def mv_init_op(logonly=True):
	global g_mv_src_map;
	global g_mv_dest_map;
	g_mv_src_map = {};
	g_mv_dest_map = {};
	return [];

def mv_batch_op(src, dest, logonly=True):
	rawlog = [];
	if src in g_mv_src_map:
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='mv_batch_op', details={
							'err_desc' : 'overlapping src',
							'src' : src,
							'new_dest' : dest,
							'original_dest' : g_mv_src_map[src],
						}));
		return rawlog;
	if dest in g_mv_dest_map:
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='mv_batch_op', details={
							'err_desc' : 'overlapping src',
							'dest' : dest,
							'new_src' : src,
							'original_src' : g_mv_dest_map[dest],
						}));
		return rawlog;
	g_mv_src_map[src] = dest;
	g_mv_dest_map[dest] = src;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='mv_batch_op', details={
						'dest' : dest,
						'src' : src,
					}));
	return rawlog;

def mv_commit_op(logonly=True):
	assert len(g_mv_src_map) == len(g_mv_dest_map);
	rawlog = [];
	for src, dest in g_mv_src_map.iteritems():
		tmp = map_tmppath(src);
		rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='mv_commit_op', details={
						'stage' : 'src to tmp',
						'src' : src,
						'tmp' : tmp,
						'dest' : dest,
					}));
		rawlog.extend(shellexec([
						['mv', src, tmp],
					] , logonly=logonly));
		rawlog.extend(rmdir_op(_path.dirname(src), logonly=logonly));
	cmd_list = [];
	for src, dest in g_mv_src_map.iteritems():
		if not logonly:
			assert not _path.exists(src);
			assert not _path.exists(dest);
		tmp = map_tmppath(src);
		rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='mv_commit_op', details={
						'stage' : 'tmp to dest',
						'src' : src,
						'tmp' : tmp,
						'dest' : dest,
					}));
		cmd_list.extend([
					['mkdir', '-p', _path.dirname(dest)],
					['mv', tmp, dest],
				]);
	rawlog.extend(shellexec(cmd_list, logonly=logonly));
	return rawlog;

def addfile_op(src, dest, logonly=True):
	if not logonly:
		incfile_register(src, dest);
	rawlog = [];
	if _path.exists(dest):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR if not logonly else LOGLEVEL_WARN, op_name='addfile_op', details={
						'err_desc' : 'file already exists',
						'src' : src,
						'dest' : dest,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='addfile_op', details={
					'src' : src,
					'dest' : dest,
				}));
	rawlog.extend(shellexec([
			['mkdir', '-p', _path.dirname(dest)],
			['cp', '-r', src, dest],
		], logonly=logonly));
	return rawlog;

def override_op(src, dest, logonly=True):
	if not logonly:
		incfile_register(src, dest);
	rawlog = [];
	if not _path.isfile(dest):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='override_op', details={
						'err_desc' : 'file is not an existing regular file',
						'src' : src,
						'dest' : dest,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='override_op', details={
					'src' : src,
					'dest' : dest,
				}));
	rawlog.extend(shellexec([
			['cp', src, dest],
		], logonly=logonly));
	return rawlog;

def untag_op(path, origin_tag, logonly=True):
	rawlog = [];
	if path not in g_tagsmap:
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='untag_op', details={
						'err_desc' : 'path not tagged',
						'path' : path,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='untag_op', details={
					'path' : path,
					'tag' : g_tagsmap[path],
				}));
	g_tagsmap.pop(path);
	return rawlog;

def rmlink_op(link_path, logonly=True):
	rawlog = [];
	if not _path.islink(link_path):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='rmlink_op', details={
						'err_desc' : 'file is not an existing link file',
						'link_path' : link_path,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='rmlink_op', details={
					'link_path' : link_path,
				}));
	rawlog.extend(shellexec([
			['rm', link_path],
		], logonly=logonly));
	rawlog.extend(rmdir_op(_path.dirname(link_path), logonly=logonly));
	return rawlog;

def rmfile_op(path, logonly=True):
	rawlog = [];
	if _path.islink(path):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='rmfile_op', details={
						'err_desc' : 'file is an existing link',
						'path' : path,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='rmfile_op', details={
					'path' : path,
				}));
	rawlog.extend(shellexec([
					['rm', '-r', path],
				], logonly=logonly));
	rawlog.extend(rmdir_op(_path.dirname(path), logonly=logonly));
	return rawlog;

def restorelink_op(src, dest, logonly=True):
	rawlog = [];
	if _path.exists(dest):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR if not logonly else LOGLEVEL_WARN, op_name='restorelink_op', details={
						'err_desc' : 'dest already exists',
						'src' : src,
						'dest' : dest,
					}));
		if not logonly:
			return rawlog;
	if not _path.exists(src):
		rawlog.append(LogEntry(level=LOGLEVEL_ERR if not logonly else LOGLEVEL_WARN, op_name='restorelink_op', details={
						'err_desc' : 'src not exists',
						'src' : src,
						'dest' : dest,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='restorelink_op', details={
					'src' : src,
					'dest' : dest,
				}));
	rawlog.extend(shellexec([
					['mkdir', '-p', _path.dirname(dest)],
					['ln', '-s', src, dest],
				], logonly=logonly));
	return rawlog;

def tagfile_op(path, tag, logonly=True):
	rawlog = [];
	if path in g_tagsmap:
		rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='tagfile_op', details={
						'err_desc' : 'overriding tag',
						'path' : path,
						'origin_tag' : g_tagsmap[path],
						'target_tag' : tag,
					}));
		return rawlog;
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='tagfile_op', details={
					'path' : path,
					'tag' : tag,
				}));
	g_tagsmap[path] = tag;
	return rawlog;

def rmdir_op(path, logonly=True):
	rawlog = [];
	rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='rmdir', details={
					'path' : path,
				}));
	while _path.exists(path) and len(os.listdir(path)) == 0 and gettag(path) != 'k':
		rawlog.extend(shellexec([
						['rmdir', path],
					], logonly=logonly));
		path = _path.dirname(path);
	return rawlog;

def shellexec(cmd_list, logonly=True):
	if logonly:
		return [];
	rawlog = [];
	for cmd in cmd_list:
		if _sp.call(cmd):
			rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='shellexec', details={
							'err_desc' : 'shell execution error',
							'cmd' : cmd,
						}));
	return rawlog;

def map_tmppath(src):
	# use base64 instead of hex encoding to compress hash digest
	# md5 hash has 128 bit length, making two '=' char in the end of based64 string, which we just remove here
	return _b64.b64encode(_hash.md5(src).digest(), '-_')[:-2];

def incfile_init():
	global incfile_list;
	incfile_list = [];

def incfile_register(src, dest):
	if _path.isfile(src):
		incfile_list.append(dest);
		return;
	for dirpath, dirnames, filenames in os.walk(src):
		dest_dirpath = _path.join(dest, _path.relpath(dirpath, src));
		for filename in filenames:
			incfile_list.append(_path.join(dest_dirpath, filename));
	return;

def incfile_check():
	rawlog = [];
	for path in incfile_list:
		if not _path.exists(path):
			rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='incfile_check', details={
							'err_desc' : 'incfile doesn\'t exist',
							'file' : path,
						}));
			continue;
		if not _path.isfile(path):
			rawlog.append(LogEntry(level=LOGLEVEL_ERR, op_name='incfile_check', details={
							'err_desc' : 'incfile isn\'t a file',
							'file' : path,
						}));
	if len(rawlog) == 0:
		rawlog.append(LogEntry(level=LOGLEVEL_INFO, op_name='incfile_check', details={
						'inc_desc' : 'done',
						'checked_num' : len(incfile_list),
					}));
	return rawlog;

g_gitmap_ptn = re.compile('\'(.*)\' => \'(.*)\'');

def gitmap_load():
	global g_gitmap_fd; # git_path => data_path
	global g_gitmap_bd; # data_path => git_path
	g_gitmap_fd = {};
	g_gitmap_bd = {};
	with open(REPO_GITMAP_PATH, 'r') as gitmapfile:
		for line in gitmapfile:
			line = line.strip();
			mth = g_gitmap_ptn.match(line);
			git_path, data_path = mth.group(1), mth.group(2);
			git_path = _path.join(REPO_GIT_PATH, git_path);
			data_path = _path.join(REPO_DATA_PATH, data_path);
			assert git_path not in g_gitmap_fd;
			assert data_path not in g_gitmap_bd;
			g_gitmap_fd[git_path] = data_path;
			g_gitmap_bd[data_path] = git_path;
	return;

def gitmap_check():
	rawlog = [];
	for git_path in g_gitmap_fd:
		data_path = g_gitmap_fd[git_path];
		assert g_gitmap_bd[data_path] == git_path;
		assert _path.exists(git_path) and not _path.islink(git_path);
		assert _path.exists(data_path) and not _path.islink(data_path);
		assert _path.isfile(git_path) == _path.isfile(data_path);
	for git_path in g_gitmap_fd:
		git_path = g_gitmap_bd[data_path];
		assert g_gitmap_fd[git_path] == data_path;
	return;

def gitmap_forward(git_path, new_data_path=None):
	data_path = g_gitmap_fd[git_path] if git_path in g_gitmap_fd else None;
	if not new_data_path is None:
		g_gitmap_fd[git_path] = new_data_path;
		if not data_path is None:
			git_path_bd = g_gitmap_bd.pop(data_path);
		assert git_path_bd == git_path;
		g_gitmap_bd[new_data_path] = git_path;
	return data_path;

def gitmap_backward(data_path, new_git_path=None):
	git_path = g_gitmap_bd[data_path] if data_path in g_gitmap_bd else None;
	if not new_git_path is None:
		g_gitmap_bd[data_path] = new_git_path;
		if not git_path is None:
			data_path_bd = g_gitmap_fd.pop(git_path);
		assert data_path_bd == data_path;
		g_gitmap_fd[new_git_path] = data_path;
	return git_path;

def gitmap_dump():
	new_gitmap_path = '%s.new' % REPO_GITMAP_PATH;
	with open(new_gitmap_path, 'w') as gitmapfile:
		for git_path, data_path in g_gitmap_fd.iteritems():
			git_path = _path.relpath(git_path, REPO_GIT_PATH);
			data_path = _path.relpath(data_path, REPO_DATA_PATH);
			assert git_path.find('\'');
			assert data_path.find('\'');
			gitmapfile.write('\'%s\' => \'%s\'\n' % (git_path, data_path));
	return;

def gitmap_remap(rename_map):
	global g_gitmap_fd;
	global g_gitmap_bd;
	gitmap_fd = {};
	gitmap_bd = {};
	for git_path, data_path in g_gitmap_fd.iteritems():
		assert isancestor(REPO_DATA_PATH, data_path);
		ancestor = data_path;
		new_data_path = None;
		while len(ancestor) > len(REPO_DATA_PATH):
			if ancestor in rename_map:
				new_ancestor = rename_map[ancestor];
				new_data_path = _path.join(new_ancestor, _path.relpath(data_path, ancestor));
				new_data_path = _path.realpath(new_data_path);
				break;
			ancestor = _path.dirname(ancestor);
		if not new_data_path is None:
			gitmap_fd[git_path] = new_data_path;
			gitmap_bd[new_data_path] = git_path;
		else:
			gitmap_fd[git_path] = data_path;
			gitmap_bd[data_path] = git_path;
	g_gitmap_fd = gitmap_fd;
	g_gitmap_bd = gitmap_bd;
	return;

def get_iter_gitmap(): # (git_path, data_path)
	return g_gitmap_fd.iteritems();

g_entryptn = re.compile(r'^{(.*)}\:'); # '{$path}:'
g_entry_labelptn = re.compile(r'^\t@(\w+)(: .*|\(.*\))?');
g_entry_commentptn = re.compile(r'^\t#.*');
g_header_commentptn = re.compile(r'^#.*');
def load_entryfile():
	global g_header;
	global g_entrylist;
	global g_active_entrymap;
	g_header = '';
	g_entrylist = [];
	g_active_entrymap = {};

	path = None;
	entry = None;
	labelset = None;

	def _push_entry():
		assert not entry is None;
		assert not labelset is None;
		if not 'discarded' in labelset and not 'renamed' in labelset:
			assert not path in g_active_entrymap;
			g_active_entrymap[path] = len(g_entrylist);
		g_entrylist.append(entry);

	with open(REPO_ENTRYFILE_PATH, 'r') as entryfile:
		for line in entryfile:
			line = line.rstrip();
			if len(line) == 0:
				continue;
			mth = g_header_commentptn.match(line);
			if mth:
				assert path is None;
				g_header += line + '\n';
				continue;
			mth = g_entryptn.match(line);
			if mth:
				if not path is None:
					_push_entry();
				entry = [];
				labelset = set();
				path = mth.group(1);
				entry.append(line);
				continue;
			mth = g_entry_labelptn.match(line);
			if mth:
				assert not path is None;
				label = mth.group(1);
				labelset.add(label);
				entry.append(line);
				continue;
			mth = g_entry_commentptn.match(line);
			if mth:
				assert not path is None;
				entry.append(line);
				continue;
			assert False;
		if not path is None:
			_push_entry();
	return;

def dump_entryfile():
	new_entryfile_path = '%s.new' % REPO_ENTRYFILE_PATH;
	with open(new_entryfile_path, 'w') as entryfile:
		entryfile.write(g_header);
		for entry in g_entrylist:
			for line in entry:
				entryfile.write('%s\n' % line);
	return;

def discard_entry(path):
	assert isancestor(REPO_BASE_PATH, path);
	path = _path.relpath(path, REPO_BASE_PATH);
	assert path in g_active_entrymap;
	g_entrylist[g_active_entrymap.pop(path)].append('\t@discarded');
	return;

def rename_entry(rename_map):
	src_map = {};
	for src, dest in rename_map.iteritems():
		assert isancestor(REPO_BASE_PATH, src);
		assert isancestor(REPO_BASE_PATH, dest);
		src = _path.relpath(src, REPO_BASE_PATH);
		dest = _path.relpath(dest, REPO_BASE_PATH);
		assert src in g_active_entrymap;
		src_entry = g_entrylist[g_active_entrymap.pop(src)];
		src_map[src] = src_entry;
	for src, dest in rename_map.iteritems():
		assert isancestor(REPO_BASE_PATH, src);
		assert isancestor(REPO_BASE_PATH, dest);
		src = _path.relpath(src, REPO_BASE_PATH);
		dest = _path.relpath(dest, REPO_BASE_PATH);
		assert not dest in g_active_entrymap;
		src_entry = src_map[src];
		dest_entry = ['{%s}:' % dest] + src_entry[1:];
		src_entry.append('\t@renamed: %s' % dest);
		g_active_entrymap[dest] = len(g_entrylist);
		g_entrylist.append(dest_entry);
	return;

def add_entry(path):
	assert isancestor(REPO_BASE_PATH, path);
	path = _path.relpath(path, REPO_BASE_PATH);
	assert path not in g_active_entrymap;
	g_active_entrymap[path] = len(g_entrylist);
	g_entrylist.append([
				'{%s}:' % path,
				'\t# @todo: new entry',
			]);
	return;

def isactive_entry(path):
	assert isancestor(REPO_BASE_PATH, path);
	path = _path.relpath(path, REPO_BASE_PATH);
	return path in g_active_entrymap;

def enum_active_entries(enum_func): # enum_func(path, entry)
	for path, idx in g_active_entrymap.items(): # use dict.items() to get a copy of map
		entry = g_entrylist[idx];
		enum_func(_path.join(REPO_BASE_PATH, path), entry);
	return;

def commonpath_set(root_path):
	global REPO_BASE_PATH;
	global REPO_CACHE_PATH;
	global REPO_AGGSRC_PATH;
	global REPO_GIT_PATH;
	global REPO_GITMAP_PATH;
	global REPO_DATA_PATH;
	global REPO_ARCH_PATH;
	global REPO_TAGS_PATH;
	global REPO_TMP_PATH;
	global REPO_ENTRYFILE_PATH;
	global REALTIME_LOGPATH;

	REPO_BASE_PATH      = root_path;
	REPO_CACHE_PATH     = _path.join(REPO_BASE_PATH, 'cache/docs');
	REPO_AGGSRC_PATH    = _path.join(REPO_BASE_PATH, 'Copy');
	REPO_GIT_PATH       = _path.join(REPO_BASE_PATH, 'github');
	REPO_GITMAP_PATH    = _path.join(REPO_BASE_PATH, 'cache/gitmap.log');
	REPO_DATA_PATH      = _path.join(REPO_BASE_PATH, 'data/docs');
	REPO_ARCH_PATH      = _path.join(REPO_BASE_PATH, 'arch');
	REPO_TAGS_PATH      = _path.join(REPO_BASE_PATH, 'tagged');
	REPO_TMP_PATH       = _path.join(REPO_BASE_PATH, 'tmp');
	REPO_ENTRYFILE_PATH = _path.join(REPO_BASE_PATH, 'data/indexes/entry.log');
	REALTIME_LOGPATH    = _path.join(REPO_BASE_PATH, 'realtime.log');
	return;
