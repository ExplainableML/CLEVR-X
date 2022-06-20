import pytest
from nlg_system.sentences import Sentence, CompositeSentence
from nlg_system.objects import CLEVRObject, Objects

def test_sentence_with_period():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("small", "red", "metallic", "sphere")
    objs = Objects([obj1, obj2])
    sent = Sentence(objs)
    assert (
        sent.realize(include_period=True)
        == "There are a small red metallic cube and sphere."
    )


def test_sentence():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([obj1])
    sent = Sentence(objs)
    assert sent.realize() == "There is a small red metallic cube"


def test_sentence_one_object_unique_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([obj1])
    sent = Sentence(objs)
    all_generations = [sent.realize(iter=i) for i in range(sent.max_iter)]
    assert len(all_generations) == len(set(all_generations))


def test_sentence_two_objects_unique_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])
    sent = Sentence(objs)
    all_generations = [sent.realize(iter=i) for i in range(sent.max_iter)]
    assert len(all_generations) == len(set(all_generations))



def test_composite_sentence_iter():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    obj3 = CLEVRObject("small", "blue", "rubber", "cylinder")
    obj4 = CLEVRObject("large", "yellow", "metallic", "sphere")
    sent1 = Sentence(Objects([obj1, obj2]))
    sent2 = Sentence(Objects([obj3, obj4]))
    com_sent = CompositeSentence([sent1, sent2])
    assert (
        com_sent.realize(iter=0)
        == "There is a small red metallic cube and a large green rubber sphere and there is a small blue rubber cylinder and a large yellow metallic sphere."
    )
    # TODO:: assert more variaions


def test_composite_sentence_unique_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    obj3 = CLEVRObject("small", "blue", "rubber", "cylinder")
    obj4 = CLEVRObject("large", "yellow", "metallic", "sphere")
    sent1 = Sentence(Objects([obj1, obj2]))
    sent2 = Sentence(Objects([obj3, obj4]))
    com_sent = CompositeSentence([sent1, sent2])
    all_generations = [com_sent.realize(iter=i) for i in range(com_sent.max_iter)]
    assert len(all_generations) == len(set(all_generations))


# variations


def test_sentence_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])
    sent = Sentence(objs)

    assert sent.max_iter == 1 * 2

    assert (
        sent.realize(iter=0)
        == "There is a small red metallic cube and a large green rubber sphere"
    )
    assert (
        sent.realize(iter=1)
        == 'There is a large green rubber sphere and a small red metallic cube'
    )
