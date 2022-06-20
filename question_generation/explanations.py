# this file holds all the explanation code called form generate_explanations

import copy
from collections import ChainMap
from random import choice, randint, sample
from statistics import mean
from typing import Dict, List, Optional, Tuple

from treelib import Node, Tree
from treelib.exceptions import NodeIDAbsentError

from custom_types import (Answer_Counts, Metadata, Scene_Struct, Synonyms,
                          Template)
from id_handling import get_id, keep_attr_items_with_id, remove_id
from new_approach import understand_question
from nlg_system.objects import CLEVRObject, Objects
from nlg_templates.compare_integer import compare_integers_new
from nlg_templates.comparison import comparison
from nlg_templates.one_hop import one_hop
from nlg_templates.same_relate import same_relate
from nlg_templates.single_and import single_and
from nlg_templates.single_or import single_or
from nlg_templates.three_hop import three_hop
from nlg_templates.two_hop import two_hop
from nlg_templates.zero_hop import zero_hop
from question_engine import execute_handlers
from search_and_expansion import do_dfs
from text_templating import compute_question_synonyms, fill_in_text_templates
from utils import create_AST, deepest_node, insert_subtree


def expand_nodes_in_tree(template_ast, node, param_to_type):
    # split node types into sub_node_types if it is not of one of the types, where _ does not indicatea short hand expression of two or more nodes

    # NOTE: this essentially reimplements the expansion step of the engine, but we skip many fields of the nodes
    node_data = node.data
    node_type = node_data["type"]

    non_expanding_types = execute_handlers.keys()
    if any(net == node_type for net in non_expanding_types):
        # nothing changes for these nodes, so abort
        return template_ast

    subtree = Tree()
    sub_node_types = node_type.split("_")
    for sub_node_type in sub_node_types[::-1]:
        if "filter" in sub_node_type:
            for si in node_data["side_inputs"][-4:][::-1]:
                this_node_type = f"filter_{param_to_type[si].lower()}"
                data = {"side_inputs": [si], "type": this_node_type}
                current_parent = deepest_node(subtree)
                subtree.create_node(this_node_type, data=data, parent=current_parent)
        elif "relate" in sub_node_type:
            si = node_data["side_inputs"][0]
            this_node_type = sub_node_type
            data = {"side_inputs": [si], "type": this_node_type}
            current_parent = deepest_node(subtree)
            subtree.create_node(this_node_type, data=data, parent=current_parent)
        else:
            data = {"type": sub_node_type}
            current_parent = deepest_node(subtree)
            subtree.create_node(sub_node_type, data=data, parent=current_parent)

    template_ast = insert_subtree(template_ast, node, subtree)
    return template_ast


