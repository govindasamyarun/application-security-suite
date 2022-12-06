from flask import Blueprint
from controllers.apiController import settings_data, download_report, scan_strat, scan_status, previous_scan_status, analysis_view, analysis_view_record

apiRoute = Blueprint('apiRoute', __name__)

apiRoute.route('/settings/data', methods=['GET', 'POST'])(settings_data)
apiRoute.route('/download/report', methods=['GET'])(download_report)
apiRoute.route('/scan/start', methods=['GET'])(scan_strat)
apiRoute.route('/scan/status', methods=['GET'])(scan_status)
apiRoute.route('/scan/analysis', methods=['GET'])(analysis_view)
apiRoute.route('/scan/analysis/record', methods=['GET'])(analysis_view_record)
apiRoute.route('/previous/scan/status', methods=['GET'])(previous_scan_status)