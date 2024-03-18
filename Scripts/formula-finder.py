import csv
import lxml.etree as etree
import pprint
from collections import defaultdict
import betacode.conv as betacode
import re

#Note: This script is in need of optimization, and as such, may take a few seconds to run

textFiles = ["Data\\Input Data\\Text Data\\IliadTextEdited.csv",
            "Data\\Input Data\\Text Data\\OdysseyTextEdited.csv"]
syllFiles = ["Data\\Input Data\\Scansion Data\\IliadEdited\\IliadCombined.csv",
            "Data\\Input Data\\Scansion Data\\OdysseyEdited\\OdysseyCombined.csv"]
xmlFiles = ["Data\\Input Data\\Diorisis\\Homer (0012) - Iliad (001).xml",
            "Data\\Input Data\\Diorisis\\Homer (0012) - Odyssey (002).xml"]

def getPOSData(tree):
    #parts of speech recorded in .xml file:
    #noun, proper, pronoun, particle, article, verb, adjective, adverb, preposition, conjunction

    #a list for part of speech data
    posData = []
    unknownCount = 0
    totalCount = 0

    #for every "word" element in the .xml file
    for item in tree.findall(f'./text/body//sentence//word'):
        if item is not None:
            #get the word's "form" child element
            wordForm = item.get("form")
            wordForm = re.sub(r"[1;()/\\+=*\|]", "", wordForm)

            #try to get "POS" child element of the word's "lemma" child element
            #but this doesn't always exist in the data, so catch errors instead of crashing
            try:
                #if it doesn't exist
                if (item.find("./lemma").get("POS") == None):
                    wordPOS = "unknown"
                else:
                    wordPOS = item.find("./lemma").get("POS")
            except:
                wordPOS = "unknown"

            #for debugging purposes
            if (wordPOS == "unknown"):
                unknownCount += 1
            totalCount += 1

            #add an element to the posData list that itself is a list of (word, POS)
            posData.append([wordForm, wordPOS])

    print(f"Percentage of words per source with \"unknown\" POS: {unknownCount / totalCount * 100:.2f}%")
    return posData


#the dict that will ultimately store a word's location with its data
#must be placed up here outside the loops so as to only be initialized once
wordData = {}

#open the three files for the Iliad and Odyssey
for (textFile, syllFile, xmlFile) in zip(textFiles, syllFiles, xmlFiles):
    with open(textFile, "r", encoding="UTF-8", newline="") as textF, \
        open(syllFile, "r", encoding="UTF-8", newline="") as syllF, \
            open(xmlFile, "rb") as xmlF:
        
        #reader object for the "text" .csv files; skip the header
        textReader = csv.reader(textF)
        next(textReader)
        #reader object for the "syllable" .csv files
        syllRows = syllF.readlines()
        #index to keep track of rows in syllRows; set to 1 to skip header
        syllIndex = 1

        #a tree object for reading the .xml file
        tree = etree.fromstring(xmlF.read())
        #index for keeping track of words in the .xml file
        xmlIndex = 0

        #get part of speech data from .xml
        posData = getPOSData(tree)
        

        #iterate through the rows of the "text" .csv files
        for line in textReader:
            #a string that is "title" + "book number" + "line number" + extra space for "word number" to be added
            location = line[0] + " " + line[1] + " " + line[2] + " "

            #find the right book and line number in syllRows,
            #i.e., the correct row in syllRows
            while (syllIndex < len(syllRows)):
                if (syllRows[syllIndex][0 : len(line[1])] == line[1] and \
                    syllRows[syllIndex][len(line[1]) + 1 : len(line[1]) + 1 + len(line[2])] == line[2]):
                    break
                
                syllIndex += 1

            #now add word numbers to each word in that line
            #where "line[3].split()" is a list of each word in the line
            for wordNum, split in enumerate(line[3].split()):
                #make word number 1-indexed rather than 0-indexed for consistency
                wordNum += 1

                #remove enclitics at start of words
                #note that this excludes enclitics from POS data, in case relevant
                if (len(split) > 2 and split[1] == "’"): #meaning there's an enclitic
                    split = re.sub(r"^.’", "", split)
                elif (len(split) > 3 and split[2] == "’"): #meaning there's an enclitic
                    split = re.sub(r"^..’", "", split)
                elif (split[0] == "’"): #also deal with words with erroneous initial ’
                    split = re.sub(r"^’", "", split)


                #a list for holding a word's scansion data
                metricInfo = []
                #the index in the "location" string where line[3] should be added
                wordNumStartIndex = len(line[1]) + 1 + len(line[2]) + 1
                #the index where line[3] should end
                wordNumEndIndex = wordNumStartIndex + len(str(wordNum))

                #find the right word number in the "syllable" .csv file
                while (syllIndex < len(syllRows) and \
                    syllRows[syllIndex][wordNumStartIndex : wordNumEndIndex] \
                            == str(wordNum)):

                    #mark the word as long or short in "metricInfo" accordingly
                    if syllRows[syllIndex].__contains__("long"):
                        metricInfo.append("long")
                    else:
                        metricInfo.append("short")
                    syllIndex += 1


                #convert Unicode polytonic Greek from .csv to Betacode Greek so it matches with Diorisis .xml
                betaForm = betacode.uni_to_beta(split) #betacode form of word
                betaForm = re.sub(r"[1;()/\\+=*\|]", "", betaForm)
                betaForm = re.sub(r"ῂ", "h", betaForm) #since the betacode library doesn't handle this

                #match each word to its POS using Diorisis .xml
                pos = "unknown"
                
                #prevXMLIndex is a backup to not get lost if a word can't be matched
                prevXMLIndex = xmlIndex
                loopCount = 0

                #keep going until the word recorded in posData is found in the .xml
                while (posData[xmlIndex][0] != betaForm):
                    if xmlIndex < len(posData) - 1:
                        xmlIndex += 1
                    loopCount += 1

                    #but don't search an unreasonable number of words ahead if the POS can't be found
                    #so just move on to the next word in that case
                    if loopCount > 10:
                        xmlIndex = prevXMLIndex
                        break
                    
                if (loopCount > 10): #if nothing could be found near the syllIndex
                    pos = "unknown"
                else:
                    pos = posData[xmlIndex][1]

                #words with "ᾐ" seem to have unknown POS
                #starting at Od. 2.388, everything is marked unknown

                wordData[location.join(['', str(wordNum)])] = \
                    {"text": split, "metrics": metricInfo, "POS": pos}


