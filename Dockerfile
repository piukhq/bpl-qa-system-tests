FROM ghcr.io/binkhq/python:3.10-poetry

WORKDIR /app
ADD . .

RUN poetry config virtualenvs.create false
RUN poetry install

CMD [ "python", "schedule.py" ]
