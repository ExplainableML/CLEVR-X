from typing import Dict

from nlg_system.clauses import Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import CompositeSentence, Sentence

from nlg_templates.nlg_utils import compute_iters


# FIXME: Remove negative evidence and look at outputs
def single_or(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
):
    # the all share the same setup
    sentences = []
    drop_neg_evidence = False

    if idx in [0]:
        # for debugging
        # if (
        #     not filter_to_objects[""].negative_objects
        #     and not filter_to_objects["2"].negative_objects
        # ):
        #     o = filter_to_objects[""] + filter_to_objects["2"]
        #     o.realize()

        sentences.append(Sentence(filter_to_objects[""]))
        sentences.append(Sentence(filter_to_objects["2"]))
        drop_neg_evidence = (len(filter_to_objects["2"]) == 0) ^ (len(filter_to_objects[""]) == 0)
    elif idx in [1, 2, 4, 5]:
        sentences.append(Sentence(filter_to_objects["3"]))
    elif idx in [3]:
        rel_clause1 = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        sentences.append(Sentence(rel_clause1))
        rel_clause2 = RelativeClause(
            filter_to_objects["4"], filter_to_relation["2"], filter_to_objects["3"]
        )
        sentences.append(Sentence(rel_clause2))
        drop_neg_evidence = (len(filter_to_objects["2"]) == 0) ^ (len(filter_to_objects["4"]) == 0)
    elif idx in [6]:
        rel_clause = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        sentences.append(Sentence(rel_clause))
        sentences.append(Sentence(filter_to_objects["3"]))
        drop_neg_evidence = (len(filter_to_objects["2"]) == 0) ^ (len(filter_to_objects["3"]) == 0)
    elif idx in [7]:
        sentences.append(Sentence(filter_to_objects[""]))
        rel_clause = RelativeClause(
            filter_to_objects["3"], filter_to_relation[""], filter_to_objects["2"]
        )
        sentences.append(Sentence(rel_clause))
        drop_neg_evidence = (len(filter_to_objects[""]) == 0) ^ (len(filter_to_objects["3"]) == 0)
    else:
        raise NotImplementedError

    cs = CompositeSentence(sentences)
    iters = compute_iters(cs)
    return [cs.realize(neg_evidence=not drop_neg_evidence, iter=iter) for iter in iters]
