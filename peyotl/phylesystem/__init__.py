#!/usr/bin/env python
'''Utilities for dealing with local filesystem
copies of the phylesystem repositories.
'''
from peyotl.utility import get_config, expand_path, get_logger
import json
try:
    import anyjson
except:
    import json
    class Wrapper(object):
        pass
    anyjson = Wrapper()
    anyjson.loads = json.loads
try:
    from dogpile.cache.api import NO_VALUE
except:
    pass #caching is optional
from peyotl.phylesystem.git_actions import GitAction
from peyotl.nexson_syntax import detect_nexson_version
from peyotl.nexson_validation import ot_validate
from peyotl.nexson_validation._validation_base import NexsonAnnotationAdder
import codecs
import os
from threading import Lock
_LOG = get_logger(__name__)
_study_index_lock = Lock()
_study_index = None


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


def get_repos(par_list=None):
    '''Returns a dictionary of name -> filepath
    `name` is the repo name based on the dir name (not the get repo). It is not
        terribly useful, but it is nice to have so that any mirrored repo directory can
        use the same naming convention.
    `filepath` will be the full path to the repo directory (it will end in `name`)
    '''
    _repos = {} # key is repo name, value repo location
    if par_list is None:
        par_list = _get_phylesystem_parent()
    elif not isinstance(par_list, list):
        par_list = [par_list]
    for p in par_list:
        if not os.path.isdir(p):
            raise ValueError('No phylesystem parent "{p}" is not a directory'.format(p=p))            
        for name in os.listdir(p):
            if os.path.isdir(os.path.join(p, name + '/.git')):
                _repos[name] = os.path.abspath(os.path.join(p, name))
    if len(_repos) == 0:
        raise ValueError('No git repos in {parent}'.format(str(par_list)))
    return _repos

def create_id2repo_pair_dict(path, tag):
    d = {}
    for triple in os.walk(path):
        root, files = triple[0], triple[2]
        for filename in files:
            if filename.endswith('.json'):
                # if file is in more than one place it gets over written.
                #TODO EJM Needs work 
                study_id = filename[:-5]
                d[study_id] = (tag, root, os.path.join(root,filename))
    return d

def _initialize_study_index(repos_par=None):
    d = {} # Key is study id, value is repo,dir tuple
    repos = get_repos(repos_par)
    for repo in _repos:
        p = os.path.join(_repos[repo], 'study')
        dr = create_id2repo_pair_dict(p, repo)
        d.update(dr)
    return d

def get_paths_for_study_id(study_id, repos_par=None):
    global _study_index
    _study_index_lock.acquire()
    if ".json" not in study_id:
         study_id=study_id+".json" #@EJM risky?
    try:
        if _study_index is None:
            _study_index = _initialize_study_index(repos_par)
        return _study_index[study_id]
    except KeyError, e:
        raise ValueError("Study {} not found in repo".format(study_id))
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

