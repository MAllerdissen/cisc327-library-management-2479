# A1_Allerdissen_20402479.md
**Name:** Martin Allerdissen  
**Student ID (last 4 digits):** 2479  
**Group:** 01

## Implementation Status
| Requirement | Function(s) / Feature | Implementation status | What is missing / notes (evidence) |
|---|---:|---|---|
| R1 - Add Book To Catalog | `add_book_to_catalog` | Partial | Validation gaps: ISBN validation does not enforce digits-only and accepts whitespace-only ISBNs. A valid insert case returned failure in tests (see `sample_test.py::test_add_book_valid_input`). Tests: `tests/test_r1.py` failures: `test_add_book_rejects_isbn_with_non_digits`, `test_add_book_rejects_whitespace_isbn`, and `sample_test.py::test_add_book_valid_input`. |
| R3 - Book Borrowing Interface | `borrow_book_by_patron` | Partial | Off-by-one bug on borrow limit: implementation allows borrowing when patron currently has 5 books (`>5` used instead of `>=5`). Test failing: `tests/test_r3.py::test_patron_reached_borrow_limit_by_spec`. Other borrow flows pass. |
| R4 - Book Return Processing | `return_book_by_patron` | Missing / Not implemented | Multiple tests failed. Placeholder/partial implementation returned 'Book return ... implemented.' instead of performing: patron ID validation, verifying active borrow record, updating borrow record return date, updating book availability, calculating and including late fees. Tests failing: all R4 tests (`tests/test_r4.py`). |
| R5 - Late Fee Calculation API | `calculate_late_fee_for_book` and `/api/late_fee/...` | Missing / Incorrect | Function did not return expected dict `{fee_amount, days_overdue}` or calculation rules not implemented. All R5 tests failed. Need to implement the fee rules: 14-day due, $0.50/day first 7 days, $1/day after, cap at $15.00. Tests failing: `tests/test_r5.py` (all). |
| R6 - Book Search | `search_books_in_catalog` | Partial | Partial/case-insensitive matching for title/author and exact-match for ISBN did not produce results in tests. Confirm the function consults `database.get_all_books()` for title/author and `database.get_book_by_isbn()` for ISBN so tests can mock correctly. Tests failing: `tests/test_r6_search.py` (title/author/isbn checks). |
| R7 - Patron Status Report | `get_patron_status_report` | Missing / Incomplete | Report is missing required keys/aggregations (no `currently_borrowed` present). Needs to aggregate borrow list, count, sum late fees via `calculate_late_fee_for_book`, and include borrowing history. Tests failing: `tests/test_r7_patron_status.py`. |

## Summary
- Test files included: `tests/test_r1.py` … `tests/test_r7.py`
- Test run (your last run): **57 tests total** — **24 failed**, **33 passed**.

## Tests
- `tests/test_r1.py` — **R1: Add Book To Catalog**  
  Validates input validation (title, author length/required, ISBN exactly 13 digits and digits-only, total copies positive integer), duplicate-ISBN rejection, DB-insert failure handling, and that trimmed title/author and `available_copies == total_copies` are passed to the DB layer.

- `tests/test_r2.py` — **R2: Catalog Display (routes + templates)**  
  Uses Flask test client to ensure the catalog page renders book fields (ID, title, author, ISBN), availability display (`X/Y Available` or `Not Available`), and that a Borrow form/button appears only for available books. Includes empty-catalog behavior and asserts the route calls the expected helper.

- `tests/test_r3.py` — **R3: Book Borrowing**  
  Exercises patron ID validation (6 digits), book existence and availability checks, patron borrowing limit (max **5** books), DB-insert/update flows, DB failure handling, and that due date = borrow_date + 14 days (verified in tests).

- `tests/test_r4.py` — **R4: Book Return Processing**  
  Verifies patron ID validation, detection of missing active borrow records, updating the borrow record with a return date, incrementing availability, handling DB failures, and inclusion/formatting of late-fee information in the result. Also checks the function passes a recent datetime return_date to the DB helper.

- `tests/test_r5.py` — **R5: Late Fee Calculation**  
  Tests `calculate_late_fee_for_book` business logic: days overdue computation and fee rules (first 7 days = $0.50/day, additional days = $1.00/day, cap $15.00). Includes no-overdue, small-overdue, long-overdue (cap), and no-borrow-record defensive behavior.

- `tests/test_r6_search.py` — **R6: Book Search**  
  Tests `search_books_in_catalog` for partial, case-insensitive matches on title/author; exact-match-only behavior for ISBN; invalid `type` handling; and that the returned items match catalog format.

- `tests/test_r7_patron_status.py` — **R7: Patron Status Report**  
  Validates that `get_patron_status_report` returns a dict containing `currently_borrowed`, `borrowing_history`, `num_currently_borrowed`, and `total_late_fees`. Tests aggregation of per-book late fees (mocked), history formatting, and safe behavior for invalid/empty patron records.

### Test design notes
- R2 employs Flask test client to validate template rendering.
- `monkeypatch` is used extensively to stub database helper functions (`database.*`, `library_service.*`) so tests are deterministic and side-effect free.
- Each function includes both positive and negative test cases. Tests intentionally assert spec-mandated behaviors and exact/consistent error messages where appropriate so they surface implementation defects.
