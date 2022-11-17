from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

as2DbHandler = SQLAlchemy()

# Scan status is captured in events table 
# This table is not used but planning to use it later 
class ComplianceTable(as2DbHandler.Model):
    __tablename__ = 'as2_compliance'

    id = as2DbHandler.Column(as2DbHandler.Integer, primary_key=True)
    eventtime = as2DbHandler.Column(as2DbHandler.DateTime, server_default=as2DbHandler.func.now())
    totalrepos = as2DbHandler.Column(as2DbHandler.Integer)
    reposcompliant = as2DbHandler.Column(as2DbHandler.Integer)
    reposnoncompliant = as2DbHandler.Column(as2DbHandler.Integer)
    noofsecretsfound = as2DbHandler.Column(as2DbHandler.Integer)
    compliancepercentage = as2DbHandler.Column(as2DbHandler.Integer)
    scanstartdate = as2DbHandler.Column(as2DbHandler.DateTime)
    scanenddate = as2DbHandler.Column(as2DbHandler.DateTime)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'eventtime': self.eventtime,
            'totalrepos': self.totalrepos,
            'reposcompliant': self.reposcompliant,
            'reposnoncompliant': self.reposnoncompliant,
            'noofsecretsfound': self.noofsecretsfound,
            'compliancepercentage': self.compliancepercentage,
            'scanstartdate': self.scanstartdate,
            'scanenddate': self.scanenddate
        }

# Application settings is stored in the settings table 
class SettingsTable(as2DbHandler.Model):
    __tablename__ = 'as2_settings'

    id = as2DbHandler.Column(as2DbHandler.Integer, primary_key=True)
    gitleaksPath = as2DbHandler.Column(as2DbHandler.String, default='/usr/src/app/gitleaks/gitleaks')
    bitbucketHost = as2DbHandler.Column(as2DbHandler.String, default='')
    bitbucketLimit = as2DbHandler.Column(as2DbHandler.Integer, default=100)
    bitbucketUserName = as2DbHandler.Column(as2DbHandler.String, default='')
    bitbucketAuthToken = as2DbHandler.Column(as2DbHandler.String, default='')
    scannerScanAllBranches = as2DbHandler.Column(as2DbHandler.String, default='false')
    scannerPathToDownloadRepository = as2DbHandler.Column(as2DbHandler.String, default='')
    scannerResultsDirectory = as2DbHandler.Column(as2DbHandler.String, default='')
    slackEnable = as2DbHandler.Column(as2DbHandler.String, default='false')
    slackHost = as2DbHandler.Column(as2DbHandler.String, default='')
    slackAuthToken = as2DbHandler.Column(as2DbHandler.String, default='')
    slackChannel = as2DbHandler.Column(as2DbHandler.String, default='')
    slackMessage = as2DbHandler.Column(as2DbHandler.String, default='')
    jiraEnable = as2DbHandler.Column(as2DbHandler.String, default='false')
    jiraHost = as2DbHandler.Column(as2DbHandler.String, default='')
    jiraEpicID = as2DbHandler.Column(as2DbHandler.String, default='')
    jiraUserName = as2DbHandler.Column(as2DbHandler.String, default='')
    jiraAuthToken = as2DbHandler.Column(as2DbHandler.String, default='')

    '''def __getitem__(self, field):
        return self.__dict__[field]'''

    @property
    def serialize(self):
        return {
            'id': self.id,
            'gitleaksPath': self.gitleaksPath,
            'bitbucketHost': self.bitbucketHost,
            'bitbucketLimit': self.bitbucketLimit,
            'bitbucketUserName': self.bitbucketUserName,
            'bitbucketAuthToken': self.bitbucketAuthToken,
            'scannerScanAllBranches': self.scannerScanAllBranches,
            'scannerPathToDownloadRepository': self.scannerPathToDownloadRepository,
            'scannerResultsDirectory': self.scannerResultsDirectory,
            'slackEnable': self.slackEnable,
            'slackHost': self.slackHost,
            'slackAuthToken': self.slackAuthToken,
            'slackChannel': self.slackChannel,
            'slackMessage': self.slackMessage,
            'jiraEnable': self.jiraEnable,
            'jiraHost': self.jiraHost,
            'jiraEpicID': self.jiraEpicID,
            'jiraUserName': self.jiraUserName,
            'jiraAuthToken': self.jiraAuthToken
        }