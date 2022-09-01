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

def fetch_balance():
    balance = exchange.fetch_balance({
        "type":"future"
    })

    return balance['total']

print(fetch_balance())