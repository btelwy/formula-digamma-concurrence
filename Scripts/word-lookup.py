import csv
import unicodedata
import mysql.connector
import sqlparse
from collections import defaultdict

#TODO: Implement features besides counting instances of a word
#Maybe have a "starts with" mode


def normalize(str):
    return ''.join(c for c in unicodedata.normalize('NFD', str.lower())
        if unicodedata.category(c) != 'Mn')


files = ["TextEdited\\IliadTextEdited.csv", "TextEdited\\OdysseyTextEdited.csv"]

print("Input a Greek word:")
target = input()

count = 0

for file in files:
    with open(file, "r", newline="", encoding="utf8") as f:
        
        reader = csv.DictReader(f)

        for line in reader:
            if target in normalize(line["Text"]).split():
                print(line["Title"] + ". " + line["Book"] + "." + line["Line"] + ": " + line["Text"])
                count += 1

print(f"{count} instances of \"{target}\" found")