def use_instantiated_template(
    scene_struct: Scene_Struct,
    template: Template,
    question,
    metadata: Metadata,
    answer_counts: Answer_Counts,
    synonyms: Synonyms,
    template_info,
    max_instances: Optional[int] = None,
    verbose: bool = False,
) -> List[List[str]]:
    """
  This implementation uses an existing question and does not generate its own question.
  
  There are two kinds of templates: abstract ones (template) and instanciated ones (program). I want to map value_inputs of the programm to the side_inputs of the template.

  One problem is, that the abstract template has more placeholders than the instanciated ones, as empty variables are dropped
  Another problem is, that both templates have similar but not identical node tree structures

  Go linearly through them
  """
    assert scene_struct["image_filename"] == question["image_filename"]

    program = question["program"]
    final_filters = {
        si: "" for node in template["nodes"] for si in node.get("side_inputs", [])
    }
    param_to_type = {p["name"]: p["type"] for p in template["params"]}

    # NEW AST BASED Approach:
    # 1. create ast of tempalate
    template_ast = create_AST(template["nodes"])
    assert len(template_ast) > 0

    # 2. expand it
    for nid in list(template_ast.expand_tree())[::-1]:

        node = template_ast[nid]
        template_ast = expand_nodes_in_tree(template_ast, node, param_to_type)

    # 3. create ast of program
    program_ast = create_AST(program)

    # 4. match it to the ast of the program
    program_nids = program_ast.expand_tree(sorting=False)
    program_nid = next(program_nids)
    assert len(template_ast) >= len(program_ast)
    for template_nid in template_ast.expand_tree(sorting=False):
        program_node = program_ast[program_nid].data
        template_node = template_ast[template_nid].data

        if template_node["type"] == program_node["function"]:
            side_inputs = template_node.get("side_inputs", [])
            assert 0 <= len(side_inputs) <= 1
            if len(side_inputs) == 1:
                value_inputs = program_node["value_inputs"]
                assert len(value_inputs) == 1
                final_filters[side_inputs[0]] = value_inputs[0]
            try:
                program_nid = next(program_nids)
            except StopIteration:
                break

    final_states = [{"vals": final_filters, "answer": question["answer"]}]

    # Second: Find a counter factual explanations
    explanation_states = run_explanation_filters(
        template,
        final_states,
        metadata,
        scene_struct,
        answer_counts,
        max_instances,
        verbose,
    )
    # Fourth: Actually instantiate the template with the solutions we've found
    # NOTE:
    # This code does not output anything that is needed for the final explanation generation. 
    # However, it is still needed to keep the random number generation state indentical to the one we used when generating the official dataset release.
    _, _, _ = fill_in_text_templates(
        final_states, explanation_states, template, synonyms, template_info, question
    )

    placeholder_to_attr: Dict[str, str] = {
        "<Z>": "size",
        "<C>": "color",
        "<M>": "material",
        "<S>": "shape",
    }

    assert len(final_states) == 1
    question_synonyms = {}
    for state in final_states:
        question_synonyms, current_synonyms = compute_question_synonyms(
            synonyms, state, template, question
        )

    fn, idx = template_info

    # 1. Scene/Question understanding
    filter_to_objects, filter_to_relation = understand_question(
        explanation_states, final_filters, synonyms, question_synonyms
    )

    # 2. Uniqueness Refinement (NOTE: Maybe all of this code could move up to the object creation)
    # leaves: List of ids for the given template, which is an output (NOTE: in the templates, we could also have a key "extra_attrs" which maps the id to a list of extra attrs, e.g. "3": ["size"]. More flexible, but also more effort and not really needed atm)
    leaves = template.get("leaves", [])
    extra_attrs = template.get("extra_attrs", [])

    # for leaf_id in leaves:
    UNIQUE = False
    DROP = False
    drop_mode = None
    if DROP:
        # we only want to drop objects from a single leaf to make it not too obvious
        id_to_drop = choice(leaves)

    id_to_attrs = {}
    for id, objects in filter_to_objects.items():
        required_attrs = [
            placeholder_to_attr[remove_id(ph)]
            for ph, value in final_filters.items()
            if get_id(ph) == id and value != "" and remove_id(ph) != "<R>"
        ]

        id_to_attrs[id] = {"required": required_attrs, "extra": extra_attrs}

        if id in leaves:
            # assigning the scene struct will enable the contained object to iterate around its unqiue descriptions
            # extra_attrs only applies to leaves
            objects.set_scene_settings(
                scene_struct, required_attrs, extra_attrs, UNIQUE
            )

            if DROP and id == id_to_drop:
                objects, drop_mode = drop_objects(objects, final_filters, id)
                # this creates a new object, reapply set_scene_settings and overwrite in filter_to_objects
                objects.set_scene_settings(
                    scene_struct, required_attrs, extra_attrs, UNIQUE
                )
                filter_to_objects[id] = objects

        else:
            objects.set_scene_settings(
                scene_struct, required_attrs, unique_descriptions=UNIQUE
            )

    # now each leaf object knows how describe itself in the given scene

    # 3. per question NLG Template
    # 4. Text Realization
    if fn == "compare_integer.json":
        text_f_expl = [compare_integers_new(idx, filter_to_objects, filter_to_relation)]
    elif fn == "comparison.json":
        text_f_expl = [
            comparison(idx, filter_to_objects, filter_to_relation, id_to_attrs)
        ]
    elif fn == "zero_hop.json":
        text_f_expl = [
            zero_hop(idx, filter_to_objects, filter_to_relation, id_to_attrs)
        ]
    elif fn == "one_hop.json":
        text_f_expl = [one_hop(idx, filter_to_objects, filter_to_relation, id_to_attrs)]
    elif fn == "two_hop.json":
        text_f_expl = [two_hop(idx, filter_to_objects, filter_to_relation)]
    elif fn == "three_hop.json":
        text_f_expl = [three_hop(idx, filter_to_objects, filter_to_relation)]
    elif fn == "single_or.json":
        text_f_expl = [single_or(idx, filter_to_objects, filter_to_relation)]
    elif fn == "single_and.json":
        text_f_expl = [single_and(idx, filter_to_objects, filter_to_relation)]
    elif fn == "same_relate.json":
        text_f_expl = [
            same_relate(idx, filter_to_objects, filter_to_relation, id_to_attrs)
        ]
    else:
        raise NotImplementedError

    if DROP and drop_mode == "nothing_to_drop":
        # we just remove the explanations, which makes them easy to filter in pandas later on
        text_f_expl = [[]]

    # the list set thing removes duplicate explanation
    assert len(text_f_expl) == 1
    return [list(set(text_f_expl[0]))]


