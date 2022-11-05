from dataclasses import dataclass
from logging import exception
import os, sys, configparser, requests, shutil, csv, json, re, redis
from datetime import datetime
from distutils.util import strtobool
from subprocess import Popen, PIPE
from datetime import datetime
from flask import request, jsonify, session
from threading import Thread
from config import gitLeaksConfig
from urllib.parse import unquote, parse_qs
from flask import send_file
from sqlalchemy.sql import text
from random import randint, randrange
from models.gitLeaksModel import gitLeaksDbHandler, gitLeaksEventsTable, gitLeaksSettingsTable
from sqlalchemy import select, update, text
from flask import current_app

import threading, glob
import queue

class as2Class:
    def __init__(self):
        # Set values from GL settings table 
        self.settingsTable = self.dbSelectOneRecord(gitLeaksSettingsTable.__tablename__, 'id=1')
        # Report file path 
        self.scanner_results_config_file_path = gitLeaksConfig.scanner_results_config_file_path
        # Variables used for scan status 
        self.no_of_secrets = {"project": {}, "repository": {}}
        self.secrets_count = []
        self.no_of_repos_scanned = []
        self.queueCheck = {}
        self.nextPageStart = 0 # get_repos pagination
        self.isLastPage = False # get_repos pagination
        # variable used in scan_all_branches fucntion
        self.branch_nextPageStart = 0 
        self.branch_isLastPage = False
        # to control worker function 
        self.end_process = False 
        # Redis cache to store scan status
        self.redis = redis.Redis(host=current_app.config["REDIS_HOST"], port=current_app.config["REDIS_PORT"], db=0)
        # Set values from GL settings table 
        try:
            self.bitbucket_host = self.settingsTable['bitbucketHost']
            self.bitbucket_base_url = "https://{}/rest/api/1.0/".format(self.bitbucket_host)
            self.limit = "?limit={}".format(self.settingsTable['bitbucketLimit'])
            self.bitbucket_auth_token = self.settingsTable['bitbucketAuthToken']
            self.bitbucket_user_name = self.settingsTable['bitbucketUserName']
            self.scan_all_repo_branches = self.settingsTable['scannerScanAllBranches']
            self.scanner_directory = os.path.join(os.path.abspath(self.settingsTable['scannerPathToDownloadRepository']), '', '')
            self.scanner_results_directory = os.path.join(os.path.abspath(self.settingsTable['scannerResultsDirectory']), '', '')
            self.slack_enable = self.settingsTable['slackEnable']
            self.slack_base_url = "https://{}/api/".format(self.settingsTable['slackHost'])
            self.slack_auth_token = self.settingsTable['slackAuthToken']
            self.slack_channel = self.settingsTable['slackChannel']
            self.slack_message = ":alert: *" + self.settingsTable['slackMessage'] + "* :alert: \n\n"
            self.gitleaks_path = self.settingsTable['gitleaksPath']
            self.jira_enable = self.settingsTable['jiraEnable']
            self.jira_host = self.settingsTable['jiraHost']
            self.jira_epic_id = self.settingsTable['jiraEpicID']
            self.jira_user_name = self.settingsTable['jiraUserName']
            self.jira_auth_token = self.settingsTable['jiraAuthToken']
        except:
            print('ERROR - as2Class_init - Failed to connect with the database')
            sys.exit()

        self.repo_url = self.bitbucket_base_url + "repos"
        self.slack_post_message_url = self.slack_base_url + "chat.postMessage"
        self.start = self.limit + "&start="
        self.bitbucket_headers = {"Authorization": "Bearer " + self.bitbucket_auth_token}
        self.slack_headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer " + self.slack_auth_token}

    def dt(self):
        # This function returns current date and time 
        print('INFO - as2Class - Execute dt function')
        dt = datetime.now()
        dt = dt.strftime('%d-%b-%Y %H:%M:%S')
        return dt

    def formatKeys(self, k):
        # This function is to remove the special characters except '-'
        return re.sub('[^A-Z-a-z0-9]+', '', k.lower())

    def dbSelectOneRecord(self, tableName, condition):
        # This function returns a record that contains all columns from a table 
        print('INFO - as2Class - Execute dbSelectOneRecord function')
        select_sql = text('select * from {} where {}'.format(tableName, condition))
        tableData = gitLeaksDbHandler.session.execute(select_sql)
        for t in tableData:
            data = dict(t)
        return data

    def dbUpdateRecord(self, tableName, condition, values):
        # This function updates a record in a table 
        print('INFO - as2Class - Execute dbUpdateRecord function')
        try:
            #gitLeaksDbHandler.session.execute(update(tableInstatnce).where(condition).values(values['data']))
            update_sql = text('update {} set {} where {}'.format(tableName, values['data'], condition))
            updateData = gitLeaksDbHandler.session.execute(update_sql)
            gitLeaksDbHandler.session.commit()
            data = {'status': 'success'}
        except Exception as e:
            print('ERROR - dbUpdateRecord - Failed to update record # {}'.format(e))
            data = {'status': 'error'}
        return data

    def get_repos(self, queryString):
        # This function returns a complete repository list 
        print('INFO - as2Class - Execute get_repos function')
        try:
            repos_output = requests.get(self.repo_url+queryString, headers = self.bitbucket_headers)
            repos_output = repos_output.json()
            self.nextPageStart = repos_output["nextPageStart"]
            self.isLastPage = repos_output["isLastPage"]
        except KeyError as e:
            #print('DEBUG - get_repos - KeyError: {}'.format(e))
            self.nextPageStart = 0
            self.isLastPage = repos_output["isLastPage"]
        except Exception as e:
            print('ERROR - get_repos - Failed to execute get_repos function - {}'.format(e))
        #print('DEBUG - get_repos - isLastPage={}, nextPageStart={}'.format(repos_output["isLastPage"], self.nextPageStart))
        return self.isLastPage, self.nextPageStart, repos_output["values"]

    def get_branches(self, queryString, project, repository):
        # This function returns branch details  
        print('INFO - as2Class - Execute get_branches function')
        branch = []
        branch_url = self.bitbucket_base_url + "projects/{}/repos/{}/branches".format(project, repository)
        try:
            branch_output = requests.get(branch_url+queryString, headers = self.bitbucket_headers)
            branch_output = branch_output.json()
            for i in range(len(branch_output["values"])):
                branch.append(branch_output["values"][i]["displayId"])
            self.branch_nextPageStart = branch_output["nextPageStart"]
            self.branch_isLastPage = branch_output["isLastPage"]
        except KeyError as e:
            self.branch_nextPageStart = 0
            self.branch_isLastPage = branch_output["isLastPage"]
        #print('DEBUG - get_branches - isLastPage={}, nextPageStart={}'.format(branch_output["isLastPage"], self.branch_nextPageStart))
        return self.branch_isLastPage, self.branch_nextPageStart, branch

    def slack_notification(self, scan_aggregated_results):
        # This function post message to the given slack channel 
        print('INFO - as2Class - Execute slack_notifications function')
        for k,v in list(scan_aggregated_results.items()):
            if v == 0:
                del scan_aggregated_results[k]
        scan_aggregated_results = str(scan_aggregated_results)
        scan_aggregated_results = scan_aggregated_results.replace('}', '')
        scan_aggregated_results = scan_aggregated_results.replace('{', '')
        scan_aggregated_results = scan_aggregated_results.replace("'", '')
        scan_aggregated_results = scan_aggregated_results.replace(', ', '\n')
        slack_message = '[{"type":"section","text":{"type":"mrkdwn","text": "' + self.slack_message + scan_aggregated_results + '"}}]'
        slack_data = {"channel": self.slack_channel, "type": "message", "blocks": slack_message}
        slack_output = requests.post(self.slack_post_message_url, headers = self.slack_headers, data = slack_data)
        #print('DEBUG - slack_notification - {}'.format(slack_output.text))

    def jira_notification(self):
        # This function attaches the scan report to the EPIC ticket
        print('INFO - as2Class - Execute jira function')
        jira_url = "https://{}/rest/api/3/issue/{}/attachments".format(self.jira_host, self.jira_epic_id)
        jira_credentials  = requests.auth.HTTPBasicAuth(self.jira_user_name, self.jira_auth_token)
        jira_headers = { 'X-Atlassian-Token': 'no-check' }
        jira_files = [ ('file', ('file.txt', open(self.scanner_results_config_file_path,'rb'), 'text/plain')) ]
        jira_output = requests.post(jira_url, auth=jira_credentials, files=jira_files, headers=jira_headers)
        #print('DEBUG - jira_notification - output: {}'.format(jira_output.text))

    def authCheck(self):
        # This function ensures Bitbucket, Slack & Jira connectivity and authentication before the settings are committed to the database 
        # And also before beginning the scan process. 
        print('INFO - as2Class - Execute authCheck function')
        bitbucket_url = "https://{}/rest/api/1.0/projects".format(self.bitbucket_host)
        bitbucket = requests.get(bitbucket_url, headers=self.bitbucket_headers)
        bitbucket_status_code = bitbucket.status_code

        # The slack auth code is set to 200, if the slack_enable setting is set to false 
        # This is to handle the auth check 
        if strtobool(self.slack_enable):
            slack_url = "https://slack.com/api/auth.test"
            slack = requests.post(slack_url, headers = self.slack_headers)
            slack_response_text = json.loads(slack.text)
            if slack_response_text['ok']:
                slack_status_code = 200
            else:
                slack_status_code = 401
        else:
            slack_status_code = 200

        # The jira auth code is set to 200, if the jira_enable setting is set to false 
        # This is to handle the auth check 
        if strtobool(self.jira_enable):
            jira_url = "https://{}/rest/api/2/project".format(self.jira_host)
            jira_credentials  = requests.auth.HTTPBasicAuth(self.jira_user_name, self.jira_auth_token)
            jira=requests.get(jira_url, auth=jira_credentials)
            jira_status_code = jira.status_code
        else:
            jira_status_code = 200

        # Execute a db query to verify the connection 
        from app import app
        with app.app_context():
            try:
                gitLeaksDbHandler.session.query(text("1")).from_statement(text("SELECT 1")).all()
                db_status_code = 200
            except Exception as e:
                print('ERROR - authCheck - error: {}'.format(e))
                db_status_code = 0

        print('INFO - authCheck - bitbucket: {}, slack: {}, jira: {}, db: {}'.format(bitbucket_status_code, slack_status_code, jira_status_code, db_status_code))
        if (bitbucket_status_code == 200 and slack_status_code == 200 and jira_status_code == 200 and db_status_code == 200):
            return True
        else:
            self.write_to_cache('CS_Status', 'Error')
            return False

    def update_ps_results(self):
        # This function writes the scan results to the cache. 
        # The home page uses PS_* cache keys 
        print('INFO - as2Class - Execute previous_scan_results function')

        # Remove the cloned repository folder 
        shutil.rmtree(self.scanner_results_config_file_path, ignore_errors=True)
        # Move the scan results to path specified in the config file 
        shutil.move(self.scanner_results_directory+'scanner_results.csv', self.scanner_results_config_file_path)

        # Set the PS status 
        totalRepos = self.redis.get('CS_TotalRepos').decode('utf-8')
        reposNonCompliant = self.redis.get('CS_ReposNonCompliant').decode('utf-8')
        self.write_to_cache('PS_TotalRepos', self.redis.get('CS_TotalRepos').decode('utf-8'))
        self.write_to_cache('PS_ReposNonCompliant', self.redis.get('CS_ReposNonCompliant').decode('utf-8'))
        self.write_to_cache('PS_ReposCompliant', str(int(totalRepos) - int(reposNonCompliant)))
        self.write_to_cache('PS_NoOfSecretsFound', self.redis.get('CS_NoOfSecretsFound').decode('utf-8'))
        self.write_to_cache('PS_ScanStartDate', self.redis.get('CS_ScanStartDate').decode('utf-8'))
        self.write_to_cache('PS_ScanEndDate', self.redis.get('CS_ScanEndDate').decode('utf-8'))
        
        # Write the scan results to the events table 
        from app import app
        with app.app_context():
            compliance_percentage = int((int(self.redis.get('PS_ReposCompliant').decode('utf-8'))/int(self.redis.get('PS_TotalRepos').decode('utf-8'))*100)) if int(self.redis.get('PS_TotalRepos').decode('utf-8')) != 0 else 0
            add_record = gitLeaksEventsTable(totalrepos=self.redis.get('PS_TotalRepos').decode('utf-8'), reposcompliant=self.redis.get('PS_ReposCompliant').decode('utf-8'), reposnoncompliant=self.redis.get('PS_ReposNonCompliant').decode('utf-8'), noofsecretsfound=self.redis.get('PS_NoOfSecretsFound').decode('utf-8'), compliancepercentage=compliance_percentage, scanstartdate=self.redis.get('PS_ScanStartDate').decode('utf-8'), scanenddate=self.redis.get('PS_ScanEndDate').decode('utf-8'))
            gitLeaksDbHandler.session.add(add_record)
            gitLeaksDbHandler.session.commit()

    def write_to_cache(self, k, v):
        # This function writes the key and value to the cache 
        self.redis.set(k, v)

    def read_cache(self, k):
        # This function retrieves the value for a given key from the cache 
        v = self.redis.get(k).decode('utf-8')
        return v

    def process_scanner_output(self, project, repository, slug, ssh, branch, scanner_results):
        # This function process the Gitleaks output 
        # Appends the Giteleaks values to a csv file 
        print('INFO - process_scanner_output - project: {}, repository: {}, branch: {}, slug: {}, ssh: {}, no_of_secrets: {}'.format(project, repository, branch, slug, ssh, scanner_results["length"]))

        # To keep track of number of secrets by project 
        # This data is used to send slack notification 
        if project in self.no_of_secrets["project"].keys():
            self.no_of_secrets["project"][project] += scanner_results["length"]
        else:
            self.no_of_secrets["project"][project] = scanner_results["length"]
        self.secrets_count.append(scanner_results["length"])

        # Write the scan results 
        with open(self.scanner_results_directory+'scanner_results.csv', 'a') as f:
            w = csv.writer(f)        
            if int(scanner_results["length"]) != 0:
                self.no_of_secrets["repository"][repository] = scanner_results["length"]
                for j in range(len(scanner_results["values"])):
                    scanner_results_dict = {"eventtime": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "project": project, "repository": repository, "slug": slug, "ssh": ssh, "branch": branch, "noOfSecrets": scanner_results["length"], "StartLine": scanner_results["values"][j]["StartLine"], "EndLine": scanner_results["values"][j]["EndLine"], "StartColumn": scanner_results["values"][j]["StartColumn"], "EndColumn": scanner_results["values"][j]["EndColumn"], "File": scanner_results["values"][j]["File"], "Author": scanner_results["values"][j]["Author"], "Email": scanner_results["values"][j]["Email"], "Date": scanner_results["values"][j]["Date"], "Message": scanner_results["values"][j]["Message"][:25]}
                    w.writerow(scanner_results_dict.values())
                    #print("DEBUG - date={}, project={}, repository={}, slug={}, ssh={}, branch={}, noOfSecrets={}, StartLine={}, EndLine={}, StartColumn={}, EndColumn={}, File={}, Author={}, Email={}, Date={}, Message={}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], project, repository, slug, ssh, branch, scan_results["length"], scan_results["values"][j]["StartLine"], scan_results["values"][j]["EndLine"], scan_results["values"][j]["StartColumn"], scan_results["values"][j]["EndColumn"], scan_results["values"][j]["File"], scan_results["values"][j]["Author"], scan_results["values"][j]["Email"], scan_results["values"][j]["Date"], scan_results["values"][j]["Message"][:25]))            
            else:
                scanner_results_dict = {"eventtime": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "project": project, "repository": repository, "slug": slug, "ssh": ssh, "branch": branch, "noOfSecrets": "0", "StartLine": "", "EndLine": "", "StartColumn": "", "EndColumn": "", "Match": "", "File": "", "Author": "", "Email": "", "Date": "", "Message": ""}
                w.writerow(scanner_results_dict.values())

        # Update number of secrets 
        self.write_to_cache('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
        # Remove the key from queueCheck
        # To identify the repositories that are not downloaded or scanned 
        del[self.queueCheck[self.formatKeys(project+'-'+repository+'-'+branch)]]
        print('INFO - process_scanner_output - Remove from queueCheck : {}'.format(self.formatKeys(project+'-'+repository+'-'+branch)))

    def scanner(self, ssh, repository, repo_directory, branch, project):
        # This function is to download the repository and performs Gitleaks scan 
        print('INFO - as2Class - Execute scanner function')
        os.chdir(self.scanner_directory)
        downloadRepo = True
        scanRepo = False
        bitbucket_user_name = self.bitbucket_user_name.replace('@', '%40')
        ssh_url = re.findall(r'(https\:\/\/)(.*)', ssh)
        git_url = ssh_url[0][0] + bitbucket_user_name + ':' + self.bitbucket_auth_token + '@' + ssh_url[0][1]

        while downloadRepo:
            # The temp directory creation is to handle the repositories with the same name 
            temp_dir = str(randrange(100000, 999999))+'_'+repo_directory+'/'
            git_clone = Popen(['git', 'clone', '--single-branch', '--branch', branch, git_url, temp_dir], stdout=PIPE, stderr=PIPE)
            git_clone_stdout, git_clone_stderr = git_clone.communicate()
            # Temp directory gets created if the path exists -> set the scanRepo to true to move on 
            # If not, failed to download the repository -> set the scanRepo to false
            # queueCheck keeps track of the failed jobs 
            if os.path.exists(self.scanner_directory+temp_dir):
                downloadRepo = False
                scanRepo = True
                dirContent = glob.glob(self.scanner_directory+temp_dir+'/*')
                #print("DEBUG - scanner - repository: {}, branch: {}, output: {}, console_output: {}, downloadRepo: {}, scanRepo: {}, dirFileCount: {}".format(repository, branch, str(git_clone_stdout), str(git_clone_stderr), downloadRepo, scanRepo, len(dirContent)))
            elif 'Could not find remote branch' in git_clone_stderr.decode('utf-8'):
                print("INFO - scanner - repository: {}, branch: {}, output: {}, console_output: {}, message: Repo or branch not found".format(repository, branch, str(git_clone_stdout), str(git_clone_stderr)))
                downloadRepo = False
                scanRepo = False
            else:
                downloadRepo = True
                scanRepo = False
                dirContent = []

        if scanRepo and len(dirContent) > 0:
            scanner = Popen([self.gitleaks_path, 'detect', '--source', temp_dir, '-v', '--log-opts='+branch], stdout=PIPE, stderr=PIPE)
            scanner_stdout, scanner_stderr = scanner.communicate()
            scanner_stdout = scanner_stdout.decode('UTF-8')
            scanner_stdout = scanner_stdout.replace('\n', '')
            scanner_stdout = scanner_stdout.replace('\t', '')
            scanner_parsed_data = re.findall(r'(.*?)\"\}', scanner_stdout)
            scanner_output = []
            # Removes the temp directory and its contents 
            shutil.rmtree(self.scanner_directory+temp_dir, ignore_errors=True)
            if len(scanner_parsed_data) != 0:
                for j in range(len(scanner_parsed_data)):
                    try:
                        scanner_output.append(json.loads(scanner_parsed_data[j] + '"}'))
                    except:
                        continue

            #print('DEBUG - {} {} {} {}'.format(repository, branch, git_clone_stdout, scan_parsed_data))
            # Execute process_scanner_output function 
            scanner_results = {"length": len(scanner_parsed_data), "branch": branch, "values": scanner_output}
            self.process_scanner_output(project, repository, repo_directory, ssh, branch, scanner_results)
        else:
            print('ERROR - scanner - Failed to download repository {}'.format(repository))
            return {'data': 'error'}

    def scan_master_branch(self, repos):
        # This function retrieves jobs from the queue and calls scanner function for further processing
        # It scans only master branch
        branch = "master"
        try:
            work = queue.Queue()
            threads = []
            def worker():
                while not self.end_process:
                    print('INFO - scan_master_branch - QueueSize: {}, ThreadCount: {}'.format(work.qsize(), threading.active_count()))
                    jobs = work.get(True, 5)
                    print('INFO - scan_master_branch - Added to Queue : {}'.format(self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+branch)))
                    self.queueCheck[self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+branch)] = True
                    
                    try:
                        for j in range(len(jobs["links"]["clone"])):
                            if jobs["links"]["clone"][j]["name"] == "http":
                                self.scanner(jobs["links"]["clone"][j]["href"], jobs["name"], jobs["slug"], "master", jobs["project"]["name"])
                                self.no_of_repos_scanned.append(1)
                                self.write_to_cache('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
                                self.write_to_cache('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
                                self.write_to_cache('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))
                    except queue.Empty:
                        print('INFO - scan_master_branch - Empty queue')

                    work.task_done()

            # assign a jobs to worker Queue
            if repos:
                for i in range(len(repos)):
                    work.put(repos[i])
            
            # append the worker Queue jobs to thread
            for unused_index in range(int(gitLeaksConfig.thread_count)):
                thread = threading.Thread(target=worker)
                thread.daemon = True
                thread.start()
                threads.append(thread)

            for thread in threads:
                if thread.is_alive():
                    thread.join()

        except Exception as err:
            print('INFO - scan_master_branch - Queue init error {}'.format(err))
            self.end_process = True
            for thread in threads:
                if thread.is_alive():
                    thread.join()

    def scan_all_branches(self, repos):
        # This function retrieves jobs from the queue and calls scanner function for further processing
        # It scans all branches 

        try:
            work = queue.Queue()
            threads = []
            def worker():
                branches = []
                while not self.end_process:
                    print('INFO - scan_all_branches - QueueSize: {}, ThreadCount: {}'.format(work.qsize(), threading.active_count()))
                    jobs = work.get(True, 5)

                    try:
                        for j in range(len(jobs["links"]["clone"])):
                            if jobs["links"]["clone"][j]["name"] == "http":
                                # Get branch details for each repository 
                                while(not self.branch_isLastPage):
                                    try:
                                        self.branch_isLastPage, self.branch_nextPageStart, branch = self.get_branches(self.start + str(self.branch_nextPageStart), jobs["project"]["name"], jobs["name"])
                                        branches = branches + branch
                                    except KeyError as e:
                                        print('ERROR - scan_all_branches - isLastPage: {}, error: {}'.format(self.branch_isLastPage, e))
                                        self.branch_isLastPage = True
                                for b in branches:
                                    #print('DEBUG - scan_all_branches repository: {}, branch: {}'.format(jobs["name"], branch))
                                    print('INFO - scan_all_branches - Add to Queue : {}'.format(self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+b)))
                                    # Remove the special characters - ''.join(e for e in branch if e.isalnum())
                                    self.queueCheck[self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+b)] = True
                                    self.scanner(jobs["links"]["clone"][j]["href"], jobs["name"], jobs["slug"], b, jobs["project"]["name"])

                        # Write CS status to cache 
                        self.no_of_repos_scanned.append(1)
                        self.write_to_cache('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
                        self.write_to_cache('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
                        self.write_to_cache('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))
                    except queue.Empty:
                        print('INFO - scan_all_branches - Empty queue')

                    work.task_done()

            # assign a jobs to worker Queue
            if repos:
                for i in range(len(repos)):
                    work.put(repos[i])
            
            # append the worker Queue jobs to thread
            for unused_index in range(int(gitLeaksConfig.thread_count)):
                thread = threading.Thread(target=worker)
                thread.daemon = True
                thread.start()
                threads.append(thread)

            for thread in threads:
                if thread.is_alive():
                    thread.join()

        except Exception as err:
            print('INFO - scan_all_branches - Queue init error : {}'.format(err))
            self.end_process = True
            for thread in threads:
                if thread.is_alive():
                    thread.join()

    def scan_engine(self):
        # This function initialize the scan 
        # Executes Jira and Slack notification function once the scan is complete 
        print('INFO - as2Class - Execute scan_engine function')
        if self.redis.get('CS_Status').decode('utf-8') == 'In Progress':
            print('INFO - scan_engine - Scan is in progress')
            return None
        else:
            self.write_to_cache('CS_Status', 'In Progress')
            self.write_to_cache('CS_TotalRepos', '0')
            self.write_to_cache('CS_NoOfReposScanned', '0')
            self.write_to_cache('CS_ReposNonCompliant', '0')
            self.write_to_cache('CS_NoOfSecretsFound', '0')
            self.write_to_cache('CS_PercentageCompletion', '0')
            self.write_to_cache('CS_ScanStartDate', '-')
            self.write_to_cache('CS_ScanEndDate', '-')
            repos = []

            if not self.authCheck():
                print('ERROR - scan_engine - Authentication failure')
                return

            # Set the CS status to In progress 
            self.write_to_cache('CS_Status', 'In Progress')

            if not (os.path.exists(self.scanner_directory) and os.path.exists(self.scanner_results_directory)):
                print('ERROR - scan_engine - Directory not found')
                sys.exit()

            # Write column names 
            with open(self.scanner_results_directory+'scanner_results.csv', 'w+') as f:
                w = csv.writer(f)
                scan_results_dict = {"eventtime": "", "project": "", "repository": "", "slug": "", "ssh": "", "branch": "", "noOfSecrets": "", "StartLine": "", "EndLine": "", "StartColumn": "", "EndColumn": "", "File": "", "Author": "", "Email": "", "Date": "", "Message": ""}
                w.writerow(scan_results_dict.keys())

            scanStartDate = self.dt()
            # Set the CS start date 
            self.write_to_cache('CS_ScanStartDate', scanStartDate)

            #print("DEBUG - scan_engine - isLastPage={}, nextPageStart={}, repoLen={}".format(repo_isLastPage, repo_nextPageStart, str(len(repos))))

            # isLastPage is to handle the pagination 
            while(not self.isLastPage):
                try:
                    self.isLastPage, self.nextPageStart, repo = self.get_repos(self.start + str(self.nextPageStart))
                    repos = repos + repo
                    #print("DEBUG - isLastPage={}, nextPageStart={}, repoLen={}".format(repo_isLastPage, repo_nextPageStart, str(len(repos))))
                except KeyError as e:
                    print('ERROR - scan_engine - isLastPage: {}, error: {}'.format(self.isLastPage, e))
                    self.isLastPage = True

            # Set the CS total repo count 
            self.write_to_cache('CS_TotalRepos', str(len(repos)))

            if not strtobool(self.scan_all_repo_branches):
                self.scan_master_branch(repos)
            else:
                self.scan_all_branches(repos)

            print('INFO - scan_engine - Scan complete')

            scanEndDate = self.dt()
            self.write_to_cache('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
            self.write_to_cache('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))      
            self.write_to_cache('CS_ScanEndDate', scanEndDate)
            self.write_to_cache('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
            self.write_to_cache('CS_Status', 'Completed')
            self.update_ps_results()

            # Any repositories that are failed to download or scan will be printed 
            if bool(self.queueCheck):
                print('ERROR - Failed to download or scan the following reposirories {}'.format(self.queueCheck))
            
            # Upload scan reults to JIRA EPIC ticket if the settings is set to true
            if strtobool(self.jira_enable):
                self.jira_notification()
            
            # Send the notification to slack if the settings is set to true
            if strtobool(self.slack_enable):
                self.slack_notification(self.no_of_secrets["project"])

# This is a lite weight class to minimize the DB calls and varaiable processing 
class as2LiteClass:
    def __init__(self):
        # Redis cache to store scan status
        self.redis = redis.Redis(host=current_app.config["REDIS_HOST"], port=current_app.config["REDIS_PORT"], db=0)

    def dt(self):
        # This function returns current date and time 
        print('INFO - dt - Execute dt function')
        dt = datetime.now()
        dt = dt.strftime('%d-%b-%Y %H:%M:%S')
        return dt

    def write_to_cache(self, k, v):
        # This function writes the key and value to the cache 
        self.redis.set(k, v)

    def read_cache(self, k):
        # This function retrieves the value for a given key from the cache 
        v = self.redis.get(k).decode('utf-8')
        return v

    def authCheck(self, bitbucket_host, bitbucket_auth_token, slack_enable, slack_auth_token, jira_enable, jira_host, jira_user_name, jira_auth_token):
        # This function ensures Bitbucket, Slack & Jira connectivity and authentication before the settings are committed to the database 
        # And also before beginning the scan process. 
        print('INFO - authCheck - Execute authCheck function')
        bitbucket_url = "https://{}/rest/api/1.0/projects".format(bitbucket_host)
        bitbucket_headers = {"Authorization": "Bearer " + bitbucket_auth_token}
        bitbucket = requests.get(bitbucket_url, headers=bitbucket_headers)
        bitbucket_status_code = bitbucket.status_code

        # The slack auth code is set to 200, if the slack_enable setting is set to false 
        # This is to handle the auth check 
        if strtobool(slack_enable):
            slack_url = "https://slack.com/api/auth.test"
            slack_headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer " + slack_auth_token}
            slack = requests.post(slack_url, headers = slack_headers)
            slack_response_text = json.loads(slack.text)
            if slack_response_text['ok']:
                slack_status_code = 200
            else:
                slack_status_code = 401
        else:
            slack_status_code = 200

        # The jira auth code is set to 200, if the jira_enable setting is set to false 
        # This is to handle the auth check 
        if strtobool(jira_enable):
            jira_url = "https://{}/rest/api/2/project".format(jira_host)
            jira_credentials  = requests.auth.HTTPBasicAuth(jira_user_name, jira_auth_token)
            jira=requests.get(jira_url, auth=jira_credentials)
            jira_status_code = jira.status_code
        else:
            jira_status_code = 200

        # Execute a db query to verify the connection 
        from app import app
        with app.app_context():
            try:
                gitLeaksDbHandler.session.query(text("1")).from_statement(text("SELECT 1")).all()
                db_status_code = 200
            except Exception as e:
                print('Error dbcheck={}'.format(e))
                db_status_code = 0

        print('INFO - authCheck - Bitbucket: {}, Slack: {}, Jira: {}, DB: {}'.format(bitbucket_status_code, slack_status_code, jira_status_code, db_status_code))
        if (bitbucket_status_code == 200 and slack_status_code == 200 and jira_status_code == 200 and db_status_code == 200):
            return True
        else:
            return False