import warnings
warnings.filterwarnings('ignore')
import config

import ccxt
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)

import numpy as np
from datetime import datetime
import time

exchange_id = config.EXCHANGE
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY
})

def fetch_balance(type_):
    balance = exchange.fetch_balance({
        "type":type_
    })

    return balance['total']

def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr_ = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr_

def atr(data, period):
    data['tr'] = tr(data)
    atr_ = data['tr'].rolling(period).mean()

    return atr_

def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df


IN_POSITION = False

def check_buy_sell_signals(df):
    global IN_POSITION

    print("checking for buy and sell signals", config.SYMBOL)
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        if not IN_POSITION:
            # order = exchange.create_market_buy_order(config.SYMBOL, 0.05)
            # print(order)
            IN_POSITION = True
        else:
            print("already in position, nothing to do")
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if IN_POSITION:
            print("changed to downtrend, sell")
            # order = exchange.create_market_sell_order(config.SYMBOL, 0.05)
            # print(order)
            IN_POSITION = False
        else:
            print("You aren't in position, nothing to sell")

def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv(config.SYMBOL, timeframe=config.TIMEFRAME, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    # print(supertrend_data.tail(5))
    check_buy_sell_signals(supertrend_data)


schedule.every(10).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)
