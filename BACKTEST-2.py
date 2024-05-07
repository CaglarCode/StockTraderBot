import yfinance as yf
import matplotlib
import pandas as pd
import numpy as np
tesla = yf.Ticker("TSLA")

tesla = tesla.history(period="max")
tesla
tesla.index
tesla.plot.line(y="Close", use_index = True)
tesla.plot.line(y="Volume",use_index=True)
del tesla["Stock Splits"] 
del tesla["Dividends"]

tesla["Tomorrow"] = tesla["Close"].shift(-1)

tesla["Target"] = (tesla["Tomorrow"]>tesla["Close"]).astype(int)
tesla

tesla= tesla["2020-01-01":].copy()
tesla

from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=1000, min_samples_split=100, random_state=1)
train = tesla.iloc[:-1000]
test = tesla.iloc[-100:]

predictors = ["Close", "Volume", "Open", "High", "Low"]
model.fit(train[predictors], train["Target"])
RandomForestClassifier(min_samples_split=100, random_state=1)

from sklearn.metrics import precision_score

preds = model.predict(test[predictors])
preds = pd.Series(preds, index=test.index)
precision_score(test["Target"], preds)

combined = pd.concat([test["Target"], preds], axis=1)
combined.plot()

def predict(train, test, predictors, model):
    model.fit(train[predictors], train["Target"])
    preds = model.predict(test[predictors])
    preds = pd.Series(preds, index=test.index, name="Predictions")
    combined = pd.concat([test["Target"], preds], axis=1)
    return combined
def backtest(data, model, predictors, start=2500, step=250):
    all_predictions = []

    for i in range(start, min(data.shape[0], start + 10000), step):
        train = data.iloc[0:i].copy()
        test = data.iloc[i:i+step].copy()

        # Eğer train veya test seti boşsa, döngüyü atla
        if len(train) == 0 or len(test) == 0:
            print(f"Train veya test seti boş. Iterasyon: {i}")
            continue

        predictions = predict(train, test, predictors, model)
        all_predictions.append(predictions)

    return pd.concatenate(all_predictions) if all_predictions else None

predictions = backtest(tesla, model, predictors)
if predictions is not None:
    predictions["Predictions"].value_counts()
precision_score(predictions["Target"], predictions["Predictions"])