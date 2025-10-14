# tests/test_r5.py
import pytest
from datetime import datetime, timedelta
import library_service
import database

def _make_record_for_book(book_id: int, due_date: datetime):
    """
    Helper that returns a list shaped like database.get_patron_borrowed_books would return for an active borrow.
    Uses the same field names that the current database helper uses (see database.get_patron_borrowed_books).
    """
    return [{
        'book_id': book_id,
        'title': 'Dummy',
        'author': 'Author',
        'borrow_date': due_date - timedelta(days=14),  # borrowed 14 days before due
        'due_date': due_date,
        'is_overdue': datetime.now() > due_date
    }]

def _expected_fee(days_overdue: int) -> float:
    """
    Compute expected fee according to R5 rules and cap at $15.00
    """
    if days_overdue <= 0:
        return 0.00
    first_tier_days = min(days_overdue, 7)
    remaining = max(0, days_overdue - 7)
    fee = 0.5 * first_tier_days + 1.0 * remaining
    if fee > 15.0:
        fee = 15.0
    return round(fee, 2)

def test_no_overdue_returns_zero(monkeypatch):
    """
    If book is not overdue, fee_amount should be 0.00 and days_overdue 0.
    """
    patron_id = '123456'
    book_id = 1
    due = datetime.now() + timedelta(days=2)  # due in future -> not overdue
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: _make_record_for_book(book_id, due))

    result = library_service.calculate_late_fee_for_book(patron_id, book_id)

    assert isinstance(result, dict), "Expected a dict result with fee_amount and days_overdue"
    assert 'fee_amount' in result and 'days_overdue' in result
    assert int(result['days_overdue']) == 0
    assert round(float(result['fee_amount']), 2) == 0.00

def test_small_overdue_within_first_7_days(monkeypatch):
    """
    3 days overdue -> fee = 3 * $0.50 = $1.50
    """
    patron_id = '123456'
    book_id = 2
    days_overdue = 3
    due = datetime.now() - timedelta(days=days_overdue)
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: _make_record_for_book(book_id, due))

    result = library_service.calculate_late_fee_for_book(patron_id, book_id)

    assert isinstance(result, dict)
    assert int(result['days_overdue']) == days_overdue
    assert round(float(result['fee_amount']), 2) == _expected_fee(days_overdue)

def test_overdue_more_than_7_days(monkeypatch):
    """
    10 days overdue -> fee = (7 * 0.5) + (3 * 1.0) = 3.5 + 3 = 6.5
    """
    patron_id = '123456'
    book_id = 3
    days_overdue = 10
    due = datetime.now() - timedelta(days=days_overdue)
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: _make_record_for_book(book_id, due))

    result = library_service.calculate_late_fee_for_book(patron_id, book_id)

    assert isinstance(result, dict)
    assert int(result['days_overdue']) == days_overdue
    assert round(float(result['fee_amount']), 2) == _expected_fee(days_overdue)

def test_fee_is_capped_at_maximum(monkeypatch):
    """
    Very large days overdue should be capped at $15.00
    """
    patron_id = '123456'
    book_id = 4
    days_overdue = 100  # intentionally large to trigger cap
    due = datetime.now() - timedelta(days=days_overdue)
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: _make_record_for_book(book_id, due))

    result = library_service.calculate_late_fee_for_book(patron_id, book_id)

    assert isinstance(result, dict)
    assert int(result['days_overdue']) == days_overdue
    assert round(float(result['fee_amount']), 2) == 15.00

def test_no_borrow_record_returns_zero_fee(monkeypatch):
    """
    If patron has no active borrow record for the given book, the function should not crash.
    """
    patron_id = '000000'
    book_id = 99
    # Simulate no active borrows
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: [])

    result = library_service.calculate_late_fee_for_book(patron_id, book_id)

    assert isinstance(result, dict)
    # defensive: if function includes status message, keep test flexible and only require zero fee/days
    assert round(float(result.get('fee_amount', 0.0)), 2) == 0.00
    assert int(result.get('days_overdue', 0)) == 0
