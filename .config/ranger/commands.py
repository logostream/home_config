from ranger.api.commands import *
from ranger.ext.get_executables import get_executables
from ranger.core.runner import ALLOWED_FLAGS
import os
from ranger.core.loader import CommandLoader

class compress(Command):
	def execute(self):
		""" Compress marked files to current directory """
		cwd = self.fm.env.cwd
		marked_files = cwd.get_selection()

		if not marked_files:
			return

		def refresh(_):
			cwd = self.fm.env.get_directory(original_path)
			cwd.load_content()

		original_path = cwd.path
		parts = self.line.split()
		au_flags = parts[1:]

		descr = "compressing files in: " + os.path.basename(parts[1])
		obj = CommandLoader(args=['apack'] + au_flags + \
				[os.path.relpath(f.path, cwd.path) for f in marked_files], descr=descr)

		obj.signal_bind('after', refresh)
		self.fm.loader.add(obj)

	def tab(self):
		""" Complete with current folder name """

		extension = ['.zip', '.tar.gz', '.rar', '.7z']
		return ['compress ' + os.path.basename(self.fm.env.cwd.path) + ext for ext in extension]

class extracthere(Command):
	def execute(self):
		""" Extract copied files to current directory """
		copied_files = tuple(self.fm.env.copy)

		if not copied_files:
			return

		def refresh(_):
			cwd = self.fm.env.get_directory(original_path)
			cwd.load_content()

		one_file = copied_files[0]
		cwd = self.fm.env.cwd
		original_path = cwd.path
		au_flags = ['-X', cwd.path]
		au_flags += self.line.split()[1:]
		au_flags += ['-e']

		self.fm.env.copy.clear()
		self.fm.env.cut = False
		if len(copied_files) == 1:
			descr = "extracting: " + os.path.basename(one_file.path)
		else:
			descr = "extracting files from: " + os.path.basename(one_file.dirname)
		obj = CommandLoader(args=['aunpack'] + au_flags \
				+ [f.path for f in copied_files], descr=descr)

		obj.signal_bind('after', refresh)
		self.fm.loader.add(obj)
