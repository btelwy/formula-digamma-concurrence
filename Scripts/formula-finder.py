import csv
import lxml.etree as etree
from pprint import pprint as pprint
from collections import defaultdict
import betacode.conv as betacode
import re
import numpy as np

#Note: This script is in need of optimization, and as such, may take a few seconds to run

textFiles = ["Data\\Input Data\\Text Data\\IliadTextEdited.csv",
            "Data\\Input Data\\Text Data\\OdysseyTextEdited.csv"]
syllFiles = ["Data\\Input Data\\Scansion Data\\IliadEdited\\IliadCombined.csv",
            "Data\\Input Data\\Scansion Data\\OdysseyEdited\\OdysseyCombined.csv"]
xmlFiles = ["Data\\Input Data\\Diorisis\\Homer (0012) - Iliad (001).xml",
            "Data\\Input Data\\Diorisis\\Homer (0012) - Odyssey (002).xml"]


#Limitation: the detection of templatic formulas doesn't take into account semantics, so it overcounts
#Consider removing the distinction between proper and common nouns
#Also switch out lists for Numpy arrays
#And try multiprocessing, divided between Iliad and Odyssey, templatic and non-templatic, etc. for thread safety


#for tracking whether the Iliad or Odyssey is being read
alreadyRun = False

def getPOSData(tree):
    #parts of speech recorded in .xml file:
    #noun, proper, pronoun, particle, article, verb, adjective, adverb, preposition, conjunction

    #a list for part of speech data
    posData = []

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

            #add an element to the posData list that itself is a list of (word, POS)
            posData.append([wordForm, wordPOS])
    
    return posData


#check if two strings share at least one word in common
def shareOneWord(str1, str2):
    for word in str1.split():
        if (word in str2.split()):
            return True

    return False


def findTemplates(formulas):
    #the possibly templatic entries in the formulas dict
    for attribute in [x for x in formulas if "long" in x]:
        numMatching = len(formulas[attribute])
        
        #a basic check to filter one-offs out
        if (numMatching > 1):
            #check that the templates have at least one word in common
            #so this isn't a purely templatic approach
            
            areTemplates = set()
            for f in range(numMatching - 1):
                template1 = formulas[attribute][f][0]

                for g in range(f + 1, numMatching):
                    template2 = formulas[attribute][g][0]

                    if (shareOneWord(template1, template2)):
                        areTemplates.add(f)
                        areTemplates.add(g)

            #iterate in reverse order to avoid index-out-of-bounds error
            for n in range(numMatching - 1, -1, -1):
                if n not in areTemplates:
                    del formulas[attribute][n]
            if (len(formulas[attribute]) == 0):
                formulas.pop(attribute)

        #if this attribute only appears once
        else:
            formulas.pop(attribute)
    
    return formulas


def removeExtraneous(formulas, templatic):
    #a set is used to ensure no double-remove errors later
    extraneous = set()

    substrings = []
    if (not templatic):
        substrings = [x for x in formulas if "long" not in x]
    else:
        substrings = [x for x in formulas if "long" in x]

    for i in range(len(substrings) - 1):
        #substrings are added to dict in order of longest to shortest for any given position
        currentStr = substrings[i].replace("long", "").replace("short", "").rstrip()
        currentStrFreq = len(formulas[substrings[i]])
        nextStr = substrings[i + 1].replace("long", "").replace("short", "").rstrip()
        nextStrFreq = len(formulas[substrings[i + 1]])

        #nextStr is shorter
        if (nextStr in currentStr):
            #discard next phrase if it's part of a longer phrase
            if (currentStrFreq == nextStrFreq):
                extraneous.add(substrings[i + 1])
            #discard current phrase if it contains a more frequent smaller phrase
            elif (currentStrFreq < nextStrFreq):
                extraneous.add(substrings[i])
    
    for key in extraneous:
        formulas.pop(key)

    return formulas



def removeDuplicates(formulas):
    


    return formulas



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

        #for tracking the number of "unknown" POS in each source
        unknownCount = 0
        totalCount = 0


        #iterate through the rows of the "text" .csv files
        for line in textReader:
            #a string that is "title" + "book number" + "line number"
            location = line[0] + " " + line[1] + " " + line[2]

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

                #match each word to its POS using Diorisis .xml, with "unknown" as the default
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
                
                #if nothing could be found near the syllIndex
                totalCount += 1
                if (loopCount > 10):
                    pos = "unknown"
                    unknownCount += 1
                else:
                    pos = posData[xmlIndex][1]

                #words with "ᾐ" seem to have unknown POS
                #starting at Od. 2.388, everything is marked unknown

                completeLocation = location + " " + str(wordNum)
                wordData[completeLocation] = \
                    {"text": split, "metrics": metricInfo, "POS": pos}


        #print data about the number of "unknown"'s
        if (not alreadyRun):
            print(f"Percentage of words in the Iliad with \"unknown\" POS: {unknownCount / totalCount * 100:.2f}%")
            alreadyRun = True
        else:
            print(f"Percentage of words in the Odyssey with \"unknown\" POS: {unknownCount / totalCount * 100:.2f}%")

