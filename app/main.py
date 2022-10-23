'''
A Price Scraper Bot that currently supports Reliance Digital and Flipkart Website
'''
# Importing necessary modules

from bs4 import BeautifulSoup
import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
import pymongo
from pymongo.server_api import ServerApi
import re
import random
load_dotenv()

# Flask
app = Flask(__name__)

# Messages
welcomeMessage = '''
*Welcome to Price scraper service bot*
_We currently only fetch product prices from Flipkart and Reliance Digital._

Choose the commands:

*/add <product-url>* -- To add the product for monitoring the price
*/list* -- To list all your products
*/reliance* -- To list all your products added from reliance
*/flipkart* -- To list all your products added from flipkart
'''

linkError_message = '''
**An error occured while getting the link of the product.**
The error can usually occur due to the following reasons:\n
1) _The link was not provided in a proper format_
2) _The link provided was not of Flipkart or Reliance Digital_
'''

chat_error = '''
*An error occurred in the bot* :/
Please try again
'''

# Base Urls
BASE_URL = {
    "reliance": 'https://www.reliancedigital.in/',
    "flipkart": 'https://www.flipkart.com/'
}

# Will hold the tag where the PRICE of product is displayed
PRICE = {
    "reliance": 'span[class="pdp__offerPrice"] span:nth-child(2)',
    "flipkart": 'div[class = "_30jeq3 _16Jk6d"]'
}

# Will hold the tag where the NAME of product is displayed
PRODUCT_NAME = {
    "reliance": 'h1[class="pdp__title mb__20"]',
    "flipkart": 'span[class="B_NuCI"]'

}

