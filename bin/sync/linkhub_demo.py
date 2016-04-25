import os
import os.path as _path
import ruamel.yaml as _yaml

_HOME = os.environ['HOME']
_LINKHUB_PATH = _path.join(_HOME, 'linkhub')
_LINKMAP_PATH = _path.join(_LINKHUB_PATH, 'linkmap.yaml')

def _load_linkmap():
	global _linkmap_yaml # original yaml text
	global _linkmap # parsed yaml object

	assert _path.exists(_LINKMAP_PATH)
	with open(_LINKMAP_PATH, 'r') as linkmap_yaml_file:
		_linkmap_yaml = ''.join(linkmap_yaml_file.readlines())
		_linkmap = _yaml.load(_linkmap_yaml, _yaml.RoundTripLoader)
	return

def _info():
	return
