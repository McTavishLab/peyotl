#!/usr/bin/env python
from peyotl import write_as_json
import codecs
import json
import time

def report_results(tag, duration, expected_fn, result):
    expected = json.load(codecs.open(expected_fn, 'rU', encoding='utf-8'))
    succeeded = True
    if expected != result:
        obtained_fn = expected_fn + '-obtained.json'
        write_as_json(result, obtained_fn)
        succeeded = False
    return {'tag': tag,
            'duration': duration,
            'expected-output':succeeded,
            'returned': True,
            'status': 200
           }

def report_error(tag, duration, err):
    r = {'tag': tag,
            'duration': duration,
            'expected-output':False,
            'returned': False,
            'returned': True,
            'status': err.response.status_code,
            'url': err.response.url,
            }
    if err.response.text:
        r['content'] = err.response.text
    return r


def _ot_call(tag, expected_fn, func, *valist, **kwargs):
    try:
        start_t = time.time()
        result = func(*valist, **kwargs)
        end_t = time.time()
        return report_results(tag, end_t - start_t, expected_fn, result)
    except HTTPError, x:
        end_t = time.time()
        return report_error(tag, end_t - start_t, x)

if __name__ == '__main__':
    from peyotl.api import APIWrapper
    from requests import HTTPError
    otwrap = APIWrapper()
    summary_list = []

    summary = _ot_call('treemachine/getSyntheticTree',
                       'curl-versions/getSyntheticTree.json',
                       otwrap.treemachine.get_synthetic_tree,
                       'otol.draft.22',
                       format='arguson',
                       node_id=3534540,
                       max_depth=3)
    summary_list.append(summary)
    
    summary = _ot_call('treemachine/getDraftTreeSubtreeForNodes',
                       'curl-versions/getDraftTreeSubtreeForNodes.json',
                       otwrap.treemachine.get_synth_tree_pruned,
                       ott_ids=[515698,515712,149491,876340,505091,840022,692350,451182,301424,876348,515698,1045579,267484,128308,380453,678579,883864,863991,3898562,23821,673540,122251,106729,1084532,541659]
                       )
    summary_list.append(summary)
    
    summary = _ot_call('treemachine/getSynthesisSourceList',
                       'curl-versions/getSynthesisSourceList.json',
                       otwrap.treemachine.get_synthetic_source_list,
                       )
    summary_list.append(summary)
    
    print summary_list
