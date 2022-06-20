from __future__ import annotations

from itertools import product
from math import prod
from typing import Dict, Union

from custom_types import Synonyms

from nlg_system.objects import CLEVRObject, Objects


class Relation:
    def __init__(self, relation: str, synonyms: Synonyms) -> None:
        self.relation = relation
        self.synonyms = {k: v for k, v in synonyms.items() if k == self.relation}

        self.update_max_iter()

    def realize(self, iter: int = 0) -> str:
        assert 0 <= iter < self.max_iter

        # create all possible synonym permutations (or rather their indices)
        permuted_synonyms_indices = list(
            product(*[range(len(v)) for v in self.synonyms.values()])
        )

        def relation2syn(attr):
            if attr in self.synonyms.keys():
                idx = list(self.synonyms.keys()).index(attr)
                syn_idx = permuted_synonyms_indices[iter][idx]
                return list(self.synonyms.values())[idx][syn_idx]
            else:
                return attr

        return relation2syn(self.relation)

    def update_max_iter(self):
        # the max iter is a product of all the synonym variations
        option_lens = [len(v) for v in self.synonyms.values()]
        self.max_iter = prod(option_lens)

    def __eq__(self, other: Relation) -> bool:
        return self.relation == other.relation


class RelativeClause:
    def __init__(
        self,
        objects: Objects,
        relation: Relation,
        object: Union[Objects, RelativeClause],
        use_verb: bool = True,
    ) -> None:
        """
        Build a relative clause.

        Args:
            objects (Union[Objects, RelativeClause]): Either the objects which are in <relation> to <object>. Or another relative clause (used for single_and)
            relation (Relation): The Relation Object (e.g. left)
            object (Union[Objects, RelativeClause]): The root object or another relation if there are multiple relations chained (e.g. three hop)
            use_verb (bool, optional): Whether to use the verb in the relation (disabling it may be useful for some sentence constructions). Defaults to True.
        """
        self.objects = objects
        self.relation = relation
        self.object = object
        self.use_verb = use_verb
        self.numerus = self.objects.numerus

        self.relation_words = ["that", "which"]

        self.effective_length = (
            self.objects.effective_length + self.object.effective_length
        )

        self.update_max_iter()

    def realize(self, neg_evidence: bool = False, iter: int = 0) -> str:
        assert 0 <= iter < self.max_iter

        relation_iter = iter // (len(self.relation_words) * self.objects.max_iter)
        relation_word_iter = iter // (self.objects.max_iter * self.relation.max_iter)
        objects_iter = iter // (len(self.relation_words) * self.relation.max_iter)

        realized_objects = self.objects.realize(
            neg_evidence=neg_evidence, iter=objects_iter
        )
        verb = "is" if self.objects.numerus == "singular" else "are"

        # realize the object (which is the root of the)
        # relations use "the" instead of "a"
        self.set_determiner("the")
        realized_object = self.object.realize()

        realized_relation = self.relation.realize(iter=relation_iter)
        if self.use_verb:
            relation_word = self.relation_words[relation_word_iter]
            joined_text = " ".join(
                [
                    realized_objects,
                    relation_word,
                    verb,
                    realized_relation,
                    realized_object,
                ]
            )
            return " ".join(joined_text.split())
        else:
            return " ".join([realized_objects, realized_relation, realized_object])

    def update_max_iter(self):
        for obj in self.objects:
            obj.update_max_iter()
        self.object.update_max_iter()
        self.relation.update_max_iter()

        if self.use_verb:
            self.max_iter = (
                len(self.relation_words)
                * self.objects.max_iter
                * self.relation.max_iter
            )
        else:
            self.max_iter = self.objects.max_iter * self.relation.max_iter

    def set_determiner(self, determiner: str):
        """
        recursive setter to set determiner. 

        calls itself if self.object is another (chained) RelativeClause

        Args:
            determiner (str): the determiner
        """
        if isinstance(self.object, RelativeClause):
            self.object.set_determiner(determiner)
            self.object.objects.set_determiner(determiner)
        elif isinstance(self.object, Objects):
            self.object.determiner = determiner
        else:
            raise NotImplementedError


