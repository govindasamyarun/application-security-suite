from flask import Blueprint
from controllers.apiController import settings_data, download_report, scan_strat, scan_status, previous_scan_status

apiRoute = Blueprint('apiRoute', __name__)

apiRoute.route('/settings/data', methods=['GET', 'POST'])(settings_data)
apiRoute.route('/download/report', methods=['GET'])(download_report)
apiRoute.route('/scan/start', methods=['GET'])(scan_strat)
apiRoute.route('/scan/status', methods=['GET'])(scan_status)
apiRoute.route('/previous/scan/status', methods=['GET'])(previous_scan_status)