import yfinance as yf
from twilio.rest import Client
import requests

# Helpful website: https://www.netnethunter.com/deep-value-investing-guide/
# Another: https://algotrading101.com/learn/yahoo-finance-api-guide/

# The Financial Modeling Prep API Key
API_KEY = ""

# Settings for Twilio
TWILIO_ACCOUNT = ""
TWILIO_TOKEN = ""
TWILIO_NUMBER = ""
YOUR_NUMBER = ""

# What exchange to use
EXCHANGE = ["NYSE", "NASDAQ"]

# What period do you want to view the balance sheets from (quarterly or anually)
PERIOD = "quarter"

stocks = []

for market in EXCHANGE:

    # Get the list of tickers
    querytickers = requests.get(f'https://financialmodelingprep.com/api/v3/search?query=&limit=10000000&exchange=' + market + '&apikey=' + API_KEY)
    querytickers = querytickers.json()

    print("Market: " + market + ", Number of Listings: " + str(len(querytickers)))

    # At the selected number of tickers to the list
    list_500 = querytickers
    for item in list_500:
        stocks.append(item['symbol'])

company_counter = 0
message = []

# Get the following info from each company within the stocks list
for company in stocks:

    # Incrament the company counter by one
    company_counter = company_counter + 1

    try:
        # Get the balance sheet of the company
        Balance_Sheet = requests.get(f'https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/{company}?period=' + PERIOD + '&apikey=' + API_KEY)
        Balance_Sheet = Balance_Sheet.json()

        # Get the total current assets
        total_current_assets = float(Balance_Sheet['financials'][0]['Total current assets'])

        # Get the total liabilities
        total_liabilities = float(Balance_Sheet['financials'][0]['Total liabilities'])

        # Get the Yahoo Finance info on the curreny company
        ticker = yf.Ticker(company)

        # Get the number of shares outstanding
        shares_outstanding = ticker.info["sharesOutstanding"]

        # Here we are calculating the Net Current Asset Value per Share (NCAVPS)
        # If a stock is trading below the NCAVPS then its a good buy
        # Aim for the stock price to be 66% less than its NCAVPS
        NCAVPS = (total_current_assets - total_liabilities) / shares_outstanding

        # Get the market cap of the company
        market_cap = ticker.info["marketCap"]

        # Get the total debt of the company
        debt = ticker.info["totalDebt"]

        # Get the total cash of the company
        cash = ticker.info["totalCash"]

        # Get the EBITDA of the company
        EBITDA = ticker.info["ebitda"]

        # Calculate the enterprise value of the company
        EV = market_cap + debt - cash

        # Calculate the Acquirer's Multiple: EV / EBITDA
        # EV = Enterprise Value = Market Cap + Debt - Cash
        ACQUIRER_MULTIPLE = EV / EBITDA

        # Get the P/E ratio
        TRAILING_PE_RATIO = ticker.info["trailingPE"]
        FORWARD_PE_RATIO = ticker.info["forwardPE"]

        # Get the current price of the company
        price = ticker.info['currentPrice']

        # Only companies where NCAVPS is below the stock price
        if price < 0.67 * NCAVPS:
            print("Company " + str(company_counter) + ": " + company + ", Current Price: " + str(price) + ", NCAVPS: " + str(NCAVPS) + ", Trailing P/E Ratio: " 
            + str(TRAILING_PE_RATIO) + ". Forward P/E Ratio: " + str(FORWARD_PE_RATIO))

            message.append("Company " + str(company_counter) + ": " + company + ", Current Price: " + str(price) + ", NCAVPS: " + str(NCAVPS) + ", Trailing P/E Ratio: " 
            + str(TRAILING_PE_RATIO) + ". Forward P/E Ratio: " + str(FORWARD_PE_RATIO) + "\n" + "https://finance.yahoo.com/quote/" + company + "/\n")
    
    except:
        pass

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