import os
import nltk
import json
import urllib2
import sys
import math
from nltk.text import TextCollection
from textblob import TextBlob


SEPARATORS = ['.', ',', ':', ';', '?', '!']
NOUNS_TAGS = ['NN', 'NNP', 'NNS', 'NNPS']

FIRST_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&omitHeader=true&wt=json"
SECOND_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=1000&omitHeader=true&wt=json"
THIRD_THOUSAND = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/RELS_EXT_hasModel_uri_ms:%22info:fedora/islandora:bookCModel%22%20AND%20ancestors_ms:%22rekl:morgan-ms010%22?rows=1000&start=2000&omitHeader=true&wt=json"

def toSingular(word):
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

def getNoums(phrases):
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
            if(tag in NOUNS_TAGS) and word.isalpha():
                sentanceNouns.append(word)
                indexes.append(i)

            i += 1

        i = 0
        last = len(sentanceNouns) - 1
        while i < last:
            if indexes[i] + 1 == indexes[i + 1]:
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
    wordFreq = []
    for word in words:
        wordFreq.append(textCol.tf(word, text))

    return wordFreq

def getIDF(words):
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

#TODO
def getTopNouns(OCR, rekl):
    name = "rekl:" + str(rekl) + ".txt"
    letters = os.listdir('./ocrList')
    if name not in letters:
        try:
            newFile = open("ocrList/" + name, "w")
        except:
            print "Could not create file!"

def calTopNouns(OCR):
    collection = TextCollection(OCR)
    phrases = getWords(OCR)
    nouns = getNoums(phrases)

    if len(nouns) < 10:
        return nouns

    tf = getTF(nouns, collection, OCR)
    idf = getIDF(nouns)

    #for i in range(len(nouns)):
    #    print nouns[i],
    #    print tf[i],
    #    print idf[i]

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

def calDataIDF():
    letters = os.listdir('./ocrList')
    wordIDF = {}
    letterFiles = []

    for letter in letters:
        try:
            letterFiles.append(open('ocrList/' + letter, 'r'))

        except:
            e = sys.exc_info()[0]
            print(e)

    texts = []
    for file in letterFiles:
        texts.append(file.read())

    collection = TextCollection(texts)

    invalidOCR = open("invalidOCR.txt", "w")

    i = 0
    for text in texts:
        try:
            phrases = getWords(text)
            nouns = getNoums(phrases)

            for noun in nouns:
                blob = TextBlob(noun.lower())
                newNoun = ""

                idf = 0
                total = len(blob.words)
                for j in range(total):
                    word = blob.words[j]
                    if j == total - 1:
                        word = blob.words[j].singularize()

                    idf += collection.idf(str(word))

                    if j != 0:
                        newNoun += " "

                    newNoun += str(word)

                if newNoun not in wordIDF:
                    wordIDF[newNoun] = idf

        except UnicodeDecodeError:
            print "Unable to parse OCR from " + letters[i]
            invalidOCR.write(letters[i][:-4] + "\n")

        i += 1

    invalidOCR.close()

    with open('IDFData.json', 'w') as output:
        json.dump(wordIDF, output)
        output.close()

    for file in letterFiles:
        file.close()

def updateData():
    crawlDatabase()
    getOCRs()
    calDataIDF()

def main():
    #crawlDatabase()
    #getOCRs()
    #calDataIDF()
    textFile = open("ocrList/rekl:12684.txt", 'r')
    text = textFile.read()

    print calTopNouns(text)

    return 0

if __name__ == '__main__':
    main()