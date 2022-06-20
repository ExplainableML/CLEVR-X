from typing import Dict

from nlg_system.clauses import Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import CompositeSentence, Sentence

from nlg_templates.nlg_utils import compute_iters


def compare_integers_new(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
):
    # the all share the same setup
    sentences = []
    if idx in [0, 1, 2]:
        sentences.append(Sentence(filter_to_objects[""]))
        sentences.append(Sentence(filter_to_objects["2"]))
    elif idx in [3, 4, 5]:
        rel_clause = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        sentences.append(Sentence(rel_clause))
        sentences.append(Sentence(filter_to_objects["3"]))
    elif idx in [6, 7, 8]:
        rel_clause1 = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        rel_clause2 = RelativeClause(
            filter_to_objects["4"], filter_to_relation["2"], filter_to_objects["3"]
        )
        sentences.append(Sentence(rel_clause1))
        sentences.append(Sentence(rel_clause2))
    else:
        raise NotImplementedError

    cs = CompositeSentence(sentences)
    iters = compute_iters(cs)
    return [cs.realize(neg_evidence=True, iter=iter) for iter in iters]

