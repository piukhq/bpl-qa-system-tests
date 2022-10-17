FROM ghcr.io/binkhq/python:3.10-poetry

WORKDIR /app
ADD . .

RUN poetry config http-basic.bink-pypi 269fdc63-af3d-4eca-8101-8bddc22d6f14 b694b5b1-f97e-49e4-959e-f3c202e3ab91
RUN poetry config virtualenvs.create false
RUN poetry install

CMD [ "python", "schedule.py" ]
