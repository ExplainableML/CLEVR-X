from typing import Dict, Tuple

from custom_types import Synonyms
from id_handling import get_id, keep_attr_items_with_id, remove_id, replace_id
from nlg_system.clauses import Relation
from nlg_system.objects import CLEVRObject, Objects

#### New Approach


# 1. Question understanding
def understand_question(
    fse_list, final_filters: Dict[str, str], synonyms: Synonyms, question_synonyms
) -> Tuple[Dict[str, Objects], Dict[str, Relation]]:
    """
    The goal of this function is to map each ID (1,2,3,4,...) to a set of found objects.

    Futhermore, we also prepare the relations.
    """

    # split the synonyms into attributes and relation related ones
    all_relations = ["left", "right", "behind", "front", "above", "below"]
    # thing synonyms are not needed, as we always use the shape
    thing_attr = ["thing"]
    all_attribute_synonyms = {
        k: v
        for k, v in synonyms.items()
        if k not in all_relations and k not in thing_attr
    }
    all_relation_synonyms = {k: v for k, v in synonyms.items() if k in all_relations}

    # compute relations
    # maps from an ID "", "2", "3", ... to the used relations
    relations: Dict[str, str] = {
        get_id(k): v for k, v in final_filters.items() if remove_id(k) == "<R>"
    }
    filter_to_relation: Dict[str, Relation] = {
        k: Relation(v, all_relation_synonyms) for k, v in relations.items()
    }

    # compute objects
    # (later) maps from an ID "", "2", "3", ... to the found objects
    filter_to_objects: Dict[str, Objects] = {}
    for fse, fltr in fse_list:
        # determine current id # BUG: how to handle same relate questions?
        attribute_names = [
            name
            for name in fltr[-2].get("side_inputs", ["<Zs>", "<Cs>", "<Ms>", "<Ss>"])
            if replace_id(name) != "<R>"
        ]
        current_id = get_id(attribute_names[0])

        question_state = fse[0]
        positive_evidence = question_state["answer"]

        relevant_synonyms = keep_attr_items_with_id(question_synonyms, current_id)

        # iterate over all synonyms
        current_attribute_synonyms = all_attribute_synonyms.copy()
        for synonym, synonym_options in current_attribute_synonyms.items():
            # iterate over the synonyms the question has used
            for attr, question_synonym_options in relevant_synonyms.items():
                # check if that matches
                if len(set(synonym_options) & set(question_synonym_options)) > 0:
                    # overwrite the more broad synonyms with the one used by the question
                    assert len(question_synonym_options) <= len(synonym_options)
                    current_attribute_synonyms[synonym] = question_synonym_options

        if len(positive_evidence) > 0:
            factual_objects = Objects.from_iterable(
                positive_evidence, current_attribute_synonyms
            )
        else:
            negative_evidence = keep_attr_items_with_id(final_filters, current_id)
            negative_object = CLEVRObject.from_filters(negative_evidence)
            factual_objects = Objects(
                objects=[],
                negative_objects=[negative_object],
                synonyms=current_attribute_synonyms,
            )

        filter_to_objects[current_id] = factual_objects

    return filter_to_objects, filter_to_relation


# 2. Uniqueness Refinement
# mapping: 1,2,3,4: List of objects

# 3. Text Realization
