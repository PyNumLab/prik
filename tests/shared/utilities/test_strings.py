"""Tests for x2py's self-contained generated-name helpers."""

from x2py.utilities.strings import create_incremented_string, random_string


class _CaseInsensitiveRules:
    def has_clash(self, name: object, symbols: set[object]) -> bool:
        return str(name).casefold() in {str(symbol).casefold() for symbol in symbols}


def test_incremented_name_skips_reserved_spellings_and_reports_next_counter():
    name, counter = create_incremented_string({"bridge_2", "bridge_3"}, prefix="bridge")

    assert name == "bridge_4"
    assert counter == 5


def test_incremented_name_uses_the_target_language_collision_rule():
    name, counter = create_incremented_string({"VALUE_2"}, prefix="value", naming_rules=_CaseInsensitiveRules())

    assert name == "value_3"
    assert counter == 4


def test_random_string_has_the_requested_length_and_alphabet():
    value = random_string(24)

    assert len(value) == 24
    assert value.isalnum()
    assert value == value.casefold()
