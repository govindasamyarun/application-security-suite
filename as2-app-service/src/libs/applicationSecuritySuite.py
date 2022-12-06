import os, sys, shutil, csv, re
import threading, queue
from datetime import datetime
from distutils.util import strtobool
from datetime import datetime
from config import GitleaksConfig
from models.as2 import as2DbHandler, ComplianceTable, SettingsTable
from models.gitleaks import gitleaksDbHandler, gitleaksScanResultsTable
from models.bitbucketServer import bitbucketServerDbHandler, bitbucketServerScanResultsTable
from libs.downloadRepository import DownloadRepository
from libs.gitleaks import Gitleaks
from libs.bitbucketServer import BitbucketServer
from libs.dbOperations import DBOperations
from libs.notifications import Jira, Slack
from libs.cache import Cache

class AS2:
    def __init__(self):
        # Set values from GL settings table 
        self.settingsTable = DBOperations().selectOneRecord(SettingsTable.__tablename__, 'id=1')
        # Report file path 
        self.scanner_results_config_file_path = GitleaksConfig.scanner_results_config_file_path
        # Variables used for scan status 
        self.no_of_secrets = {"project": {}, "repository": {}}
        self.secrets_count = []
        self.no_of_repos_scanned = []
        self.queueCheck = {}

        # to control worker function 
        self.end_process = False 

        # Set values from GL settings table 
        try:
            # Bitbucket variables
            self.bitbucket_host = self.settingsTable['bitbucketHost']
            self.limit = str(self.settingsTable['bitbucketLimit'])
            self.bitbucket_auth_token = self.settingsTable['bitbucketAuthToken']
            self.bitbucket_user_name = self.settingsTable['bitbucketUserName']
            self.scan_all_repo_branches = self.settingsTable['scannerScanAllBranches']
            # Scanner variables 
            self.scanner_directory = os.path.join(os.path.abspath(self.settingsTable['scannerPathToDownloadRepository']), '', '')
            self.scanner_results_directory = os.path.join(os.path.abspath(self.settingsTable['scannerResultsDirectory']), '', '')
            # Slack variables 
            self.slack_enable = self.settingsTable['slackEnable']
            self.slack_host = self.settingsTable['slackHost']
            self.slack_auth_token = self.settingsTable['slackAuthToken']
            self.slack_channel = self.settingsTable['slackChannel']
            self.slack_message = self.settingsTable['slackMessage']
            # Jira variables
            self.jira_enable = self.settingsTable['jiraEnable']
            self.jira_host = self.settingsTable['jiraHost']
            self.jira_epic_id = self.settingsTable['jiraEpicID']
            self.jira_user_name = self.settingsTable['jiraUserName']
            self.jira_auth_token = self.settingsTable['jiraAuthToken']
            # Gitleaks variable
            self.gitleaks_path = self.settingsTable['gitleaksPath']
        except:
            print('ERROR - as2Class_init - Failed to connect with the database')
            sys.exit()

        # Commit details
        self.latest_commit_details = {}
        # Create objects
        self.BitbucketServer = BitbucketServer(self.bitbucket_host, self.bitbucket_user_name, self.bitbucket_auth_token, self.limit)
        self.Cache = Cache()

    def dt(self):
        # This function returns current date and time 
        print('INFO - as2Class - Execute dt function')
        dt = datetime.now()
        dt = dt.strftime('%d-%b-%Y %H:%M:%S')
        return dt

    def formatKeys(self, k):
        # This function is to remove the special characters except '-'
        return re.sub('[^A-Z-a-z0-9]+', '', k.lower())

    def update_ps_results(self):
        # This function writes the scan results to the cache. 
        # The home page uses PS_* cache keys 
        print('INFO - as2Class - Execute previous_scan_results function')

        # Remove the cloned repository folder 
        shutil.rmtree(self.scanner_results_config_file_path, ignore_errors=True)
        # Move the scan results to path specified in the config file 
        shutil.move(self.scanner_results_directory+'scanner_results.csv', self.scanner_results_config_file_path)

        # Set the PS status 
        totalRepos = self.Cache.read('CS_TotalRepos')
        reposNonCompliant = self.Cache.read('CS_ReposNonCompliant')
        self.Cache.write('PS_TotalRepos', self.Cache.read('CS_TotalRepos'))
        self.Cache.write('PS_ReposNonCompliant', self.Cache.read('CS_ReposNonCompliant'))
        self.Cache.write('PS_ReposCompliant', str(int(totalRepos) - int(reposNonCompliant)))
        self.Cache.write('PS_NoOfSecretsFound', self.Cache.read('CS_NoOfSecretsFound'))
        self.Cache.write('PS_ScanStartDate', self.Cache.read('CS_ScanStartDate'))
        self.Cache.write('PS_ScanEndDate', self.Cache.read('CS_ScanEndDate'))
        
        # Write the scan results to the events table 
        from app import app
        with app.app_context():
            compliance_percentage = int((int(self.Cache.read('PS_ReposCompliant'))/int(self.Cache.read('PS_TotalRepos'))*100)) if int(self.Cache.read('PS_TotalRepos')) != 0 else 0
            add_record = ComplianceTable(totalrepos=self.Cache.read('PS_TotalRepos'), reposcompliant=self.Cache.read('PS_ReposCompliant'), reposnoncompliant=self.Cache.read('PS_ReposNonCompliant'), noofsecretsfound=self.Cache.read('PS_NoOfSecretsFound'), compliancepercentage=compliance_percentage, scanstartdate=self.Cache.read('PS_ScanStartDate'), scanenddate=self.Cache.read('PS_ScanEndDate'))
            as2DbHandler.session.add(add_record)
            as2DbHandler.session.commit()

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

        # Add to ScanResultsTable
        # project, repository, secretscount, lastcommitdate, lastcommitname, lastcommitemail, eventtime
        #insert_data = (project, repository, scanner_results["length"], self.latest_commit_details[committer_key]['committer_timestamp'], self.latest_commit_details[committer_key]['committer_name'], self.latest_commit_details[committer_key]['committer_email'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        gitleaks_upsert_data = (project, repository, scanner_results["length"], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        DBOperations().gitleaksUpsertRecord(gitleaksDbHandler, gitleaksScanResultsTable.__tablename__, gitleaks_upsert_data)

        # Write the scan results 
        with open(self.scanner_results_directory+'scanner_results.csv', 'a') as f:
            w = csv.writer(f)
            committer_key = self.formatKeys(project+'-'+repository)
            if int(scanner_results["length"]) != 0:
                self.no_of_secrets["repository"][repository] = scanner_results["length"]
                for j in range(len(scanner_results["values"])):
                    scanner_results_dict = {"eventtime": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "project": project, "repository": repository, "slug": slug, "ssh": ssh, "branch": branch, "noOfSecrets": scanner_results["length"], "StartLine": scanner_results["values"][j]["StartLine"], "EndLine": scanner_results["values"][j]["EndLine"], "StartColumn": scanner_results["values"][j]["StartColumn"], "EndColumn": scanner_results["values"][j]["EndColumn"], "File": scanner_results["values"][j]["File"], "Author": scanner_results["values"][j]["Author"], "Email": scanner_results["values"][j]["Email"], "Date": scanner_results["values"][j]["Date"], "Message": scanner_results["values"][j]["Message"][:25], "Committer Timestamp": self.latest_commit_details[committer_key]['committer_timestamp'], "Committer Name": self.latest_commit_details[committer_key]['committer_name'], "Committer email": self.latest_commit_details[committer_key]['committer_email'], "Committer Message": self.latest_commit_details[committer_key]['committer_message']}
                    w.writerow(scanner_results_dict.values())
                    #print("DEBUG - date={}, project={}, repository={}, slug={}, ssh={}, branch={}, noOfSecrets={}, StartLine={}, EndLine={}, StartColumn={}, EndColumn={}, File={}, Author={}, Email={}, Date={}, Message={}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], project, repository, slug, ssh, branch, scan_results["length"], scan_results["values"][j]["StartLine"], scan_results["values"][j]["EndLine"], scan_results["values"][j]["StartColumn"], scan_results["values"][j]["EndColumn"], scan_results["values"][j]["File"], scan_results["values"][j]["Author"], scan_results["values"][j]["Email"], scan_results["values"][j]["Date"], scan_results["values"][j]["Message"][:25]))
            else:
                scanner_results_dict = {"eventtime": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "project": project, "repository": repository, "slug": slug, "ssh": ssh, "branch": branch, "noOfSecrets": "0", "StartLine": "", "EndLine": "", "StartColumn": "", "EndColumn": "", "File": "", "Author": "", "Email": "", "Date": "", "Message": "", "Committer Timestamp": self.latest_commit_details[committer_key]['committer_timestamp'], "Committer Name": self.latest_commit_details[committer_key]['committer_name'], "Committer email": self.latest_commit_details[committer_key]['committer_email'], "Committer Message": self.latest_commit_details[committer_key]['committer_message']}
                w.writerow(scanner_results_dict.values())

        # Update number of secrets 
        self.Cache.write('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
        # Remove the key from queueCheck
        # To identify the repositories that are not downloaded or scanned 
        del[self.queueCheck[self.formatKeys(project+'-'+repository+'-'+branch)]]
        print('INFO - process_scanner_output - Remove from queueCheck : {}'.format(self.formatKeys(project+'-'+repository+'-'+branch)))
        return {}

    def scanner(self, ssh, repository, repo_directory, branch, project):
        # This function is to download the repository and performs Gitleaks scan 
        print('INFO - as2Class - Execute scanner function')

        download = DownloadRepository(self.bitbucket_user_name, self.bitbucket_auth_token, ssh, repo_directory, repository, branch, self.scanner_directory).download()

        if download['downloadRepoComplete'] and download['no_of_directories']:
            gl_scan_results = Gitleaks(self.gitleaks_path, self.scanner_directory, branch, download['temp_dir']).scan()
            self.process_scanner_output(project, repository, repo_directory, ssh, branch, gl_scan_results)
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
                                #self.scanner(jobs["links"]["clone"][j]["href"], jobs["name"], jobs["slug"], "master", jobs["project"]["name"])
                                downloadResults = DownloadRepository(self.bitbucket_user_name, self.bitbucket_auth_token, jobs["links"]["clone"][j]["href"], jobs["slug"], jobs["name"], branch, self.scanner_directory).download()
                                if downloadResults['downloadRepoComplete'] and downloadResults['no_of_directories']:
                                    gl_scan_results = Gitleaks(self.gitleaks_path, self.scanner_directory, branch, downloadResults['temp_dir']).scan()
                                    self.no_of_repos_scanned.append(1)
                                    self.process_scanner_output(jobs["project"]["name"], jobs["name"], jobs["slug"], jobs["links"]["clone"][j]["href"], branch, gl_scan_results)
                                    self.Cache.write('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
                                    self.Cache.write('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
                                    self.Cache.write('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))
                                else:
                                    print('ERROR - scanner - Failed to download repository {}'.format(jobs["name"]))
                                    return {'data': 'error'}
                    except queue.Empty:
                        print('INFO - scan_master_branch - Empty queue')

                    work.task_done()

            # assign a jobs to worker Queue
            if repos:
                for i in range(len(repos)):
                    work.put(repos[i])
            
            # append the worker Queue jobs to thread
            for unused_index in range(int(GitleaksConfig.thread_count)):
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
                while not self.end_process:
                    print('INFO - scan_all_branches - QueueSize: {}, ThreadCount: {}'.format(work.qsize(), threading.active_count()))
                    jobs = work.get(True, 5)

                    try:
                        for j in range(len(jobs["links"]["clone"])):
                            if jobs["links"]["clone"][j]["name"] == "http":
                                # Get branch details for each repository 
                                branches = self.BitbucketServer.get_branches(jobs["project"]["name"], jobs["name"])
                                
                                for branch in branches:
                                    #print('DEBUG - scan_all_branches repository: {}, branch: {}'.format(jobs["name"], branch))
                                    print('INFO - scan_all_branches - Add to Queue : {}'.format(self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+branch)))
                                    # Remove the special characters - ''.join(e for e in branch if e.isalnum())
                                    self.queueCheck[self.formatKeys(jobs["project"]["name"]+'-'+jobs['name']+'-'+branch)] = True
                                    #self.scanner(jobs["links"]["clone"][j]["href"], jobs["name"], jobs["slug"], b, jobs["project"]["name"])
                                    downloadResults = DownloadRepository(self.bitbucket_user_name, self.bitbucket_auth_token, jobs["links"]["clone"][j]["href"], jobs["slug"], jobs["name"], branch, self.scanner_directory).download()
                                    if downloadResults['downloadRepoComplete'] and downloadResults['no_of_directories']:
                                        gl_scan_results = Gitleaks(self.gitleaks_path, self.scanner_directory, branch, downloadResults['temp_dir']).scan()
                                        self.process_scanner_output(jobs["project"]["name"], jobs["name"], jobs["slug"], jobs["links"]["clone"][j]["href"], branch, gl_scan_results)
                                        self.Cache.write('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
                                        self.Cache.write('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))
                                    else:
                                        print('ERROR - scanner - Failed to download repository {}'.format(jobs["name"]))
                                        return {'data': 'error'}

                        # Write CS status to cache 
                        self.no_of_repos_scanned.append(1)
                        self.Cache.write('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
                    except queue.Empty:
                        print('INFO - scan_all_branches - Empty queue')

                    work.task_done()

            # assign a jobs to worker Queue
            if repos:
                for i in range(len(repos)):
                    work.put(repos[i])
            
            # append the worker Queue jobs to thread
            for unused_index in range(int(GitleaksConfig.thread_count)):
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
        if self.Cache.read('CS_Status') == 'In Progress':
            print('INFO - scan_engine - Scan is in progress')
            return None
        else:
            self.Cache.write('CS_Status', 'In Progress')
            self.Cache.write('CS_TotalRepos', '0')
            self.Cache.write('CS_NoOfReposScanned', '0')
            self.Cache.write('CS_ReposNonCompliant', '0')
            self.Cache.write('CS_NoOfSecretsFound', '0')
            self.Cache.write('CS_PercentageCompletion', '0')
            self.Cache.write('CS_ScanStartDate', '-')
            self.Cache.write('CS_ScanEndDate', '-')
            repos = []

            # Check bitbucket, db, jira & slack auth 
            bitbucket_status_code = BitbucketServer(self.bitbucket_host, self.bitbucket_user_name, self.bitbucket_auth_token, self.limit).auth()
            db_status_code = DBOperations().auth()
            jira_status_code = Jira(self.jira_host, self.jira_user_name, self.jira_auth_token, self.jira_enable).auth()
            slack_status_code = Slack(self.slack_host, self.slack_auth_token, self.slack_enable).auth()
            if bitbucket_status_code != 200 or db_status_code != 200 or jira_status_code != 200 or slack_status_code != 200:
                print('ERROR - scan_engine - Authentication failure Bitbucket: {}, DB: {}, JIRA: {}, Slack: {}'.format(bitbucket_status_code, db_status_code, jira_status_code, slack_status_code))
                return

            # Set the CS status to In progress 
            self.Cache.write('CS_Status', 'In Progress')

            if not (os.path.exists(self.scanner_directory) and os.path.exists(self.scanner_results_directory)):
                print('ERROR - scan_engine - Directory not found')
                sys.exit()

            # Write column names 
            with open(self.scanner_results_directory+'scanner_results.csv', 'w+') as f:
                w = csv.writer(f)
                scan_results_dict = {"eventtime": "", "project": "", "repository": "", "slug": "", "ssh": "", "branch": "", "noOfSecrets": "", "StartLine": "", "EndLine": "", "StartColumn": "", "EndColumn": "", "File": "", "Author": "", "Email": "", "Date": "", "Message": "", "Committer Timestamp": "", "Committer Name": "", "Committer email": "", "Committer Message": ""}
                w.writerow(scan_results_dict.keys())

            scanStartDate = self.dt()
            # Set the CS start date 
            self.Cache.write('CS_ScanStartDate', scanStartDate)

            #print("DEBUG - scan_engine - isLastPage={}, nextPageStart={}, repoLen={}".format(repo_isLastPage, repo_nextPageStart, str(len(repos))))

            # Get list of repositories 
            repos = self.BitbucketServer.get_repos()

            # Set the CS total repo count 
            self.Cache.write('CS_TotalRepos', str(len(repos)))

            # Debug
            #repos = repos[:10] # Debug repo 

            # Get last commit details 
            for repo in repos:
                committer_key = self.formatKeys(repo["project"]["name"]+'-'+repo["name"])
                self.latest_commit_details[committer_key] = self.BitbucketServer.get_latest_commit_details(repo["project"]["name"], repo["name"])
                bitbucketserver_upsert_data = (repo["project"]["name"], repo["name"], self.latest_commit_details[committer_key]['committer_timestamp'], self.latest_commit_details[committer_key]['committer_name'], self.latest_commit_details[committer_key]['committer_email'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                DBOperations().bitbucketServerUpsertRecord(bitbucketServerDbHandler, bitbucketServerScanResultsTable.__tablename__, bitbucketserver_upsert_data)

            if not strtobool(self.scan_all_repo_branches):
                self.scan_master_branch(repos)
            else:
                self.scan_all_branches(repos)

            print('INFO - scan_engine - Scan complete')

            scanEndDate = self.dt()
            self.Cache.write('CS_NoOfSecretsFound', str(sum(self.secrets_count)))
            self.Cache.write('CS_ReposNonCompliant', str(len(self.no_of_secrets["repository"].keys())))      
            self.Cache.write('CS_ScanEndDate', scanEndDate)
            self.Cache.write('CS_NoOfReposScanned', str(sum(self.no_of_repos_scanned)))
            self.Cache.write('CS_Status', 'Completed')
            self.update_ps_results()

            # Any repositories that are failed to download or scan will be printed 
            if bool(self.queueCheck):
                print('ERROR - Failed to download or scan the following reposirories {}'.format(self.queueCheck))
            
            # Upload scan reults to JIRA EPIC ticket if the settings is set to true
            Jira(self.jira_host, self.jira_user_name, self.jira_auth_token, self.jira_enable).send_notification(self.jira_epic_id)
            
            # Send the notification to slack if the settings is set to true
            Slack(self.slack_host, self.slack_auth_token, self.slack_enable).send_notification(self.slack_channel, self.slack_message, self.no_of_secrets["project"])