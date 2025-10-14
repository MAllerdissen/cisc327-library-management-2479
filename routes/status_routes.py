"""
Patron Status Routes - Patron status page (R7)
"""

from flask import Blueprint, render_template, request, flash
from library_service import get_patron_status_report

status_bp = Blueprint('status', __name__)

@status_bp.route('/status', methods=['GET'])
def patron_status():
    patron_id = request.args.get('patron_id', '').strip()
    report = None
    if patron_id:
        report = get_patron_status_report(patron_id)
        if report.get('error'):
            flash(report['error'], 'error')
            report = None
    return render_template('status.html', patron_id=patron_id, report=report)
