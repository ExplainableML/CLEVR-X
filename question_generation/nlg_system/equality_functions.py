from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from nlg_system.objects import CLEVRObject


def equal_except(obj_a: CLEVRObject, obj_b: CLEVRObject, attr):
    if attr == "size":
        return equal_for_subset_attrs(obj_a, obj_b, ["color", "material", "shape"])
    elif attr == "color":
        return equal_for_subset_attrs(obj_a, obj_b, ["size", "material", "shape"])
    elif attr == "material":
        return equal_for_subset_attrs(obj_a, obj_b, ["size", "color", "shape"])
    elif attr == "shape":
        return equal_for_subset_attrs(obj_a, obj_b, ["size", "color", "material"])
    else:
        raise NotImplementedError


def equal_for_subset_attrs(
    obj_a: CLEVRObject, obj_b: CLEVRObject, subset_attrs: Iterable[str]
) -> bool:
    """
    Returns whether the two objects a and b are equal on the given subset of attributes.

    Args:
        obj_a (CLEVRObject): Object A
        obj_b (CLEVRObject): Object B
        subset_attrs (Iterable[str]): A iterable of attributes

    Returns:
        bool: Whether they are equal or not
    """
    return all(obj_a.attrs[attr] == obj_b.attrs[attr] for attr in subset_attrs)
