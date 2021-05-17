import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from azure_actions.blob_storage import upload_report_to_blob_storage
from azure_actions.teams import post_to_teams
from settings import ALERT_ON_FAILURE, ALERT_ON_SUCCESS, BLOB_STORAGE_DSN, COMMAND, SCHEDULE, TEAMS_WEBHOOK, logger


def run_test() -> None:
    logger.debug(f"Starting automated test suite using command: {COMMAND}")
    try:
        process = subprocess.run(COMMAND.split(" "), timeout=2400, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        logger.error("Timeout occurred, skipping run")
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
        logger.debug(f"Successfully uploaded report to blob storage: {url}")
        if alert:
            post_to_teams(TEAMS_WEBHOOK, status, url)
    else:
        logger.debug("No BLOB_STORAGE_DSN set, skipping report upload and teams notification")


def main() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(run_test, trigger=CronTrigger.from_crontab(SCHEDULE))
    logger.debug(f"Scheduled automated test run using cron expression: {SCHEDULE}")
    scheduler.start()


if __name__ == "__main__":
    main()
