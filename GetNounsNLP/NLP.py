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
import timeout_decorator
import signal
from textblob import TextBlob
from nltk.corpus import stopwords
import xml.etree.ElementTree as ET

PORT = 1010

SEPARATORS = ['.', ',', ':', ';', '?', '!']
NOUNS_TAGS = ['NN', 'NNP', 'NNS', 'NNPS']
PROPER_NOUNS_TAGS = ['NNP', 'NNPS']
NAME_NER_TAGS = ['PERSON']#['O', 'DATE','NUM', 'TIME', 'STATE_OR_PROVINCE', 'LOCATION']

OBJECTS_URL = "https://digital.lib.calpoly.edu/islandora/rest/v1/solr/(ancestors_ms:%22rekl:steilberg-ms180%22%20OR%20ancestors_ms:%22rekl:solon-ms106%22%20OR%20ancestors_ms:%22rekl:morgansteilberg-ms144%22%20OR%20ancestors_ms:%22rekl:boutelle-ms141%22%20OR%20ancestors_ms:%22rekl:morganboutelle-ms027%22)%20AND%20"

TOP_NOUNS_NUM = 10
TELE_UPPER_RATIO = 0.8

def toSingular(word):
    """
    Makes a noun singular. It can be a compounded noun.

    :arg:
        word (str): a string containing the noun

    :returns:
         str: a string containing the new singular noun
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

@timeout_decorator.timeout(6)
def getNounsUsingStanford(stfCore, text, posTags, nerMask=None, trueCase=False, join=False):
    """
    Gets a list of nouns in a text using Stanford Core

    :arg:
        stfCore (object): a stanford core object
        text (str): the text to be parsed
        posTags (list): a list of tags that the function looks for and adds to list to be returned
        nerMask (list): (Optional) a list of NER tags that the function looks for and adds to list to be returned
        trueCase (bool): whether it should return the true case format or the original word
        join (bool): whether it should join nouns together into compounded nouns

    :returns:
        list: a list containing a list of nouns
    """

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
        if 'pos' in wordData.keys():
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

    :arg:
        text (str): a string to be parsed

    :returns:
        list: a list of the of the following structure:
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
    """
    Returns whether a OCR is a telegram or not

    :arg:
        phrases (list): A 2D list containing words

    :returns:
        bool: whether the OCR is a telegram or not
    """

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

    :arg:
        words (list): a 1D list of strings containing the words
        textCol (object): a TextCollection object
        text (str): the text from which the term frequency is determined

    :returns:
         list: containing the term frequency score for each word of the original list
    """

    wordFreq = []
    for word in words:
        wordFreq.append(textCol.tf(word, text))

    return wordFreq

def getIDF(words):
    """
    Gets the inverse document frequency score for a list of words.

    :arg:
        words (list): a list of strings containing the words

    :returns:
         list: containing the inverse document frequency score for each word of the original list
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

    :arg:
        rekl (str): a string containing the letter's identification rekl number

    :returns:
         list: containing the top nouns of the letter
    """

    with open('TopNounsData.json') as dataFile:
        data = json.load(dataFile)
        if rekl in data:
            return data[rekl]
        else:
            print "No letter with " + rekl + " of database!"


def updateTopNouns(stfCore, pro, path):
    """
    Updates the json file containing the top nouns for each letter. I can restart the Stanford Core in case of error.

    :arg:
        stfCore (object): a Stanford Core object
        pro (object): a object that points to the Stanford Core process
        path (str): a sting containing the path to this script

    :returns:
         object: a object that points to the Stanford Core process
    """

    letters = os.listdir('../Content/ocr')
    lettersTopNouns = {}

    #stopWords = stopwords.words('english')

    for letter in letters:
        try:
            print letter
            file = open('../Content/ocr/' + letter, 'r')
            OCR = file.read()
            file.close()
            try:
                topNouns = calTopNouns(OCR, stfCore)

            #Janky stuff here.
            except(timeout_decorator.timeout_decorator.TimeoutError):
                print "Timeout!"
                stopStanfordCore(pro)
                pro = spinStanfordCore(PORT, path)
                topNouns = calTopNouns(OCR, stfCore)

            lettersTopNouns[letter[:-4]] = topNouns

        except:
            print "Unable to parse OCR from " + letter
            e = sys.exc_info()[0]
            print(e)

    with open('../Content/TopNounsData.json', 'w') as output:
        json.dump(lettersTopNouns, output)
        output.close()

    return pro

