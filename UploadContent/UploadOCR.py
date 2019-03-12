import os
from Uploader import authenticate, deleteAndReUpload

def upload():
    session = authenticate()

    directoryLoc = "../Content/ocr"
    ocrFiles = os.listdir(directoryLoc)
    dsid = "OCR_BOOK"

    for file in ocrFiles:
        path = os.path.join(directoryLoc, file)
        content = open(path, 'rb')
        pid = file.strip('.txt')
        
        deleteAndReUpload(session, pid, dsid, content)
