# some middle level functions to handle text templates

from __future__ import print_function

import random
import re
import string
from typing import Dict, List

from conditions import pre_condition


def replace_optionals(s: str) -> str:
    """
  Each substring of s that is surrounded in square brackets is treated as
  optional and is removed with probability 0.5. For example the string

  "A [aa] B [bb]"

  could become any of

  "A aa B bb"
  "A  B bb"
  "A aa B "
  "A  B "

  with probability 1/4.
  """
    pat = re.compile(r"\[([^\[]*?)\]")

    # Python 3.8: while match := pat.search(s):
    while True:
        match = pat.search(s)
        if match:
            options = match.group(1).split("|")
            if len(options) == 1:
                # old behavior, keep content at 50% probability
                option = options[0] if random.random() > 0.5 else ""
            else:
                # new behavior, randomly chose an option
                option = random.choice(options)
            i0 = match.start()
            i1 = match.end()
            s = s[:i0] + option + s[i1:]
        else:
            break
    s = " ".join(s.split())
    return s


def recursive_replace_optionals(texts: List[List[str]]) -> List[List[str]]:
    """takes a list of list of strs and replaces the optionals"""
    pat = re.compile(r"\[([^\[]*?)\]")

    strs_to_work_on = texts[-1]
    # result = [strs_to_work_on, []]
    result: List[List[str]] = [*texts, []]

    for s in strs_to_work_on:
        match = pat.search(s)
        if match:
            options = match.group(1).split("|")
            if len(options) == 1:
                options += [""]
            for option in options:
                i0 = match.start()
                i1 = match.end()
                result[-1].append(s[:i0] + option + s[i1:])
        else:
            result[-1].append(s)

    if any(sen.find("[") != -1 for sen in result[-1]):
        result = recursive_replace_optionals(result)

    return result


def remove_punctuation(s):
    """removes all punctuatione except < and >"""
    return s.translate(
        str.maketrans("", "", "".join(set(string.punctuation) - set(["<", ">"])))
    )


def replace_any_brackets(text):
    # brackets_match = re.search("\(.*?\)", text)
    text = re.sub("\((.*?)\)", r"\1", text)
    text = re.sub("{(.*?)}", r"\1", text)
    text = re.sub("\$(.*?)\$", r"\1", text)

    return text


@pre_condition(lambda text, param_vals: text != "")
def other_heuristic(text: str, param_vals: Dict[str, str]) -> str:
    """
  Post-processing heuristic to handle the word "other"
  """
    if " other " not in text and " another " not in text:
        return text
    target_keys = {
        "<Z>",
        "<C>",
        "<M>",
        "<S>",
        "<Z2>",
        "<C2>",
        "<M2>",
        "<S2>",
    }
    if param_vals.keys() != target_keys:
        return text
    key_pairs = [
        ("<Z>", "<Z2>"),
        ("<C>", "<C2>"),
        ("<M>", "<M2>"),
        ("<S>", "<S2>"),
    ]
    remove_other = False
    for k1, k2 in key_pairs:
        v1 = param_vals.get(k1, None)
        v2 = param_vals.get(k2, None)
        if v1 != "" and v2 != "" and v1 != v2:
            # print('other has got to go! %s = %s but %s = %s'
            #       % (k1, v1, k2, v2))
            remove_other = True
            break
    if remove_other:
        if " other " in text:
            text = text.replace(" other ", " ")
        if " another " in text:
            text = text.replace(" another ", " a ")
    return text
