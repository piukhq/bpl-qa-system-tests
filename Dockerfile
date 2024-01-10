FROM ghcr.io/binkhq/python:3.10-poetry

WORKDIR /app
ADD . .

ARG AZURE_DEVOPS_PAT
RUN poetry config virtualenvs.create false
RUN poetry config http-basic.azure jeff ${{ secrets.AZURE_DEVOPS_PAT }}
RUN poetry install
RUN apt-get update && apt-get install -y wget && apt-get install -y curl && \
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
    apt-get autoremove -y wget && rm -rf /var/lib/apt/lists

CMD [ "python", "schedule.py" ]
