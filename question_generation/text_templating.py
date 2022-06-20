from __future__ import print_function

import random
import re
from typing import List

from custom_types import State, Synonyms, Template
from id_handling import get_id, replace_id
from text_template_handling import (other_heuristic,
                                    recursive_replace_optionals,
                                    remove_punctuation, replace_optionals)
from utils import create_AST


def get_synonym(attr, synonyms):
    return synonyms.get(attr, [attr])[0]


def zip_compare(orig_q, new_t):
    candidate_q_synonyms = {}

    # iterate over the zipped words
    for orig_q_word, new_t_word in zip(orig_q.split(), new_t.split()):
        # check for a placeholder in the candidate word
        placeholder_in_new_t_word = re.match("<[ZCMSR]\d*>", new_t_word)
        # and if it is, save the question word to the candidate dictionary
        if placeholder_in_new_t_word is not None:
            # hack a way plural version of spheres
            if "<S" in new_t_word and orig_q_word[-1] == "s":
                orig_q_word = orig_q_word[:-1]

            candidate_q_synonyms[placeholder_in_new_t_word.group()] = [orig_q_word]
        elif orig_q_word != new_t_word and not (
            new_t_word == "another" and orig_q_word == "a"
        ):
            # if the words do not match and it is not a another / a mismatch completely skip this candidate template
            break

    else:
        # for loop successfully completed
        return candidate_q_synonyms


def compare_all_templates(orig_q, state, expanded_templates):
    for t in expanded_templates:
        # also remove punctuation of the candidate template
        new_t = remove_punctuation(t)

        # replace the empty non shape attribues with nothing to potentially get the correct alignment
        for name, value in state["vals"].items():
            if value == "" and not replace_id(name) == "<S>":
                new_t = new_t.replace(name, value)

        # if the lens of the original question and candiate template do not match, continue to the next candiate
        if len(orig_q.split()) != len(new_t.split()):
            continue

        candidate_q_synonyms = zip_compare(orig_q, new_t)
        if candidate_q_synonyms:
            q_synonyms = candidate_q_synonyms

    assert len(q_synonyms) > 0

    # ignore relations, as we have broken them a bit in the beginning
    q_synonyms = {k: v for k, v in q_synonyms.items() if replace_id(k) != "<R>"}
    return q_synonyms


def compute_question_synonyms(
    synonyms: Synonyms, state, template: Template, question=None
):

    # preset synonyms mapping for questions, f explanations and cf explanations
    current_synonyms = {}
    for name, replacements in synonyms.items():
        current_synonyms[name] = [random.choice(replacements)]

    if question is not None:
        # TODO: Refactor this into a method and use it also to extract information from generated explanations

        # this code goes through the questions to find the correctly used synonyms, but it is really a restructing code :)
        q_synonyms = {}

        # remove punctuation to avoid being thrown of
        orig_q = remove_punctuation(question["question"])

        # condense relations to a single word
        for relation in ["left", "right", "behind", "front"]:
            orig_q = re.sub(f"({'|'.join(synonyms[relation])})", relation, orig_q)

        optional_other_templates = [
            [t.replace(" other", " [other]") for t in template["text"]]
        ]
        expanded_templates = recursive_replace_optionals(optional_other_templates)[-1]
        q_synonyms = compare_all_templates(orig_q, state, expanded_templates)
    else:
        q_synonyms = None

    return q_synonyms, current_synonyms


def get_relevant_nodes(template):
    filtered_template = [
        node
        for node in template["nodes"]
        if "filter" in node["type"] or "same" in node["type"]
    ]

    new_ast = create_AST(template["nodes"])
    ft = []
    for path in new_ast.paths_to_leaves()[::-1]:
        for i in path[::-1]:
            if "filter" in new_ast[i].data["type"] or "same" in new_ast[i].data["type"]:
                ft.append(new_ast[i].data)
    return ft


# NOTE:
# The code below does not output anything that is needed for the final explanation generation. 
# However, it is still needed to keep the random number generation state indentical to the one we used when generating the official dataset release.

