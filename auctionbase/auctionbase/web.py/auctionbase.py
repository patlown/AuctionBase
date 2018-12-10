#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

def string_date_to_sql(str):
    return '\''+str+'\''

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        '/add_bid', 'add_bid',
        '/search','search'
        # TODO: add additional URLs here
        # first parameter => URL, second parameter => class name
        )




class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss']
        enter_name = post_params['entername']


        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)
        try:
            sqlitedb.setTime(selected_time)
        except Exception as e:
                print str(e)
            
        
            # do something

        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('select_time.html', message = update_message)


class add_bid:
    #another get request, renders add_bid.html on '/addbid' URL
    def GET(self):
            return render_template('add_bid.html')

    def POST(self):
        post_params = web.input()
        price = post_params['price']
        itemID = post_params['itemID']
        userID = post_params['userID']
        # TODO: this currently does not give much information on the error, we could add additional queries to check if the user exists, if the item exists, if the bid is closed
        # IDK if that is necessary, this currently works correctly otherwise
        if sqlitedb.addBid(price,itemID,userID):
            update_message = '(Thank you %s,Your bid of %s was offered on Item %s)' % (userID,price,itemID)
        else:
            update_message = 'Invalid Bid, Either UserID does not exist, ItemID does not exist, ItemID is closed or the price offered was less than current bid'

        return render_template('add_bid.html',message = update_message)    

class search:
    def GET(self):
        return render_template('search.html')


    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        minPrice = post_params['minPrice']
        maxPrice = post_params['maxPrice']
        status = post_params['status']

        #prepare query
        #build dict for variables that will be used when querying
        searchVars = {}
        query_string = formatSearch(itemID,userID,minPrice,maxPrice,status,searchVars)
        result = sqlitedb.search(query_string,searchVars)

        return render_template('search.html',search_result = result, search_params = searchVars)

        # print query_string



        

        # print post_params

#helper method for handling format of a search query
def formatSearch(itemID, userID, minPrice, maxPrice,status,searchVars):

    #build dict for storing and accessing user input
    keys = {'itemID': itemID, 'userID': userID, 'minPrice':minPrice,'maxPrice':maxPrice, 'status':status}
    
    #query builder for adding keys to correct clause, will be used to build searchString
    queryBuilder = {'SELECT':['DISTINCT','*'],'FROM':[],'WHERE':[]}
    #will be used to pass to search function, built at end 
    

    #main loop: iterate through keys and add to appropriate slot in queryBuilder,
    # once key has been added to queryBuilder, add the var to searchVars
    for key,value in keys.iteritems():
        #we may not have a value for the key in keys so we must check it
        if value != "":
            #logic for handling adding item to our query
            if "itemID" == key:
                #if we haven't added Items to our FROM clause
                if "Items" not in queryBuilder['FROM']:
                    #add it in
                    queryBuilder['FROM'].append('Items')
                #append to our current WHERE clause the itemID, using $itemID for query vars
                queryBuilder['WHERE'].append('Items.itemID = $itemID')
            elif "userID" == key:
                #we can get userID from Items table, no need to use Users
                if "Items" not in queryBuilder['FROM']:
                    #add it in
                    queryBuilder['FROM'].append('Items')  
                #this query needs to handle two case:
                #   case 1: no itemID is searched so we must display all items by this user
                #   case 2: we are given itemID so the user must be a seller of the item
                #since we select from items, we can add join users with items on userID-SellerUserID
                #This will account for having an item search or not.
                #we can achieve this with a nested subquery
                queryBuilder['WHERE'].append('EXISTS (SELECT U.userID FROM Users U WHERE U.userID = $userID AND Items.Seller_UserID = U.userID)')
            elif "minPrice" == key:
                #this follow similar logic as itemID, simple WHERE clause addition
                if "Items" not in queryBuilder['FROM']:
                    queryBuilder['FROM'].append('Items')
                queryBuilder['WHERE'].append('Items.Currently >= $minPrice')
            elif "maxPrice" == key:
                #same logic as minPrice
                if "Items" not in queryBuilder['FROM']:
                    queryBuilder['FROM'].append('Items')
                queryBuilder['WHERE'].append('Items.Currently <= $maxPrice')
            elif "status" == key:
                #the status of our bid is determined by the current time of the system
                #convert the current time to a string date that sql can evaluate
                time = string_date_to_sql(sqlitedb.getTime())

                #again, we will need Items table if it hasn't been added already
                if "Items" not in queryBuilder['FROM']:
                    queryBuilder['FROM'].append('Items')
                #since status was the key, our values are one of four choices corresponding
                #to the input options in the form
                if value == "open":
                    #to be open, the time must be before it ends, after it starts, and currently must be less than the buy_price
                    queryBuilder['WHERE'].append('Items.Started<' + time + ' AND Items.Ends>'+ time + 'AND Currently < Buy_Price')
                elif value == "close":
                    #to be closed, must be after ends or currently >= buy price
                    queryBuilder['WHERE'].append('Items.Ends < ' + time + 'OR Currently >= Buy_Price')
                elif value == "notStarted":
                    #to be not stared, current time must be less than start time
                    queryBuilder['WHERE'].append('Items.Started > ' + time)
                #if we didn't execute any of the above statements, than the selected choice was all and
                #that doesn't require any additions to the where clause
            #------------end if/elif  key conditionals------------------#
            #we have filtered and added a new variables to our query, we need to keep track of the keys
            #that we used and add the values to our searchVars dictionary
            searchVars[key] = value
        
    #------------end query building loop------------------#
    #we now need to build the search string that we will use, we have our queryBuilder filled so we can use that 
    #to determine what to add to our string
    return buildQuery(queryBuilder)
    


def buildQuery(queryBuilder):
    searchString = "SELECT"
    #iterate through our select,from and where lists to add to the string
    #just append values to select clause
    for value in queryBuilder['SELECT']:
        searchString = searchString + ' ' + value
    #make sure from clause has elements to add
    if len(queryBuilder['FROM'])!=0:
        searchString = searchString + ' FROM'
        #we need to put commas after our from attributes, to do this effectively, keep track of index of element
        for index,value in enumerate(queryBuilder['FROM']):
            if(index+1 != len(queryBuilder['FROM'])):
                searchString = searchString + ' ' + value + ','
            else:
                searchString = searchString + ' ' + value
    #make sure where clause has attributes in it
    if len(queryBuilder['WHERE'])!=0:
        searchString = searchString + ' WHERE'
        #same idea as FROM but this time we need to use ANDS, all ORs are already inserted
        for index,value in enumerate(queryBuilder['WHERE']):
            if(index+1 != len(queryBuilder['WHERE'])):
                searchString = searchString + ' ' + value + ' and'
            else:
                searchString = searchString + ' ' + value

    return searchString


    
###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