class PhylesystemShard(object):
    '''Wrapper around a git repos holding nexson studies'''
    def __init__(self,
                 name,
                 path,
                 repo_nexml2json=None,
                 git_ssh=None,
                 pkey=None,
                 git_action_class=GitAction,
                 push_mirror_repo_path=None):
        self._ga_class = git_action_class
        self.git_ssh = git_ssh
        self.pkey = pkey
        self.name = name
        dot_git = os.path.join(path, '.git')
        study_dir = os.path.join(path, 'study')
        self.push_mirror_repo_path = push_mirror_repo_path
        if not os.path.isdir(path):
            raise ValueError('"{p}" is not a directory'.format(p=path))
        if not os.path.isdir(dot_git):
            raise ValueError('"{p}" is not a directory'.format(p=dot_git))
        if not os.path.isdir(study_dir):
            raise ValueError('"{p}" is not a directory'.format(p=study_dir))
        d = create_id2repo_pair_dict(study_dir, name)
        self._study_index = d
        self.path = path
        self.git_dir = dot_git
        self.study_dir = study_dir
        if repo_nexml2json is None:
            try:
                repo_nexml2json = get_config('phylesystem', 'repo_nexml2json')
            except:
                pass
            if repo_nexml2json == None:
                repo_nexml2json = self.diagnose_repo_nexml2json()
        self.repo_nexml2json = repo_nexml2json
    def get_study_index(self):
        return self._study_index
    study_index = property(get_study_index)
    def diagnose_repo_nexml2json(self):
        fp = self.study_index.values()[0][2]
        with codecs.open(fp, mode='rU', encoding='utf-8') as fo:
            fj = json.load(fo)
            return detect_nexson_version(fj)
    def create_git_action(self):
        return self._ga_class(repo=self.path, git_ssh=self.git_ssh, pkey=self.pkey)
    def push_to_remote(self, remote_name):
        if self.push_mirror_repo_path is None:
            raise RuntimeError('This PhylesystemShard has no push mirror, so it cannot push to a remote.')
        mirror_ga = self._ga_class(repo=self.push_to_remote, git_ssh=self.git_ssh, pkey=self.pkey)
        working_ga = self(create_git_action)
        with mirror_ga.lock():
            with working_ga.lock():
                mirror_ga.fetch(remote='origin')
            mirror_ga.merge('origin/master', destination='master')
            mirror_ga.push_to_known_trailing(branch='master', remote=remote_name, remote_branch='master')
        return True



_CACHE_REGION_CONFIGURED = False
_REGION = None
def _make_phylesystem_cache_region():
    '''Only intended to be called by the Phylesystem singleton.
    '''
    global _CACHE_REGION_CONFIGURED, _REGION
    if _CACHE_REGION_CONFIGURED:
        return _REGION
    _CACHE_REGION_CONFIGURED = True
    try:
        from dogpile.cache import make_region
    except:
        _LOG.debug('dogpile.cache not available')
        return
    region = None
    trial_key = 'test_key'
    trial_val =  {'test_val': [4, 3]}
    try:
        a = {
            'host': 'localhost',
            'port': 6379,
            'db': 0, # default is 0
            'redis_expiration_time': 60*60*24*2,   # 2 days
            'distributed_lock': False #True if multiple processes will use redis
        }
        region = make_region().configure('dogpile.cache.redis', arguments=a)
        _LOG.debug('cache region set up with cache.redis.')
        _LOG.debug('testing redis caching...')
        region.set(trial_key, trial_val)
        assert(trial_val == region.get(trial_key))
        _LOG.debug('redis caching works')
        region.delete(trial_key)
        _REGION = region
        return region
    except:
        _LOG.exception('redis cache set up failed.')
        region = None
    '''_LOG.debug('Going to try dogpile.cache.dbm ...')
    first_par = _get_phylesystem_parent()[0]
    cache_db_dir = os.path.split(first_par)[0]
    cache_db = os.path.join(cache_db_dir, 'phylesystem-cachefile.dbm')
    _LOG.debug('dogpile.cache region using "{}"'.format(cache_db))
    try:
        a = {'filename': cache_db}
        region = make_region().configure('dogpile.cache.dbm',
                                         expiration_time = 36000,
                                         arguments = a)
        _LOG.debug('cache region set up with cache.dbm.')
        _LOG.debug('testing anydbm caching...')
        region.set(trial_key, trial_val)
        assert(trial_val == region.get(trial_key))
        _LOG.debug('anydbm caching works')
        region.delete(trial_key)
        _REGION = region
        return region
    except:
        _LOG.exception('anydbm cache set up failed')
        _LOG.debug('exception in the configuration of the cache.')
    '''
    _LOG.debug('Phylesystem will not use caching')
    return None


