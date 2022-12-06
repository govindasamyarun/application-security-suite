import os
from flask import Flask
from flask_migrate import Migrate
from routes.apiRoute import apiRoute
from routes.webRoute import webRoute
from models.as2 import as2DbHandler, SettingsTable
from models.gitleaks import gitleaksDbHandler, gitleaksScanResultsTable
from models.bitbucketServer import bitbucketServerDbHandler, bitbucketServerScanResultsTable
from libs.cache import Cache

app = Flask(__name__)

app.debug = False

# DB and Redis config 
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://{}:{}@{}:{}/{}".format(os.environ['DB_USER'], os.environ['DB_PASSWORD'], os.environ['DB_HOST'], os.environ['DB_PORT'], os.environ['DB_DATABASE'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REDIS_HOST'] = os.environ['REDIS_HOST']
app.config['REDIS_PORT'] = os.environ['REDIS_PORT']

# AS2 DB handler 
as2DbHandler.init_app(app)
migrate = Migrate(app, as2DbHandler)

# Gitleaks DB handler 
gitleaksDbHandler.init_app(app)
migrate = Migrate(app, gitleaksDbHandler)

# BitbucketServer DB handler 
bitbucketServerDbHandler.init_app(app)
migrate = Migrate(app, bitbucketServerDbHandler)

with app.app_context():
    # Creates tables if not exists 
    as2DbHandler.create_all()
    gitleaksDbHandler.create_all()
    bitbucketServerDbHandler.create_all()
    # Sets the cache to default during application startup process 
    # CS - Current scan results
    # PS - Previous scan results
    Cache().write('CS_Status', 'Not Started')
    Cache().write('CS_TotalRepos', '0')
    Cache().write('CS_NoOfReposScanned', '0')
    Cache().write('CS_ReposNonCompliant', '0')
    Cache().write('CS_NoOfSecretsFound', '0')
    Cache().write('CS_PercentageCompletion', '0')
    Cache().write('CS_ScanStartDate', '-')
    Cache().write('CS_ScanEndDate', '-')

    Cache().write('PS_TotalRepos', '0')
    Cache().write('PS_ReposCompliant', '0')
    Cache().write('PS_ReposNonCompliant', '0')
    Cache().write('PS_NoOfSecretsFound', '0')
    Cache().write('PS_ScanStartDate', '-')
    Cache().write('PS_ScanEndDate', '-')

    # Sets default values to the DB during application startup 
    if not as2DbHandler.session.query(SettingsTable).all():
        add_record = SettingsTable(gitleaksPath='/usr/src/app/gitleaks/gitleaks', bitbucketLimit=100, scannerScanAllBranches='false', scannerPathToDownloadRepository='/usr/src/app/downloads/', scannerResultsDirectory='/usr/src/app/', slackEnable='false', jiraEnable='false')
        as2DbHandler.session.add(add_record)
        as2DbHandler.session.commit()

# Routes to the html files
app.register_blueprint(webRoute, url_prefix='/web')
# Routes to the Gitelaks controller 
app.register_blueprint(apiRoute, url_prefix='/api')


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)