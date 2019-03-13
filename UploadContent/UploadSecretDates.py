import os
from Uploader import authenticate, deleteAndReUpload

def upload():
    session = authenticate()

    with open('../Content/datesForSequenceNavigator.csv') as f:
        data = f.read().splitlines()
        dsid = 'MORGAN_PAPERS_SECRET_DATE'
        print data

        for i in range(1, len(data)):
            items = data[i].split(",")

            if items[2] != "x":
                print "ID: " + items[0]
                print "Date: " + items[2]

                deleteAndReUpload(session, items[0], dsid, items[1])


if __name__ == '__main__':
    upload()