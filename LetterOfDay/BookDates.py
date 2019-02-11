import json
import urllib2
from datetime import datetime


def get_objects():
    first_thousand = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&omitHeader=true&wt=json"
    second_thousand = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=1000&omitHeader=true&wt=json"
    third_thousand = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=2000&omitHeader=true&wt=json"

    first_request = urllib2.Request(first_thousand,
                                    headers = {"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    first_results = json.load(urllib2.urlopen(first_request))

    second_request = urllib2.Request(second_thousand,
                                     headers = {"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    second_results = json.load(urllib2.urlopen(second_request))

    third_request = urllib2.Request(third_thousand,
                                    headers = {"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    third_results = json.load(urllib2.urlopen(third_request))

    docs = first_results["response"]["docs"]
    docs.extend(second_results["response"]["docs"])
    docs.extend(third_results["response"]["docs"])
    return docs


# Make dictionary of dates and list of letters for that day
def by_day(docs):
    num_done = 1
    months = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    data = {}
    for doc in docs:
        num_done = num_done + 1
        if num_done%100 == 0:
            print num_done
        PID = doc["PID"]
        title_r = urllib2.Request("https://digital.lib.calpoly.edu/islandora/rest/v1/object/" + PID,
                                    headers = {"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
        title = json.load(urllib2.urlopen(title_r))["label"]
        try:
            date = doc["mods_originInfo_dateCreated_s"]
            # Parse date to get month and day
            # Only display if correct format
            pd = datetime.strptime(date, "%Y-%m-%d")
        except:
            continue
        index = months[pd.month - 1] + (pd.day - 1)
        DC = doc["fedora_datastreams_ms"]
        if "TN" in DC:
            if data.has_key(index):
                data[index].append({"PID": PID, "title": title})
            else:
                data[index] = [{"PID": PID, "title": title}]
    return data


# Write to file
def write_to_file(pid_by_date):
    f = open("LetterDates.txt", "w")
    for i in range(366):
        s = ""
        if i in pid_by_date:
            index = 0
            for pi in pid_by_date[i]:
                s += pi
                if index < (len(pid_by_date[i]) - 1):
                    s += ", "
                index += 1
        f.write(s + "\n")


if __name__ == '__main__':
    oid_docs = get_objects()
    data = by_day(oid_docs)
    with open('LetterDates.json', 'w') as outfile:
        json.dump(data, outfile, indent = 4)
    exit()
