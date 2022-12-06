from flask import Blueprint
from controllers.webController import home, scan, reports, settings, analysis

webRoute = Blueprint('webRoute', __name__)

webRoute.route('/home', methods=['GET'])(home)
webRoute.route('/scan', methods=['GET'])(scan)
webRoute.route('/analysis', methods=['GET'])(analysis)
webRoute.route('/reports', methods=['GET'])(reports)
webRoute.route('/settings', methods=['GET'])(settings)