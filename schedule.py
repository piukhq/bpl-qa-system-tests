import logging
import subprocess
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler

from azure.blob_storage import upload_report_to_blob_storage
from azure.teams import post_to_teams
from settings import BLOB_STORAGE_DSN, TEAMS_WEBHOOK, SCHEDULE, ALERT_ON_FAILURE, ALERT_ON_SUCCESS, COMMAND

logger = logging.getLogger(__name__)


def run_test():
    try:
        process = subprocess.run(COMMAND.split(" "), timeout=2400, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        logger.debug("Timeout occurred, skipping run")
        return

    logger.debug(process.stdout.decode())
    alert = False
    if process.returncode == 0:
        status = "Success"
        if ALERT_ON_SUCCESS:
            alert = True
    else:
        status = "Failure"
        if ALERT_ON_FAILURE:
            alert = True

    if BLOB_STORAGE_DSN:
        logger.debug("Uploading report.html to blob storage...")
        url = upload_report_to_blob_storage("report.html")
        logger.debug("Successfully uploaded report.html to blob storage")
        if alert:
            post_to_teams(TEAMS_WEBHOOK, status, url)
    else:
        logger.debug("No BLOB_STORAGE_DSN set, skipping report upload and teams notification")


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(run_test, trigger=CronTrigger.from_crontab(SCHEDULE))
    scheduler.start()


if __name__ == "__main__":
    main()
