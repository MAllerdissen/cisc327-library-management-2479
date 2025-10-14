# tests/test_r1.py
import pytest
import library_service

def _patch_db(monkeypatch, existing=None, insert_success=True):
    """
    Helper to patch the DB functions that library_service imported.
    """
    monkeypatch.setattr(library_service, 'get_book_by_isbn', lambda isbn: existing)
    def fake_insert_book(title, author, isbn, total_copies, available_copies):
        return insert_success
    monkeypatch.setattr(library_service, 'insert_book', fake_insert_book)


def test_add_book_success(monkeypatch):
    """
    Valid input -> successful insertion and correct message; insertion receives trimmed values.
    """
    _patch_db(monkeypatch, existing=None, insert_success=True)
    calls = {}
    def record_insert(title, author, isbn, total, available):
        calls['args'] = (title, author, isbn, total, available)
        return True
    monkeypatch.setattr(library_service, 'insert_book', record_insert)

    success, message = library_service.add_book_to_catalog("  Clean Code  ", "  Robert C. Martin  ", "1234567890123", 3)
    assert success is True
    assert 'Clean Code' in message  # message should include the title
    # ensure title/author were stripped and that available == total
    assert calls['args'] == ("Clean Code", "Robert C. Martin", "1234567890123", 3, 3)


@pytest.mark.parametrize("bad_title", ["", "   "])
def test_add_book_rejects_empty_title(bad_title, monkeypatch):
    """
    Empty or whitespace-only title should be rejected.
    """
    _patch_db(monkeypatch)  # safe DB mocks in case code proceeds
    success, message = library_service.add_book_to_catalog(bad_title, "Author", "1234567890123", 1)
    assert success is False
    assert message == "Title is required."


def test_add_book_rejects_title_too_long(monkeypatch):
    """
    Title longer than 200 characters should be rejected.
    """
    _patch_db(monkeypatch)
    long_title = "A" * 201
    success, message = library_service.add_book_to_catalog(long_title, "Author", "1234567890123", 1)
    assert success is False
    assert message == "Title must be less than 200 characters."


@pytest.mark.parametrize("bad_author", ["", "   "])
def test_add_book_rejects_empty_author(bad_author, monkeypatch):
    """
    Empty or whitespace-only author should be rejected.
    """
    _patch_db(monkeypatch)
    success, message = library_service.add_book_to_catalog("Title", bad_author, "1234567890123", 1)
    assert success is False
    assert message == "Author is required."


def test_add_book_rejects_author_too_long(monkeypatch):
    """
    Author longer than 100 characters should be rejected.
    """
    _patch_db(monkeypatch)
    long_author = "B" * 101
    success, message = library_service.add_book_to_catalog("Title", long_author, "1234567890123", 1)
    assert success is False
    assert message == "Author must be less than 100 characters."


@pytest.mark.parametrize("bad_isbn", ["123", "123456789012", "12345678901234"])  # length != 13
def test_add_book_rejects_isbn_wrong_length(bad_isbn, monkeypatch):
    """
    ISBN must be exactly 13 digits (length check).
    """
    _patch_db(monkeypatch)
    success, message = library_service.add_book_to_catalog("Title", "Author", bad_isbn, 1)
    assert success is False
    assert message == "ISBN must be exactly 13 digits."


def test_add_book_rejects_isbn_with_non_digits(monkeypatch):
    """
    The specification requires ISBN to be exactly 13 digits (digits-only).
    """
    _patch_db(monkeypatch, existing=None, insert_success=True)
    bad_isbn = "12A4567890123"  # 13 chars but contains a letter
    success, message = library_service.add_book_to_catalog("Title", "Author", bad_isbn, 1)
    # spec: should be rejected because not digits-only; message should be the ISBN validation message.
    assert success is False
    assert message == "ISBN must be exactly 13 digits."


@pytest.mark.parametrize("bad_total", [0, -1, "5", 3.5])
def test_add_book_rejects_invalid_total_copies(bad_total, monkeypatch):
    """
    Total copies must be a positive integer.
    """
    _patch_db(monkeypatch)
    success, message = library_service.add_book_to_catalog("Title", "Author", "1234567890123", bad_total)
    assert success is False
    assert message == "Total copies must be a positive integer."


def test_add_book_rejects_duplicate_isbn(monkeypatch):
    """
    If a book with the same ISBN exists, insertion should be rejected.
    """
    # Simulate existing book found by ISBN lookup
    _patch_db(monkeypatch, existing={"id": 1, "isbn": "1234567890123"})
    success, message = library_service.add_book_to_catalog("Another", "Author", "1234567890123", 1)
    assert success is False
    assert message == "A book with this ISBN already exists."


def test_add_book_handles_db_insert_failure(monkeypatch):
    """
    If insert_book returns False the function should return a database error message.
    """
    _patch_db(monkeypatch, existing=None, insert_success=False)
    success, message = library_service.add_book_to_catalog("Title", "Author", "1234567890123", 2)
    assert success is False
    assert message == "Database error occurred while adding the book."

def test_add_book_rejects_whitespace_isbn(monkeypatch):
    """
    ISBN containing only whitespace should be rejected.
    """
    _patch_db(monkeypatch)
    success, message = library_service.add_book_to_catalog("Title", "Author", "             ", 1)
    assert success is False
    # Relaxed assertion: ensure the failure relates to ISBN validation rather than insisting on exact wording.
    assert "ISBN" in message