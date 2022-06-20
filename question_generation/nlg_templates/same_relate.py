from typing import Dict, List

from nlg_system.clauses import (
    CummulativeRelation,
    Relation,
    RelativeClause,
    SameRelation,
)
from nlg_system.objects import CLEVRObject, Objects
from nlg_system.sentences import (
    ActiveRelateSentence,
    ActiveSentence,
    CompositeSentence,
    Sentence,
    SentenceGroup,
)

from nlg_templates.nlg_utils import compute_iters


def same_relate(
    idx: int,
    filter_to_objects: Dict[str, Objects],
    filter_to_relation: Dict[str, Relation],
    id_to_attrs: Dict[str, Dict[str, List[str]]],
):
    # the all share the same setup
    sentences = []

    if idx in [0, 4]:
        same_rel = SameRelation(filter_to_objects["s"], "size", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["s"],
            queried_attributes=id_to_attrs["s"]["extra"],
            question_filters=id_to_attrs["s"]["required"],
            same_relation="size",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [1, 5]:
        same_rel = SameRelation(filter_to_objects["s"], "color", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["s"],
            queried_attributes=id_to_attrs["s"]["extra"],
            question_filters=id_to_attrs["s"]["required"],
            same_relation="color",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [2, 6]:
        same_rel = SameRelation(
            filter_to_objects["s"], "material", filter_to_objects[""]
        )
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["s"],
            queried_attributes=id_to_attrs["s"]["extra"],
            question_filters=id_to_attrs["s"]["required"],
            same_relation="material",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [3, 7]:
        same_rel = SameRelation(filter_to_objects["s"], "shape", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["s"],
            queried_attributes=id_to_attrs["s"]["extra"],
            question_filters=id_to_attrs["s"]["required"],
            same_relation="shape",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [8, 12, 16, 17, 18]:
        same_rel = SameRelation(filter_to_objects["2"], "size", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            same_relation="size",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [9, 13, 19, 20, 21]:
        same_rel = SameRelation(filter_to_objects["2"], "color", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            same_relation="color",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [10, 14, 22, 23, 24]:
        same_rel = SameRelation(
            filter_to_objects["2"], "material", filter_to_objects[""]
        )
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            same_relation="material",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    elif idx in [11, 15, 25, 26, 27]:
        same_rel = SameRelation(filter_to_objects["2"], "shape", filter_to_objects[""])
        sentences.append(CompositeSentence([Sentence(same_rel)]))

        act_sent = ActiveRelateSentence(
            filter_to_objects["2"],
            queried_attributes=id_to_attrs["2"]["extra"],
            question_filters=id_to_attrs["2"]["required"],
            same_relation="shape",
            relation_object=filter_to_objects[""],
        )
        sentences.append(act_sent)
    else:
        raise NotImplementedError

    sg = SentenceGroup(sentences)
    iters = compute_iters(sg)
    return [sg.realize(neg_evidence=True, iter=iter) for iter in iters]
