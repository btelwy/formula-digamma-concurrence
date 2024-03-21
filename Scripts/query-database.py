import mysql.connector

#This script is an example of querying from the database dump provided
#from within Python, given you put database on your own local server
#The MySQL download can be found at:
#https://dev.mysql.com/downloads/installer/


#my configuration; replace with your own information
username = "root"
passwd = "mysql"

#"digamma" is the only database within the dump
#and it contains these tables:
#scansion, digammas, formulas, concurrence
db = mysql.connector.connect(
    database="digamma",
    host="localhost",
    user=username,
    password=passwd
)

#an example query
query = """
SELECT Book, HasDigamma, count(*) FROM concurrence
WHERE Source LIKE "Od"
GROUP BY Book, HasDigamma
"""

#execute the query
cursor = db.cursor()
try:
    cursor.execute(query)
    print("Query executed successfully.")
except:
    print("Something went wrong.")

#print the results, to show it's working
for item in cursor:
    print(item)