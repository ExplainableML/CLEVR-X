from __future__ import annotations

from collections import Counter
from itertools import chain, combinations, permutations, product
from math import prod
from typing import Dict, Iterable, List, Set

from id_handling import remove_id
from match_set_templating import join_list_with_comma_and
from num2words import num2words

from nlg_system.equality_functions import equal_except


class CLEVRObject:
    def __init__(self, size: str, color: str, material: str, shape: str) -> None:
        self.size = size
        self.color = color
        self.material = material
        self.shape = shape
        # the attrs are the main way to interact with the objects attributes
        self.attrs = {
            "size": self.size,
            "color": self.color,
            "material": self.material,
            "shape": self.shape,
        }

        self.max_iter = 1

        self.effective_length = sum(
            [attr != "" for attr in [size, color, material, shape]]
        )

        self.scene_struct = None

        # combines the mandatory shape (needed for a complete sentence to avoid the "object" replacement) with what the question mandates (c.f. set_scene_settings)
        self.required_attrs: Set[str] = set(["shape"])

        # List of possible attr combinations which could be used to describe ourselfes (uniquely or minimally)
        # each unique_attr in unique_attrs has >= number of elements than self.required_attrs
        self.describing_attrs = [self.attrs.keys()]

        self.synonyms: Dict[str, List[str]] = {}

        self.update_max_iter()

    def __eq__(self, other):
        return self.attrs == other.attrs

    def __hash__(self) -> int:
        return hash(tuple(self.attrs.values()))

    def realize(self, iter: int = 0, complete_description: bool = False) -> str:
        assert 0 <= iter < self.max_iter

        # create all possible synonym permutations
        # permuted_synonyms = list(product(*self.synonyms.values()))
        permuted_synonyms_indices = list(
            product(*[range(len(v)) for v in self.synonyms.values()])
        )

        attribute_synonym_iter = iter // len(self.describing_attrs)
        description_iter = iter // prod([len(v) for v in self.synonyms.values()])

        def attr2syn(attr):
            if attr in self.synonyms.keys():
                idx = list(self.synonyms.keys()).index(attr)
                syn_idx = permuted_synonyms_indices[attribute_synonym_iter][idx]
                return list(self.synonyms.values())[idx][syn_idx]
            else:
                return attr

        if complete_description:
            full_description = " ".join(
                attr2syn(attr)
                for attr in [self.size, self.color, self.material, self.shape]
            )
            full_description = " ".join(full_description.split())
            return full_description
        else:
            chosen_attrs = self.describing_attrs[description_iter]
            unique_description = [
                attr2syn(self.attrs[chosen_attr]) for chosen_attr in chosen_attrs
            ]
            unique_description = [desc for desc in unique_description if desc != ""]
            return " ".join(unique_description)

    def realize_attribute(self, attribute: str, iter: int = 0):
        # Technically the max_iter would be different for this, as we do not have the permutations
        assert 0 <= iter < self.max_iter

        # create all possible synonym permutations
        permuted_synonyms_indices = list(
            product(*[range(len(v)) for v in self.synonyms.values()])
        )

        attribute_synonym_iter = iter // len(self.describing_attrs)

        def attr2syn(attr):
            if attr in self.synonyms.keys():
                idx = list(self.synonyms.keys()).index(attr)
                syn_idx = permuted_synonyms_indices[attribute_synonym_iter][idx]
                return list(self.synonyms.values())[idx][syn_idx]
            else:
                return attr

        non_empty_attrs = {
            "size": self.size,
            "color": self.color,
            "material": self.material,
            "shape": self.shape,
        }

        return attr2syn(non_empty_attrs[attribute])

    def __minimal_unique_descriptions(self):
        """
        The goal is to find a unqiue descriptions and then return the list of the shortest ones.
        """
        assert self.scene_struct is not None
        assert self.required_attrs is not None
        scene_objects = self.scene_struct["objects"]

        unique_attrs = []
        all_attrs = ["size", "color", "material", "shape"]

        objects_with_all_attrs = [
            [scene_object[attr] for attr in all_attrs] for scene_object in scene_objects
        ]
        identical_objects_count = objects_with_all_attrs.count(
            list(self.attrs.values())
        )
        assert identical_objects_count > 0

        for i in range(self.lower_attr_count_bound, 5):
            # try to only use i unqiue properties
            unique = False
            for attrs in combinations(all_attrs, i):
                # the permutation has to include all required attrs,
                misses_required_attrs = not all(
                    req_attr in attrs for req_attr in self.required_attrs
                )

                # so skip this variant
                if misses_required_attrs:
                    continue

                # only look at attrs
                # Uniqueness test: Count ourself with the chosen attrs, if == 1 -> unique
                objects_with_current_attrs = [
                    [scene_object[attr] for attr in attrs]
                    for scene_object in scene_objects
                ]
                own_current_attrs = [self.attrs[attr] for attr in attrs]
                unique = (
                    objects_with_current_attrs.count(own_current_attrs)
                    == identical_objects_count
                )

                if unique:
                    unique_attrs.append(attrs)

            # if we have found something unique, we do not even try to find a longer description
            if unique:
                break

        # store it in describing_attrs
        assert len(unique_attrs) > 0
        self.describing_attrs = unique_attrs

    def __minimal_descriptions(self):
        """
        The goal is to find a minimal descriptions and then return the list of the shortest ones.
        """

        # 1. keep shape
        # 2. keep question attrs
        # -> that is in self.required_attrs
        # 3. ignore others
        # 4. aggregate

        # copy paste reference
        assert self.scene_struct is not None
        assert self.required_attrs is not None

        all_attrs = ["size", "color", "material", "shape"]

        sorted_required_attrs = [
            attr for attr in all_attrs if attr in self.required_attrs
        ]

        self.describing_attrs = [sorted_required_attrs]
        assert len(self.describing_attrs) > 0

    def set_scene_settings(
        self,
        scene_struct,
        question_required_attrs,
        extra_attrs: List[str] = [],
        unique: bool = True,
    ):
        # save the scene struct
        self.scene_struct = scene_struct

        # at least mention the required attrs + 1, but at max all 4 attrs.
        self.lower_attr_count_bound = min(4, len(question_required_attrs) + 1)

        # union the required attrs with the always required attr shape (might already be the +1)
        self.required_attrs = (
            set(question_required_attrs) | set(extra_attrs) | set(["shape"])
        )
        assert "shape" in self.required_attrs

        if unique:
            # compute the minimal unique descriptions
            self.__minimal_unique_descriptions()
        else:
            self.__minimal_descriptions()

        # Update max iter
        self.update_max_iter()

    def set_synonyms(self, synonyms):
        # TODO: It would be nicer to have this directly in __init__

        # We get all synonyms but we should restrict ourself to only those which are relevant to our attributes
        self.synonyms = {k: v for k, v in synonyms.items() if k in self.attrs.values()}

        self.update_max_iter()

    def update_max_iter(self):
        # the max iter is a product of all the synonym variations and all the variations in addressing objects uniquely
        # NOTE: Actually, if a a unique combination does not need e.g. the size, those synonym variations are irrelevant

        # a synonym option of len 1 does not give us any extra choices
        option_lens = [len(v) for v in self.synonyms.values()]
        self.max_iter = prod(option_lens) * len(self.describing_attrs)

    @staticmethod
    def from_filters(filters: Dict[str, str]):
        # remove the id from the filters and drop the empty strings (which will allow us to default to the correct values)
        cleaned_filters = {remove_id(k): v for k, v in filters.items() if v != ""}
        return CLEVRObject(
            cleaned_filters.get("<Z>", ""),
            cleaned_filters.get("<C>", ""),
            cleaned_filters.get("<M>", ""),
            cleaned_filters.get("<S>", "thing"),
        )
        pass


