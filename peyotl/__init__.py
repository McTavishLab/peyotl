#!/usr/bin/env python
'''
Small library for conducting operations over the 
entire set of NexSON files in one or more phylesystem 
repositories.

Typical usage:
################################################################################
from phylesystem_util import phylesystem_studies

for file_path in phylesystem_studies('parent/of/phylesystem/repo'):
    print (file_path)
'''
import collections
import logging
import sys
import os

_CONFIG = None
_CONFIG_FN = None
def config(section=None, param=None):
    '''
    Returns the config object if `section` and `param` are None, or the 
        value for the requested parameter.
    
    If the parameter (or the section) is missing, the exception is logged and
        None is returned.
    '''
    global _CONFIG, _CONFIG_FN
    if _CONFIG is None:
        from ConfigParser import SafeConfigParser
        _CONFIG_FN = os.path.expanduser("~/.peyotl/config")
        _CONFIG = SafeConfigParser()
        _CONFIG.read(_CONFIG_FN)
    if section is None and param is None:
        return _CONFIG
    try:
        v = _CONFIG.get(section, param)
        return v
    except:
        mf = 'Config file "{f}" does not contain option "{o}"" in section "{s}"\n'
        msg = mf.format(f=_CONFIG_FN, o=param, s=section)
        _LOG.error(msg)
        return None

_LOGGING_LEVEL_ENVAR="PEYOTL_LOGGING_LEVEL"
_LOGGING_FORMAT_ENVAR="PEYOTL_LOGGING_FORMAT"

def get_logging_level():
    if _LOGGING_LEVEL_ENVAR in os.environ:
        if os.environ[_LOGGING_LEVEL_ENVAR].upper() == "NOTSET":
            level = logging.NOTSET
        elif os.environ[_LOGGING_LEVEL_ENVAR].upper() == "DEBUG":
            level = logging.DEBUG
        elif os.environ[_LOGGING_LEVEL_ENVAR].upper() == "INFO":
            level = logging.INFO
        elif os.environ[_LOGGING_LEVEL_ENVAR].upper() == "WARNING":
            level = logging.WARNING
        elif os.environ[_LOGGING_LEVEL_ENVAR].upper() == "ERROR":
            level = logging.ERROR
        elif os.environ[_LOGGING_LEVEL_ENVAR].upper() == "CRITICAL":
            level = logging.CRITICAL
        else:
            level = logging.NOTSET
    else:
        level = logging.NOTSET
    return level

def get_logger(name="peyotl"):
    """
    Returns a logger with name set as given, and configured
    to the level given by the environment variable _LOGGING_LEVEL_ENVAR.
    """

#     package_dir = os.path.dirname(module_path)
#     config_filepath = os.path.join(package_dir, _LOGGING_CONFIG_FILE)
#     if os.path.exists(config_filepath):
#         try:
#             logging.config.fileConfig(config_filepath)
#             logger_set = True
#         except:
#             logger_set = False
    logger = logging.getLogger(name)
    if not hasattr(logger, 'is_configured'):
        logger.is_configured = False
    if not logger.is_configured:
        level = get_logging_level()
        rich_formatter = logging.Formatter("[%(asctime)s] %(filename)s (%(lineno)d): %(levelname) 8s: %(message)s")
        simple_formatter = logging.Formatter("%(levelname) 8s: %(message)s")
        raw_formatter = logging.Formatter("%(message)s")
        default_formatter = None
        logging_formatter = default_formatter
        if _LOGGING_FORMAT_ENVAR in os.environ:
            if os.environ[_LOGGING_FORMAT_ENVAR].upper() == "RICH":
                logging_formatter = rich_formatter
            elif os.environ[_LOGGING_FORMAT_ENVAR].upper() == "SIMPLE":
                logging_formatter = simple_formatter
            elif os.environ[_LOGGING_FORMAT_ENVAR].upper() == "NONE":
                logging_formatter = None
            else:
                logging_formatter = default_formatter
        else:
            logging_formatter = default_formatter
        if logging_formatter is not None:
            logging_formatter.datefmt='%H:%M:%S'
        logger.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging_formatter)
        logger.addHandler(ch)
        logger.is_configured = True
    return logger

def _expand_path(p):
    return os.path.expanduser(os.path.expandvars(p))

from phylesystem import phylesystem_study_paths, phylesystem_study_objs

def gen_otu_dict(nex_obj):
    '''Takes a NexSON object and returns a dict of 
    otu_id -> otu_obj
    '''
    o_dict = {}
    for ob in nex_obj.get('otus',[]):
        for o in ob.get('otu', []):
            oid = o['@id']
            o_dict[oid] = o
    return o_dict

def iter_tree(nex_obj):
    '''Generator over each tree object in the NexSON object.'''
    for tb in nex_obj.get('trees',[]):
        for tree in tb.get('tree',[]):
            yield tree

def iter_node(tree):
    '''Generator over each node object in the tree object.'''
    for nd in tree.get('node',[]):
        yield nd
