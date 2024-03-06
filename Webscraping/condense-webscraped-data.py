#used after update-webscraped-data
#condenses the ____Edited folders into one .csv each

import csv

headerNotWritten = True

for i in range (1, 25):
    with open("OdysseyEdited\\Odyssey" + str(i) + ".csv", "r", newline='', encoding="utf8") as input,\
    open("OdysseyCombined.csv", "a", newline='', encoding="utf8") as output:
        reader = csv.reader(input)
        writer = csv.writer(output)

        #write header once
        if headerNotWritten:
            writer.writerow(["Book","Line","Word","Text","Length","Foot"])
            headerNotWritten = False

        for line in reader:
            if line != '' and line != ["Book","Line","Word","Text","Length","Foot"]: #don't copy blank rows or headers
                writer.writerow(line)