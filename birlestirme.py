import datetime
import backtrader as bt
from strategies import *
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from finbert_utils import estimate_sentiment
import yfinance as yf
import numpy as np
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import yfinance as yf
import alpaca_trade_api as tradeapi
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest

# Alpaca API anahtar bilgileri
API_KEY = "PKTN5OI55OV4LKN7Z4J0"
API_SECRET = "1jPeSwtJMa804W6OtPJsgHoj5Cp4jBCGCzarNQO1"
BASE_URL = "https://paper-api.alpaca.markets/v2"

# Alpaca API objesi oluşturma
api = tradeapi.REST(API_KEY, API_SECRET, base_url=BASE_URL)



trading_client = TradingClient(API_KEY, API_SECRET)

# Get our account information.
account = trading_client.get_account()

# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check how much money we can use to open new positions.
print('${} is available as buying power.'.format(account.buying_power))
