import yfinance as yf
from twilio.rest import Client
import requests
import math
from datetime import date
import pandas as pd

# Helpful website: https://www.netnethunter.com/deep-value-investing-guide/
# Another: https://algotrading101.com/learn/yahoo-finance-api-guide/
# Stack Post for the MACD section https://stackoverflow.com/questions/62969946/how-to-find-macd-and-signal-for-multiple-stocks-in-python-using-yfinance-and-pan

####################################################
####################################################
# Settings
####################################################
####################################################

# The Financial Modeling Prep API Key
API_KEY = ""

# Settings for Twilio
TWILIO_ACCOUNT = ""
TWILIO_TOKEN = ""
TWILIO_NUMBER = ""
YOUR_NUMBER = ""

DO_NCAVPS = True

# What exchange to use
EXCHANGE = ["NYSE", "NASDAQ"]

# What period do you want to view the balance sheets from (quarterly or anually)
PERIOD = "quarter"

# The minimum price you want to pay attention to
MIN_PRICE = 6.00

# The minimum amount of volume a stock should trade
MIN_VOLUME = 50000

stocks = []

####################################################
####################################################
# Functions
####################################################
####################################################

###################################################
# General Functions
###################################################

def get_tickers():
    for market in EXCHANGE:

        # Get the list of tickers
        querytickers = requests.get(f'https://financialmodelingprep.com/api/v3/search?query=&limit=10000000&exchange=' + market + '&apikey=' + API_KEY)
        querytickers = querytickers.json()

        print("Market: " + market + ", Number of Listings: " + str(len(querytickers)))

        # At the selected number of tickers to the list
        list_500 = querytickers
        for item in list_500:
            stocks.append(item['symbol'])
    
    return stocks

def get_yfinance_ticker(company):
    return yf.Ticker(company)

def get_past_30_day_price(company):
    ticker = get_yfinance_ticker(company)
    past_30_days = ticker.history(period="1mo")
    return past_30_days

def get_past_30_day_price_download(company):
    past_30_days = yf.download(company, period="1mo")
    return past_30_days

###################################################
# NCAVPS Function
###################################################

def calculate_NCAVPS(company):
    # Get the balance sheet of the company
    Balance_Sheet = requests.get(f'https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/{company}?period=' + PERIOD + '&apikey=' + API_KEY)
    Balance_Sheet = Balance_Sheet.json()

    # Get the total current assets
    total_current_assets = float(Balance_Sheet['financials'][0]['Total current assets'])

    # Get the total liabilities
    total_liabilities = float(Balance_Sheet['financials'][0]['Total liabilities'])

    # Get the Yahoo Finance info on the curreny company
    ticker = get_yfinance_ticker(company)

    # Get the number of shares outstanding
    shares_outstanding = ticker.info["sharesOutstanding"]

    # Here we are calculating the Net Current Asset Value per Share (NCAVPS)
    # If a stock is trading below the NCAVPS then its a good buy
    # Aim for the stock price to be 66% less than its NCAVPS
    NCAVPS = (total_current_assets - total_liabilities) / shares_outstanding

    return NCAVPS

###################################################
# Relative Volatility Functions
###################################################

def calculate_RT(PT, PT_minus_one):
    log_value = math.log(PT / PT_minus_one)
    return math.pow(log_value, 2)

def calculate_RV(company):
    past_30_days = get_past_30_day_price(company)

    price_amount_counter = 0
    prev_close_price = 0.0
    summation_value = 0.0
    for close_price in past_30_days["Close"]:
        if price_amount_counter > 0:
            RT = calculate_RT(close_price, prev_close_price)
            summation_value += RT
        
        prev_close_price = close_price
        price_amount_counter += 1
    
    relized_vol = 100 * math.sqrt(252/30 * summation_value)

    return relized_vol

###################################################
# Implied Volatility Functions
###################################################

def parse_date():
    today = date.today()
    d3 = today.strftime("%m/%d/%y")
    date_split = d3.split('/')
    fixed_date = "20" + date_split[2] + "-" + date_split[0] + "-17"
    print(fixed_date)

    return fixed_date