# Telegram
TOKEN = os.getenv('TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
TELEGRAM_URL = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
TELEGRAM_API_SEND_MSG = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

# Connection to MongoDB Atlas Cluster
client = pymongo.MongoClient({MONGO_URI}, server_api=ServerApi('1'))

# Database and Collection initialization
db = client.teleData
userData = db['userData']


def generateProductId():
    return random.randint(1001, 9999)

# Will add the product to the database


def addDetails(user_id, userName, website, product_url):
    # Check which website url is provided
    if(website == 'flipkart'):
        base_url = BASE_URL['flipkart']
    else:
        base_url = BASE_URL['reliance']

    # Fetch user details query
    userFetchQuery = {"_id": user_id}

    # Check whether user is already present in the userData collection
    currentUser = userData.find_one(userFetchQuery)

    if(currentUser != None):
        # Fetching all the product ids of the products added by the user
        prodIds = [prod_id['product_id'] for productList in userData.find({
            "_id": user_id},
            {"_id": 0,
             "products": 1})
            for prod_id in productList['products']]

        # Generate product_id
        prodId = generateProductId()

        # Checking whether the product_id generated already exists or not
        while prodId in prodIds:
            prodId = generateProductId()

        # Query to push data into existing user document in mongoDB
        pushProductQuery = {
            "$push": {
                "products": {
                    "product_id": prodId,
                    "website": website,
                    "base_url": base_url,
                    "product_url": product_url
                }
            }
        }

        userData.update_one(userFetchQuery, pushProductQuery)
    else:
        # Adding new user details to the collection
        newProdId = random.randint(1001, 9999)
        product_data = {
            "_id": user_id,
            "name": userName,
            "products": [
                {
                    "product_id": newProdId,
                    "website": website,
                    "base_url": base_url,
                    "product_url": product_url
                }
            ]
        }
        # Inserting new user data into the database collection
        userData.insert_one(product_data)

    resp = requests.get('https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=Markdown'.format(
        TOKEN, user_id, f'Product details added successfully ✓'))

    sendWelcome = {
        "chat_id": user_id,
        "text": welcomeMessage,
        "parse_mode": 'Markdown'
    }

    r = requests.get(TELEGRAM_API_SEND_MSG, data=sendWelcome)

# Function to delete the product details from the DB


def deleteDetails(user_id, product_id):
    # Preparing the queries
    result = userData.update_one(
        {"_id": user_id},
        {"$pull": {"products": {"product_id": product_id}}},
        False
    )
    # Checking if the product is deleted successfully
    # If deleted then send a success message
    if(result.modified_count > 0):
        # Success message
        delete_message = 'Product is ignored from monitoring.'

        # Preparing to send the message
        deleteData = {
            "chat_id": user_id,
            "text": delete_message,
            "parse_mode": 'Markdown'
        }

        # Sending the message
        r = requests.get(TELEGRAM_API_SEND_MSG, data=deleteData)
    else:
        errorMessage('Product is already not monitored.', user_id)

# Function to send the products from a particular website
# that is stored on the database by the user


def sendDetails(fromWeb, url, chat_id):

    sendDetails = f'*Your products added from {fromWeb}:*\n ------------------------------- \n' if fromWeb != 'list' else '*Your products*\n ------------------------------------- \n'
    if fromWeb == 'list':
        query = {"_id": chat_id}
        allProducts = userData.find(query, {"_id": 0, "products": 1})
        if(allProducts != None):
            product_details = [
                product for x in allProducts for product in x['products']]
            for idx, products in enumerate(product_details):
                webpage = products['website']
                name_tag = PRODUCT_NAME[webpage]
                price_tag = PRICE[webpage]
                prod_id = products['product_id']

                url = products['base_url'] + products['product_url']
                r = requests.get(url)

                soup = BeautifulSoup(r.text, 'html.parser')

                # Getting the price and name of the product
                name = soup.select_one(name_tag).get_text()
                price = soup.select_one(price_tag).get_text()

                sendDetails += f'{idx+1}) Website: {webpage}\nProduct name: [{name}]({url})\nPrice: {price}\n\nTo Ignore the product, Type: /ignore#{prod_id}\n\n'
            # Preparing the message
            data = {
                'chat_id': chat_id,
                'text': sendDetails,
                'parse_mode': 'Markdown'
            }

            # Sending the product detail
            r = requests.post(TELEGRAM_API_SEND_MSG, data=data)
        else:
           # Provide error message if no product is present in the mongoDB collection
            errorMessage('Product list is empty', chat_id)
    else:
        # Preparing the queries
        pipeline = [{"$match": {
            "_id": chat_id,
            "products.website": fromWeb
        }},
            {"$project": {"_id": 0, "products": 1}},
            {"$unwind": '$products'},
            {"$match": {
                "products.website": fromWeb
            }}]

        # Fetching the user products
        products = userData.aggregate(pipeline)

        # using alive method of CommandCursor to check whether products list contain
        # the products
        if(products.alive):
            for idx, product in enumerate(products):
                webpage = product['products']['website']
                name_tag = PRODUCT_NAME[webpage]
                price_tag = PRICE[webpage]
                prod_id = product['products']['product_id']

                url = product['products']['base_url'] + \
                    product['products']['product_url']
                r = requests.get(url)

                soup = BeautifulSoup(r.text, 'html.parser')

                # Getting the price and name of the product
                name = soup.select_one(name_tag).get_text()
                price = soup.select_one(price_tag).get_text()

                sendDetails += f'{idx+1}) Website: {webpage}\nProduct name: [{name}]({url})\nPrice: {price}\n\nTo Ignore the product, Type: /ignore#{prod_id}\n\n'
            # Preparing the message
            data = {
                'chat_id': chat_id,
                'text': sendDetails,
                'parse_mode': 'Markdown'
            }

            # Sending the product detail
            r = requests.post(TELEGRAM_API_SEND_MSG, data=data)
        else:
            # Provide error message if no product is present in the mongoDB collection
            errorMessage('Product list is empty', chat_id)

# Function to reply with an error message


def errorMessage(err, user_id):

    # Create the error object
    errorData = {
        "chat_id": user_id,
        "text": err,
        "parse_mode": 'Markdown'
    }

    # Send the error message to the user
    r = requests.post(TELEGRAM_API_SEND_MSG, data=errorData)


@app.route("/", methods=['GET', 'POST'])
def main():

    if request.method == 'POST':
        data = request.get_json()

        try:
            # Fetching all the details of the sender
            userName = data['message']['from']['first_name']
            chat_id = data['message']['from']['id']
            msg = data['message']['text']
        except:
            print('##Error occured: Could not fetch the user details.')
            print('##Data Recieved: {}'.format(data))
        else:
            print('Message recieved:', msg)
            if(msg == '/list'):
                sendDetails('list', userName, chat_id)
            elif(msg == '/flipkart'):
                sendDetails('flipkart', userName, chat_id)
            elif(msg == '/reliance'):
                sendDetails('reliance', userName, chat_id)
            elif(re.findall('^/ignore', msg)):
                try:
                    # Fetching the product ID of the product to be deleted
                    product_id = int(msg.split('#')[1])
                except:
                    # Error Handling
                    errorMessage(
                        '*Product could not be deleted!*\n_Check the command properly_', chat_id)
                else:
                    # Calling the function to delete the product from tracking
                    deleteDetails(chat_id, product_id)
            elif(re.findall('^/add', msg)):
                try:
                    url = msg.split(' ')[1]
                except:
                    errorMessage(linkError_message, chat_id)
                else:
                    # Searching if link was provided in the message
                    result = re.search('^https://', url)
                    if(result):
                        base_condition = True if re.findall(
                            'flipkart', result.string) or re.findall('reliance', result.string) else False

                        if(base_condition):
                            base_url = 'flipkart' if re.findall(
                                'flipkart', result.string) else 'reliance'
                            if(base_url):
                                # Store the product url
                                product_url = re.split(
                                    '/', result.string, 3)[-1]
                                addDetails(chat_id, userName,
                                           base_url, product_url)
                        else:
                            # Provide error message to the user
                            # if the url is not valid
                            errorMessage('Please check the url', chat_id)

            else:
                sendWelcome = {
                    "chat_id": chat_id,
                    "text": welcomeMessage,
                    "parse_mode": 'Markdown'
                }

                r = requests.get(TELEGRAM_API_SEND_MSG, data=sendWelcome)

        return {'statusCode': 200, 'body': 'Success', 'data': data}
    else:
        return {'statusCode': 200, 'body': 'Success'}
