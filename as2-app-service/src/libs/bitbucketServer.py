import re, sys, requests
from datetime import datetime
from models.gitLeaksModel import gitLeaksDbHandler, gitLeaksEventsTable, gitLeaksSettingsTable
from sqlalchemy import select, update, text

class BitbucketServer():
    def __init__(self):
        # Set values from GL settings table 
        self.settingsTable = self.dbSelectOneRecord(gitLeaksSettingsTable.__tablename__, 'id=1')
        # Bitbucket server get_repos variables 
        self.nextPageStart = 0 # get_repos pagination
        self.isLastPage = False # get_repos pagination
        # variable used in scan_all_branches fucntion
        self.branch_nextPageStart = 0 
        self.branch_isLastPage = False
        # to control worker function 
        self.end_process = False 
        # Set values from GL settings table 
        try:
            self.bitbucket_host = self.settingsTable['bitbucketHost']
            self.bitbucket_base_url = "https://{}/rest/api/1.0/".format(self.bitbucket_host)
            self.limit = "?limit={}".format(self.settingsTable['bitbucketLimit'])
            self.bitbucket_auth_token = self.settingsTable['bitbucketAuthToken']
            self.bitbucket_user_name = self.settingsTable['bitbucketUserName']
        except:
            print('ERROR - BitbucketServer_init - Failed to connect with the database')
            sys.exit()

        self.repo_url = self.bitbucket_base_url + "repos"
        self.start = self.limit + "&start="
        self.bitbucket_headers = {"Authorization": "Bearer " + self.bitbucket_auth_token}
        # Commit details
        self.latest_commit_details = {}

    def dbSelectOneRecord(self, tableName, condition):
        # This function returns a record that contains all columns from a table 
        print('INFO - BitbucketServer - Execute dbSelectOneRecord function')
        select_sql = text('select * from {} where {}'.format(tableName, condition))
        from app import app
        with app.app_context():
            tableData = gitLeaksDbHandler.session.execute(select_sql)
        for t in tableData:
            data = dict(t)
        return data

    def get_repos(self):
        # This function returns a complete repository list 
        print('INFO - BitbucketServer - Execute get_repos function')
        repos = []
        while(not self.isLastPage):
            queryString = self.start + str(self.nextPageStart)
            try:
                repos_output = requests.get(self.repo_url+queryString, headers = self.bitbucket_headers)
                repos_output = repos_output.json()
                repos = repos + repos_output["values"]
                self.isLastPage = repos_output["isLastPage"]
                self.nextPageStart = repos_output["nextPageStart"]
                #print("DEBUG - isLastPage={}, nextPageStart={}, repoLen={}".format(self.isLastPage, self.nextPageStart, str(len(repos))))
            except KeyError as e:
                #print('DEBUG - get_repos - isLastPage: {}, error: {}'.format(self.isLastPage, e))
                self.isLastPage = repos_output["isLastPage"]
                self.nextPageStart = 0
            except Exception as e:
                print('ERROR - get_repos - Failed to execute get_repos function - {}'.format(e))
        return repos

    def get_branches(self, project, repository):
        # This function returns branch details  
        print('INFO - BitbucketServer - Execute get_branches function')
        branches = []
        branch_url = self.bitbucket_base_url + "projects/{}/repos/{}/branches".format(project, repository)
        while(not self.branch_isLastPage):
            queryString = self.start + str(self.branch_nextPageStart)
            try:
                branch_output = requests.get(branch_url+queryString, headers = self.bitbucket_headers)
                branch_output = branch_output.json()
                for i in range(len(branch_output["values"])):
                    branches.append(branch_output["values"][i]["displayId"])
                self.branch_isLastPage = branch_output["isLastPage"]
                self.branch_nextPageStart = branch_output["nextPageStart"]
            except KeyError as e:
                #print('DEBUG - get_branches - isLastPage: {}, error: {}'.format(self.branch_isLastPage, e))
                self.branch_isLastPage = True
                self.branch_nextPageStart = 0
        return branches

    def get_latest_commit_details(self, project, repo):
        # This function captures latest commit details 
        print('INFO - BitbucketServer - Execute get_latest_commit_details function')
        try:
            commit_url = 'projects/{}/repos/{}/commits?limit=1'.format(project, repo)
            commit_output = requests.get(self.bitbucket_base_url + commit_url, headers = self.bitbucket_headers)
            commit_output = commit_output.json()
            #self.latest_commit_details[self.formatKeys(project+'-'+repo)] = {'committer_name': commit_output['values'][0]['committer']['name'], 'committer_email': commit_output['values'][0]['committer']['emailAddress'], 'committer_message': commit_output['values'][0]['message'], 'committer_timestamp': committer_timestamp}
            committer_name = commit_output['values'][0]['committer']['name']
            committer_email = commit_output['values'][0]['committer']['emailAddress']
            committer_message = commit_output['values'][0]['message']
            committer_timestamp = datetime.fromtimestamp(commit_output['values'][0]['committerTimestamp'] / 1000)
            committer_timestamp = datetime.strftime(committer_timestamp, '%d-%b-%Y %H:%M:%S')
        except Exception as e:
            print('ERROR - get_latest_commit_details - Error: {}'.format(e))
            committer_name = 'error'
            committer_email = 'error'
            committer_message = 'error'
            committer_timestamp = 'error'
        return {'committer_name': committer_name, 'committer_email': committer_email, 'committer_message': committer_message, 'committer_timestamp': committer_timestamp}

    def formatKeys(self, k):
        # This function is to remove the special characters except '-'
        return re.sub('[^A-Z-a-z0-9]+', '', k.lower())