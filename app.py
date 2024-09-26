import hashlib
from sre_constants import SUCCESS
from unicodedata import category
from unittest import result
from colorama import Cursor
from flask import Flask, flash, redirect, render_template, request, session, template_rendered, url_for
import sqlite3 as sql
import flask
import datetime

import mysql.connector
from pandas import value_counts

app = Flask(__name__)
app.secret_key = 'CMPSC431W'

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('Main_webpage.html')

# For add-patient webpage


@app.route('/login.html', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        # firstname is the email of the user
        firstname = request.form['FirstName']
        result = add_name(firstname, request.form['LastName'])

        # login success
        if result:
            user_type = getUserType(firstname)
            session['user'] = firstname
            session['type'] = user_type

            # in this case, the user want to place order but not login yet
            # then, after login successfully, back to the placeOther.html
            '''if 'back_to_placeOther' in session:
                if session['back_to_placeOther']==True:
                    return render_template('placeOrder.html')'''

            if user_type == 'buyer' or user_type == 'seller(buyer)':
                info = getInfo(firstname)
                session['info'] = info
                if user_type == 'seller(buyer)':
                    seller_info = getSellerInfo(firstname, user_type)
                    session['seller_info'] = seller_info
                    return render_template('checkingInfo.html', error=error, result=info, value=firstname, user_type=user_type, seller_info=seller_info)

                # user type is buyer
                # do not need seller_info
                else:
                    return render_template('checkingInfo.html', error=error, result=info, value=firstname, user_type=user_type)

            # in this case, user type is local vendor
            # local venders do not have information such as gender, age, etc.
            else:
                seller_info = getSellerInfo(firstname, user_type)
                session['seller_info'] = seller_info
                return render_template('checkingInfo.html', error=error, value=firstname, user_type=user_type, seller_info=seller_info)

        # login failed
        else:
            return render_template('fail.html', error=error, result=result)
    return render_template('login.html', error=error)


def add_name(email, password):
    # hash the password using MD5
    password = hashlib.md5(password.encode()).hexdigest()
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email='" +
                   email+"' AND password='"+password+"'")
    result = cursor.fetchall()
    if result:
        return 1
    else:
        return 0


def getInfo(email):
    ''' return:
        email ID, 
        name, 
        age, 
        gender, 
        home and billing address (street, city, state, zipcode), 
        last 4 digits of credit cards
        of a buyer/seller(buyer)'''
    # connect to database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Buyers WHERE email='"+email+"'")

    # result=[(email, first_name, last_name, gender, age, home_address, billing_address, last_4_digits_of_credit_cards)]
    result = []

    # temp is the element in the result
    # right now temp is in list type, and it will be changed to tuple type later
    temp = []

    # buyer_result=[(email, first_name, last_name, gender, age, home_address_id, billing_address_id)]
    buyer_result = cursor.fetchall()

    # adding email, first_name, last_name, gender, age (first 5 elements) to temp
    for element in buyer_result[0][:5]:
        temp.append(element)

    # find the home address
    # home_address_id stored in buyer_result[-2]
    cursor.execute("SELECT * FROM Address WHERE address_id='" +
                   buyer_result[0][-2]+"'")

    # home_addr_result=[(address_id, zipcode, street_num, street_name)]
    home_addr_result = cursor.fetchall()

    # reorganize the data in home_addr_result to one str
    # right now home_addr=street,
    home_addr = home_addr_result[0][3]+', '

    # finding the city and state for home address based on the zipcode
    zipcode = home_addr_result[0][1]
    cursor.execute("SELECT * FROM Zipcode_Info WHERE zipcode="+str(zipcode))

    # zip_info=[(zipcode, city, state_id, population, density, county_name, timezone)]
    zip_info = cursor.fetchall()

    # right now, home_addr is completed (home_addr=street, city, state_id zipcode---in str type)
    home_addr += zip_info[0][1]+', '+zip_info[0][2]+' '+str(zipcode)

    # add it to temp
    temp.append(home_addr)

    # find the billing address
    # billing_address_id stored in buyer_result[-1]
    cursor.execute("SELECT * FROM Address WHERE address_id='" +
                   buyer_result[0][-1]+"'")

    # bill_addr_result=[(address_id, zipcode, street_num, street_name)]
    bill_addr_result = cursor.fetchall()

    # right now bill_addr=street,
    bill_addr = bill_addr_result[0][-1]+', '

    # finding the city and state for billing address based on zipcode
    zipcode = bill_addr_result[0][1]
    cursor.execute("SELECT * FROM Zipcode_Info WHERE zipcode="+str(zipcode))

    # zip_info=[(zipcode, city, state_id, population, density, county_name, timezone)]
    # this is same as the part in finding home address
    zip_info = cursor.fetchall()

    # right now, bill_addr is completed (bill_addr=street, city, state_id zipcode---in str type)
    bill_addr += zip_info[0][1]+', '+zip_info[0][2]+' '+str(zipcode)

    # add it to temp
    temp.append(bill_addr)

    # find the last 4 digits of credit cards
    cursor.execute("SELECT * FROM Credit_Cards WHERE Owner_email='"+email+"'")

    # card_result=[(credit_card_num, card_code, expire_month, expire_year, card_type, Owner_email)]
    card_result = cursor.fetchall()

    # note that one user may have multiple credit cards
    four_digits = []
    for i in range(len(card_result)):
        four_digits.append(card_result[i][0][-4:])

    temp.append(four_digits)

    result = [tuple(temp)]

    return result


