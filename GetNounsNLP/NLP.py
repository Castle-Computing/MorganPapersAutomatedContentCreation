import os
import nltk
from nltk.text import TextCollection

SEPARATORS = ['.', ',', ':', ';', '?', '!']
NOUNS_TAGS = ['NN', 'NNP', 'NNS', 'NNPS']

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
            if(tag in NOUNS_TAGS):
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

def getIDF(words, textCol):
    wordIDF = []
    for word in words:
        wordIDF.append(textCol.idf(word))

    return wordIDF

def main():
    letters = os.listdir('./ocrList')
    texts = []
    for letter in letters:
        texts.append(open('ocrList/' + letter, 'r'))

    textsStings = []
    for text in texts:
        textsStings.append(text.read())

    collection = TextCollection(textsStings)
    phrases = getWords(textsStings[0])
    print phrases
    print getStems(phrases)
    nouns = getNoums(phrases)
    print nouns
    print getTF(nouns, collection, textsStings[0])
    print getIDF(nouns, collection)
    return 0

if __name__ == '__main__':
    main()