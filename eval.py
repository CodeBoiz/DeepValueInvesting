import yfinance as yf
import pandas as pd

# Helpful website: https://www.netnethunter.com/deep-value-investing-guide/
# Another: https://algotrading101.com/learn/yahoo-finance-api-guide/

ticker = yf.Ticker('AAPL')

#print(ticker.info)

# Acquirer's Multiple: EV / EBITDA
# EV = Enterprise Value = Market Cap + Debt - Cash
market_cap = ticker.info["marketCap"]
debt = ticker.info["totalDebt"]
cash = ticker.info["totalCash"]

ebitda = ticker.info["ebitda"]
ev = market_cap + debt - cash

acquirer_multiple = ev / ebitda

print("Acquirer's Multiple: " + str(acquirer_multiple))

# Net Nets: NCAV
# Net Current Asset Value = Current Assets - Total Liabilities - Preferred Shares
current_assets = ""
total_liabilities = ""
preferred_shares = ""

ncav = current_assets - total_liabilities - preferred_shares