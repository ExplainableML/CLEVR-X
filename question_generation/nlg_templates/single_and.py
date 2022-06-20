from typing import Dict

from nlg_system.clauses import CummulativeRelation, Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import CompositeSentence, Sentence

from nlg_templates.nlg_utils import compute_iters


def single_and(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
):
    # the all share the same setup
    sentences = []

    if idx in [0, 1, 2, 3, 4, 5]:
        cr = CummulativeRelation(
            filter_to_objects["3"],
            filter_to_relation["2"],
            filter_to_objects["2"],
            filter_to_relation[""],
            filter_to_objects[""],
        )
        # cr.realize()
        sentences.append(Sentence(cr))
    else:
        raise NotImplementedError

    cs = CompositeSentence(sentences)
    iters = compute_iters(cs)
    return [cs.realize(neg_evidence=True, iter=iter) for iter in iters]
