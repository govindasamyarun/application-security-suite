from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

gitLeaksDbHandler = SQLAlchemy()

# Scan status is captured in events table 
# This table is not used but planning to use it later 
class gitLeaksEventsTable(gitLeaksDbHandler.Model):
    __tablename__ = 'as2_gl_events'

    id = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer, primary_key=True)
    eventtime = gitLeaksDbHandler.Column(gitLeaksDbHandler.DateTime, server_default=gitLeaksDbHandler.func.now())
    totalrepos = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer)
    reposcompliant = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer)
    reposnoncompliant = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer)
    noofsecretsfound = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer)
    compliancepercentage = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer)
    scanstartdate = gitLeaksDbHandler.Column(gitLeaksDbHandler.DateTime)
    scanenddate = gitLeaksDbHandler.Column(gitLeaksDbHandler.DateTime)

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
class gitLeaksSettingsTable(gitLeaksDbHandler.Model):
    __tablename__ = 'as2_gl_settings'

    id = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer, primary_key=True)
    gitleaksPath = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='/usr/src/app/gitleaks/gitleaks')
    bitbucketHost = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    bitbucketLimit = gitLeaksDbHandler.Column(gitLeaksDbHandler.Integer, default=100)
    bitbucketUserName = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    bitbucketAuthToken = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    scannerScanAllBranches = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='false')
    scannerPathToDownloadRepository = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    scannerResultsDirectory = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    slackEnable = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='false')
    slackHost = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    slackAuthToken = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    slackChannel = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    slackMessage = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    jiraEnable = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='false')
    jiraHost = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    jiraEpicID = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    jiraUserName = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')
    jiraAuthToken = gitLeaksDbHandler.Column(gitLeaksDbHandler.String, default='')

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