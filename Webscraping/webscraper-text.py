import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

baseURLOdyssey = "https://hypotactic.com/latin/index.html?Use_Id=odyssey"
baseURLIliad = "https://hypotactic.com/latin/index.html?Use_Id=iliad"
numbers = [str(i) for i in range (1, 25)]

browser = webdriver.Chrome()

data = []

for number in numbers:
    book = number

    browser.get(baseURLOdyssey + number)
    time.sleep(5)
    html = browser.page_source
    xpathLine = "/html/body/div[2]/div/div/div[contains(@class, 'line')]" #XPath for line class

    lines = browser.find_elements(By.XPATH, xpathLine)

    for line in lines:
        lineNumber = line.get_attribute("data-number")

        words = line.find_elements(By.XPATH, ".//span[contains(@class, 'word')]")

        lineText = ""
        firstWord = True

        for word in words:
            if (firstWord):
                lineText += word.text
                firstWord = False
            else:
                lineText += " " + word.text

        data.append([book, lineNumber, lineText])



with open("OdysseyText.csv", "w", newline='', encoding="utf8") as f:
    writer = csv.writer(f)
    writer.writerow(["Book", "Line", "Text"])
    writer.writerows(data)

browser.close()