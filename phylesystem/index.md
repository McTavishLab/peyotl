---
layout: page
title: phylesystem
permalink: /phylesystem/
---
Phylesystem is a series of git repository used to store phylogenetic statements (typically published trees).
You can download the full set of phylesystem shards (there is only one, at this point) by following the instructions on https://github.com/OpenTreeOfLife/phylesystem
and then pointing peyotl to your local copy of phylesystem as described on the [Configuration](../Configuration) page.

If you have a local copy of the phylesystem, then you can peyotl's [phylesystem-api wrapper](../PhylesystemAPIWrapper) to use your local copy by using `get_from='local'` when creating an instance of the wrapper:

    from peyotl.api.phylesystem_api import PhylesystemAPI
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    local_phylesystem_controller = phylesystem_api_wrapper.phylesystem_obj
    for study_id, file_path in local_phylesystem_controller.iter_study_filepaths():
        print study_id, 'is in', file_path

You can perform the phylesystem_api functions on a local version of the PhylesystemAPI class, as well.
But the wrappers created using `get_from='local'` are the only ones that allow you to iterate over all studies.
