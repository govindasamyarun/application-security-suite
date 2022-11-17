from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

gitleaksDbHandler = SQLAlchemy()

# This table is used to capture the scan results 
class gitleaksScanResultsTable(gitleaksDbHandler.Model):
    __tablename__ = 'gitleaks_scan_results'

    project = gitleaksDbHandler.Column(gitleaksDbHandler.String, primary_key=True)
    repository = gitleaksDbHandler.Column(gitleaksDbHandler.String, primary_key=True)
    secretscount = gitleaksDbHandler.Column(gitleaksDbHandler.Integer)
    updatedat = gitleaksDbHandler.Column(gitleaksDbHandler.DateTime, server_default=gitleaksDbHandler.func.now())

    @property
    def serialize(self):
        return {
            'project': self.project,
            'repository': self.repository,
            'secretscount': self.secretscount,
            'updatedat': self.updatedat
        }