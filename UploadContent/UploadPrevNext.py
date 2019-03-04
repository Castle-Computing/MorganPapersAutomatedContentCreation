import os
import json
from Uploader import authenticate, deleteAndReUpload

session = authenticate()

with open('../Content/prevAndNext.json') as file:
    data = json.load(file)
    dsid1 = 'PREVIOUS_MORGAN_LETTER'
    dsid2 = 'NEXT_MORGAN_LETTER'

    for id in data:
        print "Prev: " + str(data[id][0])
        print "Next: " + str(data[id][1])

        deleteAndReUpload(session, id, dsid1, data[id][0])
        deleteAndReUpload(session, id, dsid2, data[id][1])