def getUserType(email):
    '''Returns the user type (buyer, seller(buyer), local_vendor) based on the given email'''

    # at first we assume the user type is buyer
    user_type = "buyer"

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # determine whether it is a local vendor
    cursor.execute("SELECT * FROM Local_Vendors WHERE email='"+email+"'")
    result = cursor.fetchall()
    if result:
        user_type = "local_vendor"
    else:
        # not a local vendor, but seller(buyer) still possible
        cursor.execute("SELECT * FROM Sellers WHERE email='"+email+"'")
        result = cursor.fetchall()
        if result:
            user_type = "seller(buyer)"

    return user_type


def getSellerInfo(email, user_type):
    '''Returns the information of a seller(buyer) or a local vender'''

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # seller(buyer) and local vender both have information about routing number, account number, and balance
    cursor.execute(
        "SELECT * FROM Sellers WHERE email='"+email+"'")
    result = cursor.fetchall()

    # if the user is a local vendor, there are some other information (business name, business address, customer service number)
    if user_type == 'local_vendor':
        cursor.execute('''  SELECT Bussiness_Name,Customer_Service_Number,street_name,city,state_ID,address.zipcode
                            FROM Local_Vendors
                            JOIN Address ON Local_Vendors.Bussiness_Address_ID=Address.Address_ID
                            JOIn Zipcode_Info ON Address.zipcode=Zipcode_info.zipcode
                            WHERE email="'''+email+'"')
        local_vendor_info = cursor.fetchall()
        result = [result[0]+local_vendor_info[0]]

    return result


@app.route('/checkingInfo.html', methods=['POST', 'GET'])
def checkingInfo():
    # from session to get the current user name and user information
    email = session['user']
    user_type = session['type']

    # only buyer and seller(buyer) has info
    if user_type == 'buyer' or user_type == 'seller(buyer)':
        info = session['info']

    # get the new password from html
    if request.method == 'POST':
        newPassword = request.form['NewPassword']
        result = changePassword(email, newPassword)
        if result == 0:
            flash('Your password has been changed!')

        # for buyers
        if user_type == 'buyer':
            return render_template('checkingInfo.html', result=info, value=email, user_type=user_type)

        # for seller(buyer)
        elif user_type == 'seller(buyer)':
            seller_info = session["seller_info"]
            return render_template('checkingInfo.html', result=info, value=email, user_type=user_type, seller_info=seller_info)

        # for local vendors
        else:
            seller_info = session["seller_info"]
            return render_template('checkingInfo.html', value=email, user_type=user_type, seller_info=seller_info)

    # in other cases, it is returning to this page from another page
    else:
        # for buyers
        if user_type == 'buyer':
            return render_template('checkingInfo.html', result=info, value=email, user_type=user_type)

        # for seller(buyer)
        elif user_type == 'seller(buyer)':
            seller_info = session["seller_info"]
            return render_template('checkingInfo.html', result=info, value=email, user_type=user_type, seller_info=seller_info)

        # for local vendors
        else:
            seller_info = session["seller_info"]
            return render_template('checkingInfo.html', value=email, user_type=user_type, seller_info=seller_info)


