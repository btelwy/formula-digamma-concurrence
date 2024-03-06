from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import unicodedata
import torch
import csv
#import neuralnetwork

def getText(url, endPhrase):
    #consider replacing alpha iota subscripts/adscripts with an alpha-iota diphthong
    #to ensure the fact that it's probably long isn't erased by the normalizer function

    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    text = re.sub("[^Ͱ-ῼ\s.]", '', text) #remove everything except Greek letters and whitespace and periods
    text = re.sub("\s\s\s+", '', text) #make sure there is never more than one space in a row
    text = re.sub("\n\n", '\n', text) #remove empty lines
    text = re.sub("\s\s", ' ', text) #make double spaces single spaces

    endIndex = text.find(endPhrase) + len(endPhrase) - 1
    numPeriods = text.count(".", 0, endIndex)
    endIndex -= numPeriods
    text = re.sub("[.]", '', text) #remove periods

    text = text[:endIndex] #make sure there's no HTML after the end of the text
    while(text[0]) == ' ': #remove spaces at the start
        text = text[1:]

    return text


def isVowel(line, index):
    #checks if char at index is a vowel by running every possibility of isSameVowel

    line = normalize(line)

    vowel = line[index:index + 1]
    return (vowel == "α" or vowel == "ε" or vowel == "ι" or vowel == "ο" or vowel == "η" or vowel == "υ" or vowel == "ω"
            or vowel == "e" or vowel == "o")


def isLong(line, index):
    #checks if a vowel is long or short
    #returns 1 for long, 0 for short, 2 for undetermined / N/A

    vowel = line[index:index + 1]

    if (vowel == "ᾱ" or vowel == "ῑ" or vowel == "ῡ" or vowel == "η" or vowel == "ω" or vowel == "ō" or vowel == "ē"):
        return 1
    elif (vowel == "ᾰ" or vowel == "ῐ" or vowel == "ῠ" or vowel == "ĕ" or vowel == "ŏ"):
        return 0
    else:
        return 2


def isDiphthong(line, index):
    #checks if a vowel is the first part of a diphthong
    #diphthongs: αι, αυ, ει, ευ, οι, ου, ηυ, υι, ᾳ, ῃ, ῳ

    line = normalize(line)

    if (index + 1 < len(line)): #make sure it doesn't go out of bounds
        vowel = line[index : index + 1]
        nextVowel = line[index + 1 : index + 2]

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


def changeDiacritics(line, index, instruction):
    #a function to run the logic to check which vowel a vowel is
    #and then to add a macron if 1 or a breve if 0
    #only applicable to alpha, iota, omicron, epsilon, upsilon
    #since eta and omega and alpha with iota ad/subscript don't need diacritics

    vowel = line[index : index + 1] #the vowel in question is the single char at str[index]

    #lowercase alpha variants
    if (vowel == "α"):
        if instruction == 1:
            vowel = "ᾱ"
        elif instruction == 0:
            vowel = "ᾰ"
    
    #lowercase iota variants
    elif (vowel == "ι"):
        if instruction == 1:
            vowel = "ῑ"
        elif instruction == 0:
            vowel = "ῐ"
    
    #lowercase upsilon variants
    elif (vowel == "υ"):
        if instruction == 1:
            vowel = "ῡ"
        elif instruction == 0:
            vowel = "ῠ"
    
    #lowercase epsilon; actually e, but whatever
    elif (vowel == "ε"):
        if (instruction == 1):
            vowel = "ē"
        elif (instruction == 0):
            vowel = "ĕ"

    #lowercase omicron; actually uses Latin O for short and long, but ignore that
    elif (vowel == "ο"):
        if (instruction == 1):
            vowel = "ō"
        elif (instruction == 0):
            vowel = "ŏ"

    line = line[:index] + vowel + line[index + 1:] #replace the vowel at the index

    return line


def normalize(str):
    return ''.join(c for c in unicodedata.normalize('NFD', str.lower())
        if unicodedata.category(c) != 'Mn')


