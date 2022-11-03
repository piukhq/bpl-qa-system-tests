#!/bin/bash

bolb_name=$(date +%s | awk '{ print strftime("%Y%m%d-%H%M", $1);  }')-$(echo $RANDOM | md5sum | head -c 6).html
url="https://binkuksouthstaging.blob.core.windows.net/qareports/bpl/isolated/bpl-auto-${bolb_name}"

# look for report.html generated during pytest run
while [ ! -f /tmp/report.html ]; do
    sleep 2
done
sleep 2

# copy report to azureblob
az storage blob upload --account-name $(echo $BLOB_STORAGE_DSN | awk -F ';' '{print $2}' | sed 's/AccountName=//g') --container-name qareports --name "bpl/isolated/bpl-auto-$bolb_name" --file /tmp/report.html --account-key $(echo $BLOB_STORAGE_DSN | awk -F ';' '{print $3}' | sed 's/AccountKey=//g') --auth-mode key

# determine what message to POST to teams using the error.log
if
    grep -q 0 /tmp/status.txt
    [ $? -eq 0 ]
then
    echo "command was successful -> no errors -> green"
    themeColor="00FF00"
    status="SUCCESS"
else
    echo "command was unsuccessful -> error -> red"
    themeColor="FF0000"
    status="FAILURE"
fi

# POST to teams the output of pytest run
curl -H 'Content-Type: application/json' -d '{"@type": "MessageCard", "@context": "http://schema.org/extensions", "themeColor": "'"$themeColor"'", "summary": "'"$FRIENDLY_NAME"' Test Results", "Sections": [{"activityTitle": "'"$FRIENDLY_NAME"' Test Results", "facts": [{"name": "Status", "value": "'"$status"'"}, {"name": "URL", "value": "'"$url"'"}]}]}' $TEAMS_WEBHOOK
