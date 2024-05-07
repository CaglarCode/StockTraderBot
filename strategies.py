import backtrader as bt
import requests
import datetime as dt
import alpaca_trade_api as tradeapi
import yfinance as yf
from finbert_utils import estimate_sentiment



class PrintClose(bt.Strategy):

	def __init__(self):
		#Keep a reference to the "close" line in the data[0] dataseries
		self.dataclose = self.datas[0].close

	def log(self, txt, dt=None):
		dt = dt or self.datas[0].datetime.date(0)
		print(f'{dt.isoformat()} {txt}') #Print date and close

	def next(self):
		self.log(f'Close: {self.dataclose[0]}')

class MAcrossover(bt.Strategy): 
	# Moving average parameters
	params = (('pfast',20),('pslow',50),)

	def log(self, txt, dt=None):
		dt = dt or self.datas[0].datetime.date(0)
		print(f'{dt.isoformat()} {txt}') # Comment this line when running optimization

	def __init__(self):
		self.dataclose = self.datas[0].close
		
		# Order variable will contain ongoing order details/status
		self.order = None

		# Instantiate moving averages
		self.fast_sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pfast)
		self.slow_sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.pslow)
		
		''' Using the built-in crossover indicator
		self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)'''


	def notify_order(self, order):
		if order.status in [order.Submitted, order.Accepted]:
			# An active Buy/Sell order has been submitted/accepted - Nothing to do
			return

		# Check if an order has been completed
		# Attention: broker could reject order if not enough cash
		if order.status in [order.Completed]:
			if order.isbuy():
				self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
			elif order.issell():
				self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
			self.bar_executed = len(self)

		elif order.status in [order.Canceled, order.Margin, order.Rejected]:
			self.log('Order Canceled/Margin/Rejected')

		# Reset orders
		self.order = None

	def next(self):
		''' Logic for using the built-in crossover indicator
		
		if self.crossover > 0: # Fast ma crosses above slow ma
			pass # Signal for buy order
		elif self.crossover < 0: # Fast ma crosses below slow ma
			pass # Signal for sell order
		'''

		# Check for open orders
		if self.order:
			return

		# Check if we are in the market
		if not self.position:
			# We are not in the market, look for a signal to OPEN trades
				
			#If the 20 SMA is above the 50 SMA
			if self.fast_sma[0] > self.slow_sma[0] and self.fast_sma[-1] < self.slow_sma[-1]:
				self.log(f'BUY CREATE {self.dataclose[0]:2f}')
				# Keep track of the created order to avoid a 2nd order
				self.order = self.buy()
			#Otherwise if the 20 SMA is below the 50 SMA   
			elif self.fast_sma[0] < self.slow_sma[0] and self.fast_sma[-1] > self.slow_sma[-1]:
				self.log(f'SELL CREATE {self.dataclose[0]:2f}')
				# Keep track of the created order to avoid a 2nd order
				self.order = self.sell()
		else:
			# We are already in the market, look for a signal to CLOSE trades
			if len(self) >= (self.bar_executed + 5):
				self.log(f'CLOSE CREATE {self.dataclose[0]:2f}')
				self.order = self.close()

class Screener_SMA(bt.Analyzer):
	params = (('period',20), ('devfactor',2),)

	def start(self):
		self.bbands = {data: bt.indicators.BollingerBands(data, period=self.params.period, devfactor=self.params.devfactor)
					 for data in self.datas}

	def stop(self):
		self.rets['over'] = list()
		self.rets['under'] = list()

		for data, band in self.bbands.items():
			node = data._name, data.close[0], round(band.lines.bot[0], 2)
			if data > band.lines.bot:
				self.rets['over'].append(node)
			else:
				self.rets['under'].append(node)

class AverageTrueRange(bt.Strategy):

	def log(self, txt, dt=None):
		dt = dt or self.datas[0].datetime.date(0)
		print(f'{dt.isoformat()} {txt}') #Print date and close
		
	def __init__(self):
		self.dataclose = self.datas[0].close
		self.datahigh = self.datas[0].high
		self.datalow = self.datas[0].low
		
	def next(self):
		range_total = 0
		for i in range(-13, 1):
			true_range = self.datahigh[i] - self.datalow[i]
			range_total += true_range
		ATR = range_total / 14

		self.log(f'Close: {self.dataclose[0]:.2f}, ATR: {ATR:.4f}')

