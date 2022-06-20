from math import prod
from typing import List, Tuple, Union

from match_set_templating import join_list_with_comma_and

from nlg_system.clauses import (
    CummulativeRelation,
    Relation,
    RelativeClause,
    SameRelation,
)
from nlg_system.objects import CLEVRObject, Objects


class Sentence:
    def __init__(
        self, objects: Union[Objects, RelativeClause, CummulativeRelation, SameRelation]
    ):
        self.objects = objects

        self.intro_texts = [
            "There",
        ]

        self.effective_length = self.objects.effective_length

        self.update_max_iter()

    def update_max_iter(self):
        if isinstance(self.objects, Objects):
            for obj in self.objects:
                obj.update_max_iter()
        else:
            self.objects.update_max_iter()

        # own max iter contribution is all the different sentence beginnings
        self.max_iter: int = len(self.intro_texts) * self.objects.max_iter

    def realize(
        self, include_period: bool = False, neg_evidence: bool = False, iter: int = 0
    ) -> str:
        assert 0 <= iter < self.max_iter

        intro_text = self.intro_texts[iter % len(self.intro_texts)]
        verb = "is" if self.objects.numerus == "singular" else "are"
        realized_objects = self.objects.realize(
            neg_evidence, iter=iter // len(self.intro_texts)
        )

        if realized_objects == "":
            # nothing to describe
            return ""

        sentence = " ".join([intro_text, verb, realized_objects])
        if include_period:
            sentence += "."
            sentence = sentence.capitalize()

        return sentence


class ActiveSentence:
    def __init__(
        self,
        objects: Objects,
        queried_attributes: List[str],
        question_filters: List[str],
        relation: Relation = None,
        relation_object: Objects = None,
    ) -> None:
        """
        Build sentences where the objects are the subject.

        E.g. "The cube is red."
        E.g. "The cube and the sphere are red."
        E.g. "The two cubes are red."
        E.g. "The two cubes and the sphere are red."
            use the question attributes, as they are shared amongst all, maybe try to have even more attributes aggregated
        Args:
            objects (Objects): [description]
        """
        self.objects = objects

        all_attrs = ["size", "color", "material", "shape"]
        self.queried_attributes = set(queried_attributes)
        self.question_filters = set(question_filters)

        self.relation = relation
        self.relation_object = relation_object

        if self.relation is not None:
            assert self.relation_object is not None
            assert len(self.relation_object) == 1

        # restore the correct order of attributes
        self.queried_attributes = [
            attr for attr in all_attrs if attr in self.queried_attributes
        ]
        self.question_filters = [
            attr for attr in all_attrs if attr in self.question_filters
        ]

        self.effective_length = self.objects.effective_length

        self.update_max_iter()

    def update_max_iter(self):
        # how do we compute the actual iters here
        # we can exploit the synonym
        self.objects.update_max_iter()
        self.max_iter = self.objects.max_iter

        if self.relation is not None:
            self.relation.update_max_iter()

            # multiply the max_iter with the relation max_iter
            self.max_iter *= self.relation.max_iter

        if self.relation_object is not None:
            self.relation_object.update_max_iter()

            # multiply the max_iter with the relation max_iter
            self.max_iter *= self.relation_object.max_iter

    def realize(
        self, neg_evidence: bool = False, include_period: bool = False, iter: int = 0
    ) -> str:
        assert 0 <= iter < self.max_iter
        # FIXME: Use all the synonyms of the object
        # FIXME: Complete / Minimal / Minimal & Unique
        # TODO: Lets not ignore the neg_evidence flag

        if len(self.objects.negative_objects) > 0:
            return self.realize_negative_objects(iter)

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
            relation_max_iter = 1
            if self.relation is not None and self.relation_object is not None:
                relation_max_iter = (
                    self.relation.max_iter * self.relation_object.max_iter
                )

            all_other_objects = objects_list[:obj_idx] + objects_list[obj_idx + 1 :]
            iter = iter // (
                prod(obj.max_iter for obj in all_other_objects) * relation_max_iter
            )

            return iter

        # realize and join the remaining attribues (which will be before the verb)
        realized_question_filters = []
        for i, obj in enumerate(self.objects):
            obj_attrs = []
            for attr in self.question_filters:
                if obj.attrs[attr] != "EMPTY":
                    # TODO: Synonyms! with realize_attribute()
                    this_object_iter = object_iter(self.objects.objects, iter, i)
                    realized_attr = obj.realize_attribute(attr, this_object_iter)
                    obj_attrs.append(realized_attr)

            if "shape" in self.queried_attributes:
                # FIXME: proper synonyms thing/object (max_iter), respect q_syn
                things = ["thing", "object"]
                obj_attrs.append(things[iter % 2])
            elif "shape" not in [*self.question_filters, *self.queried_attributes]:
                # the question did not ask or filter for the shape, thus we can include it for better readability
                this_object_iter = object_iter(self.objects.objects, iter, i)
                obj_attrs.append(obj.realize_attribute("shape", this_object_iter))

            realized_question_filters.append(" ".join(obj_attrs))

        joined_question_filters = join_list_with_comma_and(realized_question_filters)

        # realize and join the queried attributes (which will after the verb)
        realized_queried_attributes = []
        for i, obj in enumerate(self.objects):
            this_object_iter = object_iter(self.objects.objects, iter, i)
            realized_attribute = " ".join(
                [
                    obj.realize_attribute(attr, this_object_iter)
                    for attr in self.queried_attributes
                ]
            )
            realized_queried_attributes.append(realized_attribute)

        joined_queried_attributes = join_list_with_comma_and(
            realized_queried_attributes
        )

        # determin the verb
        verb = "is" if self.objects.numerus == "singular" else "are"
        determiner = "a" if "shape" in self.queried_attributes else ""

        if self.relation is not None and self.relation_object is not None:
            realized_relation, realized_relation_object = self.__realize_relation(iter)

            realized_sentence = f"The {joined_question_filters} {realized_relation} {realized_relation_object} {verb} {determiner} {joined_queried_attributes}"
        else:

            # realize the entire sentence
            realized_sentence = f"The {joined_question_filters} {verb} {determiner} {joined_queried_attributes}"

        # add a period if needed
        if include_period:
            realized_sentence += "."

        # remove extra spaces
        realized_sentence = " ".join(realized_sentence.split())

        return realized_sentence

    def realize_negative_objects(self, iter: int) -> str:
        realized_negative_object = self.objects.negative_objects[0].realize()

        if self.relation is not None and self.relation_object is not None:
            realized_relation, realized_relation_object = self.__realize_relation(iter)
            return f"There is no {realized_negative_object} {realized_relation} {realized_relation_object}"

        else:
            return f"There is no {realized_negative_object}"

    def __realize_relation(self, iter: int) -> Tuple[str, str]:
        if self.relation is not None and self.relation_object is not None:
            relation_iter = iter // (
                self.objects.max_iter * self.relation_object.max_iter
            )
            realized_relation = self.relation.realize(iter=relation_iter)

            relation_object_iter = iter // (
                self.objects.max_iter * self.relation.max_iter
            )
            realized_relation_object = self.relation_object.realize(
                iter=relation_object_iter
            )
            return realized_relation, realized_relation_object
        else:
            return "", ""


