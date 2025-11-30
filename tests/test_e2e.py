# tests/test_e2e.py

import time

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"


# ---------- Playwright fixtures (required for browser-based E2E) ----------

@pytest.fixture(scope="session")
def browser():
    """Start a real browser (Chromium) for the whole test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """Create a fresh page for each test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


# ---------- Helper: add a unique book through the real UI ----------

def _add_unique_book_via_ui(page):
    """
    Navigate to the Add Book page, submit the form, and verify success.
    Returns the book data dict (title, author, isbn).
    """
    # i. Open the app (home redirects to catalog) and go to Add Book page
    page.goto(BASE_URL + "/")
    page.click("text=Add Book")  # navbar link "➕ Add Book" contains this text

    # ii. Fill the Add Book form with unique data
    suffix = str(int(time.time() * 1000))
    title = f"E2E Test Book {suffix}"
    author = "Playwright Tester"

    # Generate a unique 13-digit ISBN (exactly 13 digits)
    isbn = ("9" * 13)[:-len(suffix)] + suffix
    total_copies = "1"

    page.fill("#title", title)
    page.fill("#author", author)
    page.fill("#isbn", isbn)
    page.fill("#total_copies", total_copies)

    # Submit the form
    page.click("text=Add Book to Catalog")

    # iii. Verify a success flash message appears and we are back on the catalog
    page.wait_for_selector(".flash-success")
    flash_text = page.inner_text(".flash-success")
    assert "successfully added to catalog" in flash_text

    # iv. Verify the new book appears in the catalog table
    table_text = page.inner_text("table")
    assert title in table_text
    assert author in table_text
    assert isbn in table_text

    return {
        "title": title,
        "author": author,
        "isbn": isbn,
    }


# ---------- Flow 1: Add a book & verify it appears in the catalog ----------

def test_add_book_appears_in_catalog(page):
    """
    User Flow 1:
      - Add a new book (title, author, ISBN, copies)
      - Verify it appears in the catalog with correct details
    """
    book = _add_unique_book_via_ui(page)

    # Explicitly navigate to the catalog page and verify the row content
    page.click("text=Catalog")

    row = page.locator("table tbody tr", has_text=book["title"]).first
    assert row.is_visible()

    row_text = row.inner_text()
    assert book["title"] in row_text
    assert book["author"] in row_text
    assert book["isbn"] in row_text
    # New book should be fully available (e.g., "1/1 Available")
    assert "Available" in row_text


# ---------- Flow 2: Borrow a book from the catalog & verify confirmation ----------

def test_borrow_book_from_catalog(page):
    """
    User Flow 2:
      - Add a new book
      - Borrow it from the catalog using a patron ID
      - Verify borrow confirmation message
      - Verify catalog shows it as not available
    """
    book = _add_unique_book_via_ui(page)

    # Go to the catalog (home redirects to catalog)
    page.goto(BASE_URL + "/")

    # Find the row for our book
    row = page.locator("table tbody tr", has_text=book["title"]).first
    assert row.is_visible()

    # Fill the inline borrow form in that row with a valid 6-digit patron ID
    patron_id = "123456"
    row.locator("input[name='patron_id']").fill(patron_id)
    row.get_by_role("button", name="Borrow").click()

    # Verify borrow confirmation flash message appears
    page.wait_for_selector(".flash-success")
    flash_text = page.inner_text(".flash-success")
    assert "Borrowed" in flash_text
    assert book["title"] in flash_text

    # After borrowing, the book should now show as "Not Available"
    page.click("text=Catalog")
    row_after = page.locator("table tbody tr", has_text=book["title"]).first
    assert row_after.is_visible()
    assert "Not Available" in row_after.inner_text()
