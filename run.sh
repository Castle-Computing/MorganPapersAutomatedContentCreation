#!/usr/bin/env bash

python /usr/src/app/Content/Download.py >> /var/log/cron.log 2>&1
python /usr/src/app/GetNounsNLP/NLP.py -u >> /var/log/cron.log 2>&1
python /usr/src/app/UploadContent/UploadContent.py >> /var/log/cron.log 2>&1
