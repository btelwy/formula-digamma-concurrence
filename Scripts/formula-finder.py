import csv
import lxml.etree as etree
import pprint
from collections import defaultdict
import betacode.conv as betacode
import re

textFiles = ["TextEdited\\IliadTextEdited.csv", "TextEdited\\OdysseyTextEdited.csv"]
syllFiles = ["CombinedCSVs\\IliadCombined.csv", "CombinedCSVs\\OdysseyCombined.csv"]
xmlFiles = ["Diorisis\Homer (0012) - Iliad (001).xml", "Diorisis\Homer (0012) - Odyssey (002).xml"]

#these file lists put the Odyssey first, for testing
"""textFiles = ["TextEdited\\OdysseyTextEdited.csv", "TextEdited\\IliadTextEdited.csv"]
syllFiles = ["CombinedCSVs\\OdysseyCombined.csv", "CombinedCSVs\\IliadCombined.csv"]
xmlFiles = ["Diorisis\Homer (0012) - Odyssey (002).xml", "Diorisis\Homer (0012) - Iliad (001).xml"]"""


#figure out why the Odyssey is almost all "unknown" for POS

#parts of speech recorded in .xml file:
#noun, proper, pronoun, particle, article, verb, adjective, adverb, preposition, conjunction
#if a word is not found in the .xml, make POS "unknown"

wordData = {}

#open the three files for the Iliad and Odyssey
for (textFile, syllFile, xmlFile) in zip(textFiles, syllFiles, xmlFiles):
    with open(textFile, "r", encoding="UTF-8", newline="") as textF, \
        open(syllFile, "r", encoding="UTF-8", newline="") as syllF, \
            open(xmlFile, "rb") as xmlF:
        
        textReader = csv.reader(textF)

        syllRows = syllF.readlines() #read with default file IO, not as .csv
        index = 0 #index for syllRows

        tree = etree.fromstring(xmlF.read())
        xmlIndex = 0 #index for posData list
        posData = []

        for item in tree.findall(f'./text/body//sentence//word'):
            if item is not None:
                wordForm = item.get("form")
                wordForm = re.sub(r"[1;()/\\+=*\|]", "", wordForm)

                try:
                    wordPOS = item.find("./lemma").get("POS")
                except:
                    wordPOS = "unknown"

                posData.append([wordForm, wordPOS])
        

        for line in textReader:
            #title + book number + line number + extra space for word number
            location = line[0] + " " + line[1] + " " + line[2] + " "

            while (index < len(syllRows)): #find the right book and line number
                if (syllRows[index][0 : len(line[1])] == line[1] and \
                    syllRows[index][len(line[1]) + 1 : len(line[1]) + 1 + len(line[2])] == line[2]):
                    break
                
                index += 1

            #where "split" is each word in the line
            for wordNum, split in enumerate(line[3].split()):
                
                #remove enclitics at start of words
                #note that this excludes enclitics from POS data, in case relevant
                #potentially deal with this later
                if (len(split) > 2 and split[1] == "’"): #meaning there's an enclitic
                    split = re.sub(r"^.’", "", split)
                elif (len(split) > 3 and split[2] == "’"): #meaning there's an enclitic
                    split = re.sub(r"^..’", "", split)
                elif (split[0] == "’"):
                    split = re.sub(r"^’", "", split) #also deal with words with erroneous initial ’


                metricInfo = []
                
                wordNumStartIndex = len(line[1]) + 1 + len(line[2]) + 1
                wordNumEndIndex = wordNumStartIndex + len(str(wordNum))

                while (index < len(syllRows) and \
                    syllRows[index][wordNumStartIndex : wordNumEndIndex] \
                            == str(wordNum + 1)): #find the right word number

                    if syllRows[index].__contains__("long"):
                        metricInfo.append("long")
                    else:
                        metricInfo.append("short")

                    index += 1


                #convert Unicode Greek from .csv to Betacode Greek so it matches .xml
                betaForm = betacode.uni_to_beta(split) #betacode form of word
                betaForm = re.sub(r"[1;()/\\+=*\|]", "", betaForm)
                betaForm = re.sub(r"ῂ", "h", betaForm) #since the betacode library doesn't handle this

                #find POS of word from Diorisis .xml
                pos = "unknown"

                if (betaForm != "Text"): #if not the title row of .csv
                    #first item of every posData list is word form, second is POS
                    
                    loopCount = 0
                    prevXMLIndex = xmlIndex

                    while (posData[xmlIndex][0] != betaForm):
                        if xmlIndex < len(posData) - 1:
                            xmlIndex += 1
                        loopCount += 1

                        if loopCount > 10:
                            xmlIndex = prevXMLIndex
                            break
                    
                    if (loopCount > 10): #if nothing could be found near the index
                        pos = "unknown"
                    else:
                        pos = posData[xmlIndex][1]
                #words with "ᾐ" seem to have unknown POS
                #starting at Od. 2.388, everything is marked unknown

                wordData[location.join(['', str(wordNum)])] = \
                    {"text": split, "metrics": metricInfo, "POS": pos}
                #print(f'{split}, {metricInfo}, {pos}')
                #if pos == "unknown":
                    #print(f'{split}, {metricInfo}, {pos}')

del wordData["Title Book Line 0"] #remove first element from dict

#max, min word number of formula
maxLen = 4
minLen = 2

#minimum occurrences of formula in order to be counted
minFreq = 6

#split the dict into two lists, which is for some reason much faster
keys = list(wordData.keys())
values = list(wordData.values())

#dict to hold counts of substrings
substringDict = defaultdict(int)
substringLocs = defaultdict(list)

#currently only detects formulas by repetition of various lengths
for n in range(len(wordData) - maxLen): #iterate through words
    
    #for lenRange in range(minLen, maxLen + 1):
    for lenRange in range(maxLen, minLen - 1, -1): #iterate from max to min length
        substringList = [] #the list that's passed to join() to form a substring

        #create one substring of each length in lenRange
        for length in range(lenRange):
            substringList.append(values[n + length]["text"])
        
        substring = " ".join(substringList)
        
        substringDict[substring] += 1
        substringLocs[substring].append(keys[n])

        #consider issues with case here, like a substring being "ἔνειμεν Καὶ"



substringDictKeys = list(substringDict.keys())

print(len(substringDict))
removeList = set() #a set, so duplicates are removed

for i in range(len(substringDictKeys) - 1):
    #substrings are added to dict in order of longest to shortest for any given position
    #so if the current sub contains the next sub, and they have the same num of occurrences
    #that next key can be removed

    currentKey = substringDictKeys[i]
    nextKey = substringDictKeys[i + 1]

    #the case where the current phrase contains the next phrase, and both occur an equal number of times
    #the larger phrase appearing more often is impossible
    if (currentKey.__contains__(nextKey) and substringDict[currentKey] == substringDict[nextKey]):
        removeList.add(nextKey)
    #if the larger phrase occurs less often than the smaller phrase (inverse is impossible)
    elif (currentKey.__contains__(nextKey) and substringDict[currentKey] < substringDict[nextKey]):
        removeList.add(currentKey)


for key in removeList:
    substringDict.pop(key)

print(len(substringDict))


#add functionality to concatenate neighboring/overlapping substrings that occur the same number of times
#and don't surpoass the length limit once concatenated, else remove them
#adjacency can be determined using substringLocs
#consider adding a tag in substringLocs if a word is the last in its line


formulas = [x for x in substringDict if substringDict[x] >= minFreq]

#print(substringDict)

for formula in formulas:
    pprint.pprint(f"{formula}: {substringLocs[formula]}")