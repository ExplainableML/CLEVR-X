from typing import Any, Dict, List, Optional, Set, Tuple

from typing_extensions import Literal, TypedDict

# type definitions
Metadata = TypedDict(
    "Metadata",
    {
        "dataset": str,
        "types": Dict,
        "functions": List,
        "_functions_by_name": Dict,
        "_filter_options": Any,
    },
    total=False,
)
Object = TypedDict(
    "Object",
    {
        "color": str,
        "size": str,
        "rotation": float,
        "shape": str,
        "3d_coords": List[float],
        "material": str,
        "pixel_coords": List[float],
    },
)

Relationships = Dict[str, List[List[Optional[int]]]]

Directions = Dict[str, List[float]]

# FIXME: The latter part is actually Union[List[int], Set[int]], but I do not now how to model that.
Attribute_Set = Tuple[str, str, str, str]  # also called Filter sometimes
Attribute_Map = Dict[Attribute_Set, Set[int]]

# this is the scene graph description
Scene_Struct = TypedDict(
    "Scene_Struct",
    {
        "objects": List[Object],
        "relationships": Relationships,
        "image_filename": str,
        "split": str,
        "directions": Directions,
        "_filter_options": Attribute_Map,
    },
)

Node = TypedDict(
    "Node",
    {"type": str, "inputs": List[int], "side_inputs": List[str], "_output": List},
    total=False,
)
Param = Dict[str, str]

Constraint = TypedDict("Constraint", {"params": List, "type": str})  # of str or int

Template = TypedDict(
    "Template",
    {
        "text": List[str],
        "nodes": List[Node],
        "params": List[Param],
        "constraints": List[Constraint],
    },
    total=False,
)

Answer_Counts = Dict[str, int]

State = TypedDict(
    "State",
    {
        "nodes": List[Node],
        "vals": Dict[str, str],
        "input_map": Dict[int, int],
        "next_template_node": int,
        "answer": Any,
    },
)

Inputs = List[int]
Side_Inputs = List[Any]

Attribute = Literal["size", "color", "material", "shape"]

Synonyms = Dict[str, List[str]]