def longByPosition(line, syllableLengths):
    #a vowel followed by two consonants is long, with the exception that
    #a plosive followed by a liquid or a nasal will not necessarily lengthen a syllable
    #π, β, φ, τ, δ, θ, κ, γ and χ are plosives; λ and ρ are liquids
    #so in that case, it won't be marked long until later, if applicable
    #double consonants are ξ (for κς), ψ (for πς), and ζ
    #ignore spaces

    longIndices = []
    uncertainIndices = []
    
    for i in range (len(line) - 1): #no point going all the way to the end
        j = i + 1
        k = j + 1
        #i is the index of the current letter, j of the next letter, k of the next letter after that

        #if it's a vowel and not part of a diphthong, in which case it's already long
        if (isVowel(line, i) and not (isDiphthong(line, i) or (i > 0 and isDiphthong(line, i-1)))):

            while (j + 1 < len(line) and (line[j:j + 1] == " " or line[j:j + 1] == "᾽")):
                #go to the next letter
                j += 1
                k = j + 1
            while ((line[k:k + 1] == " " or line[k:k + 1] == "᾽")):
                #go to the next letter after that
                k += 1
            
            #print(line[j:j+1] + line[k:k+1])
    
            #and the next char is a double consonant, mark long
            if ((line[j:j + 1] == "ξ" or line[j:j + 1] == "ψ" or line[j:j + 1] == "ζ")):
                longIndices.append(i)
                i += 1
            
            #else if the next two letters are consonants, and categorize by whether a plosive + liquid or plosive + nasal
            elif k + 1 < len(line) and not (isVowel(line, j) or isVowel(line, k) or line[j:j + 1] == "\n" or line[k:k + 1] == "\n"):
                if ((line[j:j + 1] == "π" or line[j:j + 1] == "β" or line[j:j + 1] == "φ" or
                     line[j:j + 1] == "τ" or line[j:j + 1] == "δ" or line[j:j + 1] == "θ" or
                     line[j:j + 1] == "κ" or line[j:j + 1] == "γ" or line[j:j + 1] == "χ")
                     and (line[k:k + 1] == "λ" or line[k:k + 1] == "ρ")):
                    uncertainIndices.append(i)
                else:
                    longIndices.append(i)
                i += 2

    #update syllable lengths
    syllableCount = 0
    i = 0

    for i in range (len(line)):
        if i in longIndices:
            syllableLengths[syllableCount] = 1
        elif i in uncertainIndices:
            syllableLengths[syllableCount] = 2
        if (isVowel(line, i)):
            syllableCount += 1
        if (isDiphthong(line, i)):
            syllableCount -= 1

    return syllableLengths


def longVowelsAndDiphthongs(line):
    #creates syllableLengths list and fills it with certain and uncertain long syllables
    #from long vowels (eta, omega) and diphthongs
    #does not edit the line string at all

    lineLength = len(line)

    #mark diphthongs
    diphthongCount = 0
    vowelCount = 0
    longIndices = []
    uncertainIndices = []

    for i in range (lineLength):
        if (isVowel(line, i)):
            vowelCount += 1

            j = i + 1 #j is the index of the next letter after i
            while (j < lineLength and (line[j:j+1] == " " or line[j:j+1] == "᾽")):
                j += 1
            
            k = j + 1 #k is the index of the next letter after j, important for diphthongs
            while (k < lineLength and (line[k:k+1] == " " or line[k:k+1] == "᾽")):
                k += 1

            if (isDiphthong(line, i)):
                #if it's a non-word-final or word-final diphthong followed by vowel
                if (i < lineLength - 2 and (line[i+2:i+3] == ' ' or line[i+2:i+3] == '᾽') and (isVowel(line, k))):
                    uncertainIndices.append(vowelCount - diphthongCount)
                else:
                    longIndices.append(vowelCount - diphthongCount)
                diphthongCount += 1
                i += 1 #move past that diphthong
            #if it's a non-word-final or word-final eta or omega followed by vowel
            elif ((line[i:i + 1] == "η" or line[i:i + 1] == "ω")):
                #consider that the last letter of a line automatically goes to else; same for diphthongs above
                if (i < lineLength - 1 and (line[i+1:i+2] == ' ' or line[i+1:i+2] == '᾽') and (isVowel(line, j))):
                    uncertainIndices.append(vowelCount - diphthongCount)
                else:
                    longIndices.append(vowelCount - diphthongCount)


    syllableCount = vowelCount - diphthongCount
    syllableLengths = [None] * syllableCount #initialize list with syllable count void elements

    #fill in long syllables corresponding to diphthongs and etas and omegas
    #a 2 represents a syllable that could be long, but isn't certain
    for i in range (len(longIndices)):
        syllableLengths[longIndices[i] - 1] = 1
    for i in range (len(uncertainIndices)):
        syllableLengths[uncertainIndices[i] - 1] = 2

    return syllableLengths