def changePassword(email, newPassword):
    # hash the new password
    newPassword = hashlib.md5(newPassword.encode()).hexdigest()

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # updata the password
    cursor.execute("UPDATE Users SET password='" +
                   newPassword+"' WHERE email='"+email+"'")
    conn.commit()

    return 0


@app.route('/categoryHierarchy.html', methods=['POST', 'GET'])
def categoryHierarchy():
    pass
    categories = getCategories()
    if request.method == 'POST':
        # category is the current category/subcategory in the selection box
        category = request.form['category']

        # get all categories/subcategories from database
        result = show_products(category)
        print(result)
        print('---result is listed above')
        # tell the user if there is no product in this category/subcategory
        if result == []:
            return render_template('categoryHierarchy.html', null=True, show=category, value=categories)

        # in other cases, there is at least one product in the category/subcategory
        else:
            return render_template('categoryHierarchy.html', value=categories, result=result, show=category)

    # when method=='GET'
    else:
        return render_template('categoryHierarchy.html', value=categories)


def getCategories():
    ''' Get all categories/subcategories/sub_subcategories from the database'''

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # get all categories under root (subcategories under categories are not included)
    cursor.execute("SELECT * FROM Categories WHERE parent_category='Root'")

    # categories=[(parent_category, category_name), ...]
    categories_result = cursor.fetchall()

    # extract category names from categories_result
    # at the end, categories will look like: [[category1, [subcategory1-1], [subcategory2-1], ...], ...]
    # category[1] is the category_name
    categories = [[category[1]] for category in categories_result]

    # get all subcategories based on category names
    for i in range(len(categories)):
        cursor.execute(
            "SELECT * FROM Categories WHERE parent_category='"+categories[i][0]+"'")
        subcategories = cursor.fetchall()
        for subcategory in subcategories:
            # use '- ' to distinct categories and subcategories
            # a subcategory will look like: (parent_category, category_name)
            categories[i].append(['- '+subcategory[1]])

    # now, consider the subcategories of a subcategory. I call a subcategory of a subcategory sub_subcategory
    # get all sub_subcategories based on subcategories
    for i in range(len(categories)):
        for j in range(len(categories[i])):
            # note that '- ' was added in front of subcategory for easier reading
            # now we need to trim the '- ' (the first 2 chars)
            subcategory = categories[i][j][0][2:]
            cursor.execute(
                "SELECT * FROM Categories WHERE parent_category='"+subcategory+"'")
            sub_subcategories = cursor.fetchall()
            for sub_subcategory in sub_subcategories:
                # use '--- ' to distinct subcategories and sub_subcategories
                # a sub_subcategory will look like: (parent_category, category_name)
                categories[i][j].append('--- '+sub_subcategory[1])

    # now categories is a 3-dimension list and it looks like:
    # [[category1, [subcategory1-1, sub_subcategory1-1-1, sub_subcategory2-1-1, ...], [subcategory2-1, ...], [category2, ...], ...]
    # convert categories to 1-dimension list
    # note that 'All' is the 'Root' category
    result = ['All']
    for category in categories:
        # a category will look like: [category1, [subcategory1-1, sub_subcategory1-1-1, sub_subcategory2-1-1, ...], [subcategory2-1,...], ...]
        for subcategory in category:
            # in this case, subcategory = the name of current category
            if type(subcategory) == str:
                result.append(subcategory)
            # in other cases, subcategory = the list that contains subcategory and sub_subcategory
            else:
                for sub_subcategory in subcategory:
                    result.append(sub_subcategory)

    # now result will look like: [category1, subcategory1-1, sub_subcategory1-1-1, sub_subcategory2-1-1, ... subcategory2-1, ..., category2, subcategory1-2, ...]
    return result


