from flask import Blueprint
from controllers.gitLeaksController import settings_data, download_report, scan_strat, scan_status, previous_scan_status

gitLeaksRoute = Blueprint('gitLeaksRoute', __name__)

gitLeaksRoute.route('/settings/data', methods=['GET', 'POST'])(settings_data)
gitLeaksRoute.route('/download/report', methods=['GET'])(download_report)
gitLeaksRoute.route('/scan/start', methods=['GET'])(scan_strat)
gitLeaksRoute.route('/scan/status', methods=['GET'])(scan_status)
gitLeaksRoute.route('/previous/scan/status', methods=['GET'])(previous_scan_status)