def calTopNouns(OCR, stfCore):
    """
    Determines the top nouns of a letter

    :arg:
        OCR (str): a string containing the contents of the letter
        stfCore (object): a Stanford Core object

    :returns:
         list: containing the top nouns of the letter
    """

    collection = TextCollection(OCR)
    phrases = getWords(OCR)

    if ((not isItTele(phrases)) or stfCore is None):
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

def getDates():
    """
    Gets the previous and next letters for each letter. It saves the information on the prevAndNext.json file
    """
    dates = {}

    with open("../Content/Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]

        for line in lines:
            pidValues = line.split(",")
            xmlURL = "https://digital.lib.calpoly.edu/islandora/rest/v1/object/" + pidValues[0] + "/datastream/MODS"
            secretDateURL = "https://digital.lib.calpoly.edu/islandora/rest/v1/object/" + pidValues[0] +\
                            "/datastream/MORGAN_PAPERS_SECRET_DATE"

            secretDateRequest = urllib2.Request(secretDateURL)
            xmlRequest = urllib2.Request(xmlURL)

            print pidValues[0]

            try:
                secretDateContent = urllib2.urlopen(secretDateRequest)
                if secretDateContent.getcode() == 200:
                    date = secretDateContent.read()
                    date = date.split("-")
                    dates[pidValues[0]] = int(date[0]) * 10000 + int(date[1]) * 100 + int(date[2][:2])
                    continue
            except:
                pass

            try:
                xmlContent = urllib2.urlopen(xmlRequest)
                if xmlContent.getcode() != 200:
                    xmlContent.close()
                    continue

                xmlData = ET.fromstring(xmlContent.read())
                xmlContent.close()

                for i in range(len(xmlData)):
                    if (pidValues[0] == "rekl:90935"):
                        print xmlData[i].tag
                    if str(xmlData[i].tag) == "{http://www.loc.gov/mods/v3}originInfo":
                        date = xmlData[i][0].text

                        if date == None:
                            break
                        if "circa" in date:
                            #date = date[6:]
                            break

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

    with open('../Content/prevAndNext.json', 'w') as output:
        json.dump(prevAndNext, output)
        output.close()

def calDataIDF(stfCore, pro, path):
    """
    Calculates the IDF score for every noun in each letter and saves the information to IDFData.json

    :arg:
        stfCore (object): a Stanford Core object
        pro (object): a object that points to the Stanford Core process
        path (str): a sting containing the path to this script

    :returns:
         object: a object that points to the Stanford Core process
    """

    letters = os.listdir('../Content/ocr')
    wordIDF = {}

    texts = []
    for letter in letters:
        try:
            file = open('../Content/ocr/' + letter, 'r')
            texts.append(file.read())
            file.close()
        except:
            e = sys.exc_info()[0]
            print(e)

    collection = TextCollection(texts)

    invalidOCR = open("../Content/invalidOCR.txt", "w")

    stopWords = stopwords.words('english')

    i = 0
    for text in texts:
        try:
            print letters[i][:-4]

            phrases = getWords(text)

            if((not isItTele(phrases)) or stfCore is None):
                nouns = getNoums(phrases, NOUNS_TAGS)

            else:
                try:
                    nouns = getNounsUsingStanford(stfCore, text, NOUNS_TAGS)
                except(timeout_decorator.timeout_decorator.TimeoutError):
                    print "Timeout on " + letters[i][:-4]
                    stopStanfordCore(pro)
                    pro = spinStanfordCore(PORT, path)
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

    return pro

def getAllProperNouns(pro, path):
    """
    Gets a list of all the proper nouns on the database and saves the information to properNounsData.txt

    :arg:
        pro (object): a object that points to the Stanford Core process
        path (str): a sting containing the path to this script

    :returns:
         object: a object that points to the Stanford Core process
    """

    letters = os.listdir('../Content/ocr')
    lettersProperNouns = []

    stfCore = StanfordCoreNLP('http://localhost', port=1000, timeout=500)

    for letter in letters:
        try:
            print letter
            file = open('../Content/ocr/' + letter, 'r')
            OCR = file.read()
            file.close()

            try:
                properNouns = getNounsUsingStanford(stfCore, OCR, PROPER_NOUNS_TAGS,
                                                nerMask=NAME_NER_TAGS, trueCase=True, join=True)
            except(timeout_decorator.timeout_decorator.TimeoutError):
                print "Timeout on " + letter
                stopStanfordCore(pro)
                pro = spinStanfordCore(PORT, path)
                properNouns = getNounsUsingStanford(stfCore, OCR, PROPER_NOUNS_TAGS,
                                                nerMask=NAME_NER_TAGS, trueCase=True, join=True)

            for noun in properNouns:
                if str(noun) not in lettersProperNouns:
                    lettersProperNouns.append(str(noun))

        except:
            print "Unable to parse OCR from " + letter
            e = sys.exc_info()[0]
            print(e)

    with open('../Content/properNounsData.txt', 'w') as output:

        i = 0
        for name in lettersProperNouns:
            if i != 0:
                output.write(", ")

            output.write(str(name))
            i += 1

        output.close()

    return pro

def linkLetters():
    """
    Creates the links.json file which links the letters to other related content.
    """

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

        print k
        #print OBJECTS_URL + searchStr

        try:
            data = urllib2.Request(OBJECTS_URL + searchStr)

            parsedData = json.load(urllib2.urlopen(data))

        except:
            print "Unable to get information for " + k
            e = sys.exc_info()[0]
            print(e)

            info = {}
            info["suggestions"] = []
            info["titles"] = []

            links[k] = info

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

    with open("../Content/Children.txt") as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            pidValues = line.split(",")

            if pidValues[0] not in links.keys():
                links[pidValues[0]] = info

        f.close()


    with open('../Content/links.json', 'w') as output:
        json.dump(links, output)
        output.close()

def updateData(path, stf=True):
    """
    Runs the NLP functions in the correct order.

    :arg:
        path (str): a sting containing the path to this script
        stf (bool): whether the script should use Stanford Core or not

    """

    print"---------------------------------------------------------------"
    print "Calculating all IDFs"
    print"---------------------------------------------------------------"
    if stf:
        pro = spinStanfordCore(PORT, path)
        stfCore = StanfordCoreNLP('http://localhost', port=PORT, timeout=5000)
    else:
        stfCore = None

    #pro = calDataIDF(stfCore, pro, path)

    print"---------------------------------------------------------------"
    print"Getting all Top Nouns"
    print"---------------------------------------------------------------"
    #pro = updateTopNouns(stfCore, pro, path)

    if stf:
        stopStanfordCore(pro)

    print"---------------------------------------------------------------"
    print "Linking Letters to Other Objects"
    print"---------------------------------------------------------------"
    #linkLetters()

    print"---------------------------------------------------------------"
    print "Getting Previous and Next Letters"
    print"---------------------------------------------------------------"
    getDates()

def printDemoData(rekl):
    """
    Prints the top nouns for a specific letter

    :arg:
        rekl (str): a sting containing letter's ID
    """

    print "OCR:\n"
    try:
        file = open('../Content/ocr/' + rekl + ".txt", 'r')
        print file.read()
        file.close()
    except:
        e = sys.exc_info()[0]
        print(e)

    print "\nTop Nouns:\n"

    nouns = getTopNouns(rekl)
    for i in range(TOP_NOUNS_NUM):
        print "Noun #" + str(i + 1) + ": " + nouns[i]

def spinStanfordCore(port, path):
    """
    Starts Stanford Core

    :arg:
        port (int): the port to be used by Stanford Core
        path (str): a sting containing the path to this script

    :returns:
         object: a object that points to the Stanford Core process
    """

    print "Starting Core"
    path = path[:-6]
    pro = subprocess.Popen(['java', '-mx500m', '-cp', path + '../stanford-corenlp/*',
                      'edu.stanford.nlp.pipeline.StanfordCoreNLPServer', '-annotators',
                      'tokenize,ssplit,pos','-port', str(port), '-timeout', '5000'],#,
                      #'-truecase.overwriteText'],
                      stdout=subprocess.PIPE, preexec_fn=os.setsid)

    print "Core started"
    time.sleep(10)

    return pro

def stopStanfordCore(pro):
    """
    Stops Stanford Core

    :arg:
        pro (object): a object that points to the Stanford Core process
    """

    print "Stoping Core"
    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
    time.sleep(5)
    print "Core Stoped"

def main():
    """
    Parses the command line input and runs the appropriate functionality
    """

    os.chdir(os.path.dirname(sys.argv[0]))
    args = sys.argv

    if len(args) > 1:
        if args[1] == '-r':
            printDemoData(args[2])
        if args[1] == '-u':
            if len(args) > 2:
                if args[2] == '--stfcore=False':
                    updateData(sys.argv[0], stf=False)
                else:
                    updateData(sys.argv[0])
            else:
                updateData(sys.argv[0])
        if args[1] == '-d':
            linkLetters()
        if args[1] == '-n':
            pro = spinStanfordCore(1000, sys.argv[0])
            pro = getAllProperNouns(pro, sys.argv[0])
            stopStanfordCore(pro)
    else:
        print "USAGE: -r prints the data about a specific letter"
        print "       -u updates the data in the database"
        print "       -d run debug function"

    return 0

if __name__ == '__main__':
    main()