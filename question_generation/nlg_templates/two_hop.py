from typing import Dict

from nlg_system.clauses import Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import CompositeSentence, Sentence

from nlg_templates.nlg_utils import compute_iters


def two_hop(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
):
    # the all share the same setup
    sentences = []
    # <A> is to the left of <B> that is to the left of <a cube>
    if idx in [0, 1, 2, 3, 4, 5]:
        rel_clause1 = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        rel_clause2 = RelativeClause(
            filter_to_objects["3"], filter_to_relation["2"], rel_clause1
        )
        sentences.append(Sentence(rel_clause2))
    else:
        raise NotImplementedError

    cs = CompositeSentence(sentences)
    iters = compute_iters(cs)
    return [cs.realize(neg_evidence=True, iter=iter) for iter in iters]
