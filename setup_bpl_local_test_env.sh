#!/bin/bash
set -x

# This script aims to set up and run everything required in order to develop BPL
# automated tests. Note that it will install virtual environments in the project
# direcories.
#
# Variables:
# ROOT_DIR:           The root installation directory
# GIT_BRANCH:         The default branch for checking out in each project
# <proj-name>_REF:    e.g. COSMOS_REF, HUBBLE_REF - a specific git-ref for a project
#                     e.g. 3.0.1 (tag) or a81cafb58 (commit) or <branch-name> (branch)
#                     If omitted, GIT_BRANCH will be used
# DB_USERNAME:        Postgres username
# DB_PASSWORD:        Postgres password
# DB_PORT:            Port on which postgres is listening
# BLOB_STORAGE_DSN:   DSN for accessing Azure blob storage services

# IMPORTANT: Put these in a file called bpl_auto_test.env in your $HOME directory
#
# Note:
# Kill the tmux session in a different terminal with:
# tmux kill-session -t bpl

########## example bpl_auto_test.env #############
# export ROOT_DIR=$HOME/CHANGEME
# export GIT_BRANCH=master
# #export COSMOS_REF=develop
# export DB_USERNAME=changeme
# export DB_PASSWORD=changeme
# export DB_PORT=changeme
# export BLOB_STORAGE_DSN='changeme'
# export BLOB_IMPORT_CONTAINER=changeme (e.g. carina-imports-<my-name-here>)
# export BLOB_ARCHIVE_CONTAINER=changeme (e.g. carina-archive-<my-name-here>)
######### /example bpl_auto_test.env #############

source ~/bpl_auto_test.env

echo "Git branch is: $GIT_BRANCH"

RUN=${1}

TMUX_SESSION_NAME=bpl

BASE_DB_URI="postgresql://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT"
PROMETHEUS_ROOT_DIR=$ROOT_DIR/_prometheus_
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

setup_projects() {

    LUNA_ENV_FILE=$(
        cat <<EOF
DEBUG=True
LUNA_PORT=9001
LOG_FORMATTER=brief
USE_REDIS_CACHE=False
REDIS_URL=redis://localhost:6379/0
EOF
    )

COSMOS_ENV_FILE=$(
        cat <<EOF
SQLALCHEMY_DATABASE_URI="postgresql+psycopg://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT/{}"
POSTGRES_DB=cosmos_auto
REDIS_URL=redis://localhost:6379/0
LOG_FORMATTER=brief
BLOB_STORAGE_DSN=$BLOB_STORAGE_DSN
BLOB_IMPORT_CONTAINER=$BLOB_IMPORT_CONTAINER
BLOB_ARCHIVE_CONTAINER=$BLOB_ARCHIVE_CONTAINER
EVENT_HORIZON_CLIENT_ID=$EVENT_HORIZON_CLIENT_ID
BLOB_IMPORT_SCHEDULE=* * * * *
REWARD_ISSUANCE_REQUEUE_BACKOFF_SECONDS=15
PENDING_REWARDS_SCHEDULE=* * * * *
PROMETHEUS_HTTP_SERVER_PORT=9300
PRE_LOADED_REWARD_BASE_URL=http://reward-base.url
ACTIVITY_DB=hubble_auto
PUBLIC_URL=http://localhost:8000
USE_CALLBACK_OAUTH2=false
TASK_RETRY_BACKOFF_BASE="0.2"
SEND_EMAIL=false
KEY_VAULT_URI=https://uksouth-dev-2p5g.vault.azure.net/
EOF
    )

HUBBLE_ENV_FILE=$(
        cat <<EOF
DATABASE_NAME=hubble_auto
REDIS_URL=redis://localhost:6379/0
DATABASE_URI="postgresql+psycopg://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT/{}"
PG_CONNECTION_POOLING=False
SQL_DEBUG=False
USE_NULL_POOL=True
RABBIT_DSN=amqp://guest:guest@localhost:5672/
ROOT_LOG_LEVEL=DEBUG
EOF
    )

    cd $ROOT_DIR

    # install repositories and make correct databases
    if [[ ! -d "luna" ]]; then
        echo "- Cloning luna ..."
        git clone git@github.com:binkhq/luna.git
    fi
    cd luna
    echo "$LUNA_ENV_FILE" >.env
    poetry config --local virtualenvs.in-project true
    poetry install --sync --without dev

    cd $ROOT_DIR

    if [[ ! -d "hubble" ]]; then
        echo "- Cloning hubble ..."
        git clone git@github.com:binkhq/hubble.git
    fi
    cd hubble
    git fetch
    echo "- Writing sane .env"
    echo "$HUBBLE_ENV_FILE" >.env
    poetry config --local virtualenvs.in-project true
    poetry env use 3.11
    poetry install --sync --without dev
    checkout_ref $HUBBLE_REF
    echo "- Resetting hubble database"
    psql "${BASE_DB_URI}/postgres" -c "DROP DATABASE hubble_template ;"
    psql "${BASE_DB_URI}/postgres" -c "CREATE DATABASE hubble_template ;"
    echo "- Running alembic migrations"
    poetry run alembic -x db_dsn="postgresql+psycopg://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT/hubble_template" upgrade head

    # Cosmos
    if [[ ! -d $PROMETHEUS_ROOT_DIR/cosmos ]]; then
        mkdir -p $PROMETHEUS_ROOT_DIR/cosmos
    fi
    cd "${ROOT_DIR}"
    if [[ ! -d "cosmos" ]]; then
        echo "- Cloning cosmos..."
        git clone "git@github.com:binkhq/cosmos.git"
    fi
    cd "${ROOT_DIR}/cosmos"
    git fetch
    checkout_ref $COSMOS_REF
    echo "- Writing sane local.env"
    echo "$COSMOS_ENV_FILE" >local.env
    echo "- Updating python environment"
    poetry config --local virtualenvs.in-project true
    poetry env use 3.11
    poetry install --sync --without dev
    echo "- Resetting cosmos database"
    psql "${BASE_DB_URI}/postgres" -c "DROP DATABASE cosmos_template;"
    psql "${BASE_DB_URI}/postgres" -c "CREATE DATABASE cosmos_template;"
    echo "- Running alembic migrations"
    poetry run alembic -x db_dsn="postgresql+psycopg://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT/cosmos_template" upgrade head
}


