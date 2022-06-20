from utils import group_params, node_shallow_copy
from treelib import Node


def test_node_shallow_copy_keys_and_values():
    node: Node = {
        'type': "something",
        'inputs': [0,1],
        'side_inputs': ["<Z>"]
    }
    copied_node = node_shallow_copy(node)
    for (k, v), (kc, vc) in zip(node.items(), copied_node.items()):
        assert k == kc, "Keys must be equal!"
        assert v == vc, "Values must be equal!"


def test_node_shallow_copy_result_is_node():
    node: Node = {
        'type': "something",
        'inputs': [0,1],
        'side_inputs': ["<Z>"]
    }
    copied_node = node_shallow_copy(node)
    assert "type" in copied_node.keys()
    assert "inputs" in copied_node.keys()
    if "side_inputs" in node.keys():
        assert "side_inputs" in copied_node.keys()


def test_group_params():
    example_template = {"params": [{"name": "<Z>"}]}
    assert group_params(example_template) == [["<Z>"]], "single group"

    example_template = {"params": [{"name": "<#>"},
                                   {"name": "<A>"},
                                   {"name": "<#2>"},
                                   {"name": "<A2>"}]}
    assert group_params(example_template) == [], "non attributes must not be returned"

    example_template = {"params": [{"name": "<A>"},
                                   {"name": "<Z>"},
                                   {"name": "<C>"},
                                   {"name": "<M>"},
                                   {"name": "<S>"},
                                   {"name": "<#>"}]}
    assert group_params(example_template) == [["<Z>", "<C>", "<M>", "<S>"]], "answers and counts should be filtered out!"

    example_template = {"params": [{"name": "<Z>"},
                                   {"name": "<Z2>"},
                                   {"name": "<Z3>"}]}
    assert group_params(example_template) == [["<Z>"],["<Z2>"],["<Z3>"]], "place different ids in different lists"

    example_template = {"params": [{"name": "<Z>"},
                                   {"name": "<Z2>"},
                                   {"name": "<S>"},
                                   {"name": "<S2>"}]}
    assert group_params(example_template) == [["<Z>", "<S>"],["<Z2>","<S2>"]], "multiple attributes, multiple attributes"