def fill_in_cf_templates(
    state, fse_list: List[State], template: Template, synonyms: Synonyms
) -> List[List]:
    """
  This method fills in the values for a counter factual template.
  It assumes, that there are a list of filters in the original answer, to which counter factual explanations must contrast.

  Each object must only be used once in the explanation. Thus the answer objects directly go into the set of used objects.
  Afterwards we iterate over all almost matches and generate a explanation from them, pointing towards the properties it is missing. Afterwards we store, that we have already used that object, as it might come up with a even less specific filter later on.
  """

    cf_explanations = []
    filtered_template = get_relevant_nodes(template)

    # get final values (without thing for empty shapes)
    final_values = {k: v if v != "thing" else "" for k, v in state["vals"].items()}

    # loop over all filters of the question
    for i, (fse, fltr) in enumerate(fse_list):

        fg_cf_explanations: List[str] = []
        # add the id of the correct answer
        used_objects = get_answer_ids(fse[0]["nodes"])

        # loop over all counterfactual variations
        for cf in fse:
            almost_matches = cf["nodes"][-1]["_output"]

            for am_id, almost_match in zip(get_answer_ids(cf["nodes"]), almost_matches):
                if am_id not in used_objects:

                    # There two kinds of inputs
                    # - almost match with attributes (size, color, material, shape)
                    # - almost match with attributes (size, color, material, shape) + a relation

                    # There are multiple kinds of placeholders
                    # - <Zx> <Cx> <Mx> <Sx> with x = _, 2, 3, 4, ...: These are the base objects (x)
                    # - <Zcf> <Ccf> <Mcf> <Scf>: This is the counterfactual object, which did not match the original filter (x)
                    # - <Zr> <Cr> <Mr> <Sr>: This object is the base a relation refers to.
                    # - <Zm> <Cm> <Mm> <Sm>: True properties a cf object is missing. Not all of them need to be filled in.
                    # - <Rm>: The true relation, that is missing
                    # - <Rcf>: The cf relation

                    # Multiple rules must be implemented:
                    # - The none value is always "". Linguistic insertions like "thing" must be subsituted at the last possible time. This reduces code complexity early on
                    # - All attributes of cf objects (<Zcf> <Ccf> <Mcf> <Scf>) must be filled in
                    # - ( ) - brackets with placeholders in them need to be dropped
                    # - { } - brackets with a single () need to drop the " and "

                    # # 1. Build a replacement dict
                    attribute_names = [
                        name
                        for name in fltr[-2].get(
                            "side_inputs", ["<Z>", "<C>", "<M>", "<S>"]
                        )
                        if replace_id(name) != "<R>"
                    ]

                    # Compute attributes
                    cf_attributes, missing_attr = {}, {}
                    for name, attr in zip(attribute_names, almost_match):
                        cf_attributes[replace_id(name, "cf")] = attr
                        if final_values[name] not in ["", attr]:
                            missing_attr[replace_id(name, "m")] = final_values[name]

                    if "same" in fltr[-2]["type"]:
                        type_to_name = {
                            param["type"].lower(): param["name"]
                            for param in template["params"]
                        }
                        same_type = fltr[-2]["type"].split("_")[-1]
                        name = replace_id(type_to_name[same_type], "")
                        # look at the previous cf setting, use the first item and then the last output (which should be a query_attributes)
                        factual_object = fse_list[min(0, i - 1)][0]["nodes"][-1][
                            "_output"
                        ][0]
                        factual_attr = factual_object[attribute_names.index(name)]
                        missing_attr = {replace_id(name, "m"): factual_attr}

                    # Relations <Rm>, <Rcf>
                    relations, rel_reference_attrs = {}, {}
                    try:
                        # find all placeholders before the current ones and use the last <Rx> from em
                        all_keys = list(state["vals"].keys())
                        previous_keys = all_keys[: all_keys.index(attribute_names[0])]
                        relation_placeholder = [
                            k for k in previous_keys if replace_id(k) == "<R>"
                        ][-1]
                        rcf = cf["vals"][relation_placeholder]
                        rm = state["vals"][relation_placeholder]
                        if rm != rcf:
                            relations = {"<Rcf>": rcf, "<Rm>": rm}
                            # attrs of the object the relation refers to.
                            rel_reference_attrs = {
                                replace_id(name, "r"): final_values[name]
                                for name in fse_list[i - 1][1][-2]["side_inputs"]
                                if final_values[name] != ""
                            }
                    except (KeyError, IndexError):
                        pass

                    # all replacements
                    replacements = {
                        **final_values,
                        **cf_attributes,
                        **missing_attr,
                        **relations,
                        **rel_reference_attrs,
                    }

                    # 2. Use contents of replacements dict to determine which {() and ()} to drop
                    cf_text = random.choice(template["text_cfexpl"])
                    matches = re.findall("\([^)]*?<[ZCMSR][cf|r|m]*>.*?\)", cf_text)
                    for match in matches:
                        placeholders = re.findall("<[ZCMSR][cf|r|m]*>", match)
                        current_repl = [replacements.get(p, "") for p in placeholders]
                        if "".join(current_repl) == "":
                            cf_text = cf_text.replace(match, "")
                            cf_text = cf_text.replace(" and ", "")
                    cf_text = replace_any_brackets(cf_text)

                    # 3. Replace the placeholders with the dict contents
                    synonym = lambda word: get_synonym(word, synonyms)

                    # iteration over all placeholders
                    placeholders = re.findall("<[ZCMSR][cf|r|m]*>", cf_text)
                    for placeholder in placeholders:
                        none_value = "thing" if replace_id(placeholder) == "<S>" else ""
                        replacement = synonym(replacements.get(placeholder, none_value))
                        cf_text = cf_text.replace(placeholder, replacement)
                        cf_text = " ".join(cf_text.split())

                    # 4. replace optionals
                    cf_text = replace_optionals(cf_text).capitalize()

                    # 5. add to list and remember object
                    fg_cf_explanations.append(cf_text)
                    used_objects.add(am_id)

        cf_explanations.append(fg_cf_explanations)

    return cf_explanations


