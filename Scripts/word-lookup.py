import csv
import unicodedata

def normalize(str):
    return ''.join(c for c in unicodedata.normalize('NFD', str.lower())
        if unicodedata.category(c) != 'Mn')


files = ["TextEdited\\IliadTextEdited.csv", "TextEdited\\OdysseyTextEdited.csv"]

#maybe consider a "starts with" mode

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