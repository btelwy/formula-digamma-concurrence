import pandas as pd
#Not accessed directly, but still necessary
import mysql.connector
#suggested for use alongside pandas
from sqlalchemy import create_engine

#This script is an example of querying from the database dump provided
#from within Python, given you put database on your own local server
#The MySQL download can be found at:
#https://dev.mysql.com/downloads/installer/


#my configuration; replace with your own information
username = "root"
passwd = "mysql"
host = "localhost"
port = 3306

#"digamma" is the only database within the dump
#and it contains these tables:
#scansion, digammas, formulas, concurrence
dbName = "digamma"

connectionURL = f"mysql+mysqlconnector://{username}:{passwd}@{host}:{port}/{dbName}"
engine = create_engine(connectionURL, echo=True)


#an example query
query = """
SELECT Book, HasDigamma, count(*) FROM concurrence
WHERE Source LIKE "Od"
GROUP BY Book, HasDigamma
"""

with engine.connect() as con:
    #execute the query
    try:
        result = pd.read_sql_query(query, con)
        print("Query executed successfully.")
    except:
        print("Something went wrong.")


#print the results, to show it's working
print(result)