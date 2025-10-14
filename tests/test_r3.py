# tests/test_r3.py
import pytest
from datetime import timedelta
import library_service

def _make_book(book_id=1, title="Book Title", available=1, total=1):
    return {
        "id": book_id,
        "title": title,
        "author": "Author",
        "isbn": "1234567890123",
        "available_copies": available,
        "total_copies": total
    }

def _patch_defaults(monkeypatch, *, book=None, borrow_count=0,
                    insert_success=True, update_success=True):
    """
    Helper to patch DB functions used by borrow_book_by_patron.
    """
    if book is None:
        book = _make_book()
    monkeypatch.setattr(library_service, 'get_book_by_id', lambda book_id: book)
    monkeypatch.setattr(library_service, 'get_patron_borrow_count', lambda patron_id: borrow_count)
    monkeypatch.setattr(library_service, 'insert_borrow_record', lambda patron_id, book_id, borrow_date, due_date: insert_success)
    monkeypatch.setattr(library_service, 'update_book_availability', lambda book_id, delta: update_success)


@pytest.mark.parametrize("patron_id", ["", "12345", "1234567", "ABC123", "12A456"])
def test_invalid_patron_id_rejected(patron_id, monkeypatch):
    """
    Patron ID must be exactly 6 digits; invalid formats must be rejected.
    """
    # Patch DB to safe defaults so function doesn't fail due to DB
    _patch_defaults(monkeypatch)
    success, message = library_service.borrow_book_by_patron(patron_id, 1)
    assert success is False
    assert message == "Invalid patron ID. Must be exactly 6 digits."


def test_book_not_found(monkeypatch):
    """
    If get_book_by_id returns None the function must return Book not found.
    """
    monkeypatch.setattr(library_service, 'get_book_by_id', lambda book_id: None)
    monkeypatch.setattr(library_service, 'get_patron_borrow_count', lambda pid: 0)
    success, message = library_service.borrow_book_by_patron("123456", 999)
    assert success is False
    assert message == "Book not found."


def test_book_not_available(monkeypatch):
    """
    If available_copies <= 0 the borrow request should be rejected.
    """
    book = _make_book(1, "Unavailable Book", available=0, total=3)
    _patch_defaults(monkeypatch, book=book, borrow_count=0)
    success, message = library_service.borrow_book_by_patron("123456", 1)
    assert success is False
    assert message == "This book is currently not available."


def test_patron_reached_borrow_limit_by_spec(monkeypatch):
    """
    Asserts that if patron currently has 5 books, borrowing should be rejected.
    """
    book = _make_book(2, "Popular Book", available=2, total=5)
    # simulate patron already has 5 books
    _patch_defaults(monkeypatch, book=book, borrow_count=5)
    success, message = library_service.borrow_book_by_patron("654321", 2)
    assert success is False
    assert message == "You have reached the maximum borrowing limit of 5 books."


def test_patron_exceeds_limit_current_logic(monkeypatch):
    """
    Complementary test: when current_borrowed > 5 (e.g., 6) the function must reject borrowing.
    """
    book = _make_book(3, "Another Book", available=1, total=2)
    _patch_defaults(monkeypatch, book=book, borrow_count=6)
    success, message = library_service.borrow_book_by_patron("111111", 3)
    assert success is False
    assert message == "You have reached the maximum borrowing limit of 5 books."


def test_db_insert_failure_returns_error(monkeypatch):
    """
    If insert_borrow_record fails, function should return a database error message.
    """
    book = _make_book(4, "DB Fail Book", available=1, total=1)
    _patch_defaults(monkeypatch, book=book, borrow_count=0, insert_success=False, update_success=True)
    success, message = library_service.borrow_book_by_patron("222222", 4)
    assert success is False
    assert message == "Database error occurred while creating borrow record."


def test_update_availability_failure_returns_error(monkeypatch):
    """
    If update_book_availability fails after a successful insert, the function should return an error.
    """
    book = _make_book(5, "Avail Update Fail", available=1, total=1)
    _patch_defaults(monkeypatch, book=book, borrow_count=0, insert_success=True, update_success=False)
    success, message = library_service.borrow_book_by_patron("333333", 5)
    assert success is False
    assert message == "Database error occurred while updating book availability."


def test_successful_borrow_records_and_message(monkeypatch):
    """
    Successful flow:
    - insert_borrow_record returns True
    - update_book_availability returns True
    - return True and a message containing the title and due date in YYYY-MM-DD
    - verify that the borrow and due dates passed to insert_borrow_record differ by exactly 14 days
    """
    recorded = {}
    book = _make_book(10, "Successful Borrow", available=2, total=2)
    # Patch get_book_by_id and get_patron_borrow_count
    monkeypatch.setattr(library_service, 'get_book_by_id', lambda book_id: book)
    monkeypatch.setattr(library_service, 'get_patron_borrow_count', lambda pid: 0)

    def fake_insert(patron_id, book_id, borrow_date, due_date):
        recorded['patron_id'] = patron_id
        recorded['book_id'] = book_id
        recorded['borrow_date'] = borrow_date
        recorded['due_date'] = due_date
        return True

    monkeypatch.setattr(library_service, 'insert_borrow_record', fake_insert)
    monkeypatch.setattr(library_service, 'update_book_availability', lambda book_id, delta: True)

    success, message = library_service.borrow_book_by_patron("444444", 10)
    assert success is True
    # message must contain title and due date in YYYY-MM-DD
    assert "Successful Borrow" in message
    assert recorded.get('borrow_date') is not None and recorded.get('due_date') is not None
    # due_date - borrow_date == 14 days exactly
    assert (recorded['due_date'] - recorded['borrow_date']) == timedelta(days=14)
    expected_date_str = recorded['due_date'].strftime("%Y-%m-%d")
    assert expected_date_str in message
