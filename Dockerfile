FROM ghcr.io/binkhq/python:3.10-poetry

WORKDIR /app
ADD . .

RUN poetry install --system --deploy --ignore-pipfile

CMD [ "python", "schedule.py" ]
