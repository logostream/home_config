#!/usr/bin/python
import os;
import sys;
import argparse;

# related dirs to go

def rreplace(s, old, new, count):
    return (s[::-1].replace(old[::-1], new[::-1], count))[::-1];

g_dir_table = [];
def register_dir(group, desc):
    def dir_decoractor(transform):
        g_dir_table.append({
            'group': group,
            'desc': desc,
            'transform': transform
        });
        return transform;
    return dir_decoractor;

def list_dirs():
    for entry in g_dir_table:
        print "%s: %s" % (entry['group'], entry['desc']);
    return;

def go_dirs(gopath, srcpath):
    target = None;
    for entry in g_dir_table:
        if gopath in entry['group']:
            target = entry['transform'](gopath, srcpath);
            break;
    if target is None:
        print >> sys.stderr, "no group matched for gopath(%s), turn to treat it as a real path" % gopath;
        target = os.path.abspath(gopath);
    if not os.path.exists(target):
        print >> sys.stderr, "path %s dosen't exist, turn to its nearest parent" % target;
        while not os.path.exists(target):
            target = os.path.dirname(target);
    return target;

@register_dir(['java', 'j'], '*/javatests/* => */java/*')
def _(gopath, srcpath):
    return rreplace(srcpath, '/javatests/', '/java/', 1);

@register_dir(['javatests', 'jut'], '*/java/* => */javatests/*')
def _(gopath, srcpath):
    return rreplace(srcpath, '/java/', '/javatests/', 1);

@register_dir(['blaze-bin', 'g/bin'], 'goto google3/blaze-bin/*')
def _(gopath, srcpath):
    target = srcpath;
    if target.rfind('/google3/blaze-bin/') != -1:
        return target;
    if target == srcpath:
        target = rreplace(srcpath, '/google3/blaze-genfiles/', '/google3/blaze-bin/', 1);
    if target == srcpath:
        target = rreplace(srcpath, '/google3/', '/google3/blaze-bin/', 1);
    return target;

@register_dir(['blaze-genfiles', 'g/gen', 'gen'], 'goto google3/blaze-genfiles/*')
def _(gopath, srcpath):
    target = srcpath;
    if target.rfind('/google3/blaze-genfiles/') != -1:
        return target;
    if target == srcpath:
        target = rreplace(srcpath, '/google3/blaze-bin/', '/google3/blaze-genfiles/', 1);
    if target == srcpath:
        target = rreplace(srcpath, '/google3/', '/google3/blaze-genfiles/', 1);
    return target;

@register_dir(['google3/src', 'g/src', 'src'], 'goto google3/* (source)')
def _(gopath, srcpath):
    target = srcpath;
    if target == srcpath:
        target = rreplace(srcpath, '/google3/blaze-bin/', '/google3/', 1);
    if target == srcpath:
        target = rreplace(srcpath, '/google3/blaze-genfiles/', '/google3/', 1);
    return target;

@register_dir(['google3', 'g/'], 'goto google3/ (root)')
def _(gopath, srcpath):
    target = srcpath;
    index = srcpath.rfind('/google3/');
    if index != -1:
        target = srcpath[:index] + '/google3/';
    return target;

@register_dir(['bin', 'tmp'], 'goto home based dir')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/%s' % (home, gopath);

@register_dir(['vim', 'ssh', 'tmux', 'config'], 'goto home based hidden dir')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/.%s' % (home, gopath);

@register_dir(['notes', 'nt'], 'goto github/notes')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/github/notes' % home;

@register_dir(['home_config', 'cfg'], 'goto github/home_config')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/github/home_config' % home;

@register_dir(['cfg/bin', 'c/bin'], 'goto github/home_config/bin')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/github/home_config/bin' % home;

@register_dir(['scrapbook', 'sbk'], 'goto github/scrapbook')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/github/scrapbook' % home;

@register_dir(['pushub', 'pb'], 'goto pushub')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/pushub' % home;

@register_dir(['pushub/tmp', 'pb/tmp'], 'goto pushub/tmp')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/pushub/tmp' % home;

@register_dir(['pushub/tmp/scratch', 'pb/sch', 'sch'], 'goto pushub/tmp/scratch')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/pushub/tmp/scratch' % home;

@register_dir(['pushub/scrapbook', 'pushub/sbk', 'pb/sbk'], 'goto pushub/scrapbook')
def _(gopath, srcpath):
    home = os.getenv('HOME');
    return '%s/pushub/tmp/scrapbook' % home;

def main():
    parser = argparse.ArgumentParser();
    parser.add_argument('gopath', nargs='?', help='related path');
    parser.add_argument('-s', '--srcpath', help='source path, default is $PWD');
    parser.add_argument('-l', '--list', help='list dir tables', action='store_true');
    args = parser.parse_args();

    if args.list:
        list_dirs();
        return;
    srcpath = args.srcpath;
    gopath = args.gopath;
    if gopath is None:
        parser.print_help();
        return;
    if srcpath is None:
        srcpath = os.getenv('PWD');
    srcpath = os.path.abspath(srcpath);
    target = go_dirs(gopath, srcpath);
    print target;

if __name__ == '__main__':
    main();
