import os
from json import dumps
from treelib import Node, Tree

from typing_extensions import TypedDict

from conditions import post_condition, pre_condition
from custom_types import Template
from typing import Collection, List, Dict, Optional

def node_shallow_copy(node: Node) -> Node:
    """creates a shallow copy of a node"""
    new_node: Node = {
        "type": node["type"],
        "inputs": node["inputs"],
    }
    if "side_inputs" in node:
        new_node["side_inputs"] = node["side_inputs"]
    if "_output" in node:
        new_node["_output"] = node["_output"]
    return new_node


@post_condition(lambda retval: len(retval) > 0)
def convert_dict_to_json(data: Collection) -> str:
    """transforms nodes and states into a graph, which i can hopefully understand"""

    # basic structure
    Graph = TypedDict("Graph", {"kind": Dict[str, bool], "nodes": List, "edges": List})
    graph: Graph = {"kind": {"graph": True}, "nodes": [], "edges": []}
    for i, item in enumerate(data):
        # the label is a pretty printed version of the dictionary inside without the ', which would break the json
        label = str(item).replace("'", "")
        # label = "\n".join(["{}: {}".format(k,v) for k,v in item.items()]).replace("'", "")
        graph["nodes"].append({"id": str(i), "label": label, "shape": "box"})
        if i < len(data) - 1:
            graph["edges"].append({"from": str(i), "to": str(i + 1)})
    return dumps(graph, ensure_ascii=False)


def visualize(scene_struct, metadata, text_questions, text_f_expl, text_cf_expl):
    """
  Method to visualize a scene, its graph, the question, the answer and the explanation.
  """
    # 1. Load image - Check
    # 2. visualize scene graph
    # 3. Print Question
    # 4. Derive answer from final_states
    # 5. Print explanations
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import matplotlib.patheffects as path_effects

    fig = plt.figure(figsize=(5, 8))

    fig.add_subplot(4, 1, 1)
    img = mpimg.imread(os.path.join("images", scene_struct["image_filename"]))
    imgplot = plt.imshow(img)

    fig.add_subplot(4, 1, 2)
    text = fig.text(0, 0.25, "Q: " + str(text_questions), size=18, wrap=True)
    text.set_path_effects([path_effects.Normal()])

    fig.add_subplot(4, 1, 3)
    text = fig.text(0, 0.5, "E_f: " + str(text_f_expl), size=18, wrap=True)
    text.set_path_effects([path_effects.Normal()])

    fig.add_subplot(4, 1, 4)
    text = fig.text(0, 0.75, "E_cf: " + str(text_cf_expl), size=18, wrap=True)
    text.set_path_effects([path_effects.Normal()])

    # plt.show()

    pass


def group_params(template: Template) -> List[List[str]]:
    """
  groups params from a template into object specific specifiers e.g. Z C M S, Z2 C2 M2 S2, Z3 C3 M3 S3, ...
  Ignores #, A
  """
    # separate the params into groups of filters, where a filter filters a specific object.
    params = template["params"]
    fg: Dict[str, List[str]] = {}
    for param in params:
        param_name = param["name"]
        if "#" in param_name or "A" in param_name:
            continue
        id = param_name[2:-1]
        if fg.get(id, None) == None:
            fg[id] = [param_name]
        else:
            fg[id].append(param_name)

    return [v for k, v in sorted(fg.items())]


def back_zip(*iterables, pad_value=""):
    """
  takes iterables, right aligns them and iterates them from the fron. Exessive elements are padded.
  
  A, B, C
  X, Y

  becomes

  A, B, C
   , X, Y 
  """
    lengths = [len(it) for it in iterables]
    maximum_lengths = max(lengths)

    for i in range(maximum_lengths):
        result = []
        for j, it in enumerate(iterables):
            if maximum_lengths - i <= lengths[j]:
                result.append(it[-maximum_lengths + i])
            else:
                result.append(pad_value)
        yield tuple(result)


def recursive_add_nodes(tree, idx, nodes, parent=None) -> Tree:
    node = nodes[idx]
    node_type = node.get("type", node.get("function"))

    tree.create_node(node_type, idx, data=node, parent=parent)
    for input in node["inputs"]:
        recursive_add_nodes(tree, input, nodes, tree[idx])
    return tree


def create_AST(nodes) -> Tree:
    # create a treelib tree/AST of the current template
    return recursive_add_nodes(Tree(), len(nodes) - 1, nodes)


def insert_subtree(tree, node_to_replace, subtree):
    # assert non branching subtree
    if len(subtree.paths_to_leaves()) == 0:
        return None

    assert len(subtree.paths_to_leaves()) == 1

    # find node ID and parent of the node to replace
    nid = node_to_replace.identifier
    parent = tree.parent(nid)

    # Note the relative position in the children
    idx = None
    if parent:
        idx = tree.children(parent.identifier).index(node_to_replace)

    # cut out subtree
    children_tree = tree.remove_subtree(nid)
    children = children_tree.children(nid)
    children_subtrees = [children_tree.subtree(child.identifier) for child in children]

    # add subtree to deepest child of subtree
    deepest = deepest_node(subtree)
    for child_subtree in children_subtrees:
        subtree.paste(deepest.identifier, child_subtree)

    # paste the subtree to:
    if parent:
        # to the tree
        tree.paste(parent.identifier, subtree)
        parents_cids = parent.successors(tree.identifier)
        new_idx = parents_cids.index(subtree.root)
        if idx is not None and idx != new_idx:
            # reorder
            parents_cids.insert(idx, parents_cids.pop(new_idx))
    else:
        # top level root node, subtree is now tree
        tree = subtree

    assert len(tree) > 0
    return tree


def deepest_node(tree) -> Optional[Node]:
    """find the deepest node of a tree"""
    paths = tree.paths_to_leaves()
    if len(paths) == 0:
        return None
    elif len(paths) == 1:
        return tree[paths[0][-1]]
    else:
        raise NotImplementedError


@pre_condition(lambda nodes: nodes[-1]["type"] == "query_attributes")
@pre_condition(lambda nodes: len(nodes) > 1)
def get_answer_ids(nodes) -> set:
    """
  Explanation programs terminate with a query attribute node. This function looks at the inputs of this node and returns a set of all outputs of them.
  This are the ids of the answer objects.

  Set comprehension version: set([output for ipt in nodes[-1]["inputs"] for output in nodes[ipt]["_output"]])
  """
    ids = set()
    for ipt in nodes[-1]["inputs"]:
        for output in nodes[ipt]["_output"]:
            ids.add(output)
    return ids