def show_products(category):
    '''show the names and details of products which belong to the given category'''

    # we will use the prefix to distinguish category/subcategory/sub_subcategory
    # category (type=0): no prefix in front of it
    # subcategory (type=1): '- ' in front of it
    # sub_subcategory (type=2): '--- ' in front of it
    # we assume the input is a category at first
    input_type = 0

    # we added '- '/'--- ' in front of every subcategory/sub_subcategory for easier reading
    # now we need to trim the '- ' and '--- ' here
    if '--- ' in category:
        input_type = 2
        category = category[4:]
    # '- ' is in front of category (not '--- ')
    elif '- ' in category:
        input_type = 1
        category = category[2:]

   # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # categories list stores the category/subcategories/sub_subcategories we need to search in the Product_Listings table
    categories = []
    # obviously we need to find the products with category_name==category
    categories.append(category)

    # temp stores temporary result of cursor execution
    temp = []

    # special case: category is 'All'
    # in this case we need to show the products of all categories
    if category == 'All':
        cursor.execute("SELECT * FROM Product_Listings")
        temp = cursor.fetchall()

    # in this case, find all products in this **category**
    elif input_type == 0:

        # need to find all subcategory in this category
        cursor.execute(
            "SELECT category_name FROM Categories WHERE parent_category='"+category+"'")

        # the result provides the subcategories of this category, and it will look like: [(subcategory1),(subcategory2),...]
        subcategories = cursor.fetchall()

        # organize the subcategories
        # then subcategories looks like: [subcategory1, subcategory2, ...]
        org_subcategories = [subcategory[0] for subcategory in subcategories]

        # merge the categories and subcategories
        # now the categories looks like: [category, subcategory1, subcategory2, ...]
        categories += org_subcategories

        insert_position = len(org_subcategories)+1
        # find all sub_subcategories
        for i in range(len(subcategories)):
            cursor.execute(
                "SELECT category_name FROM Categories WHERE parent_category='"+org_subcategories[i]+"'")
            sub_sub = cursor.fetchall()

            # organize the sub_subcategories list
            sub_sub = [element[0] for element in sub_sub]
            # now, sub_sub=[sub_sub1-i, sub_sub2-i, ...]

            # now categories=[category1, subcategory1, sub_sub1-1, sub_sub2-1, sub_sub3-1, ..., subcategory2, ...]
            categories = categories[:insert_position] + \
                sub_sub+categories[insert_position:]

            # update the insert_position so that the sub_sub of the next subcategory can be added right after itself
            insert_position += len(sub_sub)+1

        # now, categories=[category1, subcategory1, sub_sub1-1, sub_sub2-1, sub_sub3-1, ..., subcategory2, ..., category2, ...]
        for element in categories:
            cursor.execute(
                "SELECT * FROM Product_Listings WHERE category='"+element+"' AND (Status IS NULL OR Status=1)")
            temp += cursor.fetchall()

    # in this case, find all products in this **subcategory**
    elif input_type == 1:
        # need to find all sub_subcategory in this category
        cursor.execute(
            "SELECT category_name FROM Categories WHERE parent_category='"+category+"'")

        # the returned result from the cursor will look like:
        # [(sub_subcategory1), (sub_subcategory2), ...]
        sub_sub = cursor.fetchall()

        # organize the sub_subcategories
        sub_sub = [element[0] for element in sub_sub]

        # merge the categories and subcategories
        # now the categories looks like: [subcategory, sub_subcategory1, sub_subcategory2, ...]
        categories += sub_sub

        # now, categories=[subcategory, sub_subcategory1, sub_subcategory2, ...]
        for element in categories:
            cursor.execute(
                "SELECT * FROM Product_Listings WHERE category='"+element+"' AND (Status IS NULL OR Status=1)")
            temp += cursor.fetchall()

    # in this case, find all products in this **sub_subcategory**
    else:
        cursor.execute(
            "SELECT * FROM Product_Listings WHERE category='"+category+"' AND (Status IS NULL OR Status=1)")
        temp = cursor.fetchall()

    # we will extract the data we need from temp to result later
    # now temp = [(Seller_email, Listing_ID, Category, Title, Product_Name, Product_Description, Price, Quantity, Active_period, Status), ...]

    # extract the data we need from temp to result
    result = []
    for element in temp:
        # do not show the product if its quantity is 0
        if element[7] == 0:
            continue

        # do not show the product if its active period is 0 (0 days remaining)
        elif element[8] == 0:
            continue

        # do not show the product if its status is inactive (status=0)
        elif element[9] == 0:
            continue

        else:
            # (Title, Product_name, Product_Description, Price, Quantity, Seller_email, Listing_ID)
            result.append(
                (element[3], element[4], element[5], element[6], element[7], element[0], element[1]))

    return result