class _Phylesystem(object):
    '''Wrapper around a set of sharded git repos.
    '''
    def __init__(self,
                 repos_dict=None,
                 repos_par=None,
                 with_caching=True,
                 repo_nexml2json=None,
                 git_ssh=None,
                 pkey=None, 
                 git_action_class=GitAction,
                 mirror_info=None):
        '''
        Repos can be found by passing in a `repos_par` (a directory that is the parent of the repos)
            or by trusting the `repos_dict` mapping of name to repo filepath.
        `with_caching` should be True for non-debugging uses.
        `repo_nexml2json` is optional. If specified all PhylesystemShard repos are assumed to store
            files of this version of nexson syntax.
        `git_ssh` is the path of an executable for git-ssh operations.
        `pkey` is the PKEY that has to be in the env for remote, authenticated operations to work
        `git_action_class` is a subclass of GitAction to use. the __init__ syntax must be compatible
            with GitAction
        If you want to use a mirrors of the repo for pushes or pulls, send in a `mirror_info` dict:
            mirror_info['push'] and mirror_info['pull'] should be dicts with the following keys:
            'parent_dir' - the parent directory of the mirrored repos
            'remote_map' - a dictionary of remote name to prefix (the repo name + '.git' will be
                appended to create the URL for pushing).
        '''
        push_mirror_repos_par = None
        push_mirror_remote_map = {}
        if mirror_info:
            push_mirror_info = mirror_info.get('push', {})
            if push_mirror_info:
                push_mirror_repos_par = push_mirror_info['parent_dir']
                push_mirror_remote_map = push_mirror_info.get('remote_map', {})
                if push_mirror_repos_par:
                    if not os.path.exists(push_mirror_repos_par):
                        os.makedirs(push_mirror_repos_par)
                    if not os.path.isdir(push_mirror_repos_par):
                        raise ValueError('Specified push_mirror_repos_par, "{}", is not a directory'.format(push_mirror_repos_par))
        if repos_dict is None:
            repos_dict = get_repos(repos_par)
        shards = []
        repo_name_list = repos_dict.keys()
        repo_name_list.sort()
        for repo_name in repo_name_list:
            repo_filepath = repos_dict[repo_name]
            push_mirror_repo_path = None
            if push_mirror_repos_par:
                expected_push_mirror_repo_path = os.path.join(push_mirror_repos_par, repo_name)
                if os.path.isdir(expected_push_mirror_repo_path):
                    push_mirror_repo_path = expected_push_mirror_repo_path
            shard = PhylesystemShard(repo_name,
                                     repo_filepath,
                                     git_ssh=git_ssh,
                                     pkey=pkey,
                                     repo_nexml2json=repo_nexml2json,
                                     git_action_class=git_action_class,
                                     push_mirror_repo_path=push_mirror_repo_path)
            # if the mirror does not exist, clone it...
            if push_mirror_repos_par and (push_mirror_repo_path is None):
                GitAction.clone_repo(push_mirror_repos_par, repo_name, repo_filepath)
                if not os.path.isdir(expected_push_mirror_repo_path):
                    raise ValueError('git clone in mirror bootstrapping did not produce a directory at {}'.format(expected_push_mirror_repo_path))
                for remote_name, remote_url_prefix in push_mirror_remote_map.items():
                    if remote_name in ['origin', 'originssh']:
                        raise ValueError('"{}" is a protected remote name in the mirrored repo setup'.format(remote_name))
                    remote_url = remote_url_prefix + '/' + repo_name + '.git'
                    GitAction.add_remote(expected_push_mirror_repo_path, remote_name, remote_url)
                shard.push_mirror_repo_path = push_mirror_repo_path
            shards.append(shard)


        d = {}
        for s in shards:
            for k, v in s.study_index.items():
                if k in d:
                    raise KeyError('study "{i}" found in multiple repos'.format(i=k))
                d[k] = s
        self._study2shard_map = d
        self._shards = shards
        self._growing_shard = shards[-1] # generalize with config...
        self.repo_nexml2json = shards[-1].repo_nexml2json
        if with_caching:
            self._cache_region = _make_phylesystem_cache_region()
        else:
            self._cache_region = None
        self.git_action_class=git_action_class
        self._cache_hits = 0

    def get_shard(self, study_id):
        return self._study2shard_map[study_id]

    def create_git_action(self, study_id):
        shard = self.get_shard(study_id)
        return shard.create_git_action()

    def create_git_action_for_new_study(self):
        ga = self._growing_shard.create_git_action()
        # studies created by the OpenTree API start with o,
        # so they don't conflict with new study id's from other sources
        new_resource_id = "o%d" % (ga.newest_study_id() + 1)
        return ga, new_resource_id

    def add_validation_annotation(self, study_obj, sha):
        need_to_cache = False
        adaptor = None
        if self._cache_region is not None:
            key = 'v' + sha
            annot_event = self._cache_region.get(key, ignore_expiration=True)
            if annot_event != NO_VALUE:
                _LOG.debug('cache hit for ' + key)
                adaptor = NexsonAnnotationAdder()
                self._cache_hits += 1
            else:
                _LOG.debug('cache miss for ' + key)
                need_to_cache = True
        
        if adaptor is None:
            bundle = ot_validate(study_obj)
            annotation = bundle[0]
            annot_event = annotation['annotationEvent']
            del annot_event['@dateCreated'] #TEMP
            del annot_event['@id'] #TEMP
            adaptor = bundle[2]
        adaptor.replace_same_agent_annotation(study_obj, annot_event)
        if need_to_cache:
            self._cache_region.set(key, annot_event)
            _LOG.debug('set cache for ' + key)

        return annot_event

    def return_study(self,
                     study_id,
                     branch='master',
                     commit_sha=None,
                     return_WIP_map=False):
        ga = self.create_git_action(study_id)
        with ga.lock():
            #_LOG.debug('pylesystem.return_study({s}, {b}, {c}...)'.format(s=study_id, b=branch, c=commit_sha))
            
            blob = ga.return_study(study_id,
                                   branch=branch,
                                   commit_sha=commit_sha,
                                   return_WIP_map=return_WIP_map)
            nexson = anyjson.loads(blob[0])
            if return_WIP_map:
                return nexson, blob[1], blob[2]
            return nexson, blob[1]

    def get_blob_sha_for_study_id(self, study_id, head_sha):
        ga = self.create_git_action(study_id)
        studypath = ga.paths_for_study(study_id)[1]
        return ga.get_blob_sha_for_file(studypath, head_sha)

    def push_study_to_remote(self, remote_name, study_id=None):
        '''This will push the master branch to the remote named `remote_name`
        using the mirroring strategy to cut down on locking of the working repo.

        `study_id` is used to determine which shard should be pushed.
        if `study_id is None, all shards are pushed.
        '''
        if study_id is None:
            #@TODO should spawn a thread of each shard...
            for shard in self._shards:
                if not shard.push_to_remote(remote_name):
                    return False
            return True
        shard = self.get_shard(study_id)
        return shard.push_to_remote(remote_name)

_THE_PHYLESYSTEM = None
def Phylesystem(repos_dict=None,
                repos_par=None,
                with_caching=True,
                repo_nexml2json=None,
                git_ssh=None,
                pkey=None, 
                git_action_class=GitAction,
                mirror_info=None):
    '''Factory function for a _Phylesystem object.

    A wrapper around the _Phylesystem class instantiation for 
    the most common use case: a singleton _Phylesystem.
    If you need distinct _Phylesystem objects, you'll need to
    call that class directly.
    '''
    global _THE_PHYLESYSTEM
    if _THE_PHYLESYSTEM is None:
        _THE_PHYLESYSTEM = _Phylesystem(repos_dict=repos_dict,
                                        repos_par=repos_par,
                                        with_caching=with_caching,
                                        repo_nexml2json=repo_nexml2json,
                                        git_ssh=git_ssh,
                                        pkey=pkey,      
                                        git_action_class=git_action_class,
                                        mirror_info=mirror_info)
    return _THE_PHYLESYSTEM

# Cache keys:
# v+SHA = annotation event from validation