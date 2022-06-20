from __future__ import print_function

import random
from typing import List

from more_itertools import powerset

from custom_types import Attribute_Map, Attribute_Set, Metadata, Scene_Struct


def precompute_filter_options(scene_struct: Scene_Struct, metadata: Metadata) -> None:
    # Keys are tuples (size, color, shape, material) (where some may be None)
    # and values are lists of object idxs that match the filter criterion
    attribute_map: Attribute_Map = {}

    if metadata["dataset"] == "CLEVR-v1.0":
        attr_keys = ["size", "color", "material", "shape"]
    else:
        assert False, "Unrecognized dataset"

    # Precompute masks (same as itertools product("01", repeat=4), but reversed)
    masks = []
    for i in range(2 ** len(attr_keys)):
        mask = []
        for j in range(len(attr_keys)):
            mask.append((i // (2 ** j)) % 2)
        masks.append(mask)

    for object_idx, obj in enumerate(scene_struct["objects"]):
        if metadata["dataset"] == "CLEVR-v1.0":
            # mypy bug 7867
            keys = [tuple(obj[k] for k in attr_keys)]  # type: ignore
        for mask in masks:
            for key in keys:
                masked_key = []
                for a, b in zip(key, mask):
                    if b == 1:
                        masked_key.append(a)
                    else:
                        masked_key.append(None)
                masked_key = tuple(masked_key)  # type: ignore
                if masked_key not in attribute_map:
                    attribute_map[masked_key] = set()  # type: ignore
                attribute_map[masked_key].add(object_idx)  # type: ignore

    scene_struct["_filter_options"] = attribute_map


def find_filter_options(
    object_idxs: List[int], scene_struct: Scene_Struct, metadata: Metadata
) -> Attribute_Map:
    # Keys are tuples (size, color, shape, material) (where some may be None)
    # and values are lists of object idxs that match the filter criterion

    if "_filter_options" not in scene_struct:
        precompute_filter_options(scene_struct, metadata)

    attribute_map = {}
    object_idxs = set(object_idxs)  # type: ignore
    for k, vs in scene_struct["_filter_options"].items():
        attribute_map[k] = sorted(list(object_idxs & vs))  # type: ignore
    return attribute_map  # type: ignore


def add_empty_filter_options(
    attribute_map: Attribute_Map, metadata: Metadata, num_to_add: int
) -> None:
    # Add some filtering criterion that do NOT correspond to objects

    if metadata["dataset"] == "CLEVR-v1.0":
        attr_keys = ["Size", "Color", "Material", "Shape"]
    else:
        assert False, "Unrecognized dataset"

    attr_vals = [metadata["types"][t] + [None] for t in attr_keys]
    if "_filter_options" in metadata:
        attr_vals = metadata["_filter_options"]

    target_size = len(attribute_map) + num_to_add
    while len(attribute_map) < target_size:
        k = (random.choice(v) for v in attr_vals)
        if k not in attribute_map:
            attribute_map[k] = []  # type: ignore


def find_relate_filter_options(
    object_idx: int,
    scene_struct: Scene_Struct,
    metadata: Metadata,
    unique: bool = False,
    include_zero: bool = False,
    trivial_frac: float = 0.1,
):
    options = {}
    if "_filter_options" not in scene_struct:
        precompute_filter_options(scene_struct, metadata)

    # TODO: Right now this is only looking for nontrivial combinations; in some
    # cases I may want to add trivial combinations, either where the intersection
    # is empty or where the intersection is equal to the filtering output.
    trivial_options = {}
    for relationship in scene_struct["relationships"]:
        related = set(scene_struct["relationships"][relationship][object_idx])  # type: ignore
        for filters, filtered in scene_struct["_filter_options"].items():
            intersection = related & filtered
            trivial = intersection == filtered
            if unique and len(intersection) != 1:
                continue
            if not include_zero and len(intersection) == 0:
                continue
            if trivial:
                trivial_options[(relationship, filters)] = sorted(list(intersection))
            else:
                options[(relationship, filters)] = sorted(list(intersection))

    N, f = len(options), trivial_frac
    num_trivial = int(round(N * f / (1 - f)))
    trivial_options = list(trivial_options.items())  # type: ignore
    random.shuffle(trivial_options)  # type: ignore
    for k, v in trivial_options[:num_trivial]:  # type: ignore
        options[k] = v

    return options


def derive_cf_attributes(current_final_filters: Attribute_Set) -> List:
    # case with only attributes

    # reduce the filter from all filtering things
    none_list = ["", "thing"]
    minimized_filter = [
        filter for filter in current_final_filters if filter not in none_list
    ]
    ps = list(powerset(minimized_filter))[::-1]

    extended_ps = []
    for s in ps:
        extended_set = [""] * len(current_final_filters)
        for item in s:
            try:
                correct_index = current_final_filters.index(item)
                extended_set[correct_index] = item
            except ValueError:
                pass
        extended_ps.append(tuple(extended_set))
    return extended_ps


def derive_cf_relations(current_final_filters) -> List:
    """
  generate combinations with varying relations
  
  this means that there is a relation which we need to deal with in a separate tuple entry
  """
    # split into relation and attributes
    current_relation = current_final_filters[0]
    final_attribute_filters = current_final_filters[1:]

    opposites_list = [["left", "right"], ["behind", "front"]]
    all_relations = [relation for opposites in opposites_list for relation in opposites]
    assert current_relation in all_relations, f"Unknown relation: {current_relation}"

    # find the correct opposites and return all of them shuffled, except the current_relation
    for opposites in opposites_list:
        if current_relation in opposites:
            relations = [current_relation] + [
                op for op in opposites if op != current_relation
            ]

    relation_attribute_filters = [
        (relation, filter_variant)
        for filter_variant in derive_cf_attributes(final_attribute_filters)
        for relation in relations
    ]
    return relation_attribute_filters

