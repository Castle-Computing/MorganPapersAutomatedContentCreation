import os
import requests
import json
from ConfigParser import RawConfigParser
from requests_toolbelt.multipart.encoder import MultipartEncoder

parser = RawConfigParser()
parser.read('configuration.ini')

m = MultipartEncoder(
    fields={'name': parser.get('DEFAULT', 'username'), 'pass': parser.get('DEFAULT', 'password'), 'op': 'Log in', 'form_id': 'user_login'}
)

session = requests.session()
response = session.post('https://digital.lib.calpoly.edu/user/login', data=m, headers={'Content-Type': m.content_type})

with open('links.json') as file:
    data = json.load(file)
    for id in data:
        print(id + ":")
        currentCSV = ""
        for y, title in enumerate(data[id]["titles"]):
            currentCSV += data[id]["suggestions"][y] + "," + data[id]["titles"][y] + "\n"
        
        multipartFormData = MultipartEncoder(
            fields={
                'file': ("RELATED_OBJECTS", currentCSV, 'text/plain'),
                'dsid': 'RELATED_OBJECTS', 
                'controlGroup': 'M'
            }
        )

        headers = { 'Content-Type': multipartFormData.content_type }

        url = 'https://digital.lib.calpoly.edu/islandora/rest/v1/object/' + id + '/datastream'

        response = session.post(url, headers=headers, data=multipartFormData)

        print(url + ": " + response.text)
