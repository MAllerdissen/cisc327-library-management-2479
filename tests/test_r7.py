# tests/test_r7.py
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import library_service
import database

def _borrow_record(book_id: int, title: str, days_ago_borrowed: int, days_until_due: int):
    borrow_date = datetime.now() - timedelta(days=days_ago_borrowed)
    due_date = datetime.now() + timedelta(days=days_until_due)
    return {
        'book_id': book_id,
        'title': title,
        'author': f'Author {book_id}',
        'borrow_date': borrow_date,
        'due_date': due_date,
        'is_overdue': datetime.now() > due_date
    }

def _history_record(book_id: int, title: str, borrow_days_ago: int, return_days_ago: int):
    borrow_date = datetime.now() - timedelta(days=borrow_days_ago)
    return_date = None if return_days_ago is None else (datetime.now() - timedelta(days=return_days_ago))
    return {
        'book_id': book_id,
        'title': title,
        'borrow_date': borrow_date,
        'return_date': return_date
    }


def test_patron_status_includes_all_keys_and_aggregates_fees(monkeypatch):
    patron_id = '123456'
    # Two current borrows: book 1 is 3 days overdue, book 2 is not overdue
    borrowed = [
        _borrow_record(1, 'Overdue Book', days_ago_borrowed=20, days_until_due=-3),
        _borrow_record(2, 'Not Overdue Book', days_ago_borrowed=1, days_until_due=13)
    ]
    history = [
        _history_record(3, 'Returned Book A', borrow_days_ago=60, return_days_ago=45),
        _history_record(4, 'Returned Book B', borrow_days_ago=120, return_days_ago=100)
    ]

    # Mock DB functions
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: borrowed)
    monkeypatch.setattr(database, 'get_patron_borrow_count', lambda pid: len(borrowed))

    # Mock history function which may or may not exist in DB module in the project.
    # Use raising=False so the patch creates attribute if missing.
    monkeypatch.setattr(database, 'get_patron_borrow_history', lambda pid: history, raising=False)

    # Mock late-fee calculation per-book: book 1 => $1.50, book 2 => $0.00
    def fake_fee_calc(pid, bid):
        if bid == 1:
            return {'fee_amount': 1.50, 'days_overdue': 3}
        else:
            return {'fee_amount': 0.00, 'days_overdue': 0}
    monkeypatch.setattr(library_service, 'calculate_late_fee_for_book', fake_fee_calc, raising=False)

    report = library_service.get_patron_status_report(patron_id)

    # Basic shape
    assert isinstance(report, dict), "Report must be a dict"

    # Required keys present
    for key in ('currently_borrowed', 'borrowing_history', 'num_currently_borrowed', 'total_late_fees'):
        assert key in report, f"Missing key in report: {key}"

    # currently_borrowed should be a list of dicts with at least book_id, title and due_date
    assert isinstance(report['currently_borrowed'], list)
    assert len(report['currently_borrowed']) == 2
    for item in report['currently_borrowed']:
        assert 'book_id' in item and 'title' in item and 'due_date' in item

    # borrowing_history should be a list (may be empty)
    assert isinstance(report['borrowing_history'], list)
    assert len(report['borrowing_history']) == 2

    # num_currently_borrowed must be integer and equal to len(currently_borrowed)
    assert isinstance(report['num_currently_borrowed'], int)
    assert report['num_currently_borrowed'] == 2

    # total_late_fees must be numeric (float or Decimal) and equal to the sum of mocked fees
    total_fees = report['total_late_fees']
    # normalize to Decimal then to 2 decimal places for robust comparison
    total_fees_dec = Decimal(str(total_fees)).quantize(Decimal('0.01'))
    assert total_fees_dec == Decimal('1.50'), f"Expected total late fees to be 1.50, got {total_fees}"


def test_no_current_borrows_returns_zero_totals(monkeypatch):
    patron_id = '222222'
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: [])
    monkeypatch.setattr(database, 'get_patron_borrow_count', lambda pid: 0)
    monkeypatch.setattr(database, 'get_patron_borrow_history', lambda pid: [], raising=False)

    # Ensure that if calculate_late_fee_for_book is called, it returns zero (defensive)
    monkeypatch.setattr(library_service, 'calculate_late_fee_for_book', lambda pid, bid: {'fee_amount': 0.0, 'days_overdue': 0}, raising=False)

    report = library_service.get_patron_status_report(patron_id)

    assert isinstance(report, dict)
    assert report.get('currently_borrowed', []) == []
    assert report.get('num_currently_borrowed', None) == 0
    # total_late_fees can be float or decimal; coerce for comparison
    assert float(report.get('total_late_fees', 0.0)) == 0.00
    assert isinstance(report.get('borrowing_history', []), list)


def test_borrowing_history_items_have_expected_fields(monkeypatch):
    """
    Borrowing history should present past borrow records with borrow_date and return_date.
    """
    patron_id = '333333'
    monkeypatch.setattr(database, 'get_patron_borrowed_books', lambda pid: [])
    monkeypatch.setattr(database, 'get_patron_borrow_count', lambda pid: 0)

    history = [
        _history_record(10, 'Old Book One', borrow_days_ago=200, return_days_ago=150),
        _history_record(11, 'Old Book Two', borrow_days_ago=400, return_days_ago=300)
    ]
    monkeypatch.setattr(database, 'get_patron_borrow_history', lambda pid: history, raising=False)

    report = library_service.get_patron_status_report(patron_id)

    assert isinstance(report, dict)
    bh = report.get('borrowing_history', [])
    assert isinstance(bh, list)
    assert len(bh) == 2
    for item in bh:
        assert 'book_id' in item and 'title' in item
        # borrow_date and return_date should be datetimes (or ISO strings depending on implementation)
        assert 'borrow_date' in item
        assert 'return_date' in item


def test_handles_invalid_patron_id_gracefully(monkeypatch):
    invalid_patron_id = 'abc'  # invalid format
    # Do not set any DB behaviour; if code tries to call DB it may error — but the acceptable behaviour
    # we assert here is that the function returns a dict and includes safe default values rather than crashing.
    try:
        report = library_service.get_patron_status_report(invalid_patron_id)
    except Exception as e:
        pytest.fail(f"get_patron_status_report raised an exception for invalid patron id: {e}")

    assert isinstance(report, dict)
    # Defensive expectations
    assert isinstance(report.get('currently_borrowed', []), list)
    assert isinstance(report.get('borrowing_history', []), list)
    assert isinstance(report.get('num_currently_borrowed', 0), int)
    assert float(report.get('total_late_fees', 0.0)) >= 0.0
