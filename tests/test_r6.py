# tests/test_r6.py
import pytest
from typing import List, Dict
import library_service
import database

# Helper sample catalog entries that match the database.get_all_books() format.
_SAMPLE_BOOKS: List[Dict] = [
    {'id': 1, 'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'isbn': '9780743273565', 'total_copies': 3, 'available_copies': 2},
    {'id': 2, 'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'isbn': '9780061120084', 'total_copies': 2, 'available_copies': 2},
    {'id': 3, 'title': '1984', 'author': 'George Orwell', 'isbn': '9780451524935', 'total_copies': 1, 'available_copies': 0},
    {'id': 4, 'title': 'Gatsby Reimagined', 'author': 'Some Author', 'isbn': '9781111111111', 'total_copies': 1, 'available_copies': 1},
]

def test_search_title_partial_case_insensitive(monkeypatch):
    """
    Partial, case-insensitive search by title.
    """
    monkeypatch.setattr(database, 'get_all_books', lambda: _SAMPLE_BOOKS.copy())

    results = library_service.search_books_in_catalog('gatsby', 'title')

    assert isinstance(results, list)
    # Expect two matches
    titles = {r['title'] for r in results}
    assert 'The Great Gatsby' in titles
    assert 'Gatsby Reimagined' in titles
    assert len(results) == 2

def test_search_author_partial_case_insensitive(monkeypatch):
    """
    Partial, case-insensitive search by author.
    """
    monkeypatch.setattr(database, 'get_all_books', lambda: _SAMPLE_BOOKS.copy())

    results = library_service.search_books_in_catalog('orWell', 'author')  # mixed case to test case-insensitive

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]['title'] == '1984'
    assert 'George Orwell' == results[0]['author']

def test_search_isbn_exact_match(monkeypatch):
    """
    ISBN search must be exact:
    - When exact ISBN provided, the result should include the matched book.
    - When partial ISBN provided, should return no matches (exact match required).
    """
    # Provide a DB-level ISBN lookup for exact-match behavior
    target_isbn = '9780451524935'
    monkeypatch.setattr(database, 'get_book_by_isbn', lambda isbn: next((b for b in _SAMPLE_BOOKS if b['isbn'] == isbn), None))
    # Ensure get_all_books is not used for ISBN search (but patching safe fallback)
    monkeypatch.setattr(database, 'get_all_books', lambda: _SAMPLE_BOOKS.copy())

    # exact match -> returns one result
    results_exact = library_service.search_books_in_catalog(target_isbn, 'isbn')
    assert isinstance(results_exact, list)
    assert len(results_exact) == 1
    assert results_exact[0]['isbn'] == target_isbn
    assert results_exact[0]['title'] == '1984'

    # partial ISBN -> should not match (require exact)
    results_partial = library_service.search_books_in_catalog('978045', 'isbn')
    assert isinstance(results_partial, list)
    assert len(results_partial) == 0

def test_search_no_results_returns_empty_list(monkeypatch):
    """
    Searching for a term that doesn't exist should return an empty list.
    """
    monkeypatch.setattr(database, 'get_all_books', lambda: _SAMPLE_BOOKS.copy())

    results = library_service.search_books_in_catalog('nonexistent term', 'title')
    assert isinstance(results, list)
    assert results == []

def test_search_invalid_type_returns_empty_list(monkeypatch):
    """
    If an invalid search type is supplied, the function should not crash.
    """
    monkeypatch.setattr(database, 'get_all_books', lambda: _SAMPLE_BOOKS.copy())
    monkeypatch.setattr(database, 'get_book_by_isbn', lambda isbn: None)

    results = library_service.search_books_in_catalog('gatsby', 'invalid_type')
    assert isinstance(results, list)
    assert results == []
