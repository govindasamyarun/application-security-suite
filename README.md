# Application Security Suite - AS{2}

<p align="center">
  <img width="1730" alt="as2-screenshot" src="https://user-images.githubusercontent.com/69586504/199255441-4aa87712-063f-4340-be76-28065f7e09d0.png">
</p>

## About The Project

AS{2} aims to provide visibility, compliance, alerting and reporting capabilities. The primary focus is to integrate open-source tools used by AppSec teams in one place with better visibility. 

AS{2} leverages Gitleaks, an open-source tool, to identify hard-coded secrets from the bitbucket server repository. It helps you track overall compliance. The integration with JIRA and Slack would be helpful for the security and engineering team to track and address the vulnerabilities. 

## Tech stack

* HTML, JavaScript
* Python Flask
* Postgresql
* Redis
* Nginx

## Integrations

* Bitbucket server (on-premise)
* JIRA
* Slack

## Roadmap 

- [x] Bitbucket server integration
- [x] Hardoded-secrets integration
- [x] Analysis view
- [ ] Bitbucket cloud integration
- [ ] GitHub integration
- [ ] SAST integration
- [ ] SCA integration
- [ ] DAST integration
- [ ] Store passwords in the secrets manager

## Getting started

### Prerequisites

* Docker
* Docker-compose

### Installation

1. Clone the repository

   ```sh
   cd /Data
   git clone https://github.com/govindasamyarun/application-security-suite.git
   ```
   
2. Suppose you wish to use a different username, password, and database. Edit docker-compose.yml to update the following values. If not, skip step 2. 

   ```sh
   pwd: /Data/application-security-suite
   vi docker-compose.yml
   ```

   ```yaml
    as2-db-service:
      environment:
        POSTGRES_DB: <<Enter DB name>>
        POSTGRES_USER: <<Enter DB username>>
        POSTGRES_PASSWORD: <<Enter DB password>>

    as2-app-service:
      environment:
        DB_USER: <<Enter DB username>>
        DB_PASSWORD: <<Enter DB password>>
        DB_DATABASE: <<Enter DB name>>
   ```
   
3. Start the containers

   ```sh
   pwd: /Data/application-security-suite
   
   docker-compose up --detach
   ```

## Application setup

1. Access localhost on port 80 

   ```sh
   http://127.0.0.1/
   ```
   
2. By default, the AS{2} scan engine uses 50 threads 
3. It can be controlled using the config file. If you wish to use more threads to speed up the scan process then the as2-app-service docker image needs to be rebuild 

   ```sh
   vi /Data/application-security-suite/as2-app-service/src/config.py
   ```
   
   ```py
    class gitLeaksConfig:
        scanner_results_config_file_path = "/usr/src/app/reports/scanner_results.csv"
        thread_count = << Enter a value >>
   ```
   
4. Navigate to settings tab
5. Enter Bitbucket hostname, username and authtoken 
6. Make sure the authtoken does not contain any forward or backward slash 
7. By default, Scan all branches, Slack & JIRA notifications are set to false 
8. To enable Slack notifications, register an application 
   * https://api.slack.com/apps
   * Set OAuth & Pernissions & Redirect URL
   * Install the app in the workspace 
   * Set the scope: 
      * channels:read
      * chat:write 
      * chat:write.public
   * Copy the bot token
9. To enable JIRA notifications, you need an EPIC ID, username and authtoken 
10. Scan output gets attached to the EPIC ticket 
11. Save the settings
12. Navigate to Scan tab and initiate the scan
13. The frontend makes REST API call and updates the scan status every 30 seconds once 
14. Once the scan is complete, you will be able to see the statistics in the home page
15. The previous scan results are shown in the home page 
16. Use Reports tab to download the report in csv format 

## Support

Use the issues tab to report any problems or issues.

## License

Distributed under the MIT License. See LICENSE for more information. 

## Note

Note: I’m a self-taught programmer. The frontend code was copied from online, and I tweaked it a bit to fit into the application logic. The backend code was written entirely by myself. 

## Contact

* [LinkedIn](https://www.linkedin.com/in/arungovindasamy/)
* [Twitter](https://twitter.com/ArunGovindasamy)

## Demo

https://user-images.githubusercontent.com/69586504/199733400-9209cc3a-a505-4ad4-ac36-e5132dc8e82c.mp4
