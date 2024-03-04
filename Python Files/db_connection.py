#-------------------------------------------------------------------------
# AUTHOR: Nathaniel Battad
# FILENAME: index.py
# SPECIFICATION: database program for question 3 of CS4250 Assignment 2
# FOR: CS 4250- Assignment #2
# TIME SPENT: About 2 hours for questions 1 and 2, and about 4 hours for the coding question 3
#-----------------------------------------------------------*/

#IMPORTANT NOTE: DO NOT USE ANY ADVANCED PYTHON LIBRARY TO COMPLETE THIS CODE SUCH AS numpy OR pandas. You have to work here only with
# standard arrays

#importing some Python libraries
import psycopg2
from string import punctuation

def connectDataBase():
    # Create a database connection object using psycopg2
    DB_NAME = "corpus"
    DB_USER = "postgres"
    DB_PASS = "123"
    DB_HOST = "localhost"
    DB_PORT = "5432"
        
    try:
        connection = psycopg2.connect(database = DB_NAME,
                                      user = DB_USER,
                                      password = DB_PASS,
                                      host = DB_HOST,
                                      port = DB_PORT)
        print("successfully connected to database")
        return connection
    except:
        print("Unable to successfully connect to Database")


def createCategory(cur, catId, catName):

    # Insert a category in the database
    sql = "Insert into category (id_cat, name) Values (%s, %s)"
    recset = [catId, catName]
    cur.execute(sql, recset)


def createDocument(cur, docId, docText, docTitle, docDate, docCat):

    # 1 Get the category id based on the informed category name
    sql = "select id_cat from Category where name = %(catName)s"
    cur.execute(sql, {'catName': docCat})
    row = cur.fetchall()
    catID = row[0]

    # 2 Insert the document in the database. For num_chars, discard the spaces and punctuation marks.
    noPunc = ''.join(char for char in docText if char not in punctuation) # discard punctuations
    numChars = sum(not char.isspace() for char in noPunc) # get number of characters without spaces
    sql = "Insert into Document (doc_number, text, title, num_chars, date, category) Values (%s, %s, %s, %s, %s, %s)"
    recset = [docId, docText, docTitle, numChars, docDate, catID]
    cur.execute(sql, recset)



    # 3 Update the potential new terms.
    # 3.1 Find all terms that belong to the document. Use space " " as the delimiter character for terms and Remember to lowercase terms and remove punctuation marks.
    # 3.2 For each term identified, check if the term already exists in the database
    # 3.3 In case the term does not exist, insert it into the database
    termsInDoc = noPunc.lower().split() # split text into list of words using " " delimeter
    for term in termsInDoc:
        try:
            sql = "Select term from term where term = %(currentTerm)s"
            cur.execute(sql, {'currentTerm': term})
            termCheck = cur.fetchall()
            if termCheck:
                print("term already exists in the database")
            else:
                print("term does not exist, adding entry to database now")
                sql = "Insert into term (term, num_chars) Values (%s, %s)"
                recset = [term, len(term)]
                cur.execute(sql, recset)
        except:
            print("unable to successfully check if term exists")
    



    # 4 Update the index
    # 4.1 Find all terms that belong to the document
    # 4.2 Create a data structure the stores how many times (count) each term appears in the document
    # 4.3 Insert the term and its corresponding count into the database
    distinctTermsInDoc = list(set(termsInDoc))  # list for all the disctinct terms in the text
    trackTermAppearances = {}
    for term in distinctTermsInDoc:             # iterate through terms and get their number of appearances
        trackTermAppearances[term] = docText.lower().count(term)

    for term, count in trackTermAppearances.items():    # add each term and their counts into the Index
        sql = "Insert into Index(doc, term, term_count) Values(%s, %s, %s)"
        recset = [docId, term, count]
        cur.execute(sql, recset)
    


def deleteDocument(cur, docId):

    # 1 Query the index based on the document to identify terms
    sql = "Select term from index where doc = %(docId)s"
    cur.execute(sql, {'docId': docId})
    termsToDelete = cur.fetchall()

    # 1.1 For each term identified, delete its occurrences in the index for that document
    for term in termsToDelete:
        sql = "Delete From index Where doc = %(docId)s And term = %(term)s"
        cur.execute(sql, {'docId': docId, 'term': term})

    # 1.2 Check if there are no more occurrences of the term in another document. If this happens, delete the term from the database.
        sql = "Select Count(*) From index Where term = %(term)s"
        cur.execute(sql, {'term': term})
        termCount = cur.fetchall()[0]

        if termCount == 0:
            sql = "Delete From term Where term = %(term)s"
            cur.execute(sql, {'term': term})

    # 2 Delete the document from the database
    sql = "Delete From document Where doc_number = %(docId)s"
    cur.execute(sql, {'docId': docId})

def updateDocument(cur, docId, docText, docTitle, docDate, docCat):

    # 1 Delete the document
    deleteDocument(cur, docId)

    # 2 Create the document with the same id
    createDocument(cur, docId, docText, docTitle, docDate, docCat)

def getIndex(cur):

    # Query the database to return the documents where each term occurs with their corresponding count. Output example:
    # {'baseball':'Exercise:1','summer':'Exercise:1,California:1,Arizona:1','months':'Exercise:1,Discovery:3'}
    # ...
    termAndOccurences = {}

    sql = """
        Select term.term, document.title, Count(*) From term Join index On term.term = index.term
        Join document On index.doc = document.doc_number
        Group By term.term, document.title
        """

    cur.execute(sql)
    results = cur.fetchall()

    for result in results:
        term, title, count = result
        if term not in termAndOccurences:
            termAndOccurences[term] = f"{title}:{count}"
        else:
            termAndOccurences[term] += f", {title}:{count}"

    return dict(sorted(termAndOccurences.items()))
