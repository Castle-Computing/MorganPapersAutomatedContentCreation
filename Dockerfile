FROM python:2

# Install cron
RUN apt-get update && apt-get -y install cron 

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/simple-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/simple-cron

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader averaged_perceptron_tagger

COPY . .

# Run the command on container startup
CMD cron -f && python /usr/src/app/GetNounsNLP/NLP.py -u