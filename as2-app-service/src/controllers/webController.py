import imp
from flask import render_template

def home():
    return render_template('home.html')

def scan():
    return render_template('scan.html')

def reports():
    return render_template('reports.html')

def settings():
    return render_template('settings.html')