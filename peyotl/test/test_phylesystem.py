#! /usr/bin/env python
from peyotl.phylesystem import _Phylesystem
import unittest
from peyotl.test.support import pathmap

class TestPhylesystem(unittest.TestCase):
    def setUp(self):
        self.r = pathmap.get_test_repos()
    def testInit(self):
        p = _Phylesystem(repos_dict=self.r)
        self.assertEqual(2, len(p._shards))
    def testStudyIndexing(self):
        p = _Phylesystem(repos_dict=self.r)
        k = p._study2shard_map.keys()
        k.sort()
        self.assertEqual(k, ['10', '11', '12', '9'])
    def testURL(self):
        p = _Phylesystem(repos_dict=self.r)
        print p.get_public_url('9')
    def testStudyList(self):
        p = _Phylesystem(repos_dict=self.r)
        print p.get_study_ids()
if __name__ == "__main__":
    unittest.main()