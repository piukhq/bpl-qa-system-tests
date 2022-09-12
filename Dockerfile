FROM ghcr.io/binkhq/python:3.10-pipenv

WORKDIR /app
ADD . .

RUN pipenv install --system --deploy --ignore-pipfile

CMD [ "python", "schedule.py" ]
