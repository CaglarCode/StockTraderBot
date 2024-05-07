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
# Diğer gerekli kütüphaneler (örneğin: finbert_utils, teknik göstergeler için gerekli kütüphaneler)

# Alpaca API anahtar bilgileri
API_KEY = "PKTN5OI55OV4LKN7Z4J0"
API_SECRET = "1jPeSwtJMa804W6OtPJsgHoj5Cp4jBCGCzarNQO1"
BASE_URL = "https://paper-api.alpaca.markets/v2"
# Alpaca API objesi oluşturma
api = tradeapi.REST(API_KEY, API_SECRET, base_url=BASE_URL)

class MLTrader:
    def __init__(self, symbol="APPL", cash_at_risk=0.5):
        self.symbol = symbol
        self.cash_at_risk = cash_at_risk

    def trade_logic(self):
        # Hesap bilgilerini al
        account = api.get_account()
        cash = float(account.cash)

        # Fiyat verilerini yükle
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        price_data = yf.download(self.symbol, start=start_date, end=end_date)

        # Teknik göstergeleri hesapla
        price_data['EMA'] = self.EMA(price_data, 20)
        price_data['MACD'], price_data['MACDSignal'] = self.MACD(price_data)
        price_data['RSI'] = self.RSI(price_data, 14)

        # Duyarlılık analizi
        def get_sentiment(self): 
            today, three_days_prior = self.get_dates()
            news = self.api.get_news(symbol=self.symbol, 
                                    start=three_days_prior, 
                                    end=today) 
            news = [ev.__dict__["_raw"]["headline"] for ev in news]
            probability, sentiment = estimate_sentiment(news)
            return probability, sentiment 
        
        # Ticaret sinyallerini belirle
        is_buy_signal = price_data['MACD'].iloc[-1] > price_data['MACDSignal'].iloc[-1] and sentiment == "positive"
        is_sell_signal = price_data['MACD'].iloc[-1] < price_data['MACDSignal'].iloc[-1] and sentiment == "negative"

        # Ticaret mantığını uygula
        if is_buy_signal and cash > 100:  # Yeterli nakit varsa
            api.submit_order(symbol=self.symbol, qty=1, side='buy', type='market', time_in_force='gtc')
        elif is_sell_signal:
            api.submit_order(symbol=self.symbol, qty=1, side='sell', type='market', time_in_force='gtc')

    # Teknik Göstergeleri Hesaplayan Fonksiyonlar
    def EMA(self, data, period, column='Close'):
        return data[column].ewm(span=period, adjust=False).mean()

    def MACD(self, data, fast_period=12, slow_period=26, signal_period=9):
        fast_ema = self.EMA(data, fast_period)
        slow_ema = self.EMA(data, slow_period)
        macd = fast_ema - slow_ema
        macdsignal = macd.ewm(span=signal_period, adjust=False).mean()
        return macd, macdsignal

    def RSI(self, data, period):
        delta = data['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=period - 1, adjust=True).mean()
        ema_down = down.ewm(com=period - 1, adjust=True).mean()
        rs = ema_up / ema_down
        return 100 - (100 / (1 + rs))