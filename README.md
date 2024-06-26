# BPL System level Intergrated Automation Tests

BDD style automated tests for testing BPL in isolation.

## Local Project Setup

### Install dependencies

Install the prerequisites for psycopg2:

```shell
brew install postgres openssl
export LDFLAGS="-L/usr/local/opt/openssl/lib"
```

Then install the project dependencies:

```shell
poetry config <pypi-url> <pypi-user> <pypi-pass>
poetry install --sync --no-root
```

#### .env setup

Everything you need for local development

```shell
# LOCAL
cp .env.example .env
```

##### Azure setup

Install Azure CLI and login to Azure for Key Vault access

```shell
brew install azure-cli
az login
```

##### Run test suite (pointing at dev)

```shell
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
  e.g. `https://api.dev.gb.bink.com/bpl/retailers`  
* `MOCK_SERVICE_BASE_URL`: URL to send for the `callback_url` during enrolment requests
* `REDIS_URL`: URL for connecting to the redis instance

## Using the setup script

This script will git clone the application repos into a directory called `bpl-auto` (configurable) as well as creating
the required databases in local postgres and starting the workers. It will then use tmux to split the screen into
tmux screens to monitor the apps and workers as you run the tests.

If you want to run any of the workers or apps
in your editor, you'll need to comment that section out of the tmux part of the setup_bpl_local_test_env.sh script and
run it again (it should be idempotent to a great degree).

* You will need tmux (`brew update && brew install tmux`)
* You will need to create a script called `bpl_auto_test.env` in your home directory (example contents below)
* You will need to have local postgres and redis running, probably as docker containers. It's easiest to stick to default ports
* Run the setup script in the root of this project: `./setup_bpl_local_test_env.sh`
* To kill the tmux sessions, run  tmux kill-session -t bpl  in terminal.

### Example content for `~/bpl_auto_test.env` file

```shell
    export ROOT_DIR=$HOME/dev/bpl-auto
    export DB_USERNAME=postgres
    export DB_PASSWORD=postgres
    export DB_PORT=5432
    export BLOB_STORAGE_DSN="DefaultEndpointsProtocol=https;AccountName=binkuksouthdev;AccountKey=L/xU6NZswZAJbFhKjIGr0feakhY8QsCw4oUuj6bXNfxhWQv2caNkDo8czIu05DBcaZbSL7vfpYGP7OZsbpXuhw==;EndpointSuffix=core.windows.net"
    export BLOB_IMPORT_CONTAINER=carina-import-<my-name-here>
    export BLOB_ARCHIVE_CONTAINER=carina-archive-<my-name-here>
```

### Optional `~/bpl_auto_test.env` environment variables

The project supports checking out specific references for individual projects with `<PROJECT>_REF` environment variables.

For example if `POLARIS_REF=1.4.4` is set, then the 1.4.4 git tag will be checked out.

You may also set `GIT_BRANCH` and this will be used for ALL projects.

For example if `GIT_BRANCH=develop` is set, then the `develop` branch will be used for all projects.

If neither `<PROJECT>_REF` nor `GIT_BRANCH` environment variables are set, then *the latest tagged version* for each project will be checked out.

### Other

* If you see any `KeyVaultError` errors, check that you have the VPN running, kill the tmux session and run the script again.
* The DBs `*_auto` will not exist until you run the first pytest, so you may see warnings about that in the apps' output
