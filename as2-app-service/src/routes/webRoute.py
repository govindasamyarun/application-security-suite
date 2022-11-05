from flask import Blueprint
from controllers.webController import home, scan, reports, settings

webRoute = Blueprint('webRoute', __name__)

webRoute.route('/home', methods=['GET'])(home)
webRoute.route('/scan', methods=['GET'])(scan)
webRoute.route('/reports', methods=['GET'])(reports)
webRoute.route('/settings', methods=['GET'])(settings)