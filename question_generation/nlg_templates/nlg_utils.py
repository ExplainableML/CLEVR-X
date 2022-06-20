import random
import sys
from typing import List, Union

from id_handling import get_id
from nlg_system.clauses import RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import CompositeSentence, Sentence, SentenceGroup


def compute_iters(
    component: Union[Sentence, CompositeSentence, SentenceGroup], k: int = 10
) -> List[int]:
    try:
        iters = random.choices(range(component.max_iter), k=k)
    except OverflowError:
        iters = random.choices(range(sys.maxsize), k=k)

    return iters


def build_objs_with_negative_evidence(found_objs, filters, id):
    if len(found_objs[id]) > 0:
        objs = Objects.from_iterable(found_objs[id])
    else:
        current_filter = filters[id]

        # make sure a negative object has a noun if it does not have any shape
        assert len(current_filter) == 4
        if current_filter[-1] == "":
            current_filter[-1] = "thing"
        objs = Objects([], [CLEVRObject(*current_filter)])
    return objs


def compute_filters(state):
    final_values = {k: v if v != "thing" else "" for k, v in state["vals"].items()}

    filters = {}
    for attr, value in final_values.items():
        current_id = get_id(attr)
        filter_list = filters.get(current_id, [""] * 4)

        if "Z" in attr:
            filter_list[0] = value
        elif "C" in attr:
            filter_list[1] = value
        elif "M" in attr:
            filter_list[2] = value
        elif "S" in attr:
            filter_list[3] = value
        else:
            pass
        filters[current_id] = filter_list

    return filters

