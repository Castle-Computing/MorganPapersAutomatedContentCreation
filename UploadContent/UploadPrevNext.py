import os
import json
from Uploader import authenticate, deleteAndReUpload

session = authenticate()

with open('../Content/prevAndNext.json') as file:
    data = json.load(file)
    dsid1 = 'PREVIOUS_LETTER'
    dsid1 = 'NEXT_LETTER'

    for id in data:
        #currentCSV = ""
        print "Prev: " + str(data[id][0])
        print "Next: " + str(data[id][1])
        #for y, title in enumerate(data[id]["titles"]):
        #    currentCSV += data[id]["suggestions"][y] + "," + data[id]["titles"][y] + "\n"

        #deleteAndReUpload(session, id, dsid, currentCSV)