class BtcSentiment(bt.Strategy):
	params = (('period', 10), ('devfactor', 1),)

	def log(self, txt, dt=None):
		dt = dt or self.datas[0].datetime.date(0)
		print(f'{dt.isoformat()} {txt}')

	def __init__(self):
		self.btc_price = self.datas[0].close
		self.google_sentiment = self.datas[1].close
		self.bbands = bt.indicators.BollingerBands(self.google_sentiment, period=self.params.period, devfactor=self.params.devfactor)

		self.order = None

	def notify_order(self, order):
		if order.status in [order.Submitted, order.Accepted]:
			return

		if order.status in [order.Completed]:
			if order.isbuy():
				self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
			elif order.issell():
				self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
			self.bar_executed = len(self)

		elif order.status in [order.Canceled, order.Margin, order.Rejected]:
			self.log('Order Canceled/Margin/Rejected')

		self.order = None

	def next(self):
		# Check for open orders
        
		if self.order:
			return

		#Long signal
         
		if self.google_sentiment > self.bbands.lines.top[0] and price_data['MACD'].iloc[-1] > price_data['MACDSignal'].iloc[-1] and sentiment == "positive":
			# Check if we are in the market
			if not self.position:
				self.log(f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
				self.log(f'Top band: {self.bbands.lines.top[0]:.2f}')
				# We are not in the market, we will open a trade
				self.log(f'***BUY CREATE {self.btc_price[0]:.2f}')
				# Keep track of the created order to avoid a 2nd order
				self.order = self.buy()       

		#Short signal
		elif self.google_sentiment < self.bbands.lines.bot[0] and self.macd[0] < self.macdsignal[0] and sentiment == "negative":
			# Check if we are in the market
			if not self.position:
				self.log(f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
				self.log(f'Bottom band: {self.bbands.lines.bot[0]:.2f}')
				# We are not in the market, we will open a trade
				self.log(f'***SELL CREATE {self.btc_price[0]:.2f}')
				# Keep track of the created order to avoid a 2nd order
				self.order = self.sell()
		
		#Neutral signal - close any open trades     
		else:
			if self.position:
				# We are in the market, we will close the existing trade
				self.log(f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
				self.log(f'Bottom band: {self.bbands.lines.bot[0]:.2f}')
				self.log(f'Top band: {self.bbands.lines.top[0]:.2f}')
				self.log(f'CLOSE CREATE {self.btc_price[0]:.2f}')
				self.order = self.close()
  
def RSI(self, data, period):
	delta = data['Close'].diff()
	up = delta.clip(lower=0)
	down = -1 * delta.clip(upper=0)
	ema_up = up.ewm(com=period - 1, adjust=True).mean()
	ema_down = down.ewm(com=period - 1, adjust=True).mean()
	rs = ema_up / ema_down
	return 100 - (100 / (1 + rs))

def EMA(self, data, period, column='Close'):
	return data[column].ewm(span=period, adjust=False).mean()

def MACD(self, data, fast_period=12, slow_period=26, signal_period=9):
	fast_ema = self.EMA(data, fast_period)
	slow_ema = self.EMA(data, slow_period)
	macd = fast_ema - slow_ema
	macdsignal = macd.ewm(span=signal_period, adjust=False).mean()
	return macd, macdsignal



    
class MLTrader:
    # Gerekli metotlar ve içerik buraya eklenecek

    def get_dates(self):
        today = dt.datetime.now()
        three_days_prior = today - dt.timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self, symbol):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=symbol, start=three_days_prior, end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment 
    
    def trade_logic_alpaca(self):
        API_KEY = "PKTN5OI55OV4LKN7Z4J0"
        API_SECRET = "1jPeSwtJMa804W6OtPJsgHoj5Cp4jBCGCzarNQO1"
        BASE_URL = "https://paper-api.alpaca.markets/v2"
        api = tradeapi.REST(API_KEY, API_SECRET, base_url=BASE_URL)
        # Hesap bilgilerini al
        account = api.get_account()
        cash = float(account.cash)

        # Fiyat verilerini yükle
        end_date = dt.datetime.now()
        start_date = end_date - dt.timedelta(days=60)
        price_data = yf.download(self.symbol, start=start_date, end=end_date)

        # Teknik göstergeleri hesapla
        price_data['EMA'] = self.EMA(price_data, 20)
        price_data['MACD'], price_data['MACDSignal'] = self.MACD(price_data)
        price_data['RSI'] = self.RSI(price_data, 14)
        
        