@app.route('/publishProductListing.html', methods=['POST', 'GET'])
def publishProductListing():
    seller = session['user']
    categories = getCategories()
    print(seller)
    # get the product listing published by the current buyer
    productListing = getProductListings(seller)

    if request.method == 'POST':
        # when method=="POST", it could be:
        # 1. add product listing
        # 2. change product listing status
        # we need to distinct which is the current case first
        if 'change' in request.form:
            # in this case, we need to change the status from 1/NULL (active) to 0 (inactive) or from 0 to 1
            listingID = request.form['change']
            changeStatus(listingID, seller)

            # if change status, need to show the updated product listing in the html page
            productListing = getProductListings(seller)

        # in other cases, we need to add product listing
        else:
            # collecting information from the form in the html page
            title = request.form['ProductTitle']
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']

            # note that the price stored in dataset is $+number
            # need to check if the price from the form has '$'
            # add '$' in front of price if the price does not have '$'
            if '$' not in price:
                price = '$'+price

            quantity = request.form['quantity']
            period = request.form['period']
            category = request.form['category']

            # notice that '- '/'--- ' was added in front of a subcategory/sub_subcategory
            # now need to trim '- '/'--- '
            if '--- ' == category[:4]:
                category = category[4:]
            elif '- ' == category[:2]:
                category = category[2:]

            # concentrate the information on a list
            listingInfo = [seller, title, category, name,
                           description, price, int(quantity), int(period)]
            print(listingInfo)
            # add the listing
            result = addListing(listingInfo)
            print(result, '--this is result')

            # if successfully added the listing, tell the user via a flash message
            if result:
                flash('The product listing has been added!')
                # refresh the product listing shown to seller
                productListing = getProductListings(seller)
            else:
                flash('Oops! Error occured!')

    # when request.method=="GET"
    else:
        # listingID=request.form['change']
        # print()
        # print(listingID)
        print()

    # whatever method=="GET" or method=="POST", both need to return the same thing
    return render_template('publishProductListing.html', user=seller, categories=categories, product_listing=productListing)


