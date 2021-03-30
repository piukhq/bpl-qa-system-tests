# BPL Automation Tests

BDD style automated tests for testing BPL in isolation.

## Local Project Setup

##### Install dependencies:
Install the prerequisites for psycopg2:
```
brew install postgres openssl
export LDFLAGS="-L/usr/local/opt/openssl/lib"
```
Then install the project dependencies: 
```
pipenv install --dev
```

##### .env setup
Copy the .env.example file which should have everything you need 
for local development
```
cp .env.example .env
```

##### Azure setup
Install Azure CLI and login to Azure for Key Vault access
```
brew install azure-cli

az login
```

##### Run test suite (pointing at dev):
```
pytest --html report.html --self-contained-html -s -m customer_management_api
```


## Current Test Support:
#### Customer Management API 
* Enrolment (In progress)

## Environment Variables
* `SQLALCHEMY_DATABASE_URI`: URI to the Polaris database  
* `VAULT_URL`: URL for Azure Key Vault  
* `LOCAL`: Set to True for local testing, disables teams webhook and saving reports to blob storage. 
Defaults to `False`  
* `TEAMS_WEBHOOK`: Webhook to send alerts to the "Alerts - QA" channel when the test suite runs  
* `BLOB_STORAGE_DSN`: DSN to connect to blob storage  
* `REPORT_CONTAINER`: Blob storage container to save reports to. Defaults to `qareports`  
* `REPORT_DIRECTORY`: Blob storage directory to save repots to. Defaults to `bpl/isolated/`  
* `FRIENDLY_NAME`: Name used on report headers and teams alerts. Defaults to `BPL`  
* `SCHEDULE`: Cron schedule for running the scheduled reports  
* `COMMAND`: Command that the the scheduled task runs, Defaults to: 
`pytest --html report.html --self-contained-html -s -m bpl`  
* `ALERT_ON_SUCCESS`: Set to True to send teams alerts when the test suite runs successfully. 
Defaults to `True`  
* `ALERT_ON_FAILURE`: Set to True to send teams alerts when the test suite fails to run. 
Defaults to `True`  
* `ENV_BASE_URL`: Base URL for the automated tests e.g. `https://api.dev.gb.bink.com`  
* `MOCK_SERVICE_BASE_URL`: URL to send for the `callback_url` during enrolment requests  
