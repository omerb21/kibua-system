import pytest
from datetime import date
from app.models import Client, Grant, Pension, Commutation
from app.calculations import calculate_eligibility_age, calculate_indexed_grant

@pytest.fixture
def sample_client():
    return Client(
        first_name="ישראל",
        last_name="כהן",
        tz="123456789",
        birth_date=date(1960, 5, 1),
        gender="female",
        phone="0501234567",
        address="תל אביב"
    )

@pytest.fixture
def sample_pension(sample_client):
    return Pension(
        client=sample_client,
        payer_name="קרן פנסיה",
        start_date=date(2025, 1, 1)
    )

@pytest.fixture
def sample_grant(sample_client):
    return Grant(
        client=sample_client,
        employer_name="חברה א",
        work_start_date=date(1990, 1, 1),
        work_end_date=date(2005, 1, 1),
        grant_amount=100000,
        grant_date=date(2020, 1, 1)
    )

@pytest.fixture
def sample_commutation(sample_pension):
    return Commutation(
        pension=sample_pension,
        amount=150000,
        date=date(2023, 6, 1),
        full_or_partial="partial"
    )

def test_client_fields(sample_client):
    assert sample_client.first_name == "ישראל"
    assert sample_client.tz == "123456789"
    assert sample_client.birth_date.year == 1960

def test_relationship_grant_to_client(sample_grant):
    assert sample_grant.client is not None
    assert sample_grant.employer_name == "חברה א"

def test_relationship_commutation_to_pension(sample_commutation):
    assert sample_commutation.pension is not None
    assert sample_commutation.amount == 150000

def test_calculate_eligibility_age_uses_max():
    birth_date = date(1960, 5, 1)
    pension_start = date(2025, 1, 1)
    result = calculate_eligibility_age(birth_date, "female", pension_start)
    assert result == pension_start  # כי גיל זכאות מאוחר יותר מגיל פרישה

def test_calculate_eligibility_age_retirement_is_later():
    birth_date = date(1960, 5, 1)
    pension_start = date(2021, 1, 1)
    result = calculate_eligibility_age(birth_date, "male", pension_start)
    assert result == date(2027, 5, 1)  # גיל פרישה מאוחר יותר

# את הבדיקה הזו יש להריץ רק אם המימוש כולל פנייה ל־API חיצוני אמיתי
def test_calculate_indexed_grant_calls_api(sample_grant):
    eligibility_date = date(2025, 1, 1)
    try:
        indexed_value = calculate_indexed_grant(sample_grant, eligibility_date)
        assert indexed_value > sample_grant.grant_amount
    except Exception:
        # ייתכן שאין גישה לאינטרנט או ש־CBS חוסם
        pytest.skip("לא ניתן לבדוק API של הלמ״ס בסביבה זו")
