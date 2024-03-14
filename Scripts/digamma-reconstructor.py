import csv
import pprint
from collections import defaultdict
import unicodedata


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


def insertDigamma(line, index):
    #Ϝ, ϝ
    #insert digamma at the index in the line
    line = line[: index] + "ϝ" + line[index + 1 :]
    return line

#possible limitation of not checking what's after the end of a line

#Case 1: hiatus after a short vowel, preventing elision
def case1(line):
    

    return -1


#Case 2: non-shortening of vowels and diphthongs in hiatus
def case2(line):


    return -1


#Case 3: a vowel that should be short scanning as long
#because digamma made it long by position
def case3(line):


    return -1


#and now do the reconstructing