def addListing(listingInfo):
    '''Insert the listing into the Product_Listings table'''

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # determine listing_id (max(listing_ID)+quantity of this listing)
    # find the max listing_ID
    cursor.execute("SELECT max(Listing_ID) FROM Product_Listings")

    # cursor.fetchall() will look like: [(max_id,)]
    id = cursor.fetchall()[0][0]

    # listingInfo[-2] is the quantity of the listing in int type
    id += listingInfo[-2]

    # insert the listing
    sql = '''INSERT IGNORE INTO Product_Listings 
            (Seller_Email, Listing_ID, Category, Title, Product_Name, Product_Description, Price, Quantity, Active_period, Status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

    # note that listingInfo=[seller, title, category,title, name,description,price,quantity,period,status=1]
    val = (listingInfo[0],
           id,
           listingInfo[2],
           listingInfo[1],
           listingInfo[3],
           listingInfo[4],
           listingInfo[5],
           listingInfo[6],
           listingInfo[7],
           1)

    # return val
    cursor.execute(sql, val)
    conn.commit()
    return 1


def getProductListings(seller):
    '''Returns the product listings published by the given seller'''
    pass

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    cursor.execute("SELECT Listing_ID, Category, Title, Product_Name, Product_Description, Price, Quantity, Active_period, Status FROM Product_Listings WHERE Seller_Email='"+seller+"'")

    listing_result = cursor.fetchall()

    return listing_result


def changeStatus(listingID, seller):
    '''Changes the status of a listing from 1/NULL (active) to 0 (inactive) or from 0 (inactive) to 1 (active)'''

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # find the listing
    cursor.execute(
        "SELECT Status FROM Product_Listings WHERE Listing_ID="+listingID)

    # status will look like: [(status)]
    status = cursor.fetchall()[0][0]

    # if active, change to inactive (status=0)
    if status == 1 or status == None:
        change_to = '0'

    # if inactive, change to active (status=1)
    else:
        change_to = '1'

    # update the status
    cursor.execute("UPDATE Product_Listings SET Status="+change_to +
                   " WHERE Listing_ID="+listingID+" AND Seller_Email='"+seller+"'")
    conn.commit()

    return 0


@app.route('/searching.html', methods=['POST', 'GET'])
def searching():
    if request.method == "POST":
        searchBy = request.form['searchBy']
        content = request.form['search']

        # search by keyword
        if searchBy == 'keyword':
            result = search_in_ProductListings(content)
            print(result)
            print(type(result))

    return render_template('searching.html', value=content, result=result)


def search_in_ProductListings(keyword):
    pass
    # keyword may be the seller's email, the category, the title, the name, the description of a product

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    result = []

    # search by category
    cursor.execute(
        "SELECT Category, Title, Product_Name,Product_Description, Price, Quantity,Seller_Email, Listing_ID FROM Product_Listings WHERE Category LIKE '%" +
        keyword+"%' AND (Status IS NULL OR Status=1) AND Quantity>0")
    result += cursor.fetchall()

    # search by title
    cursor.execute(
        "SELECT Category, Title, Product_Name,Product_Description, Price, Quantity,Seller_Email,Listing_ID FROM Product_Listings WHERE Title LIKE '%"+keyword+"%' AND (Status IS NULL OR Status=1) AND Quantity>0")
    temp = cursor.fetchall()

    # eliminate duplicate result
    for element in temp:
        if element not in result:
            result.append(element)

    # search by name
    cursor.execute("SELECT Category, Title, Product_Name,Product_Description, Price, Quantity,Seller_Email,Listing_ID FROM Product_Listings WHERE Product_Name LIKE '%" +
                   keyword+"%' AND (Status IS NULL OR Status=1) AND Quantity>0")
    temp = cursor.fetchall()

    # eliminate duplicate result
    for element in temp:
        if element not in result:
            result.append(element)

    # search by description
    cursor.execute("SELECT Category, Title, Product_Name,Product_Description, Price, Quantity,Seller_Email,Listing_ID FROM Product_Listings WHERE Product_Description LIKE '%" +
                   keyword+"%' AND (Status IS NULL OR Status=1) AND Quantity>0")
    temp = cursor.fetchall()

    # eliminate duplicate result
    for element in temp:
        if element not in result:
            result.append(element)

    # search by seller
    cursor.execute("SELECT Category, Title, Product_Name,Product_Description, Price, Quantity,Seller_Email,Listing_ID FROM Product_Listings WHERE Seller_email LIKE '%" +
                   keyword+"%' AND (Status IS NULL OR Status=1) AND Quantity>0")
    temp = cursor.fetchall()

    # eliminate duplicate result
    for element in temp:
        if element not in result:
            result.append(element)

    return result


@app.route('/placeOrder.html', methods=['POST', 'GET'])
def placeOrderHTML():
    if request.method == 'POST':
        # check if the buyer login
        # if not, need to login first
        if 'user' not in session:
            # need to go back from login.html to here
            session['back_to_placeOther'] = True
            return render_template('login.html')

        # the user already login
        else:
            # do not need to back again
            session['back_to_placeOther'] = False
        
        buyer = session['user']

        # if the buyer already enter the quantity he/she wants to buy
        # then place the order
        if 'quantity' in request.form:
            # first, decide if the buyer can buy
            # only buyer and seller(buyer) can buy, local vendor cannot buy
            if session['type'] == 'local_vendor':
                flash('You are a local vendor! You cannot buy a product!')
                listing_ID = session['buy_listing_id']
                orderInfo = build_order_page(listing_ID)
                return render_template('placeOrder.html', result=orderInfo, user=buyer)
            else:
                quantity = int(request.form['quantity'])
                listing_ID = session['buy_listing_id']
                result = placeOrder(buyer, listing_ID, quantity)
                
                # successful
                # redirect to success.html page
                if result > 0:
                    return render_template('success.html', total='$'+str(result))
                # entered quantity is greater than the quantity in the listing
                # return to the placeOrder.html page
                elif result < 0:
                    flash(
                        'The quantity you entered is greater than the quantity in the listing!')
                    listing_ID = session['buy_listing_id']
                    orderInfo = build_order_page(listing_ID)
                    return render_template('placeOrder.html', result=orderInfo, user=buyer)
        
        # in other cases:
        # the user has not entered the quantity yet
        # get the info from the html form to build the orderInfo list
        else:
            listing_ID = int(request.form['buy'])
            session['buy_listing_id'] = listing_ID
            orderInfo = build_order_page(listing_ID)

            # collect credit card info from session
            credit_card = None
            if 'info' in session and (session['type']=='buyer' or session['type']=='seller(buyer)'):
                credit_card = session['info'][0][-1]
            return render_template('placeOrder.html', result=orderInfo, user=buyer, credit_card=credit_card)

    return render_template('placeOrder.html')


def build_order_page(listing_id):
    '''Provides information to build a placeOrder page based on the Listing_ID'''
    pass

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # find the product listing based on the listing ID
    cursor.execute(
        "SELECT Category,Title,Product_Name,Product_Description,Price,Quantity,Seller_Email FROM Product_Listings WHERE Listing_ID="+str(listing_id)+" AND (Status IS NULL OR Status=1)")

    # listing_result=[(Category,Title,Product_Name,Product_Description,Price,Quantity,Seller_Email)]
    listing_result = cursor.fetchall()

    return listing_result


def placeOrder(buyer, listing_id, quantity):
    ''' 1. Insert new order to Orders 
        2. decrease the quantity of the product
        3. add balance to Seller'''

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # check if there is enough quantity to buy
    cursor.execute(
        "SELECT Quantity, Seller_Email, Price FROM Product_Listings WHERE Listing_ID="+str(listing_id))

    # cursor.fetchall() will look like: [(int quantity, str seller_email, str price)]
    result = cursor.fetchall()
    listing_quantity = int(result[0][0])

    # quantity want to buy greater than the quantity in the listing or input quantity is invalid
    if int(quantity) > listing_quantity or int(quantity) <= 0:
        # cannot buy
        return -1

    # get the seller email of the product
    seller_email = result[0][1]

    # calculate the total of the order
    # convert price from str to int
    price = result[0][2]
    # eliminate "$"
    price = price.strip('$')
    # eliminate ","
    price = price.replace(",", "")
    # convert to int
    price = int(price)

    total = price*int(quantity)

    # figure out the transaction ID
    cursor.execute("SELECT MAX(Transaction_ID) FROM Orders")
    transID = int(cursor.fetchall()[0][0])+1

    # prepare the date for the order
    now = datetime.datetime.now()
    month = str(now.month)+'/'
    day = str(now.day)+'/'
    year = str(now.year)[2:]

    # date=mm/dd/yy
    date = month+day+year

    # insert the order to Orders
    sql = "INSERT INTO Orders (Transaction_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Quantity, Payment) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    val = (transID, seller_email, listing_id, buyer, date, quantity, total)

    cursor.execute(sql, val)
    conn.commit()

    # update the product listing
    listing_quantity -= int(quantity)
    cursor.execute("UPDATE Product_Listings SET Quantity="+str(listing_quantity) +
                   " WHERE Listing_ID="+str(listing_id)+" AND Seller_Email='"+seller_email+"'")
    conn.commit()

    # update the seller's balance
    # first, get the original balance
    cursor.execute(
        "SELECT balance FROM Sellers WHERE email='"+seller_email+"'")
    # cursor.fetchall() will look like: [(balance)]
    balance = int(cursor.fetchall()[0][0])
    balance += total

    cursor.execute("UPDATE Sellers SET balance="+str(balance) +
                   " WHERE email='"+seller_email+"'")
    conn.commit()

    return total


@app.route('/viewOrders.html', methods=["POST", "GET"])
def viewOrder():
    # get information from session
    user = session['user']
    print(user)
    user_type = session['type']
    if user_type == 'buyer':
        bought = getOrders(user, user_type)
        return render_template('viewOrders.html', user_type=user_type, bought=bought)
    elif user_type == 'seller(buyer)':
        bought, sold = getOrders(user, user_type)
        print(bought)
        print(sold)
        return render_template('viewOrders.html', user_type=user_type, bought=bought, sold=sold)

    # local vendors
    else:
        sold = getOrders(user, user_type)
        return render_template('viewOrders.html', user_type=user_type, sold=sold)


def getOrders(user, user_type):
    '''Returns Orders bought/sold by the given user based on the user type'''
    pass

    # return Order(bought) for buyer
    # return Order(bought) and Order(sold) for seller(buyer)
    # return Order(sold) for local vendor

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()

    # find all orders he/she bought
    cursor.execute("""SELECT Transaction_ID, Orders.Seller_Email, Product_Name, Buyer_Email, Date, Orders.Quantity, Payment 
                   FROM Orders 
                   JOIN Product_Listings 
                   ON Orders.listing_id=Product_Listings.listing_id 
                   WHERE Buyer_Email='"""
                   + user+"'")
    bought = cursor.fetchall()

    # find all orders he/she sold
    cursor.execute("""SELECT Transaction_ID, Orders.Seller_Email, Product_Name, Buyer_Email, Date, Orders.Quantity, Payment 
                   FROM Orders 
                   JOIN Product_Listings 
                   ON Orders.listing_id=Product_Listings.listing_id 
                   WHERE Orders.Seller_Email='"""
                   + user+"'")
    sold = cursor.fetchall()

    if user_type == 'buyer':
        return bought
    elif user_type == 'seller(buyer)':
        return bought, sold

    # local vendor
    else:
        return sold

@app.route('/shoppingCart.html',methods=['POST','GET'])
def shopping_Cart():
    buyer=session['user']
    if request.method=='POST':
        # if the buyer clicked "Buy" button
        if 'buy' in request.form:
            # redirect to the place order page
            listing_ID = int(request.form['buy'])
            session['buy_listing_id'] = listing_ID
            orderInfo = build_order_page(listing_ID)
            # collect credit card info from session
            credit_card = None
            if 'info' in session and (session['type']=='buyer' or session['type']=='seller(buyer)'):
                credit_card = session['info'][0][-1]
            return render_template('placeOrder.html', result=orderInfo, user=buyer, credit_card=credit_card)

        
        #
        elif 'addCart' in request.form:
            listing_id=request.form['addCart']
            add_to_cart(buyer,listing_id)
            flash("Added to your shopping cart!")
            print('----listing_id:')
            print(listing_id)
            print()
            
            # rebuild the placeOrder.html page
            orderInfo = build_order_page(listing_id)
            # collect credit card info from session
            credit_card = None
            if 'info' in session and (session['type']=='buyer' or session['type']=='seller(buyer)'):
                credit_card = session['info'][0][-1]
            return render_template('placeOrder.html', result=orderInfo, user=buyer, credit_card=credit_card)
        
        # else if: the buyer clicked "Remove" button
        elif 'remove' in request.form:
            shopping_cart_ID=request.form['remove']
            remove_from_cart(buyer,shopping_cart_ID)
            result=showShoppingCart(buyer)
            return render_template('shoppingCart.html',result=result)
        else:
            result=showShoppingCart(buyer)
            print('------------request.form:')
            print(request.form)
            return render_template('shoppingCart.html',result=result)
    # method=='GET'
    else:
        result=showShoppingCart(buyer)
        print('------------result:')
        print(result)
        return render_template('shoppingCart.html',result=result)

def add_to_cart(buyer,listing_id):
    '''Add a product to a specific buyer's shopping cart based on the given buyer and listing_id'''
    pass

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()
    
    # insert into shopping_cart table
    sql="INSERT INTO Shopping_Cart (Buyer_Email,Listing_ID) VALUES (%s,%s)"
    val=(buyer,listing_id)
    cursor.execute(sql,val)
    conn.commit()
    
    return 0;