def drop_objects(
    objects: Objects, final_filters: Dict, current_id
) -> Tuple[Objects, str]:
    """
  This generates INCORRECT explanations, by randomly dropping objects from the leaf objects (if possible). It is used for the user study on (object) completeness.

  Args:
      objects (Objects): The Objects object to drop from.
      final_filters (Dict): The final filters of the given question.

  Returns:
      Tuple[Objects, str]: The remaining objects wrapped as Objects and the drop_mode which describes what has happened.
  """
    # we create a new Objects object from the remaining objects to correctly set numerus, aggregation, etc. ...

    number_of_objects = len(objects.objects)

    # we can only do this if we have found an object
    if number_of_objects > 0:
        # in any case we have to drop at least one object
        number_of_objects_to_keep = randint(0, number_of_objects - 1)
        kept_objects = sample(objects.objects, number_of_objects_to_keep)

        if number_of_objects_to_keep == 0:
            # if there is only one object to drop, we need to create a negative object
            # we find the negative evidence
            negative_evidence = keep_attr_items_with_id(final_filters, current_id)
            negative_object = CLEVRObject.from_filters(negative_evidence)
            # we chain the synonyms from the objects (hopefully this uses the synonyms good enough)
            synonyms = ChainMap(*[o.synonyms for o in objects.objects])
            remaining_objects = Objects(
                objects=[], negative_objects=[negative_object], synonyms=synonyms,
            )
        else:
            # one or more objects are kept, so we just create it
            remaining_objects = Objects(kept_objects)

        # keep track of what operation has happend
        drop_mode = f"kept_{number_of_objects_to_keep}"

        # overwrite the original objects with our modified variant.
        assert len(remaining_objects) < len(objects)
        objects = remaining_objects
    else:
        # no objects found, so we cannot drop any of them
        drop_mode = "nothing_to_drop"

    return objects, drop_mode


def run_explanation_filters(
    template: Template,
    final_states,
    metadata: Metadata,
    scene_struct: Scene_Struct,
    answer_counts: Answer_Counts,
    max_instances: Optional[int],
    verbose: bool = False,
) -> List:
    """
  If a question contains multiple references to the objects, we need to do cf explanations individually for each of them. So this is a per filter iteration (for which we find all objects which almost match), in contrast to a per object iteration (for which we would find all filters, which almost match the object).
  """

    sub_template = copy.deepcopy(template)

    fse_list = []

    if len(final_states) == 0:
        return fse_list
    final_filters = final_states[0]["vals"]

    # get the AST of the nodes
    ast = create_AST(sub_template["nodes"])

    # Take the question template and derive multiple shorter sub templates for all the filter nodes and make them individual programs

    scene_node: Node = {"inputs": [], "type": "scene"}
    query_attributes_node = lambda inputs: {
        "inputs": [inputs],
        "type": "query_attributes",
    }

    # run individual sub programs from each filter node
    all_filter_subtrees = [
        ast.subtree(nid.identifier)
        for nid in ast.filter_nodes(
            lambda n: "filter" in n.data["type"] or "same" in n.data["type"]
        )
    ][::-1]
    prev_outputs = []
    for i, nodes_along_path in enumerate(all_filter_subtrees):

        # iterate over the last tree fragments and freeze all their parts
        for j in range(i):
            try:
                # freeze whats already been comupted
                amputated_nid = nodes_along_path.parent(all_filter_subtrees[j].root)
                nodes_along_path.remove_node(all_filter_subtrees[j].root)
                nodes_along_path.create_node(
                    "frozen",
                    identifier=all_filter_subtrees[j].root,
                    parent=amputated_nid,
                    data={"type": "frozen", "_output": [*prev_outputs[j]]},
                )
            except NodeIDAbsentError:
                pass

        # Fix up Tree
        expanded_tree = list(nodes_along_path.expand_tree())
        for nid in expanded_tree:
            # Remove _unique, _count and _exist
            nodes_along_path[nid].data["type"] = (
                nodes_along_path[nid]
                .data["type"]
                .replace("_count", "")
                .replace("_unique", "")
                .replace("_exist", "")
            )

            # attach inputs of children
            children_nodes = nodes_along_path.children(nid)
            inputs: List[Optional[int]] = []
            for child in children_nodes:
                inputs.append(expanded_tree[::-1].index(child.identifier))
            nodes_along_path[nid].data["inputs"] = inputs

        # utility to convert a tree into a node sequence
        tree_to_nodes = lambda ast: [ast[nid].data for nid in ast.expand_tree()]

        # append the query attributes node
        nodes_with_qa = tree_to_nodes(nodes_along_path)[::-1]
        nodes_with_qa = nodes_with_qa + [query_attributes_node(len(nodes_with_qa) - 1)]

        sub_template["nodes"] = nodes_with_qa

        # run the sub template against the engine, reverse the result and append it to the list
        e, fse = do_dfs(
            sub_template,
            metadata,
            scene_struct,
            verbose,
            answer_counts,
            max_instances,
            final_filters=final_filters,
        )

        if any(["same" in nid["type"] for nid in nodes_with_qa]):
            # for questions with same node, we need to create two variants, one with same and one with different for the counter factual
            for j, nid in enumerate(nodes_with_qa):
                if "same" in nid["type"]:
                    nodes_with_qa[j]["type"] = nodes_with_qa[j]["type"].replace(
                        "same", "different"
                    )
            sub_template["nodes"] = nodes_with_qa
            _, fse_cf = do_dfs(
                sub_template,
                metadata,
                scene_struct,
                verbose,
                answer_counts,
                max_instances,
                final_filters=final_filters,
            )
            fse = fse_cf + fse

        fse.reverse()
        fse_list.append((fse, nodes_with_qa))
        prev_outputs.append(e["nodes"][-2]["_output"])

    return fse_list

