import sys
import json
import urllib2


FIRST_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&omitHeader=true&wt=json"
SECOND_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=1000&omitHeader=true&wt=json"
THIRD_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=2000&omitHeader=true&wt=json"

URLS_LIST = [FIRST_THOUSAND, SECOND_THOUSAND, THIRD_THOUSAND]

def crawlDatabase():
    """
    Goes through the libraries Islandora database and maps all the children to their parents.
    It saves this information to the Children.txt file where the first entry on a line if the parent.
    """
    childrenFile = open("../Content/Children.txt", "w")

    for url in URLS_LIST:
        request = urllib2.Request(url,
                        headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
        results = json.load(urllib2.urlopen(request))
        docs = results["response"]["docs"]

        for doc in docs:
            parentPID = doc["PID"]
            childrenURL = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/ancestors_ms:%22" + parentPID + "%22%20?rows=100&omitHeader=true&wt=json"
            childRequest = urllib2.Request(childrenURL,
                                           headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
            childResults = json.load(urllib2.urlopen(childRequest))
            childDocs = childResults["response"]["docs"]
            childPids = list()

            for childDoc in childDocs:
                childPID = childDoc["PID"]
                childPids.append(childPID)

            childPids.sort()

            pids = ",".join(childPids)

            childrenFile.write(parentPID + "," + pids + '\n')

            print(parentPID + "," + pids)

    childrenFile.close()

def getOCRs():
    """
    Uses the Children.txt file to download all the letters' OCRs and save them to the ocr directory.
    It bunches the children OCRs into one parent OCR.
    """

    with open("../Content/Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            pidValues = line.split(",")
            pidValues.reverse()

            parentPID = pidValues.pop()
            print parentPID

            ocr = ""

            while len(pidValues) > 0:
                ocrURL = "https://digital.lib.calpoly.edu/islandora/rest/v1/object/" + pidValues.pop() + "/datastream/OCR"
                ocrRequest = urllib2.Request(ocrURL, headers={
                    "authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
                try:
                    ocrContent = urllib2.urlopen(ocrRequest)
                    if ocrContent.getcode() == 200:
                        ocr = ocr + ocrContent.read()

                    ocrContent.close()
                except:
                    e = sys.exc_info()[0]
                    print(e)

            if len(ocr) > 0:
                ocrFile = open("../Content/ocr/" + parentPID + ".txt", "w+")
                ocrFile.write(ocr)
                ocrFile.close()

if __name__ == '__main__':
    print"---------------------------------------------------------------"
    print "Crawling Islandora Database"
    print"---------------------------------------------------------------"
    crawlDatabase()

    print"---------------------------------------------------------------"
    print "Getting all OCRs"
    print"---------------------------------------------------------------"
    getOCRs()