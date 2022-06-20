from filters import *
import pytest


def test_wrong_dataset():
    # setup
    scene_struct = {
        "objects": [{
            "size": "small",
            "color": "red",
            "material": "metal",
            "shape": "cube",
        }]
    }
    metadata = {
        "dataset": "wrong_dataset",
    }

    with pytest.raises(AssertionError) as e:
        precompute_filter_options(scene_struct, metadata)
    assert str(e.value) == 'Unrecognized dataset'


def test_precompute_filter_options_single_object():
    # setup
    scene_struct = {
        "objects": [{
            "size": "small",
            "color": "red",
            "material": "metal",
            "shape": "cube",
        }]
    }
    metadata = {
        "dataset": "CLEVR-v1.0",
    }

    precompute_filter_options(scene_struct, metadata)
    result = scene_struct['_filter_options']
    for fltr, obj_idx in result.items():
        assert 0 in obj_idx, "The only object must be in all object_idx sets"
    assert len(result.keys()) == len(set(result.keys())), "each filter must be unique"


def test_precompute_filter_options_two_disjoint_object():
    # setup
    scene_struct = {
        "objects": [
            {
            "size": "small",
            "color": "red",
            "material": "metal",
            "shape": "cube",
            },
            {
            "size": "large",
            "color": "green",
            "material": "rubber",
            "shape": "sphere",
            }
            ]
    }
    metadata = {
        "dataset": "CLEVR-v1.0",
    }

    precompute_filter_options(scene_struct, metadata)
    result = scene_struct['_filter_options']
    for fltr, obj_idx in result.items():
        # avoid the match all filter
        if fltr != (None, None, None, None):
            assert not ((0 in obj_idx) and (1 in obj_idx)), "Disjoint objects must yield disjoint filters"
        

def test_find_filter_options_empty_object_idxs():
    # setup
    object_idxs = []
    scene_struct = {
        "objects": [{
            "size": "small",
            "color": "red",
            "material": "metal",
            "shape": "cube",
        }]
    }
    metadata = {
        "dataset": "CLEVR-v1.0",
    }

    result = find_filter_options(object_idxs, scene_struct, metadata)
    for fltr, obj_idxs in result.items():
        assert len(obj_idxs) == 0, "Object indices should contain zero elements, if the object indices list is empty!"

# TODO: Create individual tests from these functions
def test_derive_cf_filter_variants():
    assert derive_cf_attributes(("", "", "", "")) == [('', '', '', '')], "empty filters must yield a single empty variant"
    assert derive_cf_attributes(("", "", "", "thing")) == [('', '', '', '')], "thing is also an empty filter and empty filters must yield a single empty variant"
    assert derive_cf_attributes(("", "", "", "cube")) == [('', '', '', 'cube'), ('', '', '', '')], "a single filters must yield a single empty variant and the filter itself"
    assert derive_cf_attributes(("", "", "metal", "cube")) == [('', '', 'metal', 'cube'), ('', '', '', 'cube'), ('', '', 'metal', ''), ('', '', '', '')]


def test_derive_cf_relations():
    assert derive_cf_relations(("right", "", "", "", "")) == [
        ("right", ('', '', '', '')),
        ("left", ('', '', '', ''))
        ], "empty filters with a spatial relation must yield empty variants with all other spatial relations."

    assert derive_cf_relations(("behind", "", "", "", "")) == [
        ("behind", ('', '', '', '')),
        ("front", ('', '', '', ''))
        ], "empty filters with a spatial relation must yield empty variants with all other spatial relations."
        
    assert derive_cf_relations(("right", "", "", "", "cube")) == [
        ("right", ('', '', '', 'cube')),
        ("left", ('', '', '', 'cube')),
        ("right", ('', '', '', '')),
        ("left", ('', '', '', ''))
        ], "attribute filters with a spatial relation must yield all attribute variants and empty variants combined with all other spatial relations."
