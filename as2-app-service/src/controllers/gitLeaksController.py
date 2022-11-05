import re, ast
from subprocess import Popen, PIPE
from datetime import datetime
from turtle import update
from certifi import where
from flask import request, jsonify
from threading import Thread
from config import gitLeaksConfig
from urllib.parse import unquote, parse_qs
from flask import send_file
from controllers.applicationSecuritySuite import as2Class, as2LiteClass
from models.gitLeaksModel import gitLeaksDbHandler, gitLeaksSettingsTable
from sqlalchemy import select, update, text

def settings_data():
    # This function is to process and store the settings values to the db 
    print('INFO - Execute settings_data function')
    settingsTable = as2Class().dbSelectOneRecord(gitLeaksSettingsTable.__tablename__, 'id=1')
    if request.method == 'POST':
        print('INFO - settings_data POST method')
        data = dict(ast.literal_eval(str(parse_qs(request.get_data().decode("utf-8")))))
        # Controls sensitive fields response
        for k, v in data.items():
            if v[0][:5] != 'XXXXX':
                settingsTable[k] = v[0]
        # Handle empty strings 
        for k, v in settingsTable.items():
            if v == '':
                settingsTable[k] = ''
        if (settingsTable['bitbucketHost'] == '' or settingsTable['bitbucketUserName'] == '' or settingsTable['bitbucketAuthToken'] == '' or settingsTable['scannerScanAllBranches'] == ''):
            print('INFO - Set mandatory values')
            return {"status": "error", "message": "set mandatory values"}
        if (settingsTable['slackEnable'].lower() == "true" and (settingsTable['slackHost'] == '' or settingsTable['slackAuthToken'] == '' or settingsTable['slackChannel'] == '' or settingsTable['slackMessage'] == '')):
            print('INFO - Set Slack mandatory values')
            return {"status": "error", "message": "set slack mandatory values"}
        if (settingsTable['jiraEnable'].lower() == "true" and (settingsTable['jiraHost'] == '' or settingsTable['jiraEpicID'] == '' or settingsTable['jiraUserName'] == '' or settingsTable['jiraAuthToken'] == '')):
            print('INFO - Set JIRA mandatory values')
            return {"status": "error", "message": "set jira mandatory values"}
        if not as2LiteClass().authCheck(settingsTable['bitbucketHost'], settingsTable['bitbucketAuthToken'], settingsTable['slackEnable'], settingsTable['slackAuthToken'], settingsTable['jiraEnable'], settingsTable['jiraHost'], settingsTable['jiraUserName'], settingsTable['jiraAuthToken']):
            print('INFO - Authentication failure')
            return {"status": "error", "message": "Authentication failure"}

        values = {'data': '''"bitbucketHost" = '{}', "bitbucketUserName" = '{}', "bitbucketAuthToken" = '{}', "scannerScanAllBranches" = '{}', "slackEnable" = '{}', "slackHost" = '{}', "slackAuthToken" = '{}', "slackChannel" = '{}', "slackMessage" = '{}', "jiraEnable" = '{}', "jiraHost" = '{}', "jiraEpicID" = '{}', "jiraUserName" = '{}', "jiraAuthToken" = '{}\''''.format(settingsTable['bitbucketHost'], settingsTable['bitbucketUserName'], settingsTable['bitbucketAuthToken'], settingsTable['scannerScanAllBranches'], settingsTable['slackEnable'], settingsTable['slackHost'], settingsTable['slackAuthToken'], settingsTable['slackChannel'], settingsTable['slackMessage'], settingsTable['jiraEnable'], settingsTable['jiraHost'], settingsTable['jiraEpicID'], settingsTable['jiraUserName'], settingsTable['jiraAuthToken'])}
        updateSettingsData = as2Class().dbUpdateRecord(gitLeaksSettingsTable.__tablename__, 'id=1', values)
        return updateSettingsData
    else:
        print('INFO - settings_data GET method')
        settingsTable = as2Class().dbSelectOneRecord(gitLeaksSettingsTable.__tablename__, 'id=1')
        # Sensitive fields will be masked except the last 4 digits 
        data = {"bitbucket_host_name": settingsTable['bitbucketHost'], "bitbucket_user_name": settingsTable['bitbucketUserName'], "bitbucket_auth_token": re.sub(r'\S', 'X', settingsTable['bitbucketAuthToken'][:-4])+settingsTable['bitbucketAuthToken'][-4:], "scan_all_branches": settingsTable['scannerScanAllBranches'], "enable_slack_notifications": settingsTable['slackEnable'], "slack_host_name": settingsTable['slackHost'], "slack_auth_token": re.sub(r'\S', 'X', settingsTable['slackAuthToken'][:-4])+settingsTable['slackAuthToken'][-4:], "slack_channel_id": settingsTable['slackChannel'], "slack_message": settingsTable['slackMessage'], "enable_jira_notifications": settingsTable['jiraEnable'], "jira_host_name": settingsTable['jiraHost'], "jira_epic_id": settingsTable['jiraEpicID'], "jira_user_name": settingsTable['jiraUserName'], "jira_auth_token": re.sub(r'\S', 'X', settingsTable['jiraAuthToken'][:-4])+settingsTable['jiraAuthToken'][-4:]}
        return data

