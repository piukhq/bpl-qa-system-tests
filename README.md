#  BPL System level Intergrated Automation Tests

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
Everything you need for local development
```
# LOCAL
LOCAL=True
SCHEDULE="*/15 * * * *"
MOCK_SERVICE_BASE_URL=http://127.0.0.1:9000
VAULT_URL=https://bink-uksouth-dev-com.vault.azure.net/
FRIENDLY_NAME="Local - Customer Management API - BPL"
ALERT_ON_SUCCESS=False
ALERT_ON_FAILURE=False
POLARIS_TEMPLATE_DB_NAME=polaris_template
VELA_TEMPLATE_DB_NAME=vela_template
CARINA_TEMPLATE_DB_NAME=carina_template
POLARIS_DATABASE_URI=postgresql://postgres:pass@localhost:5555/polaris_auto
POLARIS_ENV_BASE_URL=http://127.0.0.1:8000/bpl/loyalty
VELA_DATABASE_URI=postgresql://postgres:pass@localhost:5555/vela_auto
VELA_ENV_BASE_URL=http://127.0.0.1:8001/bpl/rewards
CARINA_DATABASE_URI=postgresql://postgres:pass@localhost:5555/carina_auto
CARINA_ENV_BASE_URL=http://127.0.0.1:8002/bpl/vouchers
BLOB_STORAGE_DSN=DefaultEndpointsProtocol=https;AccountName=binkuksouthdev;AccountKey=L/xU6NZswZAJbFhKjIGr0feakhY8QsCw4oUuj6bXNfxhWQv2caNkDo8czIu05DBcaZbSL7vfpYGP7OZsbpXuhw==;EndpointSuffix=core.windows.net
BLOB_IMPORT_CONTAINER=carina-imports-smpCollapse
```

##### Azure setup
Install Azure CLI and login to Azure for Key Vault access
```
brew install azure-cli

az login
```

##### Run test suite (pointing at dev):
```
pytest -m bpl
```

## Environment Variables
* `POLARIS_DATABASE_URI`: URI to the Polaris database  
* `VELA_DATABASE_URI`: URI to the Vela database  
* `VAULT_URL`: URL for Azure Key Vault  
* `LOCAL`: Set to True for local testing, disables teams webhook and saving reports to blob storage. 
Defaults to `False`  
* `TEAMS_WEBHOOK`: Webhook to send alerts to the "Alerts - QA" channel when the test suite runs  
* `BLOB_STORAGE_DSN`: DSN to connect to blob storage  
* `REPORT_CONTAINER`: Blob storage container to save reports to. Defaults to `qareports`  
* `REPORT_DIRECTORY`: Blob storage directory to save reports to. Defaults to `bpl/isolated/`  
* `FRIENDLY_NAME`: Name used on report headers and teams alerts. Defaults to `BPL`  
* `SCHEDULE`: Cron schedule for running the scheduled reports  
* `COMMAND`: Command that the the scheduled task runs, Defaults to: 
`pytest --html report.html --self-contained-html -s -m bpl`  
* `ALERT_ON_SUCCESS`: Set to True to send teams alerts when the test suite runs successfully. 
Defaults to `True`  
* `ALERT_ON_FAILURE`: Set to True to send teams alerts when the test suite fails to run. 
Defaults to `True`  
* `POLARIS_BASE_URL`: Base URL for the customer management api 
  e.g. `https://api.dev.gb.bink.com/bpl/loyalty`  
* `VELA_BASE_URL`: Base URL for the rewards rule management api 
  e.g. `https://api.dev.gb.bink.com/bpl/rewards`  
* `MOCK_SERVICE_BASE_URL`: URL to send for the `callback_url` during enrolment requests  