def showShoppingCart(buyer):
    '''Show the buyer's shopping cart based on the give buyer email'''
    pass

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()
    
    # get the shopping cart info
    cursor.execute("""SELECT Shopping_Cart_ID, 
                    Product_Listings.Category,
                    Product_Listings.Title,
                    Product_Listings.Product_Name,
                    Product_Listings.Product_Description,
                    Product_Listings.Price,
                    Product_Listings.Quantity,
                    Product_Listings.Seller_Email,
                    Product_Listings.Listing_ID 
                    FROM Shopping_Cart 
                    JOIN Product_Listings ON Shopping_Cart.Listing_ID=Product_Listings.Listing_ID 
                    WHERE Buyer_Email='"""+buyer+"""' 
                    AND Product_Listings.Quantity>0 
                    AND (Product_Listings.Status IS NULL 
                    OR Product_Listings.Status=1)
                    AND (Product_Listings.Active_period>0
                    OR Product_Listings.Active_period IS NULL)""")
    result=cursor.fetchall()
    
    return result

def remove_from_cart(shopping_cart_ID):
    '''Removes a product from the buyer's shopping cart based on the given listing_id'''
    pass

    # connect to the database
    conn = mysql.connector.connect(
        host='localhost', user='root', passwd='admin', database='phase2')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Shopping_Cart WHERE Shopping_Cart_ID="+str(shopping_cart_ID))
    conn.commit()
    
    return 0;
    

if __name__ == "__main__":
    app.run(debug=True)