def fill_in_text_templates(
    final_states: List[State],
    final_state_explanations: List[State],
    template: Template,
    synonyms: Synonyms,
    template_info,
    question=None,
):
    """
  This function fills in text templates of questions, answers and factual and counter factual explanations.

  It should do three things:

  1. Build the questions (text)
  2. Build the factual explanation (text & structured)
  3. Build the counter factual explanation (text & structured)

  """

    text_questions = []
    text_f_expl = []
    text_cf_expl = [[]]

    for state in final_states:
        q_synonyms, current_synonyms = compute_question_synonyms(
            synonyms, state, template, question
        )

        # question
        q_text = random.choice(template["text"])
        q_text = fill_values_in_q_text_template(state, current_synonyms, q_text)
        text_questions.append(q_text)

    return text_questions, text_f_expl, text_cf_expl


def create_factual_explanation(
    state,
    fse_list: List[List[State]],
    template: Template,
    synonyms: Synonyms,
    q_synonyms,
    template_info,
) -> List[str]:
    """Convert the answer to a factual explanation text"""

    # Requirements

    # the approach must be able to:
    # - output counts
    # - output reference objects Zr Cr Mr Sr, and multiple ones (R, R2, etc.) (maybe do this through the req below)
    # - output objects of the answer Z, C, M, S, Z2, C2, M2, S2, Z3, C3, M3, S3, Z4, C4, M4, S4, etc
    # - output "how many/any other objects" {(Zf Cf Mf Cf)} factual objects (based on query attributes)! This is important
    # - different formulations depending on the answer (a bool, cases?)?
    # - deal with the setting when there are no matching objects

    # new strategy
    # - remove any early "things"
    # - build a replacement dict, with 1,2,3,r,f,etc. ids
    # - look at which {(|)} to repeat or to drop (manipulate the template): {(<Zi> <Ci> <Mi> <Si>)}
    # - fill in the placeholders with the replacement dict and remove the others
    # - replace optionals
    # - add to a list

    # examples
    # template: "<A>, because [in this image|in this setting] there is {no <Z> <C> <M> <S>s|(a <Zi> <Ci> <Mi> <Si>)} and there is {no <Z2> <C2> <M2> <S2>s|also (a <Z2i> <C2i> <M2i> <S2i>)}."
    # account for the settings when there are 0, 1, 2, many cases
    # 0: select the first part of the template
    # 1: select the second part of the template
    # 2: repeat the second part (and put numbers behind the i) of the template (" and ".join(:-1))
    # many: repeat the second part (and put numbers behind the i) of the template (", ".join() und " and ")

    # here we need to do the same trick again, if there is a same node drop the previous filter nodes

    # Scene understanding
    replacements, objs = build_replacements_dict(state, fse_list)
    fn, idx = template_info

    # 2. use contents of replacement dicts to determine which {(<Zi> <Ci> <Mi> <Si>), } to repeat or drop
    text_templates = template["text_fexpl"]
    # TODO: create all optional variants / use random choiceS to pick a couple of them
    text_templates = set(recursive_replace_optionals([text_templates])[-1])

    variants = []
    for text in random.sample(text_templates, k=5):
        # find all { } brackets and iterate over them
        matches = re.findall("{(.*?<[ZCMSR]\d*[cf|r|m|i|s]*>.*?)}", text)
        for match in matches:
            text = handle_match(text, match, objs, fn, replacements)

        # remove any brackets
        text = replace_any_brackets(text)

        # 3. Replace the placeholders with the dict contents
        text = fill_values_in_f_text_template(text, synonyms, replacements, q_synonyms)

        # 4. replace optionals and clean up
        text = replace_optionals(text)
        text = " ".join(text.split()).capitalize()

        variants.append(text)

    return variants


