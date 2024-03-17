import csv
import unicodedata

#limitation: plosive + liquid is always treated as
#not satisfying long by position
#another one: the way the source represents elision


"""
Cases where initial digamma can be reconstructed:
1. hiatus after a short vowel, preventing elision which normally would have occurred, or the presence of νῦ ἐφελκυστικόν (“movable letter ν”)
    (the phenomenon in Ionic and Attic Greek where certain word forms ending in a vowel over time developed a ν at the end to prevent hiatus with the following word)
2. non-shortening of long vowels and diphthongs in hiatus, that is, the absence of correption
3. a vowel that should be short scanning as long, because the digamma served to make that vowel long by position
"""

def normalize(str):
    #normalizes a string, removing diacritics,
    #and making everything lowercase, for easy comparison
    return ''.join(c for c in unicodedata.normalize('NFD', str.lower())
        if unicodedata.category(c) != 'Mn')


def isVowel(phrase, index):
    #checks if char at index is a vowel by running every possibility of isSameVowel

    phrase = normalize(phrase)

    vowel = phrase[index:index + 1]
    return (vowel == "α" or vowel == "ε" or vowel == "ι"
        or vowel == "ο" or vowel == "η" or vowel == "υ"
        or vowel == "ω" or vowel == "e" or vowel == "o")


def isDiphthong(phrase, index):
    #checks if a vowel is the first part of a diphthong
    #diphthongs: αι, αυ, ει, ευ, οι, ου, ηυ, υι, ᾳ, ῃ, ῳ

    phrase = normalize(phrase)

    if (index + 1 < len(phrase)): #make sure it doesn't go out of bounds
        vowel = phrase[index : index + 1]
        nextVowel = phrase[index + 1 : index + 2]

        if (vowel == "α"):
            if (nextVowel == "ι" or nextVowel == "υ"):
                return True
        
        elif (vowel == "ε" or vowel == "e"):
            if (nextVowel == "ι" or nextVowel == "υ"):
                return True

        elif (vowel == "ο" or vowel == "o"):
            if (nextVowel == "ι" or nextVowel == "υ"):
                return True

        elif (vowel == "υ"):
            if (nextVowel == "ι"):
                return True

        elif (vowel == "η"):
            if (nextVowel == "υ"):
                return True
    
    return False


def longByPosition(prevPhrase, phrase):
    #add the first two letters of the current row
    #to the previous row for necessary context
    phrase = prevPhrase + phrase[0 : 2]
    
    for i in range (0, len(phrase) - 1):
        j = i + 1
        k = j + 1
        #i is the index of the current letter, j of the next letter, k of the next letter after that

        #if it's a vowel and not part of a diphthong, in which case it's already long
        if (isVowel(phrase, i) and not (isDiphthong(phrase, i) or (i > 0 and isDiphthong(phrase, i - 1)))):
            while (j + 1 < len(phrase) and (phrase[j:j + 1] == " " or phrase[j:j + 1] == "᾽")):
                #go to the next letter
                j += 1
                k = j + 1
            while ((phrase[k:k + 1] == " " or phrase[k:k + 1] == "᾽")):
                #go to the next letter after that
                k += 1
                
            #and the next char is a double consonant, mark long
            if ((phrase[j:j + 1] == "ξ" or phrase[j:j + 1] == "ψ" or phrase[j:j + 1] == "ζ")):
                return True
            
            #else if the next two letters are consonants,
            #categorize by if they're possibley a
            #plosive + liquid or #losive + nasal
            if (k + 1 < len(phrase) and not (isVowel(phrase, j) or isVowel(phrase, k) or phrase[j:j + 1] == "\n"
                or phrase[k:k + 1] == "\n")):
                if ((phrase[j:j + 1] == "π" or phrase[j:j + 1] == "β" or phrase[j:j + 1] == "φ" or
                    phrase[j:j + 1] == "τ" or phrase[j:j + 1] == "δ" or phrase[j:j + 1] == "θ" or
                    phrase[j:j + 1] == "κ" or phrase[j:j + 1] == "γ" or phrase[j:j + 1] == "χ")
                    and (phrase[k:k + 1] == "λ" or phrase[k:k + 1] == "ρ")):
                    return False
                
            return True


#Case 1: hiatus after a short vowel, preventing elision
def case1(row, prevRow):
    #ensure the previous vowel is short
    if (prevRow['Length'] == "long"):
        return False
    
    #that the previous vowel is word-final
    if (not isVowel(prevRow['Text'], len(prevRow['Text']) - 1)):
        return False

    #and that there's a word-initial vowel in the current word
    if (not isVowel(row['Text'], 0)):
        return False

    return True


