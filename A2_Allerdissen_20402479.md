# A2_Allerdissen_20402479.md
**Name:** Martin Allerdissen  
**Student ID (last 4 digits):** 2479  

## Complete Function Implementation
The implementation is completed fully. Finished the missing business logic (R1–R7), added the Patron Status route, page, and nav link, and removed the “Not Yet Implemented” notices. Made sure to enforced validation rules, handled borrow/return flows with availability bounds, and implement fee calculations with clear messages and API responses. The app now meets all requirements end-to-end.

## Comprehensive Test Suite Development
No new tests had to be added. When adding requirments that were not met had to adjust many times to tests along way and gear code to passing established tests.

## AI-Assisted Test Generation
**AI**: Google Gemini

**Prompts**:

Message 1 (User):

"Complete the following task. Analyze the requirements R1 through to R7 in `requirements_specification.md` and generate a suite of tests for each that is compatible with the uploaded code. 

Writing Unit Test
- Write unit test script using python pytest framework for all the functionalities specified in `requirements_specification.md` file
- For each function, write at least 4-5 test cases, including positive and negative test cases
- Create a separate folder named `tests` and store the test script file there. You may create separate script files for each function
- A sample of test script is given in [`sample_test.py`](sample_test.py) file"

Message 2 (User):

"Attached are the routes from `./routes` and html template files from `./tempaltes`. Develop the test suite for R2 using these files. Edit and add to the test suites for the previous tests (R1-R7). Each test suite should be complete and come as a separate file."

