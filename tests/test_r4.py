# tests/test_r4.py
import pytest
from datetime import datetime
import library_service

def _make_book(book_id=1, title="Returned Book", author="Author", isbn="1234567890123", total=2, available=1):
    return {
        "id": book_id,
        "title": title,
        "author": author,
        "isbn": isbn,
        "total_copies": total,
        "available_copies": available
    }

def _patch_defaults(monkeypatch, *, book=None,
                    update_return_success=True, update_avail_success=True,
                    fee_result=None):
    """
    Patch the DB and helper functions library_service would call:
      - get_book_by_id -> returns book dict
      - update_borrow_record_return_date -> returns update_return_success
      - update_book_availability -> returns update_avail_success
      - calculate_late_fee_for_book -> returns fee_result (dict) or {'fee_amount':0.0,...} if None
    """
    if book is None:
        book = _make_book()
    monkeypatch.setattr(library_service, 'get_book_by_id', lambda book_id: book)
    def fake_update_return(patron_id, book_id, return_date):
        return update_return_success
    monkeypatch.setattr(library_service, 'update_borrow_record_return_date', fake_update_return)
    monkeypatch.setattr(library_service, 'update_book_availability', lambda bid, delta: update_avail_success)
    if fee_result is None:
        fee_result = {'fee_amount': 0.0, 'days_overdue': 0, 'status': 'No late fee'}
    monkeypatch.setattr(library_service, 'calculate_late_fee_for_book', lambda patron_id, book_id: fee_result)


@pytest.mark.parametrize("patron_id", ["", "12345", "1234567", "ABCDEF", "12A456"])
def test_return_invalid_patron_id_rejected(patron_id, monkeypatch):
    """Patron ID must be exactly 6 digits (digits-only). Invalid IDs must be rejected."""
    # patch safe defaults so implementation proceeds to validation only
    _patch_defaults(monkeypatch)
    success, message = library_service.return_book_by_patron(patron_id, 1)
    assert success is False
    assert message == "Invalid patron ID. Must be exactly 6 digits."


def test_return_no_active_borrow_record(monkeypatch):
    """
    If there is no active borrow record for the patron/book, the function should reject the return.
    Implementations commonly detect this because updating the borrow record returns False (no rows affected).
    This test asserts the spec-driven behavior and expects an explanatory error message.
    """
    book = _make_book(1, title="Never Borrowed", available=1)
    # Simulate DB update returning False (no active borrow record)
    _patch_defaults(monkeypatch, book=book, update_return_success=False, update_avail_success=True)
    success, message = library_service.return_book_by_patron("123456", 1)
    assert success is False
    # Expected message according to spec: no active borrow record found
    assert message == "No active borrow record found for this patron and book."


def test_return_update_availability_failure(monkeypatch):
    """
    If updating availability fails after a successful return-record update, function should return an error.
    """
    book = _make_book(2, title="Availability Fail", available=0, total=1)
    # update return succeeds but update availability fails
    _patch_defaults(monkeypatch, book=book, update_return_success=True, update_avail_success=False)
    success, message = library_service.return_book_by_patron("222222", 2)
    assert success is False
    assert message == "Database error occurred while updating book availability."


def test_successful_return_shows_late_fee(monkeypatch):
    """
    Successful return flow:
    - update_borrow_record_return_date returns True
    - update_book_availability returns True
    - calculate_late_fee_for_book returns a non-zero fee
    The returned message should include the book title and the late fee formatted with 2 decimal places (e.g., $1.50)
    """
    book = _make_book(3, title="Late Fee Book", available=0, total=1)
    fee = {'fee_amount': 1.5, 'days_overdue': 3, 'status': 'Overdue'}
    _patch_defaults(monkeypatch, book=book, update_return_success=True, update_avail_success=True, fee_result=fee)

    success, message = library_service.return_book_by_patron("333333", 3)
    assert success is True
    assert "Late fee" in message or "$1.50" in message or "1.50" in message
    # Title should be included
    assert "Late Fee Book" in message


def test_successful_return_no_late_fee(monkeypatch):
    """
    Successful return with no late fee: message should still confirm return and indicate $0.00 or no fee.
    """
    book = _make_book(4, title="OnTime Book", available=0, total=1)
    fee = {'fee_amount': 0.0, 'days_overdue': 0, 'status': 'No late fee'}
    _patch_defaults(monkeypatch, book=book, update_return_success=True, update_avail_success=True, fee_result=fee)

    success, message = library_service.return_book_by_patron("444444", 4)
    assert success is True
    # Expect either explicit zero-dollar mention or wording indicating no late fee
    assert "$0.00" in message or "no late fee" in message.lower()
    assert "OnTime Book" in message


def test_return_records_return_date(monkeypatch):
    """
    The function should pass a return_date to update_borrow_record_return_date.
    We record the argument and assert it's a datetime close to now.
    """
    recorded = {}
    book = _make_book(5, title="Record Date Book", available=0, total=1)

    monkeypatch.setattr(library_service, 'get_book_by_id', lambda bid: book)
    def fake_update_return(patron_id, book_id, return_date):
        recorded['patron_id'] = patron_id
        recorded['book_id'] = book_id
        recorded['return_date'] = return_date
        return True
    monkeypatch.setattr(library_service, 'update_borrow_record_return_date', fake_update_return)
    monkeypatch.setattr(library_service, 'update_book_availability', lambda bid, delta: True)
    monkeypatch.setattr(library_service, 'calculate_late_fee_for_book', lambda pid, bid: {'fee_amount': 0.0, 'days_overdue': 0, 'status': 'No late fee'})

    success, message = library_service.return_book_by_patron("555555", 5)
    assert success is True
    assert recorded.get('return_date') is not None
    assert isinstance(recorded['return_date'], datetime)
    # return_date should be recent (within 10 seconds)
    assert (datetime.now() - recorded['return_date']).total_seconds() < 10
