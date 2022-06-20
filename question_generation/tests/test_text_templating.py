from text_template_handling import replace_optionals
from hypothesis import given
import hypothesis.strategies as st


def test_replace_optionals_without_optionals():
    text = "Text without square brackets."
    assert text == replace_optionals(text)


def test_replace_optionals_only_complete_removal():
    text = "[hallo]"
    replaced = replace_optionals(text)
    assert replaced == "" or replaced == text.replace("[", "").replace("]", "") 


def test_replace_optionals_two_replacements():
    text = "A [aa] B [bb]"
    replaced = replace_optionals(text)
    assert replaced in ["A aa B bb", "A B bb", "A aa B", "A B"] 


def test_replace_optionals_probability():
    text = "[aa]"
    removed_count = 0

    iterations = 1000
    for i in range(iterations):
        replaced_text = replace_optionals(text)
        removed_count += 1 if replaced_text in "" else 0
    assert round(removed_count/iterations, 1) == 0.5


def test_replace_optionals_nested_replacements():
    text = "A [a B [bb] a]"
    replaced = replace_optionals(text)
    assert replaced in ['A a B bb a', 'A', 'A a B a']


@given(st.text())
def test_hypo_replace_optionals(text):
    replaced = replace_optionals(text)
    assert len(text) >= len(replaced), "length must not increase"