def identifyFeet(syllableLengths):
    #using only the syllable lengths list, with 0 for short, 1 for long, and 2 for unsure
    #note that 0 is less "short" and more "set to short by default, since it had no other value"
    #fill in a list to classify each of the probably six feet as "spondee" or "dactyl" or sometimes "trochee"
    #works from the back of the list to the start
    #once each foot is identified, remove corresponding syllables from list to make processing easier

    #since this function will destroy the list
    syllables = list.copy(syllableLengths)

    feet = ["x"] * 6

    numSyllables = len(syllables)
    syllablesRemoved = 0 #incremented each time an item from syllableLengths is deleted to subtract from numSyllables
    currentFoot = 5 #index of next foot to add
   
    if (syllables[-2] == 1 and syllables[-1] == 1):
        feet[currentFoot] = "spondee"
    #not necessarily true, it could still be a spondee, adjust later
    else:
        feet[currentFoot] = "trochee"

    del syllables[-2:] #remove last two elements
    syllablesRemoved += 2
    currentFoot -= 1

    #work backwards from the end
    for currentFoot in range(4, -1, -1):
        #if there's room to take three syllables
        if (numSyllables - syllablesRemoved > 2):
            #if the second to last or last syllable is long, it must be a spondee
            if (syllables[-2] == 1 or syllables[-1] == 1):
                feet[currentFoot] = "spondee"
                del syllables[-2:] #remove last two elements

            #the harder cases remaining (no penultimate or final 1), it could either be a spondee or dactyl
            #dactyl case: 0 0 0, 1 0 0, 0 2 0, 0 0 2, 2 0 0, 2 0 2
            #spondee case: 2 0, 0 0, 0 2
            #problem case: 1 0 2;
            #it goes into the else and becomes a spondee, if it's not the final three syllables remaining
            #assume that if the last two syllables are both 0, it's a dactyl
            elif (syllables[-2] == 0 and syllables[-1] == 0):
                feet[currentFoot] = "dactyl"
                del syllables[-3:]

            elif (syllables[-3] == 2 and syllables[-2] == 0 and syllables[-1] == 2):
                feet[currentFoot] = "dactyl"
                del syllables[-3:]

            elif ((syllables[-3] == 1 and syllables[-2] == 0 and syllables[-1] == 0) or 
                  (syllables[-3] == 2 and syllables[-2] == 0 and syllables[-1] == 0)):
                feet[currentFoot] = "dactyl"
                del syllables[-3:]

            elif (syllables[-3] == 1 and syllables[-2] == 0 and syllables[-1] == 2):
                feet[currentFoot] = "dactyl"
                del syllables[-3:]

            elif (syllables[-3] == 2 and syllables[-2] == 0 and syllables[-1] == 2):
                feet[currentFoot] = "dactyl"
                del syllables[-3:]

            #if there are exactly three syllables left
            elif (numSyllables - syllablesRemoved == 3):
                feet[0] = "dactyl"
                del syllables[-3:]

            #if none of that is true, assume it's a spondee
            else:
                feet[currentFoot] = "spondee"
                del syllables[-2:]

        else: #if there's only two syllables left, it must be a spondee in the first foot, ending the loop
            feet[0] = "spondee"
            del syllables[-2:]

        if (feet[currentFoot] == "dactyl"):
            syllablesRemoved += 3
        else:
            syllablesRemoved += 2

    return feet


def markMetrics(line, feet):
    #convert list of "spondee", "dactyl", and "trochee" to syllable lengths list
    #syllable break algorithm:
    #ignore spaces and '᾽'

    syllables = []

    for i in range(len(feet)):
        if (feet[i] == "dactyl"):
            syllables.append(1)
            syllables.append(0)
            syllables.append(0)
        elif (feet[i] == "spondee"):
            syllables.append(1)
            syllables.append(1)
        elif (feet[i] == "trochee"):
            syllables.append(1)
            syllables.append(0)


    vowelCount = 0
    diphthongIndex = 100 #some arbitrary high number

    for i in range (len(line)):
        if isVowel(line, i):
            if (i < len(line) - 1 and isDiphthong(line, i)):
                line = changeDiacritics(line, i, syllables[vowelCount])
                diphthongIndex = i
                vowelCount += 1
            elif (i - 1 != diphthongIndex): #if it's not the second part of a diphthong
                line = changeDiacritics(line, i, syllables[vowelCount])
                vowelCount += 1

    return line