#end of looping through the files for data collection; now process that data
#---------------------------------------------------------------------------------------
#max, min word number of formula
maxLen = 7
minLen = 2

#minimum occurrences of formula in order to be counted
minFreq = 4

#split the dict into two lists for speed:
#the words' textual locations
wordDataKeys = list(wordData.keys())
#and the words' data
wordDataValues = list(wordData.values())


#dict to hold locations of both regular and templatic formulas
#the keys are the formulas themselves for regular ones, the attributes for templatic ones
formulas = defaultdict(list)


#the actual formula recognition part:
#iterate through all the words
for n in range(len(wordData) - maxLen):

    #iterate from max length to min length
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
        qualifyingPOS = ["noun", "proper", "verb", "adjective"]
        posStr = " ".join(posInStr)

        #a string of "long"s and "short"s
        metricsStr = " ".join(metricsInStr)


        #regardless of whether a formula is templatic, the parts of speech need to be okay first
        posOkay = False

        for pos in qualifyingPOS:
            #validate the substring as soon as it has a POS from the list
            if (pos in posStr):
                posOkay = True
        

        if (posOkay):
            substring = " ".join(joinList)
            attribute = posStr + " " + metricsStr

            #and record the location of this substring instance
            formulas[substring].append([substring, wordDataKeys[n], attribute])
            #as well as information about it as a potential template
            formulas[attribute].append([substring, wordDataKeys[n], attribute])


#to count as a formula repetition, either the formula's text needs to match another's,
#or both its parts of speech and metrics need to match another's

#remove templatic entries that aren't actually templates
formulas = findTemplates(formulas)

#remove extraneous templates
formulas = removeExtraneous(formulas, True)
#remove extraneous standard formulas
formulas = removeExtraneous(formulas, False)

#remove overlap between templatic and standard formulas
formulas = removeDuplicates(formulas)



#TODO:
#Add functionality to concatenate neighboring/overlapping substrings that occur the same number of times
#and that don't surpoass the length limit once concatenated, else remove them
#adjacency can be determined using substringLocs


allFormulas = [x for x in formulas if len(formulas[x]) > minFreq]
totalFormulas, totalStandard, totalTemplatic, totalStandardUnique, totalTemplaticUnique = 0, 0, 0, 0, 0

for formula in allFormulas:
    totalFormulas += len(formulas[formula])
    if ("long" in formula):
        totalTemplatic += len(formulas[formula])
        totalTemplaticUnique += 1
    else:
        totalStandard += len(formulas[formula])
        totalStandardUnique += 1

    """uncomment this line in order to print all the formulas (will be long)"""
    pprint(f"{formula}: {len(formulas[formula])}, {formulas[formula]}")


#print a summary of the data
print(f"Number of formulas fitting the chosen criteria min length = {minLen}, max length = {maxLen}, min frequency = {minFreq}:\n" +
    f"Total: {totalFormulas}\n" +
    f"Standard: {totalStandard}\n" +
    f"Templatic: {totalTemplatic}\n" +
    f"Standard unique: {totalStandardUnique}\n" +
    f"Templatic unique: {totalTemplaticUnique}")

#Note: there were 60,000 total formulas before this editing


#Uncomment the code below in order to print the detected formulas into a .csv file
"""headerNotWritten = True
csvName = "Iliad+OdysseyFormulas" + ".csv"

#a variable that will be used to uniquely identify each row of the .csv; the primary key in the table
count = 1

for formula in formulas:
    for location in substringLocs[formula]:
        with open("Data\\Output Data\\" + csvName, "a", newline='', encoding="utf8") as output:
            writer = csv.writer(output)

            #number of words in the formula
            numWords = len(formula.split())
            
            #whether it's a templatic instance; boolean represented as int, to be compatible with SQL
            templatic = 0
            template = ""
            if ("T-" in location):
                #remove the "T-" from the front so it's not printed in the end result
                location = location[2:]
                templatic = 1
                template = wordData[location]

            #Each location value consists of four "words", e.g., "Od 23 318 1"
            locationData = location.split()

            #The source is "Il" or "Od"
            source = locationData[0]
            book = locationData[1]
            line = locationData[2]
            wordInLine = locationData[3]

            #write .csv header once
            if headerNotWritten:
                writer.writerow(["Source","Book","Line","Word","NumWords","Formula","IsTemplatic","Template","ID"])
                headerNotWritten = False

            #Write the row in the .csv with data corresponding to this formula
            #Increment count by 1 just so it being 1-syllIndexed is consistent with data collected through SQL
            writer.writerow([source, book, line, wordInLine, numWords, formula, templatic, template, count])

            #increment in preparation for next row
            count += 1
            
print("Finished.")"""