"""
API Routes - JSON API endpoints
"""

from flask import Blueprint, jsonify, request
from library_service import calculate_late_fee_for_book, search_books_in_catalog

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/late_fee/<patron_id>/<int:book_id>')
def get_late_fee(patron_id, book_id):
    """
    Calculate late fee for a specific book borrowed by a patron.
    API endpoint for R5: Late Fee Calculation
    """
    result = calculate_late_fee_for_book(patron_id, book_id)
    status = result.get('status', 'ok')
    code = 200
    if status == 'invalid patron id':
        code = 400
    return jsonify(result), code

@api_bp.route('/search')
def search_books_api():
    """
    Search for books via API endpoint.
    Alternative API interface for R6: Book Search Functionality
    """
    search_term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'title')
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400
    books = search_books_in_catalog(search_term, search_type)
    return jsonify({'search_term': search_term, 'search_type': search_type, 'results': books, 'count': len(books)}), 200
