import os
import sys
sys.path.append(os.path.abspath("/usr/local/lib/python2.7/site-packages"))
import nltk
import json
import urllib2
import math
from nltk.text import TextCollection
from stanfordcorenlp import StanfordCoreNLP
import subprocess
import os
import time
import signal
from textblob import TextBlob
from nltk.corpus import stopwords
import xml.etree.ElementTree as ET


SEPARATORS = ['.', ',', ':', ';', '?', '!']
NOUNS_TAGS = ['NN', 'NNP', 'NNS', 'NNPS']
PROPER_NOUNS_TAGS = ['NNP', 'NNPS']
NAME_NER_TAGS = ['PERSON']#['O', 'DATE','NUM', 'TIME', 'STATE_OR_PROVINCE', 'LOCATION']

FIRST_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&omitHeader=true&wt=json"
SECOND_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=1000&omitHeader=true&wt=json"
THIRD_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=2000&omitHeader=true&wt=json"

OBJECTS_URL = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/(ancestors_ms:%22rekl:steilberg-ms180%22%20OR%20ancestors_ms:%22rekl:solon-ms106%22%20OR%20ancestors_ms:%22rekl:morgansteilberg-ms144%22%20OR%20ancestors_ms:%22rekl:boutelle-ms141%22%20OR%20ancestors_ms:%22rekl:morganboutelle-ms027%22)%20AND%20"

TOP_NOUNS_NUM = 10
TELE_UPPER_RATIO = 0.8

def toSingular(word):
    """
    Makes a noun singular. It can be a compounded noun.

    Args:
        word: a string containing the noun

    Returns:
         a string containing the new singular noun
    """
    newNoun = ""

    blob = TextBlob(word)
    total = len(blob.words)

    for j in range(total):
        noun = blob.words[j]
        if j == total - 1:
            noun = blob.words[j].singularize()

        if j != 0:
            newNoun += " "

        newNoun += str(noun)

    return newNoun

def getNounsUsingStanford(stfCore, text, posTags, nerMask=None, trueCase=False, join=False):
    nouns = []

    dataString = stfCore.annotate(text)
    try:
        data = json.loads(str(dataString))
    except(UnicodeEncodeError):
        print "Could not parse letter!"
        return None


    lastIndex = -2
    index = 0

    if len(data["sentences"]) == 0:
        return nouns

    for wordData in data["sentences"][0]["tokens"]:
        if 'pos' in wordData.keys() and 'ner' in wordData.keys():
            if wordData['pos'] in posTags and (nerMask is None or wordData['ner'] in nerMask):
                if 'truecaseText' in wordData.keys() and trueCase:
                    tag = 'truecaseText'
                elif 'text' in wordData.keys():
                    tag = 'text'
                else:
                    tag = 'word'

                if(wordData[tag].isalpha()):
                    if index == lastIndex + 1 and join:
                        nouns[-1] = nouns[-1] + ' ' + str(wordData[tag])
                    else:
                        nouns.append(str(wordData[tag]))

                    lastIndex = index

        index += 1

    return nouns

def getWords(text):
    """
    Gets a 2D list of the words in a text string

    Args:
        text: a string to be parsed

    Returns:
        a list of the of the following structure:
        "Hello World! Goodbye Cruel World!"
        becomes:
        [["Hello", "World", "!"], ["Goodbye", "Cruel", "World", "!"]]
    """
    sentances = nltk.sent_tokenize(text)
    phrases = []

    for sentance in sentances:
        phrases.append(nltk.word_tokenize(sentance))

    return phrases

def isItTele(phrases):

    count = 0
    upper = 0

    for phrase in phrases:
        for word in phrase:
            count += 1

            if word.isupper():
                upper +=1

    if count * 0.7 <= upper:
        return True

    return False

def getNoums(phrases, tags):
    """
    gets a list of nouns from a 2D list created from getWords()

    Args:
        phrases: a 2D list to be analyzed

    Returns:
        a list containing all the nouns
    """

    nouns = []

    for words in phrases:
        sentanceNouns = []
        indexes = []

        i = 0
        for word, tag in nltk.pos_tag(words):
            if(tag in tags) and word.isalpha():
                sentanceNouns.append(word)
                indexes.append(i)

            i += 1

        i = 0
        last = len(sentanceNouns) - 1
        while i < last:
            if indexes[i] + 1 == indexes[i + 1] and \
                    sentanceNouns[i].lower() != "hearst" and \
                    sentanceNouns[i + 1].lower() != "hearst":

                sentanceNouns[i] += " " + sentanceNouns[i + 1]
                indexes.pop(i + 1)
                sentanceNouns.pop(i + 1)

                last -= 1

            i += 1

        nouns += sentanceNouns

    return nouns

