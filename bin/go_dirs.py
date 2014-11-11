#!/usr/bin/python
import os;
import sys;
import argparse;

# related dirs to go

def rreplace(s, old, new, count):
	return (s[::-1].replace(old[::-1], new[::-1], count))[::-1];

def go_dirs(gopath, srcpath):
	target = srcpath;
	if gopath in ['java', 'j']:
		target = rreplace(srcpath, '/javatests/', '/java/', 1);
	elif gopath in ['javatests', 'jut']:
		target = rreplace(srcpath, '/java/', '/javatests/', 1);
	elif gopath in ['blaze-bin', 'bin']:
		if target.rfind('/google3/blaze-bin/') != -1:
			return target;
		if target == srcpath:
			target = rreplace(srcpath, '/google3/blaze-genfiles/', '/google3/blaze-bin/', 1);
		if target == srcpath:
			target = rreplace(srcpath, '/google3/', '/google3/blaze-bin/', 1);
	elif gopath in ['blaze-genfiles', 'gen']:
		if target.rfind('/google3/blaze-genfiles/') != -1:
			return target;
		if target == srcpath:
			target = rreplace(srcpath, '/google3/blaze-bin/', '/google3/blaze-genfiles/', 1);
		if target == srcpath:
			target = rreplace(srcpath, '/google3/', '/google3/blaze-genfiles/', 1);
	elif gopath in ['google3/src', 'src']:
		if target == srcpath:
			target = rreplace(srcpath, '/google3/blaze-bin/', '/google3/', 1);
		if target == srcpath:
			target = rreplace(srcpath, '/google3/blaze-genfiles/', '/google3/', 1);
	elif gopath in ['google3/root', '/', 'google3']:
		index = srcpath.rfind('/google3/');
		if index != -1:
			target = srcpath[:index] + '/google3/';
	if not os.path.exists(target):
		print >> sys.stderr, "path %s dosen't exist, turn to its nearest partent" % target;
		while not os.path.exists(target):
			target = os.path.dirname(target);
	return target;

if __name__ == '__main__':
	parser = argparse.ArgumentParser();
	parser.add_argument('gopath', help='related path');
	parser.add_argument('-s', '--srcpath', help='source path, default is $PWD');
	args = parser.parse_args();

	srcpath = args.srcpath;
	gopath = args.gopath;
	if srcpath is None:
		srcpath = os.getenv('PWD');
	srcpath = os.path.abspath(srcpath);
	target = go_dirs(gopath, srcpath);
	print target;
