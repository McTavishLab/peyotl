#!/usr/bin/env python
'''Utilities for dealing with local filesystem
copies of the phylesystem repositories.
'''
from peyotl.utility import get_config, expand_path
try:
    import anyjson
except:
    import json
    class Wrapper(object):
        pass
    anyjson = Wrapper()
    anyjson.loads = json.loads
import codecs
import os
from threading import Lock
_study_index_lock = Lock()
_study_index = None


def get_HEAD_SHA1(git_dir):
    '''Not locked!
    '''
    head_file = os.path.join(git_dir, 'HEAD')
    with open(head_file, 'rU') as hf:
        head_contents = hf.read().strip()
    assert(head_contents.startswith('ref: '))
    ref_filename = head_contents[5:] #strip off "ref: "
    real_ref = os.path.join(git_dir, ref_filename)
    with open(real_ref, 'rU') as rf:
        return rf.read().strip()

def _get_phylesystem_parent():
    if 'PHYLESYSTEM_PARENT' in os.environ:
        phylesystem_parent = os.environ.get('PHYLESYSTEM_PARENT')
    else:
        try:
            phylesystem_parent = expand_path(get_config('phylesystem', 'parent'))
        except:
            raise ValueError('No phylesystem parent specified in config or environmental variables')
    x = phylesystem_parent.split(':') #TEMP hardcoded assumption that : does not occur in a path name
    return(x)


def _initialize_study_index():
    d = {} # Key is study id, value is repo,dir tuple
    _repos = {} # key is repo name, value repo location
    par_list = _get_phylesystem_parent()
    for p in par_list:
        if not os.path.isdir(p):
            raise ValueError('No phylesystem parent "{p}" is not a directory'.format(p=p))            
        for name in os.listdir(p):
            if os.path.isdir(os.path.join(p, name + '/.git')):
                _repos[name] = os.path.join(p, name)
    if len(_repos)==0:
        raise ValueError('No git repos in {parent}'.format(str(par_list)))
    for repo in _repos:
        for triple in os.walk(os.path.join(_repos[repo], 'study')):
            root, files = triple[0], triple[2]
            for filename in files:
                if ".json" in filename:
                    # if file is in more than one place it gets over written.
                    #TODO EJM Needs work 
                    d[filename] = (repo, root)
    return d

def get_paths_for_study_id(study_id):
    global _study_index
    _study_index_lock.acquire()
    try:
        if _study_index is None:
            _study_index = _initialize_study_index()
        return _study_index[study_id]
    finally:
        _study_index_lock.release()


def create_new_path_for_study_id(study_id):
    _study_index_lock.acquire()
    try:
        pass
    finally:
        _study_index_lock.release()

def phylesystem_study_objs(**kwargs):
    '''Generator that iterates over all detected phylesystem studies.
    Returns a pair (study_id, study_obj)
    See documentation about specifying PHYLESYSTEM_PARENT
    '''
    for study_id, fp in phylesystem_study_paths(**kwargs):
        with codecs.open(fp, 'rU', 'utf-8') as fo:
            try:
                nex_obj = anyjson.loads(fo.read())['nexml']
                yield (study_id, nex_obj)
            except Exception:
                pass