def get_implied_volatility(company):
    ticker = get_yfinance_ticker(company)
    date = parse_date()
    opt = ticker.option_chain(date)
    #option_price = opt.calls["strike"]
    option_implied_volotility = opt.calls["impliedVolatility"] * 100
    print("Found IV: " + str(option_implied_volotility))

    return option_implied_volotility

###################################################
# MACD Functions
###################################################

def calculate_MACD(DF, a, b, c):
    df = DF.copy()
    df['MA Fast'] = df['Adj Close'].ewm(span=a, min_periods=a).mean()
    df['MA Slow'] = df['Adj Close'].ewm(span=b, min_periods=b).mean()
    df["MACD"] = df['MA Fast'] - df['MA Slow']
    df['Signal'] = df.MACD.ewm(span=c, min_periods=c).mean()
    df = df.dropna()

    return df

###################################################
# Testing Functions
###################################################

def testing_RV_and_IV():
    rv = calculate_RV("AAPL")
    print("Found RV For AAPL: " + str(rv))
    get_implied_volatility("AAPL")

def testing_MACD():
    price_history = get_past_30_day_price_download("AAPL")
    df = pd.DataFrame(price_history)
    result = calculate_MACD(df, 12, 26, 9)
    print("MACD")
    print(result["MACD"])

####################################################
####################################################
# Run Functions
####################################################
####################################################

testing_MACD()

stocks = get_tickers()
    
print("Total Stocks To Evaluate: " + str(len(stocks)))

company_counter = 0
message = []

# Get the following info from each company within the stocks list
for company in stocks:

    if DO_NCAVPS:
        # Incrament the company counter by one
        company_counter = company_counter + 1

        try:
            NCAVPS = calculate_NCAVPS(company)

            ticker = get_yfinance_ticker(company)

            # Get volume of the company
            volume = ticker.info["volume"]

            # Get the P/E ratio
            TRAILING_PE_RATIO = ticker.info["trailingPE"]
            FORWARD_PE_RATIO = ticker.info["forwardPE"]

            # Get the current price of the company
            price = ticker.info['currentPrice']

            # Only companies where NCAVPS is below the stock price
            if price < 0.67 * NCAVPS and volume > MIN_VOLUME:
                print("Company " + str(company_counter) + ": " + company + ", Current Price: " + str(price) + ", NCAVPS: " + str(NCAVPS) + ", Trailing P/E Ratio: " 
                + str(TRAILING_PE_RATIO) + ", Forward P/E Ratio: " + str(FORWARD_PE_RATIO) + ", Volume: " + str(volume))

                if price > MIN_PRICE:
                    message.append("Company " + str(company_counter) + ": " + company + ", Current Price: " + str(price) + ", NCAVPS: " + str(NCAVPS) + ", Trailing P/E Ratio: " 
                    + str(TRAILING_PE_RATIO) + ", Forward P/E Ratio: " + str(FORWARD_PE_RATIO) + ", Volume: " + str(volume) + "\n" + "https://finance.yahoo.com/quote/" + company + "/\n")
        
        except:
            pass
    else:
        print("here")


# DO SOMETHING WITH MACD AND RSS HERE, LOOKING FOR STOCKS THAT ARE GOING TO CHANGE BASED ON PAST TRENDS

####################################################
####################################################
# Messaging Functionality
####################################################
####################################################

# Use the Twilio client
client = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)

output = ""
for msg in message:
    output = output + msg

if not output:
    client.messages.create(from_=TWILIO_NUMBER, to=YOUR_NUMBER, body="No Stocks Today :(")
else:

    # Check if the message is larger than 1600 characters
    if len(output) > 1600:
        for msg in message:
            client.messages.create(from_=TWILIO_NUMBER, to=YOUR_NUMBER, body=msg)
    else:
        client.messages.create(from_=TWILIO_NUMBER, to=YOUR_NUMBER, body=output)