class ActiveRelateSentence:
    def __init__(
        self,
        objects: Objects,
        queried_attributes: List[str],
        question_filters: List[str],
        same_relation: str,
        relation_object: Objects,
    ) -> None:
        """
        Generates sentences as "The cube has the same size as a large ball.
        """
        self.objects = objects

        all_attrs = ["size", "color", "material", "shape"]
        self.queried_attributes = set(queried_attributes)
        self.question_filters = set(question_filters)

        self.same_relation = same_relation
        self.relation_object = relation_object

        if self.same_relation is not None:
            assert self.relation_object is not None
            assert len(self.relation_object) == 1

        # restore the correct order of attributes
        self.queried_attributes = [
            attr for attr in all_attrs if attr in self.queried_attributes
        ]
        self.question_filters = [
            attr for attr in all_attrs if attr in self.question_filters
        ]

        self.effective_length = self.objects.effective_length

        self.update_max_iter()

    def update_max_iter(self):
        # how do we compute the actual iters here
        # we can exploit the synonym
        self.objects.update_max_iter()
        self.relation_object.update_max_iter()

        # NOTE: the objects actual respond with too many iters, as we realize it themselves :/
        self.max_iter = self.objects.max_iter * self.relation_object.max_iter

    def realize(
        self, include_period: bool = True, neg_evidence: bool = False, iter: int = 0
    ) -> str:
        """
        'The three large spheres have the same size as a yellow rubber ball.'
        """
        # NOTE: Currently we ignore: neg_evidence

        # overwrite the determiner to prefer "the"
        if self.objects.determiner == "a":
            self.objects.determiner = "the"

        objects_iter = iter // self.relation_object.max_iter
        realized_objects = self.objects.realize(neg_evidence=True, iter=objects_iter)

        verb = "has" if self.objects.numerus == "singular" else "have"
        same_relation = f"the same {self.same_relation} as"

        relation_object_iter = iter // self.objects.max_iter
        realized_relation_object = self.relation_object.realize(
            iter=relation_object_iter
        )

        realized_sentence = " ".join(
            [realized_objects, verb, same_relation, realized_relation_object,]
        )

        if include_period:
            realized_sentence += "."

        # clean duplicate spaces
        realized_sentence = " ".join(realized_sentence.split()).capitalize()

        return realized_sentence


