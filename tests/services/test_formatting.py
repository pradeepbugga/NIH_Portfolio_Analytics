from core.services.formatting import format_output_grants


def test_format_output_grants():
    """Test the format_output_grants function to ensure it correctly normalizes grant document fields for JavaScript rendering.
    It should combine organization name, funding amount, and principal investigator information into a standardized format.
    """

    docs = [
        {
            "org_name": "Harvard",
            "amount": 500000,
            "pi_first_name": "John",
            "pi_middle_name": "A.",
            "pi_last_name": "Smith",
        }
    ]

    result = format_output_grants(docs)

    assert result[0]["organization"] == "Harvard"
    assert result[0]["funding"] == 500000
    assert result[0]["pi"] == "John A. Smith"


def test_format_output_grants_missing_pi():
    """ Test the format_output_grants function when principal investigator information is missing. \
    It should handle None values gracefully and return an empty string for the PI field.
    """

    docs = [
        {
            "org_name": "MIT",
            "amount": 1000,
            "pi_first_name": None,
            "pi_middle_name": None,
            "pi_last_name": None,
        }
    ]

    result = format_output_grants(docs)

    assert result[0]["pi"] == ""
