import requests

from settings import FRIENDLY_NAME


def post_to_teams(webhook, status, url):
    if status == "Success":
        themeColor = "00FF00"
    else:
        themeColor = "FF0000"
    template = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": themeColor,
        "summary": f"{FRIENDLY_NAME} Test Results",
        "Sections": [
            {
                "activityTitle": f"{FRIENDLY_NAME} Test Results",
                "facts": [
                    {"name": "Status", "value": status},
                    {"name": "URL", "value": f"[{url}]({url})"},
                ],
                "markdown": True,
            }
        ],
    }
    return requests.post(webhook, json=template)