#max, min word number of formula
maxLen = 7
minLen = 2

#minimum occurrences of formula in order to be counted
minFreq = 4

#split the dict into two lists for speed
#the words' textual locations
wordDataKeys = list(wordData.keys())
#and the words' data
wordDataValues = list(wordData.values())

#dict to hold counts of substrings
substringDict = defaultdict(int)
#dict to hold locations of substrings
substringLocs = defaultdict(list)

#the actual formula recognition part
#iterate through the words in wordData, making sure there's no overshoot
for n in range(len(wordData) - maxLen):

    #iterate from max to min length
    for lenRange in range(maxLen, minLen - 1, -1):
        #a list that will be passed to join() to form a substring
        joinList = []
        #a list to hold the parts of speech in the substring
        posInStr = []
        #a list to hold the length values of the syllables in the substring
        metricsInStr = []

        #create one substring of each length in lenRange, concatenating data from each word
        for currentLength in range(lenRange):
            joinList.append(wordDataValues[n + currentLength]["text"])
            posInStr.append(wordDataValues[n + currentLength]["POS"])
            metricsInStr.append(" ".join(wordDataValues[n + currentLength]["metrics"]))
        

        #filter out substrings that do not have any of these parts of speech
        qualifyingPOS = ["noun", "proper", "verb", "adjective", "unknown"]
        posStr = " ".join(posInStr)

        #a string of "long" and "short"
        metricsStr = " ".join(metricsInStr)

        #TODO: Implement checking for templatic formulas with POS and metrical data
        #If something is templatic, a flag should be added to it to count its frequency differently

        posOkay = False
        isTemplate = True #set to True for now so code runs, will default to False later
        for pos in qualifyingPOS:
            #validate the substring as soon as it has a POS from the list
            if (pos in posStr):
                posOkay = True
        
        
        if (posOkay):
            substring = " ".join(joinList)
                    
            #increment the number of times this substring has been found
            substringDict[substring] += 1
            #and record the location of this substring instance in a list in the dict
            substringLocs[substring].append(wordDataKeys[n])


#a set is used to ensure no duplicates that could lead to double-remove errors later
removeList = set()
substringDictKeys = list(substringDict.keys())

for i in range(len(substringDictKeys) - 1):
    #substrings are added to dict in order of longest to shortest for any given position
    #so if the current sub contains the next sub, and they have the same num of occurrences
    #that next key can be removed

    currentStr = substringDictKeys[i]
    nextStr = substringDictKeys[i + 1]

    #the impossible case where the current phrase contains the next phrase, and both occur an equal number of times
    #the longer phrase appearing more often is impossible
    if (currentStr.__contains__(nextStr) and substringDict[currentStr] == substringDict[nextStr]):
        removeList.add(nextStr)
    #the impossible case where the longer phrase occurs less often than the shorter phrase
    elif (currentStr.__contains__(nextStr) and substringDict[currentStr] < substringDict[nextStr]):
        removeList.add(currentStr)


for key in removeList:
    substringDict.pop(key)

#TODO:
#Add functionality to concatenate neighboring/overlapping substrings that occur the same number of times
#and don't surpoass the length limit once concatenated, else remove them
#adjacency can be determined using substringLocs

numFormulas = 0
formulas = [x for x in substringDict if substringDict[x] >= minFreq]

#uncomment the line below in order to print all the formulas (will be long)
for formula in formulas:
    #pprint.pprint(f"{formula}: {substringLocs[formula]}")
    numFormulas += len(substringLocs[formula])

#print a summary of the data
print(f"Number of formulas fitting the criteria min length = {minLen}, max length = {maxLen}, min frequency = {minFreq}:\n" +
    f"Non-unique: {numFormulas}\n" +
    f"Unique: {len(formulas)}")


#Uncomment the code below in order to print the detected formulas into a .csv file
"""headerNotWritten = True
csvName = "Iliad+OdysseyFormulas"

#a variable that will be used to uniquely identify each row of the .csv; the primary key in the table
count = 1

for formula in formulas:
    for location in substringLocs[formula]:
        with open("Data\\Output Data\\" + csvName + ".csv", "a", newline='', encoding="utf8") as output:
            writer = csv.writer(output)

            #number of words in the formula
            numWords = len(formula.split())

            #Each location value consists of four "words",
            #e.g., "Od 23 318 0"
            locationData = location.split()

            #The source is "Il" or "Od"
            source = locationData[0]
            book = locationData[1]
            line = locationData[2]
            wordInLine = locationData[3]

            #write header once
            if headerNotWritten:
                writer.writerow(["Source,""Book","Line","Word","NumWords","Formula","ID"])
                headerNotWritten = False

            #Write the row in the .csv with data corresponding to this formula
            #Increment count by 1 just so it being 1-syllIndexed is consistent with data collected through SQL
            writer.writerow([source, book, line, wordInLine, numWords, formula, count])

            #increment in preparation for next row
            count += 1"""