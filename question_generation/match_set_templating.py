# all kinds of functions to fill a set of objects into a match

import random
import re
from typing import Dict, List

from num2words import num2words

from id_handling import get_id


def handle_match(text: str, match, objs: Dict, fn, replacements) -> str:
    """
    Takes a match (which is a {|()} delimited part of the template) and extends it based on the number of found objects.

    Args:
        text (str): the whole template
        match ([type]): the matched region
        objs (Dict): the objects

    Returns:
        str: the extended text template
    """
    # split on "|"
    parts = match.split("|")

    # get the current id from the match
    id_text = get_id(re.search("<[AZCMSRV]\d*[cf|r|m|i|s]*\d*>", match).group())

    if "s" in id_text:
        id_text = "s"

    current_objs = objs[id_text]
    count = len(current_objs)

    # set the correct verb: is or are
    # verb_placeholder = replace_id("<V>", current_id)
    # replacements[verb_placeholder] = "is" if count <= 1 else "are"
    # help_verb_placeholder = replace_id("<H>", current_id)
    # replacements[help_verb_placeholder] = "has" if count <= 1 else "have"

    # # dectect aggregation
    # aggregate = False
    # if count > 1:
    #   for attr_idx in range(4):
    #     subset_objects = [o[:attr_idx] + o[attr_idx+1:] for o in objs[id_text]]
    #     if len(set(subset_objects)) == 1:
    #       aggregate = True

    if count == 0:
        # just use the first part of the template
        matching_objects_text = parts[0]
    elif len(current_objs) > 1 and len(set(current_objs)) == 1:
        # all objects are the same, we can just add a counting word
        matching_objects_text = all_reps(parts, current_objs, id_text, replacements)
    elif len(current_objs) - len(set(current_objs)) > 0:
        # some repitions, some objects are unique
        matching_objects_text = some_reps_some_unique(
            parts, current_objs, id_text, replacements
        )
    else:
        matching_objects_text = all_different(parts, current_objs)

    # replace the { } part in the original text template
    text = text.replace(match, matching_objects_text)
    return text


def join_list_with_comma_and(list: List[str]) -> str:
    # Join matching_objects to a text with "," and "and"
    joined_list = ", ".join(list[:-2] + [" and ".join(list[-2:])])
    return joined_list


def all_different(parts, current_objs):
    # all objects are different, repeat the second part of the template
    count = len(current_objs)
    matching_objects = []
    part = parts[1]

    boundary = part.index("(")
    init, part = part[:boundary], part[boundary:]

    # for each of the objects
    for j in range(count):
        if len(part) > 0:
            match_pattern = "(<[ZCMSR]\d*(?:i|s|si))(>)"
            match_replacement = f"\g<1>{j}\g<2>"
            object_template = re.sub(match_pattern, match_replacement, part)
            matching_objects.append(object_template)

    # shuffle the object_templates in matching_objects to have sets of factual objects being presented in different orders in multiple runs of this function
    random.shuffle(matching_objects)

    # Join matching_objects to a text with "," and "and"
    matching_objects_text = join_list_with_comma_and(matching_objects)

    return init + " " + matching_objects_text


def some_reps_some_unique(parts, current_objs, id_text, replacements):
    # some repitions, some objects are unique
    new_count = len(set(current_objs))

    matching_objects = []
    part = parts[1]

    for j, o in zip(range(new_count), set(current_objs)):
        if len(part) > 0:
            k = current_objs.index(o)
            if current_objs.count(o) > 1:
                # all objects are the same, we can just add a counting word
                count_word = num2words(current_objs.count(o))

                # replace "a" with the count word
                counted_object_template = parts[1].replace("(a ", f"({count_word} ")

                # insert the correct "identifiers"
                match_pattern = "(<[ZCMSR]\d*(?:i|s|si))(>)"
                match_replacement = f"\g<1>{k}\g<2>"
                counted_object_template = re.sub(
                    match_pattern, match_replacement, counted_object_template,
                )

                # add plural s at the end
                matching_objects.append(counted_object_template + "s")
            else:
                object_template = re.sub(
                    "(<[ZCMSR]\d*(?:i|s|si))(>)", f"\g<1>{k}\g<2>", part
                )
                matching_objects.append(object_template)

    # shuffle the object_templates in matching_objects to have sets of factual objects being presented in different orders in multiple runs of this function
    random.shuffle(matching_objects)

    # Join matching_objects to a text with "," and "and"
    matching_objects_text = join_list_with_comma_and(matching_objects)

    return matching_objects_text


def all_reps(parts, current_objs, id_text, replacements):
    # all objects are the same, we can just add a counting word
    count = len(current_objs)
    count_word = num2words(count)

    # replace "a" with the count word
    counted_object_template = parts[1].replace("(a ", f"({count_word} ")

    # insert the correct "identifiers"
    k = 0
    match_pattern = "(<[ZCMSR]\d*(?:i|s|si))(>)"
    match_replacement = f"\g<1>{k}\g<2>"
    counted_object_template = re.sub(
        match_pattern, match_replacement, counted_object_template
    )

    # add plural s at the end
    matching_objects_text = counted_object_template + "s"
    return matching_objects_text
