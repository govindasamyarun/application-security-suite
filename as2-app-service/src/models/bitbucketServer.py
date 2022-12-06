from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

bitbucketServerDbHandler = SQLAlchemy()

# This table is used to capture the scan results 
class bitbucketServerScanResultsTable(bitbucketServerDbHandler.Model):
    __tablename__ = 'bitbucketserver_scan_results'

    project = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.String, primary_key=True)
    repository = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.String, primary_key=True)
    lastcommitdate = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.DateTime)
    lastcommitname = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.String)
    lastcommitemail = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.String)
    updatedat = bitbucketServerDbHandler.Column(bitbucketServerDbHandler.DateTime, server_default=bitbucketServerDbHandler.func.now())

    @property
    def serialize(self):
        return {
            'project': self.project,
            'repository': self.repository,
            'lastcommitdate': self.lastcommitdate,
            'lastcommitname': self.lastcommitname,
            'lastcommitemail': self.lastcommitemail,
            'updatedat': self.updatedat
        }