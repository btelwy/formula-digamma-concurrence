import csv
import pprint
from collections import defaultdict

"""
Cases where initial digamma can be reconstructed:
1. hiatus after a short vowel, preventing elision which normally would have occurred, or the presence of νῦ ἐφελκυστικόν (“movable letter ν”)
    (the phenomenon in Ionic and Attic Greek where certain word forms ending in a vowel over time developed a ν at the end to prevent hiatus with the following word)
2. non-shortening of long vowels and diphthongs in hiatus, that is, the absence of correption
3. a vowel that should be short scanning as long, because the digamma served to make that vowel long by position
"""

