# Telegram Price Scraper Bot

A Telegram Bot that scrapes the prices of the product from the websites.

## Installing the required modules

1) Open the Command Prompt inside the folder where the repository is downloaded

2) Install the python virtual environment module by running the following command:
```
pip install virtualenv
```
3) For creation of the virtual environment and activation refer the official
[Python Virtual Environment documentation](https://virtualenv.pypa.io/en/latest/) link

4) Install all the requirements for the project by executing the following command:
```
pip install -r requirements.txt
```

___Create a___ `.env` ___file in the project directory for storing the___ `TOKEN` ___and___ `MONGO_URI`

## Telegram Bot creation
1) Search for the **BotFather** telegram channel on the telegram app and create your bot.
2) Copy the token of your bot and add it in the .env file
```
TOKEN = YOUR_BOT_TOKEN
```

## Creating a MongoDB Atlas DB
Refer the [MongoDB Atlas documentation](https://www.mongodb.com/docs/atlas/getting-started/) for creating and connecting the MongoDB database.

Copy the url of your MongoDB Cluster and add it in the .env file
```
MONGO_URI = "YOUR_MONGODB_CLUSTER_URL"
```

## Deploy your bot on heroku
Refer the [Deploying on Heroku documentation](https://devcenter.heroku.com/categories/deployment) for deploying the project on Heroku.

_Heroku has announced that it will eliminate all of its free services starting from 28th November, 2022\
[Read more](https://help.heroku.com/RSBRUH58/removal-of-heroku-free-product-plans-faq)_