Dependency
===
python-simplejson # support utf-8 encoding/decoding

Usage
===
bvt.py -- set of basic test cases
repo.py -- cli tool, entry point
	usage: req [-h] [-r ROOT] [-l]
		{status,agg,cache-commit,restore,entryfile,git-commit} ...

	optional arguments:
	-h, --help            show this help message and exit
	-r ROOT, --root ROOT  base root
	-l, --logonly         logonly

	action:
	{status,agg,cache-commit,restore,entryfile,git-commit}
	status              cache file status query
	agg                 aggregate from copy to cache
	cache-commit        commit from cache to data
	restore             restore miss from data to cache
	entryfile           sync entryfiles
	git-commit          commit from git to data
rsync_cd.sh $src_root $dest_root
	# sync includes cache/, data/, pushub/; not include github/, arch/
	# no --checksum by default
snapshot_test.sh $src_root $dest_root
	# depends on rsync_cd.sh
	# no --checksum by default
snapshot_take.sh $src_root $dest_root
	# including tagged (cache/tagged), data/, cache/, pushub/, not include github/
	# depends on rsync_cd.sh
	# has --checksum
snapshot_take.sh $src_root $dest_root
	# depends on rsync_cd.sh
	# has --checksum
pushub.sh
	# sync ~/pushub/tmp --> ssh://foo:~/pushub/$box_name
	# with -b syncback ssh://foo:~/pushub/$box_name -> ~/pushub, without affect ~/pushub/tmp
	# has --checksum
mirror_upload.sh
	# sync includes cache/, data/, pushub/, github/, arch/
	# has --checksum
mirror_download.sh
	# deprecated

Routine
===
1. check baseline ~/arch/snapshot/latest, have a test with snapshot_test.sh
2. check ~/pushub, ensure all stuff have been sync
3. `$ repo [-l] agg`, and check ~/cache/tagged, ~/cache/gitmap.log, snapshot_test.sh
4. take a before commit snapshot
5. restart ranger and make manually change
6. `$ repo [-l] cache-commit`, and check ~/cache/tagged, ~/cache/gitmap.log, snapshot_test.sh
7. `$ repo entryfile`, and check ~/data/indexes/entryfile.log
8. take a after commit snapshot, remove before one

Important Paths
===
# from common_def.py
directories
* cache     = ~/cache/docs
* data      = ~/data/docs
* aggsrc    = ~/pushub
* git       = ~/github
* arch      = ~/arch

files # all placed under some of the important path, so, no need to sync for alone
* tags      = ~/cache/tagged
* gitmap    = ~/cache/gitmap.log
* entryfile = ~/data/indexes/entry.log

tmp files
* tmp       = ~/tmp
* log       = ~/realtime.log
