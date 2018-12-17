import web

db = web.database(dbn='sqlite',
        db='AuctionBase.db' 
        #TODO: add your SQLite database filename
    )

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()
# Sample usage (in auctionbase.py):
#
# t = sqlitedb.transaction()
# try:
#     sqlitedb.query('[FIRST QUERY STATEMENT]')
#     sqlitedb.query('[SECOND QUERY STATEMENT]')
# except Exception as e:
#     t.rollback()
#     print str(e)
# else:
#     t.commit()
#
# check out http://webpy.org/cookbook/transactions for examples

# returns the current time from your database
def getTime():
    # TODO: update the query string to match
    # the correct column and table name in your database
    query_string = 'select Time from CurrentTime'
    results = query(query_string)
    # alternatively: return results[0]['currenttime']
    return results[0].Time 

# returns a single item specified by the Item's ID in the database
# Note: if the `result' list is empty (i.e. there are no items for a
# a given ID), this will throw an Exception!
def getItemById(item_id):
    # TODO: rewrite this method to catch the Exception in case `result' is empty
    query_string = 'select * from Items where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        result[0]
        return result[0]
    except:
        return None

#sets the time to a time specified by the user on the /selecttime page
# will not run if the time selected is before the current time
def setTime(time):
    query_string = 'update CurrentTime set Time = $t'
    db.query(query_string, {'t': time})


## the following three functions help us display relevant information to users
#  when they do a search

def getBid(itemID):
    query_string = 'SELECT * FROM Bids WHERE ItemID = $itemID'
    try:
        return query(query_string,{'itemID' : itemID})
    except:
        return None

def getCategories(itemID):
    
    query_string = 'select Category from Categories where ItemID = $item_id'
    try:
        return query(query_string, {'item_id': itemID})
    except:
        return None

def getAuctionWinner(itemID, price):
    query_string = 'select UserID FROM Bids WHERE Amount = $price AND ItemID = $item_id'
    try:
        return query(query_string,{'price':price, 'item_id' : itemID})
    except:
        return None


def addBid(price,itemID,userID):
    query_string = 'INSERT INTO Bids VALUES ($itemID,$userID,$price,$time)'
    t = transaction()
    try:
        db.query(query_string,{'itemID':itemID, 'userID':userID, 'price':price, 'time': getTime()})
        result = True
    except Exception as e:
        t.rollback()
        print str(e)
        result = False
    return result


def search(queryString,searchVars):
    t = transaction()
    try:
        result = query(queryString,searchVars)
    except Exception as e:
        t.rollback()
        result = str(e)
        return result
    else:
        t.commit()
    return result


    

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}):
    return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################

#TODO: additional methods to interact with your database,
# e.g. to update the current time
