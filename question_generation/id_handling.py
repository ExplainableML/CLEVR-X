from __future__ import print_function

from typing import Dict

from conditions import pre_condition


@pre_condition(lambda ph, t="", d0=True: ph[0] == "<" and ph[-1] == ">")
@pre_condition(lambda ph, t="", d0=True: len(ph) >= 3)
def replace_id(placeholder: str, text="") -> str:
    """transforms <Z> --> <Z>. transforms <Z2> --> <Z>. optionally inserts an alternative text"""
    if type(text) == int:
        text = str(text) if text > 1 else ""

    return placeholder[:2] + text + placeholder[-1]


def remove_id(placeholder: str) -> str:
    return replace_id(placeholder, "")


@pre_condition(lambda ph: ph[0] == "<" and ph[-1] == ">")
@pre_condition(lambda ph: len(ph) >= 3)
def get_id(placeholder: str) -> str:
    """returns the id value of a placeholder by stripping of the beginning and end"""
    return placeholder[2:-1]


def keep_attr_items_with_id(dictionary: Dict, current_id: str) -> Dict:
    clean_dictionary = {
        k: v
        for k, v in dictionary.items()
        if get_id(k) == current_id and remove_id(k) != "<R>"
    }
    return clean_dictionary
