# tests/test_r2.py
import pytest
from app import create_app
import app as app_module
import routes.catalog_routes as catalog_routes

@pytest.fixture
def client(monkeypatch):
    """
    Create Flask test client while preventing DB init/sample-data side effects.
    """
    # Prevent database initialization and sample data insertion during tests
    monkeypatch.setattr(app_module, 'init_database', lambda: None)
    monkeypatch.setattr(app_module, 'add_sample_data', lambda: None)
    app = create_app()
    app.testing = True
    return app.test_client()

def test_catalog_displays_available_and_unavailable_books(client, monkeypatch):
    """
    Ensure catalog page lists books with ID, title, author, ISBN
    """
    sample_books = [
        {'id': 1, 'title': 'Available Book', 'author': 'Author A', 'isbn': '1111111111111', 'total_copies': 3, 'available_copies': 2},
        {'id': 2, 'title': 'Unavailable Book', 'author': 'Author B', 'isbn': '2222222222222', 'total_copies': 1, 'available_copies': 0},
    ]

    # Monkeypatch the get_all_books used by the catalog route module
    monkeypatch.setattr(catalog_routes, 'get_all_books', lambda: sample_books)

    resp = client.get('/catalog')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Basic fields present
    assert 'Available Book' in html
    assert 'Author A' in html
    assert '1111111111111' in html

    assert 'Unavailable Book' in html
    assert 'Author B' in html
    assert '2222222222222' in html

    # Availability rendering checks
    assert '2/3 Available' in html  # available book shows available count
    assert 'Not Available' in html  # unavailable book shows 'Not Available'

    # Borrow form/button exists for available book (should contain Borrow and hidden book_id input)
    assert 'Borrow' in html
    assert 'type="hidden" name="book_id" value="1"' in html or 'value="1"' in html

    # Unavailable book should not have a Borrow form for its row (there will still be some "Borrow" text from the available row)
    # Check that the unavailable book row renders "Not Available" (above) and does not render an input value "2" for borrowing
    assert 'name="book_id" value="2"' not in html

def test_catalog_empty_shows_empty_message(client, monkeypatch):
    """
    Ensure When no books present, catalog should show "No books in catalog" message. Provide link to add the first book.
    """
    monkeypatch.setattr(catalog_routes, 'get_all_books', lambda: [])

    resp = client.get('/catalog')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert 'No books in catalog' in html
    assert 'Add the first book' in html or 'Add New Book' in html

def test_get_all_books_is_invoked(client, monkeypatch):
    """
    Ensure the route actually calls get_all_books (sanity of wiring)
    """
    called = {'count': 0}
    def fake_get_all_books():
        called['count'] += 1
        return [
            {'id': 9, 'title': 'X', 'author': 'Y', 'isbn': '9999999999999', 'total_copies': 1, 'available_copies': 1}
        ]

    monkeypatch.setattr(catalog_routes, 'get_all_books', fake_get_all_books)

    resp = client.get('/catalog')
    assert resp.status_code == 200
    assert called['count'] == 1, "Expected get_all_books to be called exactly once"
    assert '9999999999999' in resp.get_data(as_text=True)
