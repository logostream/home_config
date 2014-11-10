#!/usr/bin/python
import os;
import argparse;

# related dirs to go

def go_dirs(gopath, srcpath):
	if gopath == 'java':
	elif gopath == 'javatest':
	elif gopath == 'blaze-bin':
	elif gopath == 'blaze-genfiles':

if __name__ == '__main__':
	parser.add_argument('gopath', help='related path');
	parser.add_argument('-s', '--srcpath', help='source path, default is $PWD');
	args = parser.parse_args();

	srcpath = args.srcpath;
	gopath = args.gopath;
	if srcpath is None:
		srcpath = os.path.abspath(os.curdir);
	target = go_dirs(gopath, srcpath);
	print target;