checkout_ref() {
    if [[ -n $1 ]]; then
        GIT_REF=$1
    elif [[ -n ${GIT_BRANCH} ]]; then
        GIT_REF=${GIT_BRANCH}
    else
        GIT_REF=$(git describe --tags $(git rev-list --tags --max-count=1))
    fi
    echo "- Checking out and updating $GIT_REF branch/ref"
    git checkout $GIT_REF;
    git pull --ff-only origin $GIT_REF
}

run_services() {
    echo "Starting services in tmux session: $TMUX_SESSION_NAME"
    tmux -2 new-session -d -s $TMUX_SESSION_NAME
    tmux new-window -t $TMUX_SESSION_NAME -n 'BPL'

    for p in {0..7}; do
        tmux split-pane -v
        tmux select-layout tiled
    done

    rm -rf $PROMETHEUS_ROOT_DIR/cosmos/*


    # tmux gui formatting
    tmux set -g mouse on
    tmux set -g pane-border-status on
    tmux set -g pane-border-status top
    tmux set -g pane-border-format "[#[fg=white]#{?pane_active,#[bold],} #P - #T #[fg=default,nobold]]"

    # create tmux panes with the following layout example
    ## Cosmos
    tmux select-pane -t 0 -T Cosmos_Public_API
    tmux send-keys -t 0 "cd $ROOT_DIR/cosmos && poetry run cosmos api public --port 8000" C-m
    tmux select-pane -t 1 -T Cosmos_Campaigns_API
    tmux send-keys -t 1 "cd $ROOT_DIR/cosmos && poetry run cosmos api campaigns --port 8001" C-m
    tmux select-pane -t 2 -T Cosmos_Transactions_API
    tmux send-keys -t 2 "cd $ROOT_DIR/cosmos && poetry run cosmos api transactions --port 8002" C-m
    tmux select-pane -t 3 -T Cosmos_Accounts_API
    tmux send-keys -t 3 "cd $ROOT_DIR/cosmos && poetry run cosmos api accounts --port 8003" C-m
    tmux select-pane -t 4 -T Cosmos_Task_Worker
    tmux send-keys -t 4 "cd $ROOT_DIR/cosmos && PROMETHEUS_HTTP_SERVER_PORT=9101 PROMETHEUS_MULTIPROC_DIR=$PROMETHEUS_ROOT_DIR/cosmos poetry run cosmos task-worker" C-m
    tmux select-pane -t 5 -T Cosmos_Cron_Scheduler
    tmux send-keys -t 5 "cd $ROOT_DIR/cosmos && PROMETHEUS_HTTP_SERVER_PORT=9102 PROMETHEUS_MULTIPROC_DIR=$PROMETHEUS_ROOT_DIR/cosmos poetry run cosmos cron-scheduler" C-m

    ## Luna
    tmux select-pane -t 6 -T Luna
    tmux send-keys -t 6 "cd $ROOT_DIR/luna && poetry run python wsgi.py" C-m

    ## Hubble Consumer
    tmux select-pane -t 7 -T HubbleConsumer
    tmux send-keys -t 7 "cd $ROOT_DIR/hubble && poetry run python -m hubble.cli activity-consumer" C-m

    # Attach to the tmux session
    tmux attach-session -t $TMUX_SESSION_NAME
}

if [ $RUN = "services" ]; then
    run_services
else
    setup_projects
    run_services
fi
