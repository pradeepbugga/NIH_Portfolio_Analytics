import pytest
from core.ingest.normalize import normalize_project_num, normalize_name

def test_normalize_project_num():

    """ Tests that normalize_project_num correctly normalizes a project number by removing the leading character and subproject ID. """

    assert normalize_project_num(
        "1R01CA123456-01"
    ) == "R01CA123456"

def test_normalize_project_num_normalized():

    assert normalize_project_num(
        "NR01CA123456-01"
    ) == "NR01CA123456"



@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        123,
        [],
    ],
)
def test_normalize_project_num_invalid(value):

    """ Tests that normalize_project_num returns None for invalid input. """

    assert normalize_project_num(value) is None


def test_normalize_name_last_first():

    first, middle, last, canonical = normalize_name(
        "Smith, John A"
    )

    assert first == "John"
    assert middle == "A"
    assert last == "Smith"
    assert canonical == "Smith, J"


def test_normalize_name_first_middle_last():

    """ Tests that normalize_name correctly handles names in "First M Last" format. """

    first, middle, last, canonical = normalize_name(
        "John A Smith"
    )

    assert first == "John"
    assert middle == "A"
    assert last == "Smith"
    assert canonical == "Smith, J"

def test_normalize_name_two_part():

    """ Tests that normalize_name correctly handles names with only first and last parts. """

    first, middle, last, canonical = normalize_name(
        "John Smith"
    )

    assert first == "John"
    assert middle == ""
    assert last == "Smith"
    assert canonical == "Smith, J"

def test_normalize_name_multiword_middle():

    """ Tests that normalize_name correctly handles names with multi-word middle names. """

    first, middle, last, canonical = normalize_name(
        "John Adam Brian Smith"
    )

    assert first == "John"
    assert middle == "Adam Brian"
    assert last == "Smith"
    assert canonical == "Smith, J"

@pytest.mark.parametrize(
"value",
[
    None,
    "",
    123,
    "John",
],
)
def test_normalize_name_invalid(value):

    """ Tests that normalize_name returns empty strings and None for the canonical format when given invalid input. """

    assert normalize_name(value) == (
        "",
        "",
        "",
        None,
    )


def test_normalize_name_strips_and_titles():

    """ Tests that normalize_name correctly strips leading/trailing whitespace and converts to title case. """

    first, middle, last, canonical = normalize_name(
        "   jOhN   sMiTh   "
    )

    assert first == "John"
    assert middle == ""
    assert last == "Smith"
    assert canonical == "Smith, J"