#Case 2: non-shortening of vowels and diphthongs in hiatus
def case2(row, prevRow):
    #ensure that the previous syllable is long
    if (prevRow['Length'] == "short"):
        return False
    
    #that the previous vowel is word-final
    if (not isVowel(prevRow['Text'], len(prevRow['Text']) - 1)):
        return False

    #and that there's a word-initial vowel in the current word
    if (not isVowel(row['Text'], 0)):
        return False

    return True


#Case 3: a vowel that should be short scanning as long
#because digamma made it long by position
def case3(row, prevRow):
    #ensure that the previous syllable is long
    if (prevRow['Length'] == "short"):
        return False

    #and that the previous vowel does not qualify
    #for being long by position
    if (longByPosition(prevRow['Text'], row['Text'])):
        return False
    
    #but that it could if digamma were reconstructed
    #before it as either VϝC or VCϝ
    VϝC = longByPosition(prevRow['Text'], "ϝ" + row['Text'])
    VCϝ = longByPosition(prevRow['Text'], row['Text'][0] + "ϝ" + row['Text'][1:])

    if (not (VϝC or VCϝ)):
        return False

    return True


def doAllChecks(row, prevRow):
    #it is assumed that there could only be one
    #digamma per syllable, and there is only one
    #syllable per .csv row

    if (case1(row, prevRow)):
        return True
    
    if (case2(row, prevRow)):
        return True
    
    if (case3(row, prevRow)):
        return True

    return False


def canCheck(row, prevRow, rowNum, totalRows):
    #if it's not the last syllable in the file
    #in which case checking would cause an error
    #or if it's the first, in which case
    #there's not enough data to check
    if (rowNum > totalRows - 2 or rowNum == 1):
        return False
    
    #if it's the first syllable of a word
    #otherwise it probably wouldn't be initial digamma
    if (row['Word'] == prevRow['Word']):
        return False
    
    #if the two rows are not from the same line or book
    #otherwise there's not enough context
    if (row['Line'] != prevRow['Line']):
        return False
    if (row['Book'] != prevRow['Book']):
        return False
    
    #if there's elision in this syllable
    #or the previous one
    if ("’" in row['Text'] or "’" in prevRow['Text']):
        return False

    return True


#and now do the reconstructing
newCsvName = "Iliad+OdysseyDigammas"
newCsv = "Data\\Output Data\\" + newCsvName + ".csv"
inputCsvs = ["Data\\Input Data\\Scansion Data\\IliadEdited\\IliadCombined.csv",
            "Data\\Input Data\\Scansion Data\\OdysseyEdited\\OdysseyCombined.csv"]

csvs = [inputCsvs[0], inputCsvs[1]]

#Set to true to write output to a .csv file
shouldWriteCsv = False

#so the first line of the .csv isn't repeated
headerWritten = False

prevRow = None
rowNum = 1
totalRows = 0
digammaCount = 0 #number of possible digamma reconstructions


for inputCsv in inputCsvs:
    with open(newCsv, "a", newline='', encoding="utf8") as output:
        with open(inputCsv, "r", newline='', encoding="utf8") as input:
            
            writer = csv.writer(output)
            reader = csv.DictReader(input)

            #exhaust iterator to find number of rows
            #then reset it back to the start
            totalRows = len(list(reader))
            input.seek(0)
            next(reader)

            if (not headerWritten and shouldWriteCsv):
                writer.writerow(["Source","Book","Line","Word","Foot","Syllable","Text","Length","HasDigamma"])
                headerWritten = True

            for row in reader:
                isDigamma = 0 #indicating False

                source = ""
                if (inputCsv == csvs[0]):
                    source = "Il"
                else:
                    source = "Od"

                #make sure it's appropriate to
                #check for initial digamma here
                if (canCheck(row, prevRow, rowNum, totalRows)):
                
                    #if a digamma can be reconstructed
                    if (doAllChecks(row, prevRow)):
                        isDigamma = 1 #indicating True
                        digammaCount += 1
                
                if (shouldWriteCsv):
                    contents = [source, row['Book'], row['Line'],
                        row['Word'], row['Foot'], rowNum, row['Text'], row['Length'],
                        isDigamma]
                    writer.writerow(contents)

                prevRow = row
                rowNum += 1
    
print(f"Digamma count: {digammaCount}\n"
    f"Total number of syllables: {rowNum - 1}\n"
    f"Percentage of syllables with initial digamma: {digammaCount / rowNum * 100:.3f}\n"
    "Finished.")