def getStems(phrases):
    """
    gets a list of stems (roots) of words from a 2D list created from getWords()

    Args:
        phrases: a 2D list to be analyzed

    Returns:
        a list containing all the stems (roots)
    """

    stemmer = nltk.stem.porter.PorterStemmer()
    stems = []
    for sentance in phrases:
        for word in sentance:
            if word not in SEPARATORS and not word.isdigit():
                stems.append(stemmer.stem(word))

    return stems

def getTF(words, textCol, text):
    """
    Gets the term frequencies for a list of words.

    Args:
        words: a list of strings containing the words
        textCol: a TextCollection object
        text: the text from which the term frequency is determined

    Returns:
         a list containing the term frequency score for each word of the original list
    """

    wordFreq = []
    for word in words:
        wordFreq.append(textCol.tf(word, text))

    return wordFreq

def getIDF(words):
    """
    Gets the inverse document frequency score for a list of words.

    Args:
        words: a list of strings containing the words

    Returns:
         a list containing the inverse document frequency score for each word of the original list
    """

    with open('IDFData.json') as dataFile:

        data = json.load(dataFile)
        wordIDF = []

        for word in words:
            singular = toSingular(word.lower())

            if singular in data:
                wordIDF.append(data[singular])
            else:
                wordIDF.append(0)

    return wordIDF

def getTopNouns(rekl):
    """
    Gets the tops nouns from a specific letter

    Args:
        rekl: a string containing the letter's identification rekl number

    Returns:
         a list containing the top nouns of the letter
    """

    with open('TopNounsData.json') as dataFile:
        data = json.load(dataFile)
        if rekl in data:
            return data[rekl]
        else:
            print "No letter with " + rekl + " of database!"


def updateTopNouns(stfCore):
    """
    Updates the json file containing the top nouns for each letter
    """

    letters = os.listdir('./ocrList')
    lettersTopNouns = {}

    stopWords = stopwords.words('english')

    for letter in letters:
        try:
            file = open('ocrList/' + letter, 'r')
            OCR = file.read()
            file.close()
            topNouns = calTopNouns(OCR, stfCore, stopWords)
            lettersTopNouns[letter[:-4]] = topNouns

        except:
            print "Unable to parse OCR from " + letter
            e = sys.exc_info()[0]
            print(e)

    with open('TopNounsData.json', 'w') as output:
        json.dump(lettersTopNouns, output)
        output.close()

def calTopNouns(OCR, stfCore, stopWords):
    """
    Determines the top nouns of a letter

    Args:
        OCR: a string containing the contents of the letter

    Returns:
         a list containing the top nouns of the letter
    """

    collection = TextCollection(OCR)
    phrases = getWords(OCR)

    if (not isItTele(phrases)):
        print "Not telem!"
        nouns = getNoums(phrases, NOUNS_TAGS)

    else:
        nouns = getNounsUsingStanford(stfCore, OCR, NOUNS_TAGS)

        if nouns is None:
            nouns = getNoums(phrases, NOUNS_TAGS)

    if len(nouns) < TOP_NOUNS_NUM:
        return nouns

    tf = getTF(nouns, collection, OCR)
    idf = getIDF(nouns)

    maxNum = max(idf)

    tfidf = []
    for i in range(len(tf)):
        if idf[i] == 0:
            idf[i] = maxNum + math.log(2)

        tfidf.append(tf[i] * idf[i])

    topTen = []
    for i in range(len(tfidf)):
        for j in range(10):
            if len(topTen) == j:
                topTen.append(i)
                break

            if tfidf[topTen[j]] == tfidf[i] and nouns[topTen[j]] == nouns[i]:
                break

            if tfidf[i] > tfidf[topTen[j]]:
                if len(topTen) == 10:
                    topTen[j + 1:] = topTen[j: -1]
                else:
                    topTen[j + 1:] = topTen[j:]

                topTen[j] = i
                break

    topNouns = []
    for i in range(len(topTen)):
        topNouns.append(nouns[topTen[i]])

    return topNouns