**Generated Test Cases [R1-R7]**:
```
"""
Unit and Integration tests for R1: Add Book to Catalog functionality.
"""
import pytest
from library_service import add_book_to_catalog

# --- Unit Tests for Service Logic ---

def test_add_book_success(monkeypatch):
    """R1-TC1: Test successfully adding a valid book."""
    monkeypatch.setattr('library_service.get_book_by_isbn', lambda isbn: None)
    monkeypatch.setattr('library_service.insert_book', lambda *args, **kwargs: 1)
    success, message = add_book_to_catalog("Brave New World", "Aldous Huxley", "9780060850524", 5)
    assert success is True
    assert message == 'Book "Brave New World" successfully added to catalog.'

def test_add_book_missing_title():
    """R1-TC2: Test adding a book with a missing title."""
    success, message = add_book_to_catalog(title="", author="Some Author", isbn="9780060850524", total_copies=1)
    assert success is False
    assert message == "Title is required."

def test_add_book_title_too_long():
    """R1-TC3: Test adding a book with a title exceeding 200 characters."""
    long_title = "a" * 201
    success, message = add_book_to_catalog(title=long_title, author="Some Author", isbn="9780060850524", total_copies=1)
    assert success is False
    assert message == "Title must be less than 200 characters."

def test_add_book_invalid_isbn_non_digit():
    """R1-TC4: Test adding a book with a non-numeric ISBN."""
    success, message = add_book_to_catalog(title="A Book", author="An Author", isbn="1234567890abc", total_copies=1)
    assert success is False
    assert message == "ISBN must be exactly 13 digits."

def test_add_book_invalid_copies_zero():
    """R1-TC5: Test adding a book with zero total copies."""
    success, message = add_book_to_catalog(title="A Book", author="An Author", isbn="9780060850524", total_copies=0)
    assert success is False
    assert message == "Total copies must be a positive integer."

def test_add_book_isbn_already_exists(monkeypatch):
    """R1-TC6: Test adding a book whose ISBN already exists."""
    monkeypatch.setattr('library_service.get_book_by_isbn', lambda isbn: {"isbn": isbn})
    success, message = add_book_to_catalog("Another Book", "Another Author", "9780060850524", 2)
    assert success is False
    assert message == "A book with this ISBN already exists."

# --- Integration Tests for Web Route ---

def test_add_book_page_loads(client):
    """R1-TC7: Test that the GET /add_book page loads correctly."""
    response = client.get('/add_book')
    assert response.status_code == 200
    assert b"Add New Book" in response.data

def test_add_book_post_success(client, monkeypatch):
    """R1-TC8: Test successfully adding a book via a POST request."""
    # Mock the service function that the route calls
    monkeypatch.setattr('library_service.add_book_to_catalog', lambda *args: (True, "Success message"))
    
    response = client.post('/add_book', data={
        "title": "Fahrenheit 451", "author": "Ray Bradbury",
        "isbn": "9781451673319", "total_copies": 3
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Success message" in response.data # Check for flash message
    assert b"Book Catalog" in response.data # Check if redirected to catalog

def test_add_book_post_failure(client, monkeypatch):
    """R1-TC9: Test a failed book addition via a POST request."""
    # Mock the service function to return failure
    monkeypatch.setattr('library_service.add_book_to_catalog', lambda *args: (False, "ISBN is required."))

    response = client.post('/add_book', data={"title": "A Book", "author": "An Author", "isbn": "", "total_copies": 1})
    
    assert response.status_code == 200 # Should re-render the add_book page
    assert b"ISBN is required." in response.data # Check for flash error message
    assert b"Add New Book" in response.data # Check we are still on the add book page

"""
Unit and Integration tests for R2: Book Catalog Display.
"""
import pytest

# R2: Book Catalog Display
# - Display all books in a table format.
# - Show ID, Title, Author, ISBN, Availability.
# - Show "Borrow" button for available books.

@pytest.fixture
def mock_books():
    """Fixture to create a sample list of book dictionaries for mocking."""
    return [
        {
            "id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald",
            "isbn": "9780743273565", "total_copies": 3, "available_copies": 2
        },
        {
            "id": 2, "title": "1984", "author": "George Orwell",
            "isbn": "9780451524935", "total_copies": 4, "available_copies": 0
        }
    ]

def test_catalog_page_with_books(client, monkeypatch, mock_books):
    """
    R2-TC1: Test the catalog page renders correctly when books are in the database.
    """
    # Mock the database function to return our sample books
    monkeypatch.setattr('database.get_all_books', lambda: mock_books)

    response = client.get('/catalog')
    html = response.data.decode()

    assert response.status_code == 200
    # Check for book titles
    assert "The Great Gatsby" in html
    assert "George Orwell" in html
    # Check for availability text
    assert "2/3 Available" in html
    assert "Not Available" in html
    # Check for the borrow form for the available book
    assert 'action="/borrow"' in html
    assert 'value="1"' in html # hidden input for book_id 1
    # Check that the borrow button appears
    assert '<button type="submit" class="btn btn-success">Borrow</button>' in html

def test_catalog_page_empty(client, monkeypatch):
    """
    R2-TC2: Test the catalog page displays a message when no books exist.
    """
    # Mock the database function to return an empty list
    monkeypatch.setattr('database.get_all_books', lambda: [])

    response = client.get('/catalog')
    html = response.data.decode()

    assert response.status_code == 200
    assert "No books in catalog" in html
    assert "Add the first book" in html
    # Ensure the table headers are not present if there are no books
    assert "<th>Title</th>" not in html

def test_catalog_page_columns(client, monkeypatch, mock_books):
    """
    R2-TC3: Verify that all required table columns are present.
    """
    monkeypatch.setattr('database.get_all_books', lambda: mock_books)
    response = client.get('/catalog')
    html = response.data.decode()

    assert response.status_code == 200
    assert "<th>ID</th>" in html
    assert "<th>Title</th>" in html
    assert "<th>Author</th>" in html
    assert "<th>ISBN</th>" in html
    assert "<th>Availability</th>" in html
    assert "<th>Actions</th>" in html

"""
Unit and Integration tests for R3: Book Borrowing functionality.
"""
import pytest
from library_service import borrow_book_by_patron

# --- Unit Tests for Service Logic ---

@pytest.fixture
def mock_book():
    return {"id": 1, "title": "Dune", "available_copies": 2}

def test_borrow_book_success(monkeypatch, mock_book):
    """R3-TC1: Test successful borrowing logic."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    monkeypatch.setattr('library_service.get_patron_borrow_count', lambda pid: 2)
    monkeypatch.setattr('library_service.insert_borrow_record', lambda *a, **kw: 1)
    monkeypatch.setattr('library_service.update_book_availability', lambda *a, **kw: True)
    success, message = borrow_book_by_patron("123456", 1)
    assert success is True
    assert 'Borrowed "Dune" successfully.' in message

def test_borrow_book_invalid_patron_id():
    """R3-TC2: Test borrowing with an invalid patron ID."""
    success, message = borrow_book_by_patron("123", 1)
    assert success is False
    assert message == "Invalid patron ID. Must be exactly 6 digits."

def test_borrow_book_not_found(monkeypatch):
    """R3-TC3: Test borrowing a book that does not exist."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: None)
    success, message = borrow_book_by_patron("123456", 999)
    assert success is False
    assert message == "Book not found."

def test_borrow_book_not_available(monkeypatch, mock_book):
    """R3-TC4: Test borrowing a book with no available copies."""
    mock_book["available_copies"] = 0
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    success, message = borrow_book_by_patron("123456", 1)
    assert success is False
    assert message == "This book is currently not available."

def test_borrow_book_patron_at_limit(monkeypatch, mock_book):
    """R3-TC5: Test borrowing when the patron has reached the borrowing limit."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    monkeypatch.setattr('library_service.get_patron_borrow_count', lambda pid: 5)
    success, message = borrow_book_by_patron("123456", 1)
    assert success is False
    assert message == "You have reached the maximum borrowing limit of 5 books."

# --- Integration Tests for Web Route ---

def test_borrow_book_route_success(client, monkeypatch):
    """R3-TC6: Test the POST /borrow route with a successful outcome."""
    # Mock the service layer function to simulate success
    monkeypatch.setattr('library_service.borrow_book_by_patron', lambda *args: (True, "Borrowed successfully."))

    response = client.post('/borrow', data={'patron_id': '111222', 'book_id': '1'}, follow_redirects=True)
    
    assert response.status_code == 200 # Follows redirect to the catalog
    assert b"Borrowed successfully." in response.data # Check for flash message

def test_borrow_book_route_failure(client, monkeypatch):
    """R3-TC7: Test the POST /borrow route with a failed outcome."""
    # Mock the service layer function to simulate failure
    monkeypatch.setattr('library_service.borrow_book_by_patron', lambda *args: (False, "Book not available."))
    
    response = client.post('/borrow', data={'patron_id': '111222', 'book_id': '2'}, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Book not available." in response.data # Check for error flash message

def test_borrow_book_route_invalid_book_id(client):
    """R3-TC8: Test the POST /borrow route with a non-integer book ID."""
    response = client.post('/borrow', data={'patron_id': '111222', 'book_id': 'abc'}, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid book ID." in response.data

"""
Unit and Integration tests for R4: Book Return Processing functionality.
"""
import pytest
from library_service import return_book_by_patron

# --- Unit Tests for Service Logic ---

@pytest.fixture
def mock_book():
    return {"id": 2, "title": "1984"}

def test_return_book_success_no_fee(monkeypatch, mock_book):
    """R4-TC1: Test a successful return with no late fee."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    monkeypatch.setattr('library_service.update_borrow_record_return_date', lambda *a: True)
    monkeypatch.setattr('library_service.update_book_availability', lambda *a: True)
    monkeypatch.setattr('library_service.calculate_late_fee_for_book', lambda *a: {'fee_amount': 0.0})
    success, message = return_book_by_patron("654321", 2)
    assert success is True
    assert message == 'Return processed for "1984". No late fee.'

def test_return_book_success_with_fee(monkeypatch, mock_book):
    """R4-TC2: Test a successful return with a late fee."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    monkeypatch.setattr('library_service.update_borrow_record_return_date', lambda *a: True)
    monkeypatch.setattr('library_service.update_book_availability', lambda *a: True)
    monkeypatch.setattr('library_service.calculate_late_fee_for_book', lambda *a: {'fee_amount': 5.50})
    success, message = return_book_by_patron("654321", 2)
    assert success is True
    assert message == 'Return processed for "1984". Late fee: $5.50.'

def test_return_book_no_active_borrow_record(monkeypatch, mock_book):
    """R4-TC3: Test returning a book with no active borrow record."""
    monkeypatch.setattr('library_service.get_book_by_id', lambda bid: mock_book)
    monkeypatch.setattr('library_service.update_borrow_record_return_date', lambda *a: False)
    success, message = return_book_by_patron("654321", 2)
    assert success is False
    assert message == "No active borrow record found for this patron and book."

# --- Integration Tests for Web Route ---

def test_return_book_page_loads(client):
    """R4-TC4: Test that the GET /return page loads correctly."""
    response = client.get('/return')
    assert response.status_code == 200
    assert b"Return Book" in response.data

def test_return_book_post_success(client, monkeypatch):
    """R4-TC5: Test a successful book return via POST request."""
    monkeypatch.setattr('library_service.return_book_by_patron', lambda *a: (True, "Return successful."))
    response = client.post('/return', data={'patron_id': '123456', 'book_id': '1'})
    assert response.status_code == 200
    assert b"Return successful." in response.data # Check flash message
    assert b"Return Book" in response.data # Stays on return page

def test_return_book_post_failure(client, monkeypatch):
    """R4-TC6: Test a failed book return via POST request."""
    monkeypatch.setattr('library_service.return_book_by_patron', lambda *a: (False, "Return failed."))
    response = client.post('/return', data={'patron_id': '123456', 'book_id': '999'})
    assert response.status_code == 200
    assert b"Return failed." in response.data # Check flash message

"""
Unit and Integration tests for R5: Late Fee Calculation functionality.
"""
from datetime import datetime, timedelta
import pytest
import json
from library_service import calculate_late_fee_for_book, _compute_fee

# --- Unit Tests for Service Logic ---

def test_compute_fee_not_overdue():
    """R5-TC1: Fee should be 0 for a book that is not overdue."""
    assert _compute_fee(0) == 0.0

def test_compute_fee_within_first_tier():
    """R5-TC2: Fee calculation for books 1-7 days overdue."""
    assert _compute_fee(7) == 3.50

def test_compute_fee_into_second_tier():
    """R5-TC3: Fee calculation for books more than 7 days overdue."""
    assert _compute_fee(10) == 6.50

def test_compute_fee_at_max_cap():
    """R5-TC4: Fee calculation should not exceed the $15.00 maximum."""
    assert _compute_fee(100) == 15.00

@pytest.fixture
def mock_borrowed_books():
    now = datetime.now()
    return [{"book_id": 2, "due_date": now - timedelta(days=3)}]

def test_calculate_fee_book_is_overdue(monkeypatch, mock_borrowed_books):
    """R5-TC5: Test main service function for an overdue book."""
    monkeypatch.setattr('database.get_patron_borrowed_books', lambda pid: mock_borrowed_books)
    result = calculate_late_fee_for_book("111222", 2)
    assert result['fee_amount'] == 1.50
    assert result['days_overdue'] == 3

# --- Integration Tests for API Endpoint ---

def test_late_fee_api_success(client, monkeypatch):
    """R5-TC6: Test the GET /api/late_fee endpoint with a valid request."""
    mock_response = {'fee_amount': 2.50, 'days_overdue': 5}
    monkeypatch.setattr('library_service.calculate_late_fee_for_book', lambda *a: mock_response)
    
    response = client.get('/api/late_fee/123456/1')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['fee_amount'] == 2.50
    assert data['days_overdue'] == 5

def test_late_fee_api_no_record(client, monkeypatch):
    """R5-TC7: Test the API when no borrow record is found."""
    mock_response = {'fee_amount': 0.0, 'days_overdue': 0}
    monkeypatch.setattr('library_service.calculate_late_fee_for_book', lambda *a: mock_response)
    
    response = client.get('/api/late_fee/123456/999')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['fee_amount'] == 0.0

"""
Unit and Integration tests for R6: Book Search Functionality.
"""
import pytest
from library_service import search_books_in_catalog

# --- Unit Tests for Service Logic ---

@pytest.fixture
def mock_all_books():
    return [
        {"id": 1, "title": "The Lord of the Rings", "author": "J.R.R. Tolkien"},
        {"id": 2, "title": "A Game of Thrones", "author": "George R.R. Martin"},
    ]

def test_search_by_title_partial_match(monkeypatch, mock_all_books):
    """R6-TC1: Test service logic for title search."""
    monkeypatch.setattr('database.get_all_books', lambda: mock_all_books)
    results = search_books_in_catalog("game", "title")
    assert len(results) == 1
    assert results[0]["title"] == "A Game of Thrones"

def test_search_by_author_partial_match(monkeypatch, mock_all_books):
    """R6-TC2: Test service logic for author search."""
    monkeypatch.setattr('database.get_all_books', lambda: mock_all_books)
    results = search_books_in_catalog("tolkien", "author")
    assert len(results) == 1
    assert results[0]["author"] == "J.R.R. Tolkien"

def test_search_no_results(monkeypatch, mock_all_books):
    """R6-TC3: Test a search that yields no results."""
    monkeypatch.setattr('database.get_all_books', lambda: mock_all_books)
    results = search_books_in_catalog("Dune", "title")
    assert len(results) == 0

# --- Integration Tests for Web Route ---

def test_search_page_loads(client):
    """R6-TC4: Test that the GET /search page loads correctly."""
    response = client.get('/search')
    assert response.status_code == 200
    assert b"Search Books" in response.data

def test_search_route_with_results(client, monkeypatch):
    """R6-TC5: Test the search route and verifies results are displayed."""
    mock_results = [{"title": "Found Book", "author": "An Author", "isbn": "123", "available_copies": 1, "total_copies": 1, "id": 1}]
    monkeypatch.setattr('library_service.search_books_in_catalog', lambda *a: mock_results)
    
    response = client.get('/search?q=Found&type=title')
    
    assert response.status_code == 200
    assert b'Search Results for "Found"' in response.data
    assert b"Found Book" in response.data

def test_search_route_no_results(client, monkeypatch):
    """R6-TC6: Test the search route when no results are found."""
    monkeypatch.setattr('library_service.search_books_in_catalog', lambda *a: [])
    
    response = client.get('/search?q=nonexistent&type=title')
    
    assert response.status_code == 200
    assert b'No results found' in response.data

"""
Unit and Integration tests for R7: Patron Status Report functionality.
"""
from datetime import datetime, timedelta
import pytest
from library_service import get_patron_status_report

# --- Unit Tests for Service Logic ---

@pytest.fixture
def mock_patron_data():
    now = datetime.now()
    return {
        "current": [{"book_id": 2, "title": "Late Book", "due_date": now - timedelta(days=10)}],
        "history": [{"book_id": 3, "title": "Returned Book"}]
    }

def test_patron_status_full_report(monkeypatch, mock_patron_data):
    """R7-TC1: Test a full patron status report logic."""
    monkeypatch.setattr('database.get_patron_borrowed_books', lambda pid: mock_patron_data["current"])
    monkeypatch.setattr('database.get_patron_borrow_history', lambda pid: mock_patron_data["history"])
    report = get_patron_status_report("123123")
    assert report['num_currently_borrowed'] == 1
    assert report['total_late_fees'] == 6.50
    assert len(report['borrowing_history']) == 1

def test_patron_status_no_activity(monkeypatch):
    """R7-TC2: Test report for a patron with no activity."""
    monkeypatch.setattr('database.get_patron_borrowed_books', lambda pid: [])
    monkeypatch.setattr('database.get_patron_borrow_history', lambda pid: [])
    report = get_patron_status_report("123123")
    assert report['num_currently_borrowed'] == 0
    assert report['total_late_fees'] == 0.0

def test_patron_status_invalid_patron_id():
    """R7-TC3: Test report generation with an invalid patron ID."""
    report = get_patron_status_report("invalid-id")
    assert report['num_currently_borrowed'] == 0
    assert report['borrowing_history'] == []

# --- Integration Tests for Web Route ---

def test_status_page_no_patron(client):
    """R7-TC4: Test status page without a patron_id query parameter."""
    response = client.get('/status')
    assert response.status_code == 200
    assert b"Enter Patron ID to View Status" in response.data
    assert b"Currently Borrowed Books" not in response.data

def test_status_page_with_patron(client, monkeypatch):
    """R7-TC5: Test status page when a valid patron_id is provided."""
    mock_report = {
        'currently_borrowed': [{'title': 'A Borrowed Book', 'due_date': '2025-10-20'}],
        'borrowing_history': [], 'num_currently_borrowed': 1, 'total_late_fees': 0.0
    }
    monkeypatch.setattr('library_service.get_patron_status_report', lambda *a: mock_report)
    
    response = client.get('/status?patron_id=123456')
    
    assert response.status_code == 200
    assert b"Status for Patron: 123456" in response.data
    assert b"A Borrowed Book" in response.data
    assert b"Total Late Fees Due: $0.00" in response.data

def test_status_page_with_invalid_patron(client, monkeypatch):
    """R7-TC6: Test status page with an invalid patron_id."""
    mock_report = {
        'currently_borrowed': [], 'borrowing_history': [],
        'num_currently_borrowed': 0, 'total_late_fees': 0.0
    }
    monkeypatch.setattr('library_service.get_patron_status_report', lambda *a: mock_report)
    
    response = client.get('/status?patron_id=abc')
    assert response.status_code == 200
    # The service function handles the invalid ID and returns an empty report
    assert b"Total Late Fees Due: $0.00" in response.data
```

## Test-Case Comparison & Analysis
The AI-generated test suite provides a significant range of testing by incorporating integration testing. While my tests focus on isolating and validating the business logic within the library_service layer, the AI tests also verify the application's web routes and API endpoints. This is accomplished by using a Flask test client to simulate HTTP requests, ensuring that the web layer correctly handles form data, calls the appropriate service functions, and renders the expected responses or redirects. This approach provides end-to-end validation which my own tests lacked.

However when analyzing the pure unit tests, the AI's approach is functionally correct but less sophisticated than the my own. The AI's tests cover the primary cases but are more bloated, often using separate functions for each validation case. In contrast my tests demonstrate a higher quality through the use of pytest.mark.parametrize to cover numerous edge cases concisely and employ deeper assertions that verify internal side effects, such as checking the arguments passed to mocked functions. Therefore, while the AI excels at providing broad integration coverage, the human-written tests offer superior depth, precision, and maintainability for validating the core business logic.