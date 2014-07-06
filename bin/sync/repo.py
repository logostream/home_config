#!/usr/bin/python
import argparse;
import cache_ops as _cache;
import common_def as _common;
import os.path as _path;
import agg_ops as _agg;
import git_ops as _git;
import data_ops as _data;

def cachefile_status_query(args):
	root = '/home/stream';
	if args.root:
		assert len(args.root) == 1;
		root = _path.abspath(args.root[0]);
	assert _path.exists(root);
	_common.commonpath_set(root);
	_common.loadtags();
	path = _path.abspath(args.path);
	(status, ancestor) = _cache.status_check(path);
	print 'status: %s' % _common.get_status_desc(status);
	print 'ancestor: %s' % ancestor;
	return;

def aggregate_update(args):
	root = '/home/stream';
	if args.root:
		assert len(args.root) == 1;
		root = _path.abspath(args.root[0]);
	assert _path.exists(root);
	logonly = args.logonly;
	_common.commonpath_set(root);

	_common.LogEntry.open_realtime_log();
	_common.loadtags();
	_common.gitmap_load();
	_common.gitmap_check();
	rawlog = _agg.aggregate_update(_common.REPO_AGGSRC_PATH, logonly=logonly);
	if not logonly:
		_git.gitmap_update(rawlog);
	_common.gitmap_check();
	if not logonly:
		_common.gitmap_dump();
		_common.dumptags();
	_common.LogEntry.close_realtime_log();

	for logentry in rawlog:
		assert logentry.level != _common.LOGLEVEL_ERR;
	return;

def cache_commit_update(args):
	root = '/home/stream';
	if args.root:
		assert len(args.root) == 1;
		root = _path.abspath(args.root[0]);
	assert _path.exists(root);
	logonly = args.logonly;
	_common.commonpath_set(root);

	_common.LogEntry.open_realtime_log();
	_common.load_entryfile();
	_common.loadtags();
	_common.gitmap_load();
	_common.gitmap_check();
	rawlog = _cache.commit_update(_common.REPO_CACHE_PATH, logonly=logonly);
	if not logonly:
		_git.gitmap_update(rawlog);
	_common.gitmap_check();
	if not logonly:
		_common.gitmap_dump();
		_common.dumptags();
		_data.entryfile_update(rawlog);
		_common.dump_entryfile();
	_common.LogEntry.close_realtime_log();

	for logentry in rawlog:
		assert logentry.level != _common.LOGLEVEL_ERR;
	return;

def cache_restore_miss_update(args):
	root = '/home/stream';
	if args.root:
		assert len(args.root) == 1;
		root = _path.abspath(args.root[0]);
	assert _path.exists(root);
	logonly = args.logonly;
	_common.commonpath_set(root);

	_common.LogEntry.open_realtime_log();
	_common.loadtags();
	_common.gitmap_load();
	_common.gitmap_check();
	rawlog = _cache.restore_miss_update(_common.REPO_CACHE_PATH, _common.REPO_DATA_PATH, logonly=logonly);
	if not logonly:
		_git.gitmap_update(rawlog);
	_common.gitmap_check();
	if not logonly:
		_common.gitmap_dump();
		_common.dumptags();
	_common.LogEntry.close_realtime_log();

	for logentry in rawlog:
		assert logentry.level != _common.LOGLEVEL_ERR;
	return;

def entryfile_sync_update(args):
	root = '/home/stream';
	if args.root:
		assert len(args.root) == 1;
		root = _path.abspath(args.root[0]);
	assert _path.exists(root);
	logonly = args.logonly;
	_common.commonpath_set(root);

	_common.load_entryfile();
	_data.entryfile_sync(_common.REPO_DATA_PATH);
	_common.dump_entryfile();
	return;

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog='req'); # req standard for repo execution and query
	subparsers = parser.add_subparsers(title='action');
	parser.add_argument('-r', '--root', nargs=1, help='base root');
	parser.add_argument("-l", "--logonly", help="logonly", action='store_true');

	# status
	parser_status = subparsers.add_parser('status', help='cache file status query');
	parser_status.add_argument('path', help='file path');
	parser_status.set_defaults(action='status');

	# agg
	parser_agg = subparsers.add_parser('agg', help='aggregate from copy to cache');
	parser_agg.set_defaults(action='agg');

	# commit
	parser_commit = subparsers.add_parser('commit', help='commit from cache to data');
	parser_commit.set_defaults(action='commit');

	# restore
	parser_restore = subparsers.add_parser('restore', help='restore miss from cache to cache');
	parser_restore.set_defaults(action='restore');

	# entryfile
	parser_restore = subparsers.add_parser('entryfile', help='sync entryfiles');
	parser_restore.set_defaults(action='entryfile');

	args = parser.parse_args();
	{
		'status': cachefile_status_query,
		'agg': aggregate_update,
		'commit': cache_commit_update,
		'restore': cache_restore_miss_update,
		'entryfile': entryfile_sync_update,
	}[args.action](args);
	pass;
