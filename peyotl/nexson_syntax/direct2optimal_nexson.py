#!/usr/bin/env python
'Direct2OptimalNexson class'
from peyotl.nexson_syntax.helper import NexsonConverter, \
                                        _get_index_list_of_values, \
                                        _index_list_of_values, \
                                        BY_ID_HONEY_BADGERFISH
from peyotl.utility import get_logger
_LOG = get_logger(__name__)

class Direct2OptimalNexson(NexsonConverter):
    '''Conversion of the direct port of NeXML to JSON (v 1.0)
    to the more optimized version (v 1.2).
    This is a dict-to-dict in-place conversion. No serialization is included.
    '''
    def __init__(self, conv_cfg):
        NexsonConverter.__init__(self, conv_cfg)
        self.suppress_label_if_ott_taxon = getattr(conv_cfg, 'suppress_label_if_ott_taxon', True)
    
    def convert_otus(self, otus_list):
        otusById = dict((i['@id'], i) for i in otus_list)
        otusElementOrder = [i['@id'] for i in otus_list]
        otusIdToOtuObj = {}
        for oid, otus_el in otusById.items():
            o_list = _index_list_of_values(otus_el, 'otu')
            otuById = dict((i['@id'], i) for i in o_list)
            otusIdToOtuObj[oid] = otuById
        # If all that succeeds, add the new object to the dict, creating a fat structure
        for k, v in otusIdToOtuObj.items():
            otusById[k]['otuById'] = v
        # Make the struct leaner
        if self.remove_old_structs:
            for v in otusById.values():
                del v['@id']
            for k, otu_obj in otusIdToOtuObj.items():
                o = otusById[k]
                del o['otu']
                for v in otu_obj.values():
                    del v['@id']
                    # move @label to ^ot:manualLabel if it is not ottTaxonName
                    # if self.suppress_label_if_ott_taxon:
                    #     if '@label' in v:
                    #         tax_name = v.get('^ot:ottTaxonName')
                    #         label = v.get('@label').strip()
                    #         if tax_name is None:
                    #             orig_name = v.get('^ot:originalLabel')
                    #             assert(orig_name is not None)
                    #             if label != orig_name:
                    #                 v['^ot:manualLabel'] = label
                    #         elif label != tax_name:
                    #             v['^ot:manualLabel'] = label
                    #         del v['@label']
        return otusById, otusElementOrder

    def convert_tree(self, tree):
        nodesById = {}
        root_node = None
        node_list = _index_list_of_values(tree, 'node')
        for node in node_list:
            nodesById[node['@id']] = node
            if node.get('@root') == "true":
                assert(root_node is None)
                root_node = node
        assert(root_node is not None)
        edgeBySourceId = {}
        edge_list = _get_index_list_of_values(tree, 'edge')
        for edge in edge_list:
            sourceId = edge['@source']
            eid = edge['@id']
            del edge['@id']
            byso = edgeBySourceId.setdefault(sourceId, {})
            byso[eid] = edge
        # If all that succeeds, add the new object to the dict, creating a fat structure
        tree['nodesById'] = nodesById
        tree['edgeBySourceId'] = edgeBySourceId
        tree['ot:rootNodeId'] = root_node['@id']
        # Make the struct leaner
        tid = tree['@id']
        if self.remove_old_structs:
            del tree['@id']
            del tree['node']
            del tree['edge']
            for node in node_list:
                if '^ot:isLeaf' in node:
                    del node['^ot:isLeaf']
                del node['@id']
        return tid, tree

    def convert(self, obj):
        '''Takes a dict corresponding to the honeybadgerfish JSON blob of the 1.0.* type and
        converts it to BY_ID_HONEY_BADGERFISH version. The object is modified in place
        and returned.
        '''
        if self.pristine_if_invalid:
            raise NotImplementedError('pristine_if_invalid option is not supported yet')

        nex = obj.get('nex:nexml') or obj['nexml']
        assert(nex)
        # Create the new objects as locals. This section should not
        #   mutate obj, so that if there is an exception the object
        #   is unchanged on the error exit
        otus = _index_list_of_values(nex, 'otus')
        o_t = self.convert_otus(otus)
        otusById, otusElementOrder = o_t
        trees = _get_index_list_of_values(nex, 'trees')
        treesById = dict((i['@id'], i) for i in trees)
        treesElementOrder = [i['@id'] for i in trees]
        treeContainingObjByTreesId = {}
        for tree_group in trees:
            treeById = {}
            treeElementOrder = []
            tree_array = _get_index_list_of_values(tree_group, 'tree')
            for tree in tree_array:
                t_t = self.convert_tree(tree)
                tid, tree_alias = t_t
                assert(tree_alias is tree)
                treeById[tid] = tree
                treeElementOrder.append(tid)
            treeContainingObjByTreesId[tree_group['@id']] = treeById
            tree_group['^ot:treeElementOrder'] = treeElementOrder

        # If all that succeeds, add the new object to the dict, creating a fat structure
        nex['otusById'] = otusById
        nex['^ot:otusElementOrder'] = otusElementOrder
        nex['treesById'] = treesById
        nex['^ot:treesElementOrder'] = treesElementOrder
        for k, v in treeContainingObjByTreesId.items():
            treesById[k]['treeById'] = v
        nex['@nexml2json'] = str(BY_ID_HONEY_BADGERFISH)
        # Make the struct leaner
        if self.remove_old_structs:
            del nex['otus']
            del nex['trees']
            for k, v in treesById.items():
                if 'tree' in v:
                    del v['tree']
                del v['@id']
        return obj
