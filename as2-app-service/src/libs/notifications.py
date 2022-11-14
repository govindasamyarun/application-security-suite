import requests, json
from distutils.util import strtobool
from config import GitleaksConfig

class Jira():
    def __init__(self, host_name, user_name, auth_token, enable):
        self.jira_host = host_name
        self.jira_user_name = user_name
        self.jira_auth_token = auth_token
        self.jira_enable = enable

    def auth(self):
        # Check authentication
        if strtobool(self.jira_enable):
            jira_url = "https://{}/rest/api/2/project".format(self.jira_host)
            jira_credentials  = requests.auth.HTTPBasicAuth(self.jira_user_name, self.jira_auth_token)
            jira_output=requests.get(jira_url, auth=jira_credentials)
            jira_status_code = jira_output.status_code
        else:
            jira_status_code = 200
        return jira_status_code

    def send_notification(self, epic_id):
        # This function attaches the scan report to the EPIC ticket
        if strtobool(self.jira_enable):
            print('INFO - JIRA - Execute jira function')
            jira_url = "https://{}/rest/api/3/issue/{}/attachments".format(self.jira_host, epic_id)
            jira_credentials  = requests.auth.HTTPBasicAuth(self.jira_user_name, self.jira_auth_token)
            jira_headers = { 'X-Atlassian-Token': 'no-check' }
            jira_files = [ ('file', ('file.txt', open(GitleaksConfig().scanner_results_config_file_path,'rb'), 'text/plain')) ]
            jira_output = requests.post(jira_url, auth=jira_credentials, files=jira_files, headers=jira_headers)
            #print('DEBUG - jira_notification - output: {}'.format(jira_output.text))
            #return {'status_code': jira_output.status_code, 'data': jira_output.json()}
        else:
            print('INFO - JIRA - Notification is set to False')

class Slack():
    def __init__(self, host_name, auth_token, enable):
        self.slack_base_url = "https://{}/api/".format(host_name)
        self.slack_post_message_url = self.slack_base_url + "chat.postMessage"
        self.slack_auth_token = auth_token
        self.slack_headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer " + self.slack_auth_token}
        self.slack_enable = enable

    def auth(self):
        # The slack auth code is set to 200, if the slack_enable setting is set to false 
        # This is to handle the auth check 
        if strtobool(self.slack_enable):
            slack_url = "https://slack.com/api/auth.test"
            slack_headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Bearer " + self.slack_auth_token}
            slack = requests.post(slack_url, headers = slack_headers)
            slack_response_text = json.loads(slack.text)
            if slack_response_text['ok']:
                slack_status_code = 200
            else:
                slack_status_code = 401
        else:
            slack_status_code = 200
        return slack_status_code

    def send_notification(self, channel, message, scan_aggregated_results):
        # This function post message to the given slack channel 
        message = ":alert: *" + message + "* :alert: \n\n"
        if strtobool(self.slack_enable):
            print('INFO - as2Class - Execute slack_notifications function')
            for k,v in list(scan_aggregated_results.items()):
                if v == 0:
                    del scan_aggregated_results[k]
            scan_aggregated_results = str(scan_aggregated_results)
            scan_aggregated_results = scan_aggregated_results.replace('}', '')
            scan_aggregated_results = scan_aggregated_results.replace('{', '')
            scan_aggregated_results = scan_aggregated_results.replace("'", '')
            scan_aggregated_results = scan_aggregated_results.replace(', ', '\n')
            slack_message = '[{"type":"section","text":{"type":"mrkdwn","text": "' + message + scan_aggregated_results + '"}}]'
            slack_data = {"channel": channel, "type": "message", "blocks": slack_message}
            slack_output = requests.post(self.slack_post_message_url, headers = self.slack_headers, data = slack_data)
            #print('DEBUG - slack_notification - {}'.format(slack_output.text))