class Objects:
    def __init__(
        self,
        objects: List[CLEVRObject],
        negative_objects: List[CLEVRObject] = [],
        determiner: str = "a",
        numerus: str = "singular",
        aggregation: str = "internal",
        synonyms=None,
    ) -> None:
        self.objects = objects
        self.negative_objects = negative_objects
        assert len(self.objects) == 0 or len(self.negative_objects) == 0
        self.determiner = determiner
        self.numerus = numerus
        self.aggregation = aggregation
        # TODO: maybe merge negative objects into objects and use a negative: bool Flag
        # for different variants of the same thing

        # rough approximation how many attrs there are
        self.effective_length: int = -1

        self.permutation_max_iter: int = 1
        self.objects_max_iter: int = 1

        self.unique_descriptions: bool = False

        self.__set_synonyms(synonyms)

        # it is important to run this last, as the step before modifies how __eq__ behaves
        self.__run_aggregation()

        self.update_max_iter()

    def __run_aggregation(self):

        # BUG: the all_equal_except always compares to the first object, so it will not find that objects 2 and 3 are almost equal. Fix: Implement a custom counter, which has its own custom equality check and then if else on the results of that.

        # set internal states according to input
        if len(self.objects) == 0:
            assert len(self.negative_objects) == 1
            self.numerus = "plural"
            self.determiner = "no"
            self.effective_length = self.negative_objects[0].effective_length
            self.objects_max_iter = self.negative_objects[0].max_iter
            self.aggregation_mode = "negativ_object"
        elif len(self.objects) == 1:
            # only one object
            self.numerus = "singular"
            self.determiner = "a"
            self.effective_length = self.objects[0].effective_length
            self.objects_max_iter = self.objects[0].max_iter
            self.aggregation_mode = "one_object"
        elif all(self.objects[0] == o for o in self.objects):
            # all objects are the same count them
            self.numerus = "plural"
            self.determiner = num2words(len(self.objects))
            self.effective_length = 1 + self.objects[0].effective_length
            self.objects_max_iter = self.objects[0].max_iter
            self.aggregation_mode = "all_identical"
        elif len(set(self.objects)) < len(self.objects):
            # some objects are the same
            counted_objs = Counter(self.objects)
            self.multiple_objects = [
                Objects([obj] * count) for obj, count in counted_objs.items()
            ]
            self.numerus = "plural"
            self.effective_length = sum(
                obj.effective_length for obj in self.multiple_objects
            )
            self.permutation_max_iter = len(list(permutations(self.multiple_objects)))
            self.objects_max_iter = prod(obj.max_iter for obj in self.multiple_objects)
            self.aggregation_mode = "some_identical"
        elif all(equal_except(self.objects[0], o, "size") for o in self.objects):
            self.numerus = "plural"
            self.effective_length = 3 + len(self.objects)
            self.objects_max_iter = self.objects[0].max_iter
            self.aggregation_mode = "identical_except_size"
        # elif all(equal_except(self.objects[0], o, "color") for o in self.objects):
        #     self.effective_length = 3 + len(self.objects)
        # elif all(equal_except(self.objects[0], o, "material") for o in self.objects):
        #     self.effective_length = 3 + len(self.objects)
        elif all(equal_except(self.objects[0], o, "shape") for o in self.objects):
            self.numerus = "plural"
            self.effective_length = 3 + len(self.objects)
            self.objects_max_iter = self.objects[0].max_iter
            self.aggregation_mode = "identical_except_shape"
        else:
            # all different (maybe some shared properties), we use proximity singular
            self.numerus = "singular"
            self.determiner = "a"
            self.effective_length = self.objects[0].effective_length * len(self.objects)
            self.permutation_max_iter = len(list(permutations(self.objects)))
            self.objects_max_iter = prod(obj.max_iter for obj in self.objects)
            self.aggregation_mode = "all_different"

    def __len__(self):
        return len(self.objects)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        # NOTE: maybe iterate over both, self.objects and self.negative_objects?
        if self.n < len(self.objects):
            self.n += 1
            return self.objects[self.n - 1]
        else:
            raise StopIteration

    def realize(self, neg_evidence: bool = False, iter: int = 0) -> str:
        assert 0 <= iter < self.max_iter

        def object_iter(
            objects_list: List[CLEVRObject], iter: int, obj_idx: int,
        ) -> int:
            """
            computes the iter of the object located at obj_idx in objects_list

            Args:s
                objects_list (List[CLEVRObject]): the list of objects (e.g. self.objects or could be the permuted self.objects)
                iter (int): the iter
                obj_idx (int): the idx of the object

            Returns:
                int: the final iter
            """
            all_other_objexts = objects_list[:obj_idx] + objects_list[obj_idx + 1 :]
            iter = iter // (
                self.permutation_max_iter
                * prod(obj.max_iter for obj in all_other_objexts)
            )
            return iter

        if len(self.objects) > 1:
            permutation_iter = iter // prod(obj.max_iter for obj in self.objects)
        else:
            permutation_iter = 0

        if len(self.objects) == 0:
            if neg_evidence:
                return f"{self.determiner} {self.negative_objects[0].realize()}s"
            else:
                return ""
        elif len(self.objects) == 1:
            # only one object
            this_object_iter = object_iter(self.objects, iter, 0)
            realized_object = self.objects[0].realize(iter=this_object_iter)
            return f"{self.determiner} {realized_object}"
        elif all(self.objects[0] == o for o in self.objects):
            # all objects are the same, count them
            this_object_iter = object_iter(self.objects, iter, 0)
            realized_object = self.objects[0].realize(iter=this_object_iter)
            return f"{self.determiner} {realized_object}s"
        elif len(set(self.objects)) < len(self.objects):
            # some objects are the same
            permuted_objects = list(permutations(self.multiple_objects))[
                permutation_iter
            ]
            realized_objs = [f"{obj.realize()}" for obj in permuted_objects]
            return join_list_with_comma_and(realized_objs)
        elif all(equal_except(self.objects[0], o, "size") for o in self.objects):
            if self.aggregation == "internal":
                base_obj = self.objects[0]

                # sizes
                sizes = [
                    f"{self.determiner} {o.realize_attribute('size', object_iter(self.objects, iter, i))}"
                    for i, o in enumerate(self.objects)
                ]
                joined_sizes = join_list_with_comma_and(sizes)

                # shared attributes
                this_object_iter = object_iter(self.objects, iter, 0)
                color = base_obj.realize_attribute("color", this_object_iter)
                material = base_obj.realize_attribute("material", this_object_iter)
                shape = base_obj.realize_attribute("shape", this_object_iter)
                shared_attrs = f"{color} {material} {shape}"

                return f"{joined_sizes} {shared_attrs}"
            elif self.aggregation == "front":
                raise NotImplementedError
            else:
                raise NotImplementedError
        # elif all(equal_except(self.objects[0], o, "color") for o in self.objects):
        #     base_obj = self.objects[0]
        #     raise NotImplementedError
        # elif all(equal_except(self.objects[0], o, "material") for o in self.objects):
        #     base_obj = self.objects[0]
        #     raise NotImplementedError
        elif all(equal_except(self.objects[0], o, "shape") for o in self.objects):
            if self.aggregation == "internal":
                base_obj = self.objects[0]

                # shared attributes
                this_object_iter = object_iter(self.objects, iter, 0)
                size = base_obj.realize_attribute("size", this_object_iter)
                color = base_obj.realize_attribute("color", this_object_iter)
                material = base_obj.realize_attribute("material", this_object_iter)
                shared_attrs = f"{self.determiner} {size} {color} {material}"

                # shapes
                shapes = [
                    o.realize_attribute("shape", object_iter(self.objects, iter, i))
                    for i, o in enumerate(self.objects)
                ]
                joined_shapes = join_list_with_comma_and(shapes)

                return f"{shared_attrs} {joined_shapes}"
            elif self.aggregation == "front":
                raise NotImplementedError
            else:
                raise NotImplementedError
        else:
            permuted_objects = list(permutations(self.objects))[permutation_iter]
            realized_objects = [
                obj.realize(object_iter(permuted_objects, iter, i))
                for i, obj in enumerate(permuted_objects)
            ]
            realized_objs = [
                f"{self.determiner} {realized_object}"
                for realized_object in realized_objects
            ]
            return join_list_with_comma_and(realized_objs)

    @staticmethod
    def from_iterable(iterables: Iterable[Iterable], synonyms=None):
        return Objects(
            [CLEVRObject(*iterable) for iterable in iterables], synonyms=synonyms
        )

    def __set_synonyms(self, synonyms: Dict):
        # pass the synoynm to all of our objects
        if synonyms is not None:
            for obj in self.objects:
                obj.set_synonyms(synonyms)
            for neg_obj in self.negative_objects:
                neg_obj.set_synonyms(synonyms)

    def update_max_iter(self):

        # the max_iter from Objects come from the individual CLEVRObject as well as the permutation iter

        for obj in self.objects:
            obj.update_max_iter()

        for neg_obj in self.negative_objects:
            neg_obj.update_max_iter()

        if len(self.objects) > 0:
            self.max_iter = self.objects_max_iter * self.permutation_max_iter
        elif len(self.negative_objects) == 1:
            # for negative objects, there is only one, thus no permutations
            self.max_iter = self.negative_objects[0].max_iter
        else:
            raise ValueError("Either of the previous two options must have triggered.")

    def set_scene_settings(
        self,
        scene_struct,
        required_attrs,
        extra_attrs: List[str] = [],
        unique_descriptions: bool = False,
    ):
        self.unique_descriptions = unique_descriptions

        # Do not set set_scene_settings for negative objects, only for positive objects!
        for obj in self.objects:
            obj.set_scene_settings(
                scene_struct, required_attrs, extra_attrs, unique_descriptions
            )

        if not self.unique_descriptions:
            # only minimal descriptions, this affects how we check if we have repeated objects in the scene.
            # we need to update our aggregation status
            all_attrs = set(["size", "color", "material", "shape"])
            attrs_to_mute = all_attrs - (
                set(required_attrs) | set(extra_attrs) | set(["shape"])
            )
            for obj in self.objects:
                for attr_to_mute in attrs_to_mute:
                    obj.attrs[attr_to_mute] = "EMPTY"

            self.__run_aggregation()

        self.update_max_iter()

    def set_determiner(self, determiner):
        self.determiner = determiner
