import os
import json
from Uploader import authenticate, deleteAndReUpload

def upload():
    session = authenticate()

    with open('../Content/links.json') as file:
        data = json.load(file)
        dsid = 'RELATED_OBJECTS'
        
        for id in data:
            currentCSV = ""
            for y, title in enumerate(data[id]["titles"]):
                currentCSV += data[id]["suggestions"][y] + "," + data[id]["titles"][y] + "\n"
            
            deleteAndReUpload(session, id, dsid, currentCSV)
