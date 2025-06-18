import pytest
from deep_research.utils.parsers import parse_date, parse_amount

def test_parse_date_valid():
    assert parse_date("18 avril 2024") is not None
    assert parse_date("2023-11-01") == parse_date("2023-11-01")

def test_parse_date_invalid():
    assert parse_date("") is None
    assert parse_date("not a date") is None

def test_parse_amount():
    assert parse_amount("Montant: 15 000 000 XOF") == 15000000.0
    assert parse_amount("No amount here") is None
    assert parse_amount("Budget: 1,200.50 EUR") == 1200.50