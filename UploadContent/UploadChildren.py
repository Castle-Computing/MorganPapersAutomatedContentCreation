import os
import sys
from Uploader import authenticate, deleteAndReUpload

session = authenticate()
dsid = 'BOOK_CHILDREN'

with open("../Content/Children.txt") as f:
    lines = [line.rstrip('\n') for line in f]
    for line in lines:
        pidValues = line.split(",")
        pidValues.reverse()
        
        parentPID = pidValues.pop()
        pidValues.reverse()
        content = ",".join(pidValues)

        deleteAndReUpload(session, parentPID, dsid, content)