def download_report():
    # This function download's the scan results in csv format 
    print('INFO - Execute download_report function')
    file_path = gitLeaksConfig.scanner_results_config_file_path
    return send_file(file_path, mimetype='text/csv', as_attachment=True)

def scan_strat():
    # This function starts the scan process 
    print('INFO - Execute scan_start function')
    Thread(target=as2Class().scan_engine).start()
    data = [["", "Status", "In Progress"], ["", "Total Number Of Repositories", "0"], ["", "Number of Repos scanned", "0"], ["", "Number of Repos Non compliant", "0"], ["", "Number of Secrets found", "0"], ["", "Percentage Completion", "0"], ["", "Scan start date", "-"]]
    return {'data': data}

def scan_status():
    # This function returns the scan status 
    # This function is called by the frontend every 30 seconds  
    print('INFO - Execute scan_status function')
    stats = ['Status', 'TotalRepos', 'NoOfReposScanned', 'ReposNonCompliant', 'NoOfSecretsFound', 'PercentageCompletion', 'ScanStartDate']
    scan_completion_percentage = str(int((int(as2LiteClass().read_cache('CS_NoOfReposScanned'))/int(as2LiteClass().read_cache('CS_TotalRepos')))*100)) if int(as2LiteClass().read_cache('CS_TotalRepos')) != 0 else 0
    data = [["", "Status", as2LiteClass().read_cache('CS_Status')], ["", "Total Number Of Repositories", as2LiteClass().read_cache('CS_TotalRepos')], ["", "Number of Repos scanned", as2LiteClass().read_cache('CS_NoOfReposScanned')], ["", "Number of Repos Non compliant", as2LiteClass().read_cache('CS_ReposNonCompliant')], ["", "Number of Secrets found", as2LiteClass().read_cache('CS_NoOfSecretsFound')], ["", "Percentage Completion", scan_completion_percentage], ["", "Scan start date", as2LiteClass().read_cache('CS_ScanStartDate')]]
    return {"data": data}

def previous_scan_status():
    # This function returns the previous scan status 
    # Home page status 
    print('INFO - Execute previous_scan_status function')
    stats = ['TotalRepos', 'ReposCompliant', 'ReposNonCompliant', 'NoOfSecretsFound', 'ScanStartDate', 'ScanEndDate']
    compliance_percentage = int((int(as2LiteClass().read_cache('PS_ReposCompliant'))/int(as2LiteClass().read_cache('PS_TotalRepos'))*100)) if int(as2LiteClass().read_cache('PS_TotalRepos')) != 0 else 0
    data = [["", "Total Number Of Repositories", as2LiteClass().read_cache('PS_TotalRepos')], ["", "Number of Repos compliant", as2LiteClass().read_cache('PS_ReposCompliant')], ["", "Number of Repos Non compliant", as2LiteClass().read_cache('PS_ReposNonCompliant')], ["", "Number of Secrets found", as2LiteClass().read_cache('PS_NoOfSecretsFound')], ["", "Compliance Percentage", compliance_percentage], ["", "Scan start date", as2LiteClass().read_cache('PS_ScanStartDate')], ["", "Scan end date", as2LiteClass().read_cache('PS_ScanEndDate')]]
    return {"data": data}