def crawlDatabase():
    """
    Determines the top nouns of a letter

    Args:
        OCR: a string containing the contents of the letter

    Returns:
         a list containing the top nouns of the letter
    """

    firstRequest = urllib2.Request(FIRST_THOUSAND,
                                   headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    firstResults = json.load(urllib2.urlopen(firstRequest))

    secondRequest = urllib2.Request(SECOND_THOUSAND,
                                    headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    secondResults = json.load(urllib2.urlopen(secondRequest))

    thirdRequest = urllib2.Request(THIRD_THOUSAND,
                                   headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})
    thirdResults = json.load(urllib2.urlopen(thirdRequest))

    docs = firstResults["response"]["docs"]
    docs.extend(secondResults["response"]["docs"])
    docs.extend(thirdResults["response"]["docs"])

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

        print(parentPID + "," + pids)

def getOCRs():

    with open("Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            pidValues = line.split(",")
            pidValues.reverse()

            parentPID = pidValues.pop()
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
                ocrFile = open("ocrList/" + parentPID + ".txt", "w+")
                ocrFile.write(ocr)
                ocrFile.close()

def getDates():
    dates = {}

    with open("Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]

        for line in lines:
            pidValues = line.split(",")
            xmlURL = "https://digital.lib.calpoly.edu/islandora/rest/v1/object/" + pidValues[0] + "/datastream/MODS"
            xmlRequest = urllib2.Request(xmlURL, headers={
                "authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})

            try:
                xmlContent = urllib2.urlopen(xmlRequest)
                if xmlContent.getcode() != 200:
                    xmlContent.close()
                    continue

                print pidValues[0]

                xmlData = ET.fromstring(xmlContent.read())
                xmlContent.close()

                for i in range(len(xmlData)):
                    if str(xmlData[i].tag) == "{http://www.loc.gov/mods/v3}originInfo":
                        date = xmlData[i][0].text

                        if date == None:
                            break
                        if "circa" in date:
                            date = date[6:]

                        date = date.split("-")

                        if len(date) == 3:
                            dateIndex = int(date[0]) * 10000 + int(date[1]) * 100 + int(date[2][:2])
                        elif len(date) == 2:
                            dateIndex = int(date[0]) * 10000 + int(date[1]) * 100
                        else:
                            dateIndex = int(date[0]) * 10000

                        dates[pidValues[0]] = dateIndex
                        break

            except:
                e = sys.exc_info()[0]
                print(e)

    prevAndNext = {}

    sortedList = sorted(dates, key=dates.__getitem__)
    for i in range(len(sortedList)):
        sortedList[i] = (sortedList[i], dates[sortedList[i]])

    for i in range(len(sortedList)):
        prevAndNext[sortedList[i][0]] = (sortedList[i-1][0], sortedList[(i+1) % len(sortedList)][0])

    with open('prevAndNext.json', 'w') as output:
        json.dump(prevAndNext, output)
        output.close()

def calDataIDF(stfCore):
    letters = os.listdir('./ocrList')
    wordIDF = {}

    texts = []
    for letter in letters:
        try:
            file = open('ocrList/' + letter, 'r')
            texts.append(file.read())
            file.close()
        except:
            e = sys.exc_info()[0]
            print(e)

    collection = TextCollection(texts)

    invalidOCR = open("invalidOCR.txt", "w")

    stopWords = stopwords.words('english')

    i = 0
    for text in texts:
        try:
            phrases = getWords(text)

            if(not isItTele(phrases)):
                nouns = getNoums(phrases, NOUNS_TAGS)

            else:
                nouns = getNounsUsingStanford(stfCore, text, NOUNS_TAGS)

                if nouns is None:
                    nouns = getNoums(phrases, NOUNS_TAGS)

            for noun in nouns:
                blob = TextBlob(noun)
                newNoun = ""

                idf = 0
                total = len(blob.words)
                for j in range(total):
                    word = blob.words[j]

                    if str(word) in stopWords:
                        print "Ignoring " + str(word)
                        continue

                    if j == total - 1:
                        word = blob.words[j].singularize()

                    idf += collection.idf(str(word))

                    if j != 0:
                        newNoun += " "

                    newNoun += str(word)

                if newNoun.lower() not in wordIDF:
                    wordIDF[newNoun.lower()] = idf

        except UnicodeDecodeError:
            print "Unable to parse OCR from " + letters[i]
            invalidOCR.write(letters[i][:-4] + "\n")

        i += 1

    invalidOCR.close()

    with open('IDFData.json', 'w') as output:
        json.dump(wordIDF, output)
        output.close()

def getAllProperNouns():
    letters = os.listdir('./ocrList')
    lettersProperNouns = []

    stfCore = StanfordCoreNLP('http://localhost', port=1000, timeout=5000)

    for letter in letters:
        try:
            file = open('ocrList/' + letter, 'r')
            OCR = file.read()
            file.close()

            properNouns = getNounsUsingStanford(stfCore, OCR, PROPER_NOUNS_TAGS,
                                                nerMask=NAME_NER_TAGS, trueCase=True, join=True)

            for noun in properNouns:
                if str(noun) not in lettersProperNouns:
                    lettersProperNouns.append(str(noun))

        except:
            print "Unable to parse OCR from " + letter
            e = sys.exc_info()[0]
            print(e)

    with open('properNounsData.txt', 'w') as output:

        i = 0
        for name in lettersProperNouns:
            if i != 0:
                output.write(", ")

            output.write(str(name))
            i += 1

        output.close()


def linkLetters():

    links = {}
    with open('TopNounsData.json', 'r') as input:
        topNouns = json.load(input)
        input.close()

    for k,v in topNouns.iteritems():
        searchStr = "("

        if len(v) == 0:
            continue

        for i in range(len(v)):
            if i != 0:
                searchStr += "%20OR%20"

            searchStr += "(dc.title:" + v[i].replace(" ", "%20") + ")^" + str(10 - i)

        searchStr += ")"

        print OBJECTS_URL + searchStr
        try:
            data = urllib2.Request(OBJECTS_URL + searchStr,
                        headers={"authorization": "Basic Y2FzdGxlX2NvbXB1dGluZzo4PnoqPUw0QmU2TWlEP1FB"})

            parsedData = json.load(urllib2.urlopen(data))

        except:
            print "Unable to get information for " + k
            e = sys.exc_info()[0]
            print(e)

            links[k] = []

            continue

        info = {}
        PIDS = []
        titles = []

        length = len(parsedData["response"]["docs"])

        if length > 5:
            length = 5

        for j in range(length):
            PIDS.append(parsedData["response"]["docs"][j]["PID"])
            titles.append(parsedData["response"]["docs"][j]["fgs_label_s"])

        info["suggestions"] = PIDS
        info["titles"] = titles

        links[k] = info

    info = {}
    info["suggestions"] = []
    info["titles"] = []

    with open("Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            pidValues = line.split(",")

            if pidValues[0] not in links.keys():
                links[pidValues[0]] = info

        f.close()


    with open('links.json', 'w') as output:
        json.dump(links, output)
        output.close()

def updateData():
    print"---------------------------------------------------------------"
    print "Crawling Islandora Database"
    print"---------------------------------------------------------------"
    crawlDatabase()

    print"---------------------------------------------------------------"
    print "Getting all OCRs"
    print"---------------------------------------------------------------"
    getOCRs()

    print"---------------------------------------------------------------"
    print "Calculating all IDFs"
    print"---------------------------------------------------------------"
    pro = spinStanfordCore(1010)
    stfCore = StanfordCoreNLP('http://localhost', port=1010, timeout=5000)
    calDataIDF(stfCore)

    print"---------------------------------------------------------------"
    print "Getting all Top Nouns"
    print"---------------------------------------------------------------"
    updateTopNouns(stfCore)
    stopStanfordCore(pro)

    print"---------------------------------------------------------------"
    print "Linking Letters to Other Objects"
    print"---------------------------------------------------------------"
    linkLetters()


    print"---------------------------------------------------------------"
    print "Getting Previous and Next Letters"
    print"---------------------------------------------------------------"
    getDates()

def printDemoData(rekl):
    print "OCR:\n"
    try:
        file = open('ocrList/' + rekl + ".txt", 'r')
        print file.read()
        file.close()
    except:
        e = sys.exc_info()[0]
        print(e)

    print "\nTop Nouns:\n"

    nouns = getTopNouns(rekl)
    for i in range(TOP_NOUNS_NUM):
        print "Noun #" + str(i + 1) + ": " + nouns[i]

def spinStanfordCore(port):
    print "Starting Core"
    pro = subprocess.Popen(['java', '-mx4g', '-cp', '../stanford-corenlp-full-2018-10-05/*',
                      'edu.stanford.nlp.pipeline.StanfordCoreNLPServer', '-annotators',
                      'tokenize,ssplit,truecase,pos,lemma,ner','-port', str(port), '-timeout', '5000',
                      '-truecase.overwriteText'],
                      stdout=subprocess.PIPE, preexec_fn=os.setsid)

    print "Core started"
    time.sleep(10)

    return pro

def stopStanfordCore(pro):
    print "Stoping Core"
    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
    print "Core Stoped"

def main():
    os.chdir(os.path.dirname(sys.argv[0]))
    args = sys.argv

    if len(args) > 1:
        if args[1] == '-r':
            printDemoData(args[2])
        if args[1] == '-u':
            updateData()
        if args[1] == '-d':
            linkLetters()
        if args[1] == '-n':
            pro = spinStanfordCore(1000)
            getAllProperNouns()
            stopStanfordCore(pro)
    else:
        print "USAGE: -r prints the data about a specific letter"
        print "       -u updates the data in the database"
        print "       -d run debug function"

    return 0

if __name__ == '__main__':
    main()