class CummulativeRelation:
    """
    This calss builds texts like "A is to the left of B and to the right of C."
    """

    def __init__(
        self,
        objects: Objects,
        relation_a: Relation,
        object_a: Objects,
        relation_b: Relation,
        object_b: Objects,
    ) -> None:
        self.objects = objects
        self.relation_a = relation_a
        self.relation_b = relation_b
        self.object_a = object_a
        self.object_b = object_b

        self.numerus = self.objects.numerus

        self.effective_length = (
            self.objects.effective_length
            + self.object_a.effective_length
            + self.object_b.effective_length
        )

        self.update_max_iter()

    def update_max_iter(self):
        self.objects.update_max_iter()
        self.relation_a.update_max_iter()
        self.relation_b.update_max_iter()
        self.object_a.update_max_iter()
        self.object_b.update_max_iter()

        # our own contributions come from the three components
        self.max_iter = (
            self.objects.max_iter
            * self.relation_a.max_iter
            * self.relation_b.max_iter
            * self.object_a.max_iter
            * self.object_b.max_iter
        )

    def realize(self, neg_evidence: bool = False, iter: int = 0):
        assert 0 <= iter < self.max_iter

        # compute the per-component iters
        objects_iter = iter // (
            self.relation_a.max_iter
            * self.relation_b.max_iter
            * self.object_a.max_iter
            * self.object_b.max_iter
        )
        relation_a_iter = iter // (
            self.objects.max_iter
            * self.relation_b.max_iter
            * self.object_a.max_iter
            * self.object_b.max_iter
        )
        relation_b_iter = iter // (
            self.objects.max_iter
            * self.relation_a.max_iter
            * self.object_a.max_iter
            * self.object_b.max_iter
        )
        object_a_iter = iter // (
            self.objects.max_iter
            * self.relation_a.max_iter
            * self.relation_b.max_iter
            * self.object_b.max_iter
        )
        object_b_iter = iter // (
            self.objects.max_iter
            * self.relation_a.max_iter
            * self.relation_b.max_iter
            * self.object_a.max_iter
        )

        self.set_determiner("the")
        realized_objects = self.objects.realize(neg_evidence, iter=objects_iter)
        realized_relation_a = self.relation_a.realize(relation_a_iter)
        realized_relation_b = self.relation_b.realize(relation_b_iter)
        realized_object_a = self.object_a.realize(iter=object_a_iter)
        realized_object_b = self.object_b.realize(iter=object_b_iter)

        # Use this for the "[that|which] <verb>" constructions / add this to the max_iter
        # verb = "is" if self.objects.numerus == "singular" else "are"

        if self.relation_a == self.relation_b:
            # "<A> <is> <to the left of> <B> and <of> <C>."
            assert realized_relation_a == realized_relation_b
            components = [
                realized_objects,
                # verb,
                realized_relation_a,
                realized_object_a,
                "and",
                realized_object_b,
            ]
        else:
            # "<A> <is> <to the left of> <B> and <to the right of> <C>."
            components = [
                realized_objects,
                # verb,
                realized_relation_a,
                realized_object_a,
                "and",
                realized_relation_b,
                realized_object_b,
            ]

        return " ".join(components)

    def set_determiner(self, determiner: str):
        """
        setter to set determiner. 

        Args:
            determiner (str): the determiner
        """
        self.object_a.determiner = determiner
        self.object_b.determiner = determiner


class SameRelation:
    """
    <A> has the same <size/color/...> as <B>.

    Very similar to the RelativeClause but the "relation" are attributes here, has no synonyms and a help verb is used
    """

    def __init__(self, objects: Objects, attribute: str, object: Objects) -> None:
        self.objects = objects
        self.attribute = attribute
        self.object = object

        # just use the numerus of the objects
        self.numerus = self.objects.numerus

        self.relation_words = ["that", "which"]
        self.identity_words = ["same", "identical"]

        self.effective_length = (
            self.objects.effective_length + self.object.effective_length
        )

        self.update_max_iter()

    def update_max_iter(self):
        self.objects.update_max_iter()
        self.object.update_max_iter()

        self.max_iter = (
            self.objects.max_iter
            * self.object.max_iter
            * len(self.relation_words)
            * len(self.identity_words)
        )

    def realize(self, neg_evidence: bool = False, iter: int = 0) -> str:
        assert 0 <= iter < self.max_iter

        objects_iter = iter // (
            self.object.max_iter * len(self.relation_words) * len(self.identity_words)
        )
        object_iter = iter // (
            self.objects.max_iter * len(self.relation_words) * len(self.identity_words)
        )
        relation_word_iter = iter // (
            self.object.max_iter * self.objects.max_iter * len(self.identity_words)
        )
        identity_word_iter = iter // (
            self.object.max_iter * self.objects.max_iter * len(self.relation_words)
        )

        realized_objects = self.objects.realize(
            neg_evidence=neg_evidence, iter=objects_iter
        )
        realized_object = self.object.realize(
            neg_evidence=neg_evidence, iter=object_iter
        )
        relation_word = self.relation_words[relation_word_iter]
        identity_word = self.identity_words[identity_word_iter]

        help_verb = "has" if self.objects.numerus == "singular" else "have"

        components = [
            realized_objects,
            relation_word,
            help_verb,
            "the",
            identity_word,
            self.attribute,
            "as",
            realized_object,
        ]

        return " ".join(components)
