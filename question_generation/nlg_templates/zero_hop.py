from typing import Dict, List

from nlg_system.clauses import Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import (
    ActiveSentence,
    CompositeSentence,
    Sentence,
    SentenceGroup,
)

from nlg_templates.nlg_utils import compute_iters


def zero_hop(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
    id_to_attrs: Dict[str, Dict[str, List[str]]],
):
    # the all share the same setup
    sentences = []

    if idx in [0, 1]:
        sentence = Sentence(filter_to_objects[""])
        sentences.append(CompositeSentence([sentence]))
    elif idx in [2, 3, 4, 5]:
        sentence = Sentence(filter_to_objects[""])
        sentences.append(CompositeSentence([sentence]))

        act_sent = ActiveSentence(
            filter_to_objects[""],
            queried_attributes=id_to_attrs[""]["extra"],
            question_filters=id_to_attrs[""]["required"],
        )
        sentences.append(act_sent)
    else:
        raise NotImplementedError

    sg = SentenceGroup(sentences)
    iters = compute_iters(sg)
    return [sg.realize(neg_evidence=True, iter=iter) for iter in iters]
