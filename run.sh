#!/usr/bin/env bash

python /usr/src/app/Content/Download.py >> /var/log/cron.log 2>&1
python /usr/src/app/GetNounsNLP/NLP.py -u >> /var/log/cron.log 2>&1
python /usr/src/app/UploadContent/UploadPrevNext.py >> /var/log/cron.log 2>&1
python /usr/src/app/UploadContent/UploadSuggestions.py >> /var/log/cron.log 2>&1