class CompositeSentence:
    def __init__(self, sentences: List[Union[Sentence, ActiveSentence]]):
        self.sentences = sentences

        self.starters = ["In addition,", "Furthermore,"]

        self.effective_length = sum(sent.effective_length for sent in self.sentences)

        for i, sentence in enumerate(self.sentences):
            if i > 0 and isinstance(sentence, Sentence):
                # avoid "There is", etc. in the middle of the sentence
                sentence.intro_texts = ["there"]

        self.update_max_iter()

    def realize(
        self,
        multiple_sentences: bool = False,
        neg_evidence: bool = False,
        include_period: bool = True,
        iter: int = 0,
    ) -> str:

        sentences_max_iter = prod(sentence.max_iter for sentence in self.sentences)
        if multiple_sentences:  # or self.effective_length > 16:
            # max iter also includes different starts at the sentences
            self.max_iter = len(self.starters) * prod(
                sentence.max_iter for sentence in self.sentences
            )
            assert 0 <= iter < self.max_iter

            realized_sentences = []
            for i, sentence in enumerate(self.sentences):
                prev_max_iters = prod(
                    sentence.max_iter for sentence in self.sentences[:i]
                )
                current_iter = iter // prev_max_iters % sentence.max_iter
                include_period = True
                if i == 0:
                    new_sentence = sentence.realize(
                        include_period=include_period,
                        neg_evidence=neg_evidence,
                        iter=current_iter,
                    )
                else:
                    starter = self.starters[iter // sentences_max_iter]
                    realized_sentence = sentence.realize(
                        include_period=include_period,
                        neg_evidence=neg_evidence,
                        iter=current_iter,
                    )
                    starter_with_sentence = [
                        starter,
                        realized_sentence,
                    ]
                    new_sentence = " ".join(starter_with_sentence).capitalize()
                realized_sentences.append(new_sentence)

            sentence = " ".join(realized_sentences)

        else:
            # max iter is only the variants provided by the sentences, we do not scramble them.
            self.max_iter = sentences_max_iter
            assert 0 <= iter < self.max_iter

            realized_sentences = []
            for i, sentence in enumerate(self.sentences):
                prev_max_iters = prod(
                    sentence.max_iter for sentence in self.sentences[:i]
                )
                current_iter = iter // prev_max_iters % sentence.max_iter
                realized_sentence = sentence.realize(
                    neg_evidence=neg_evidence, iter=current_iter,
                )
                realized_sentences.append(realized_sentence)

            # clean away empty sentences (e.g. caused through negative evidence, which is not mentioned)
            realized_sentences = [
                realized_sentence
                for realized_sentence in realized_sentences
                if realized_sentence != ""
            ]
            sentence = join_list_with_comma_and(realized_sentences).capitalize()

            if include_period:
                sentence += "."

        return sentence

    def update_max_iter(self):
        for sentence in self.sentences:
            sentence.update_max_iter()

        self.max_iter: int = prod(sentence.max_iter for sentence in self.sentences)


class SentenceGroup:
    def __init__(self, sentences: List[Union[Sentence, CompositeSentence]]) -> None:
        self.sentences = sentences
        self.update_max_iter()

    def realize(self, neg_evidence: bool = False, iter: int = 0):
        # depending on the iter we need

        all_max_iters = [sentence.max_iter for sentence in self.sentences]

        for i, sentence in enumerate(self.sentences):
            all_max_iter_until_here = sum(all_max_iters[: i + 1])
            if iter < all_max_iter_until_here:
                this_sentence_iter = iter - sum(all_max_iters[:i])
                # TODO: Include period
                realized_sentence = sentence.realize(
                    neg_evidence=neg_evidence,
                    include_period=True,
                    iter=this_sentence_iter,
                )
                return realized_sentence

    def update_max_iter(self):
        for sentence in self.sentences:
            sentence.update_max_iter()

        self.max_iter = sum(sentence.max_iter for sentence in self.sentences)
