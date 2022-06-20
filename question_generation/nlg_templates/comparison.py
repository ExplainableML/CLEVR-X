from typing import Dict, List

from nlg_system.clauses import Relation, RelativeClause
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import (
    CompositeSentence,
    Sentence,
    ActiveSentence,
    SentenceGroup,
)

from nlg_templates.nlg_utils import compute_iters


def comparison(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
    id_to_attrs: Dict[str, Dict[str, List[str]]],
):
    # the all share the same setup
    sentences = []

    if idx in [0, 1, 2, 3]:
        cs1 = CompositeSentence(
            [Sentence(filter_to_objects[""]), Sentence(filter_to_objects["2"])]
        )
        sentences.append(cs1)

        act_sent1 = ActiveSentence(
            filter_to_objects[""],
            queried_attributes=id_to_attrs[""]["extra"],
            question_filters=id_to_attrs[""]["required"],
        )
        act_sent2 = ActiveSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
        )
        cs2 = CompositeSentence([act_sent1, act_sent2])
        sentences.append(cs2)

    elif idx in [4, 7, 10, 13]:
        rel_clause = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )

        cs = CompositeSentence([Sentence(rel_clause), Sentence(filter_to_objects["3"])])
        sentences.append(cs)

        # lets try an active sentnce hier
        act_sent1 = ActiveSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            relation=filter_to_relation[""],
            relation_object=filter_to_objects[""],
        )
        act_sent2 = ActiveSentence(
            filter_to_objects["3"],
            queried_attributes=id_to_attrs["3"]["extra"],
            question_filters=id_to_attrs["3"]["required"],
        )
        sentences.append(CompositeSentence([act_sent1, act_sent2]))

    elif idx in [5, 8, 11, 14]:
        rel_clause = RelativeClause(
            filter_to_objects["3"], filter_to_relation[""], filter_to_objects["2"]
        )

        cs = CompositeSentence([Sentence(filter_to_objects[""]), Sentence(rel_clause)])
        sentences.append(cs)

        # lets try an active sentnce hier
        act_sent1 = ActiveSentence(
            filter_to_objects[""],
            queried_attributes=id_to_attrs[""]["extra"],
            question_filters=id_to_attrs[""]["required"],
        )
        act_sent2 = ActiveSentence(
            filter_to_objects["3"],
            queried_attributes=id_to_attrs["3"]["extra"],
            question_filters=id_to_attrs["3"]["required"],
            relation=filter_to_relation[""],
            relation_object=filter_to_objects["2"],
        )
        sentences.append(CompositeSentence([act_sent1, act_sent2]))

    elif idx in [6, 9, 12, 15]:
        rel_clause1 = RelativeClause(
            filter_to_objects["2"], filter_to_relation[""], filter_to_objects[""]
        )
        rel_clause2 = RelativeClause(
            filter_to_objects["4"], filter_to_relation["2"], filter_to_objects["3"]
        )

        cs = CompositeSentence([Sentence(rel_clause1), Sentence(rel_clause2)])
        sentences.append(cs)

        # lets try an active sentnce hier
        act_sent1 = ActiveSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            relation=filter_to_relation[""],
            relation_object=filter_to_objects[""],
        )
        act_sent2 = ActiveSentence(
            filter_to_objects["4"],
            queried_attributes=id_to_attrs["4"]["extra"],
            question_filters=id_to_attrs["4"]["required"],
            relation=filter_to_relation["2"],
            relation_object=filter_to_objects["3"],
        )
        sentences.append(CompositeSentence([act_sent1, act_sent2]))

    else:
        raise NotImplementedError

    sg = SentenceGroup(sentences)
    iters = compute_iters(sg)
    return [sg.realize(neg_evidence=True, iter=iter) for iter in iters]

