import os
from Uploader import authenticate, deleteAndReUpload

session = authenticate()

ocrFiles = os.listdir("ocr")
dsid = "OCR_BOOK"

for file in ocrFiles:
    path = os.path.join('ocr', file)
    content = open(path, 'rb')
    pid = file.strip('.txt')
    
    deleteAndReUpload(session, pid, dsid, content)