def scanLine(line):
    #algorithm:
    #first mark diphthongs
    #given number of vowels, start to make a list of bits representing long vs. short syllables
    #use that list and some assumptions to identify the type of each foot
    #then mark foot boundaries and caesurae using the foot list, and add more macrons and breves as necessary
    #mark caesurae with |, feet with /

    syllableLengths = longVowelsAndDiphthongs(line)
    syllableLengths = longByPosition(line, syllableLengths)
    
    #the first and penultimate syllables must always be long, and if the last syllable is empty, it should be uncertain
    syllableLengths[0] = 1
    syllableLengths[-2] = 1
    if (syllableLengths[-1] == None):
        syllableLengths[-1] = 2

    #for now, mark all other syllables as 0
    for i in range(len(syllableLengths)):
        if syllableLengths[i] == None:
            syllableLengths[i] = 0

    #identifyFeet is causing index out of bounds errors in markMetrics;
    #replace identifyFeet with a neural network function

    #feet = identifyFeet(syllableLengths)
    #line = markMetrics(line, feet)

    syllableLengthsString = ''.join([str(i) for i in syllableLengths])

    #remember to remove newline at the end of the file
    with(open("iliad-scansion-program.csv", "a", encoding="utf8", newline='')) as file:
        writer = csv.writer(file)
        writer.writerow([syllableLengthsString, line[-1]])

    #print(line)
    #print(syllableLengths)
    #print(feet)

    return line

"""
url = "https://www.perseus.tufts.edu/hopper/text?doc=Hom.+Od.+1&fromdoc=Perseus%3Atext%3A1999.01.0135"
#URL for Book 1: "https://www.perseus.tufts.edu/hopper/text?doc=Hom.+Od.+1&fromdoc=Perseus%3Atext%3A1999.01.0135"
endPhrase = "ὁδὸν τὴν πέφραδ᾽ Ἀθήνη" #the last part of the text; should be unique, so it can be searched for

iliadBaseURL = "https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0133%3Abook%3D"
iliadBooks = [["1", "δὲ χρυσόθρονος Ἥρη."],
              ["2", "Ξάνθου ἄπο δινήεντος"],
              ["3", "γλυκὺς ἵμερος αἱρεῖ"],
              ["4", "ἀλλήλοισι τέταντο"],
              ["5", "Ἄρη᾽ ἀνδροκτασιάων"],
              ["6", "ἐϋκνήμιδας Ἀχαιούς"],
              ["7", "ὕπνου δῶρον ἕλοντο"],
              ["8", "ἐΰθρονον Ἠῶ μίμνον"],
              ["9", "ὕπνου δῶρον ἕλοντο"],
              ["10", "λεῖβον μελιηδέα οἶνον"],
              ["11", "παύσατο δ᾽ αἷμα"],
              ["12", "ἀλίαστος ἐτύχθη"],
              ["13", "καὶ Διὸς αὐγάς"],
              ["14", "ἐν φόβον ὄρσῃ"],
              ["15", "αὐτοσχεδὸν οὖτα"],
              ["16", "δόσαν ἀγλαὰ δῶρα"],
              ["17", "οὐ γίγνετ᾽ ἐρωή"],
              ["18", "Ἡφαίστοιο φέρουσα"],
              ["19", "ἐλάσαι πολέμοιο"],
              ["20", "χεῖρας ἀάπτους"],
              ["21", "καὶ γοῦνα σαώσαι"],
              ["22", "Τρωϊάδων κλέος εἶναι"],
              ["23", "κέλομαι γὰρ ἔγωγε"],
              ["24", "διοτρεφέος βασιλῆος"]]

for book in iliadBooks:
    text = getText(iliadBaseURL + book[0], book[1]) #url and endphrase

    assert(text[-1] == book[1][-2])

    lines = text.splitlines()

    textLength = len(text)
    numLines = len(lines)

    #note that this removes iota subscripts and adscripts as well, though that only matters for alpha
    normalizedText = normalize(text) 
    normalizedLines = normalizedText.splitlines()

    scannedLines = []

    for i in range(numLines):
        scannedLines.append(scanLine(normalizedLines[i]))

    scannedText = ""

    #so there's no line break at the end when printing
    for i in range(numLines):
        if (i < numLines - 1):
            scannedText += (scannedLines[i] + "\n")
        else:
            scannedText += (scannedLines[i])

    #print(scannedText)"""