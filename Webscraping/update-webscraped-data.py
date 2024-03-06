#use after webscraper-all

import csv

for i in range (1, 25):
    with open("Iliad\\Iliad" + str(i) + ".csv", "r", newline='', encoding="utf8") as input,\
    open("IliadEdited\\Iliad" + str(i) + ".csv", "w", newline='', encoding="utf8") as output:
        reader = csv.DictReader(input)
        writer = csv.writer(output)
        writer.writerow(["Book", "Line", "Word", "Text", "Length", "Foot"])

        footNumber = 1
        footNumbers = []
        lastFoot = []
        #firstRow = True

        for row in reader:
            #if (firstRow):
            #    firstRow = False
            #    continue
            
            if (footNumber == 7):
                footNumber = 1

            footNumbers.append(footNumber)

            if (row["Length"] != "elided synecphonesis" and row["Length"] != "elided"):
                lastFoot.append(row["Length"])

            if (lastFoot == ["long", "long"]):
                footNumber += 1
                #print(lastFoot)
                lastFoot = []
            elif (lastFoot == ["long", "short", "short"]):
                footNumber += 1
                #print(lastFoot)
                lastFoot = []

        #Iliad errors (fixed): 5.92 has "long hiatus" (changed to "long"), 7.409, 8.211, 10.343, 11.629,
        #                      16.20, 17.89 has "elided", 18.458 has "elided",
        #                      21.507, 24.296
        #Odyssey errors (fixed): 1.216, 12.142, 14.32, 24.115 and 24.236
        
        input.seek(0)
        next(reader)

        for n, row in enumerate(reader):
            rowLst = [row["Book"], row["Line"], row["Word"], row["Text"], row["Length"]]
            
            rowLst.append(footNumbers[n])
            assert(footNumbers[n] in range(1, 8))

            writer.writerow(rowLst)

