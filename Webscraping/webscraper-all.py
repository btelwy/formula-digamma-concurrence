import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

baseURLOdyssey = "https://hypotactic.com/latin/index.html?Use_Id=odyssey"
baseURLIliad = "https://hypotactic.com/latin/index.html?Use_Id=iliad"
numbers = [str(i) for i in range (1, 25)]

browser = webdriver.Chrome()

for number in numbers:
    data = []
    book = number

    browser.get(baseURLIliad + number)
    time.sleep(5)
    html = browser.page_source
    xpathLine = "/html/body/div[2]/div/div/div[contains(@class, 'line')]" #XPath for line class

    lines = browser.find_elements(By.XPATH, xpathLine)

    for line in lines:
        lineNumber = line.get_attribute("data-number")
        wordNumber = 0

        words = line.find_elements(By.XPATH, ".//span[contains(@class, 'word')]")

        lineText = ""

        for word in words:
            wordNumber += 1

            sylls = word.find_elements(By.XPATH, ".//span[starts-with(@class, 'syll')]")
            lengths = ""

            for syll in sylls:
                length = syll.get_attribute("class")[5:]

                data.append([book, lineNumber, wordNumber, syll.text, length])

                #print(syll.text)
                #print(length)
            

    with open("Iliad\\Iliad" + number + ".csv", "w", newline='', encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerow(["Book", "Line", "Word", "Text", "Length"])
        writer.writerows(data)

browser.close()