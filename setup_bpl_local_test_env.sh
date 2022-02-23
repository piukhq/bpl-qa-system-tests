#!/bin/bash
set -x

# This script aims to set up and run everything required in order to develop BPL
# automated tests. Note that it will install virtual environments in the project
# direcories.
#
# Variables:
# ROOT_DIR:           The root installation directory
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
# export DB_USERNAME=changeme
# export DB_PASSWORD=changeme
# export DB_PORT=changeme
# export BLOB_STORAGE_DSN='changeme'
######### /example bpl_auto_test.env #############

source ~/bpl_auto_test.env

TMUX_SESSION_NAME=bpl
BASE_DB_URI="postgresql://$DB_USERNAME:$DB_PASSWORD@localhost:$DB_PORT"
PROMETHEUS_ROOT_DIR=$ROOT_DIR/_prometheus_
export PIPENV_VENV_IN_PROJECT=1
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

LUNA_ENV_FILE=$(cat <<EOF
DEBUG=True
LUNA_PORT=9001
LOG_FORMATTER=brief
USE_REDIS_CACHE=False
REDIS_URL=redis://localhost:6379/0
EOF
)

POLARIS_ENV_FILE=$(cat <<EOF
POSTGRES_USER=$DB_USERNAME
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=polaris_auto
LOG_FORMATTER=brief
DISABLE_METRICS=true
USE_CALLBACK_OAUTH2=false
VELA_HOST=http://localhost:8001
REDIS_URL=redis://localhost:6379/0
TASK_RETRY_BACKOFF_BASE="0.2"
PENDING_REWARDS_SCHEDULE=* * * * *
POLARIS_PUBLIC_URL=http://localhost:8000
SEND_EMAIL=false
EOF
)

VELA_ENV_FILE=$(cat <<EOF
POSTGRES_USER=$DB_USERNAME
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=vela_auto
LOG_FORMATTER=brief
POLARIS_URL=http://localhost:8000
CARINA_URL=http://localhost:8002
REDIS_URL=redis://localhost:6379/0
EOF
)

CARINA_ENV_FILE=$(cat <<EOF
POSTGRES_USER=$DB_USERNAME
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=carina_auto
LOG_FORMATTER=brief
POLARIS_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
BLOB_STORAGE_DSN=$BLOB_STORAGE_DSN
BLOB_IMPORT_SCHEDULE=* * * * *
EOF
)
cd $ROOT_DIR

# install repositories and make correct databases
if [[ ! -d "luna" ]]; then
    echo "- Cloning luna ..."
    git clone git@github.com:binkhq/luna.git
fi
cd luna && echo "$LUNA_ENV_FILE" > .env && pipenv sync --dev

for p_name in "polaris" "vela" "carina"; do
    if [[ ! -d $PROMETHEUS_ROOT_DIR/$p_name ]]; then
        mkdir -p $PROMETHEUS_ROOT_DIR/$p_name
    fi
    cd "${ROOT_DIR}"
    if [[ ! -d $p_name ]]; then
        echo "- Cloning $p_name..."
        git clone "git@github.com:binkhq/$p_name.git"
    fi
    cd "${ROOT_DIR}/${p_name}"
    echo "Working on ${p_name}"
    echo "- Checking out and updating master branch"
    git checkout master
    git pull --ff-only origin master
    echo "- Writing sane local.env";
    env_var_name=$(echo "${p_name}_env_file" | tr 'a-z' 'A-Z')
    echo "${!env_var_name}" > local.env
    echo "- Updating python environment";
    pipenv sync
    echo "- Resetting database"
    psql "${BASE_DB_URI}/postgres" -c "drop database ${p_name}_template ;"
    psql "${BASE_DB_URI}/postgres" -c "create database ${p_name}_template ;"
    echo "- Running alembic migrations"
    SQLALCHEMY_DATABASE_URI="${BASE_DB_URI}/${p_name}_template" pipenv run alembic upgrade head
done

# run up all BPL services
echo "Starting services in tmux session: $TMUX_SESSION_NAME"
tmux -2 new-session -d -s $TMUX_SESSION_NAME
tmux new-window -t $TMUX_SESSION_NAME -n 'BPL'

for p in {0..7}; do
    tmux split-pane -v
    tmux select-layout tiled
done

for proj in polaris vela carina; do
    rm -rf $PROMETHEUS_ROOT_DIR/$proj/*
done
tmux select-pane -t 0
tmux send-keys "cd $ROOT_DIR/polaris && pipenv run uvicorn asgi:app --port 8000" C-m
tmux select-pane -t 3
tmux send-keys "cd $ROOT_DIR/polaris && rm -rf && PROMETHEUS_HTTP_SERVER_PORT=9101 PROMETHEUS_MULTIPROC_DIR=$PROMETHEUS_ROOT_DIR/polaris pipenv run python -m app.core.cli task-worker" C-m
tmux select-pane -t 1
tmux send-keys "cd $ROOT_DIR/vela && pipenv run uvicorn asgi:app --port 8001" C-m
tmux select-pane -t 4
tmux send-keys "cd $ROOT_DIR/vela && PROMETHEUS_HTTP_SERVER_PORT=9102 PROMETHEUS_MULTIPROC_DIR=$PROMETHEUS_ROOT_DIR/vela pipenv run python -m app.tasks.worker worker" C-m
tmux select-pane -t 2
tmux send-keys "cd $ROOT_DIR/carina && pipenv run uvicorn asgi:app --port 8002" C-m
tmux select-pane -t 5
tmux send-keys "cd $ROOT_DIR/carina && PROMETHEUS_HTTP_SERVER_PORT=9103 PROMETHEUS_MULTIPROC_DIR=$PROMETHEUS_ROOT_DIR/carina pipenv run python -m app.tasks.worker worker" C-m
tmux select-pane -t 6
tmux send-keys "cd $ROOT_DIR/luna && pipenv run python wsgi.py" C-m
tmux select-pane -t 7
tmux send-keys "cd $ROOT_DIR/carina && pipenv run python -m app.imports.agents.file_agent reward-import-agent" C-m
tmux select-pane -t 8
tmux send-keys "cd $ROOT_DIR/carina && pipenv run python -m app.imports.agents.file_agent reward-updates-agent" C-m
tmux attach-session -t $TMUX_SESSION_NAME