def fill_values_in_f_text_template(text, synonyms, replacements, q_synonyms):
    # 3. Replace the placeholders with the dict contents
    # TODO: Create a joint method with cf explanations code, this is a duplicate / c.f.fill_values_in_q_text_template
    synonym = lambda word: get_synonym(word, synonyms)

    # iteration over all placeholders
    placeholders = re.findall("<[AZCMSRVH]\d*[cf|r|m|i|si]*\d*>", text)
    for placeholder in placeholders:
        none_value = "thing" if replace_id(placeholder) == "<S>" else ""
        replacement = synonym(replacements.get(placeholder, none_value))

        # if there is something to replace, check whether we know a better synonym from the questions
        if replacement != "" and q_synonyms is not None and not "s" in placeholder:
            # clean the placeholder
            cleaned_placeholder = replace_id(
                placeholder, re.match("(\d*)(s)*(i0)*", get_id(placeholder)).group(1)
            )

            # check if we know a question specific synonym
            if q_synonyms.get(cleaned_placeholder, False):
                q_syn = q_synonyms.get(cleaned_placeholder)

                # for shapes avoid replacing meaningful things like ball/cube with the unknown object/thing determinations
                if not (replacement in ["thing", "object"]) != (
                    q_syn[0] in ["object", "thing"]
                ):
                    replacement = q_syn[0]

        text = text.replace(placeholder, replacement)
        text = " ".join(text.split())
    return text


def fill_values_in_q_text_template(state, synonyms, text):
    """
  This function uses the values from a state to fill them into a text_template
  """
    # TODO: This is duplicate from the cf explanations code, also use synonyms for thing
    synonym = lambda word: get_synonym(word, synonyms)
    values = state["vals"]
    replacements = {k: v for k, v in values.items() if v != ""}

    # iteration over all placeholders
    placeholders = re.findall("<[AZCMSRV]\d*[cf|r|m|i]*\d*>", text)
    for placeholder in placeholders:
        none_value = "thing" if replace_id(placeholder) == "<S>" else ""
        replacement = synonym(replacements.get(placeholder, none_value))
        text = text.replace(placeholder, replacement)
        text = " ".join(text.split())

    text = replace_optionals(text)
    text = other_heuristic(text, values)
    return text


def build_replacements_dict(state, fse_list):
    # get final values (without thing for empty shapes)
    final_values = {k: v if v != "thing" else "" for k, v in state["vals"].items()}

    # in contrast to cf, we want merge all factual objects into a single sentence
    replacements = {k: v for k, v in final_values.items() if v != ""}

    objs = {}
    factual_objects = tuple()
    for j, (fse, fltr) in enumerate(fse_list):

        question_state = fse[0]
        factual_objects = question_state["answer"]
        attribute_names = [
            name
            for name in fltr[-2].get("side_inputs", ["<Zs>", "<Cs>", "<Ms>", "<Ss>"])
            if replace_id(name) != "<R>"
        ]

        # set the correct verb: is or are
        current_id = get_id(attribute_names[0])
        verb_placeholder = replace_id("<V>", current_id)
        replacements[verb_placeholder] = "is" if len(factual_objects) <= 1 else "are"
        help_verb_placeholder = replace_id("<H>", current_id)
        replacements[help_verb_placeholder] = (
            "has" if len(factual_objects) <= 1 else "have"
        )

        objs[current_id] = factual_objects

        for i, obj in enumerate(factual_objects):

            # 1. build replacement dict
            default_attrs = ["<Z>", "<C>", "<M>", "<S>"]
            ids = [get_id(attr) for attr in attribute_names]
            assert all(id == ids[0] for id in ids)
            f_attributes = {
                replace_id(placeholder, f"{ids[0]}i{i}"): attr
                for placeholder, attr in zip(default_attrs, obj)
            }

            replacements = {**replacements, **f_attributes}

    return replacements, objs
