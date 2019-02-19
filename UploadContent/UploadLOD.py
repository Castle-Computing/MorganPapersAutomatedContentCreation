import os
import json
from Uploader import authenticate, deleteAndReUpload

session = authenticate()
dsid = 'LETTER_OF_THE_DAY_VALUE'

with open('../Content/LetterDates.json') as file:
    data = json.load(file)
    for value in data:
        for entry in data[value]:
            pid = entry["PID"]
            deleteAndReUpload(session, pid, dsid, value)