import pytest
from nlg_system.objects import CLEVRObject, Objects


def test_object_creation():
    obj = CLEVRObject("small", "red", "metallic", "cube")
    assert obj.realize() == "small red metallic cube"


def test_objects_single_object():
    obj = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([obj])
    assert objs.realize() == "a small red metallic cube"


def test_objects_two_different_objects():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])
    assert objs.realize() == "a small red metallic cube and a large green rubber sphere"


def test_object_unique_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])
    all_generations = [objs.realize(iter=i) for i in range(objs.max_iter)]
    assert len(all_generations) == len(set(all_generations))


def test_object_with_synonyms():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    synonyms = {"small": ["small", "tiny"]}
    objs = Objects([obj1], synonyms=synonyms)
    assert objs.objects[0].synonyms == synonyms
    assert objs.max_iter == 2
    assert objs.realize(iter=0) == "a small red metallic cube"
    assert objs.realize(iter=1) == "a tiny red metallic cube"


def test_objects_two_indentical_objects():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([obj1, obj2])
    assert objs.realize() == "two small red metallic cubes"


def test_objects_two_almost_indentical_objects():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("small", "red", "metallic", "sphere")
    objs = Objects([obj1, obj2])
    assert objs.realize() == "a small red metallic cube and sphere"


def test_objects_two_indentical_objects_one_different():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("small", "red", "metallic", "cube")
    obj3 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2, obj3])
    assert (
        objs.realize() == "two small red metallic cubes and a large green rubber sphere"
    )


def test_objects_one_different_two_indentical_objects():
    obj1 = CLEVRObject("large", "green", "rubber", "sphere")
    obj2 = CLEVRObject("small", "red", "metallic", "cube")
    obj3 = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([obj1, obj2, obj3])
    assert (
        objs.realize() == "a large green rubber sphere and two small red metallic cubes"
    )


def test_objects_size_aggregation():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "red", "metallic", "cube")
    objs = Objects([obj1, obj2])
    assert objs.realize() == "a small and a large red metallic cube"


def test_objects_shape_aggregation():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("small", "red", "metallic", "sphere")
    objs = Objects([obj1, obj2])
    assert objs.realize() == "a small red metallic cube and sphere"


def test_objects_negativ_evidence():
    neg_obj1 = CLEVRObject("small", "red", "metallic", "cube")
    objs = Objects([], [neg_obj1])
    assert objs.realize() == ""
    assert objs.realize(neg_evidence=True) == "no small red metallic cubes"
    pass


def test_objects_from_iterable_one_item():
    iterables = [["small", "red", "metallic", "cube"]]
    objs = Objects.from_iterable(iterables)
    assert objs.realize() == "a small red metallic cube"


def test_objects_from_iterable_two_items():
    iterables = [
        ["small", "red", "metallic", "cube"],
        ["small", "red", "metallic", "cube"],
    ]
    objs = Objects.from_iterable(iterables)
    assert objs.realize() == "two small red metallic cubes"


# variations
def test_objects_variations():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])
    assert (
        objs.realize(iter=0)
        == "a small red metallic cube and a large green rubber sphere"
    )
    assert (
        objs.realize(iter=1)
        == "a large green rubber sphere and a small red metallic cube"
    )


def test_objects_variations_invalid_iter():
    obj1 = CLEVRObject("small", "red", "metallic", "cube")
    obj2 = CLEVRObject("large", "green", "rubber", "sphere")
    objs = Objects([obj1, obj2])

    with pytest.raises(AssertionError) as e_info:
        # there are only two possible iters
        objs.realize(iter=2)
