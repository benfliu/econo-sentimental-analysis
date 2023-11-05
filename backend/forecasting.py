from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

import yfinance as yf
from finqual import finqual as fq
from fredapi import Fred

from statsmodels.tsa.api import VAR
from sklearn.preprocessing import StandardScaler

def get_company_data(ticker, start, end):
    
    income = fq.Ticker(ticker).income(start.year, end.year, quarter = True).transpose()
    balance = fq.Ticker(ticker).balance(start.year, end.year, quarter = True).transpose()
    cashflow = fq.Ticker(ticker).cashflow(start.year, end.year, quarter = True).transpose()
    stock = yf.Ticker(ticker).history(start = start, end = end, interval = '3mo')
    
    stock.set_index(pd.PeriodIndex(stock.index, freq='Q'), inplace = True)

    company = pd.merge(income, balance, left_index = True, right_index = True)
    company = pd.merge(company, cashflow, left_index = True, right_index = True)
    company.set_index(pd.PeriodIndex(company.index, freq='Q'), inplace = True)
    company = pd.merge(company, stock, left_index = True, right_index = True)

    company = company[["Revenues", "EBIT", "Gross Profit", "Basic EPS", "Cost of Revenue",
                 "Total Assets", "Total Liabilities", "Stockholder's Equity",
                 "Operating Cash Flow", "Free Cash Flow", "Volume", "Close"]]
    
    return company

def get_macroeconomic_data (start, end):
    
    f = Fred(api_key = '2a9a09745f768dbc831afd556b96c5d2')
    
    unemployment = f.get_series('UNRATE', observation_start = start, frequency = 'q')
    gdp = f.get_series('GDP', observation_start = start, frequency = 'q')
    cpi = f.get_series('CPIAUCSL', observation_start = start, frequency = 'q') # CPI
    dollar = f.get_series('DTWEXBGS', observation_start = start, frequency = 'q') # Nominal Broad US Dollar Index
    cci = f.get_series('CSCICP03USM665S', observation_start = start, frequency = 'q') # CCI
    
    macro = pd.concat((unemployment, gdp, cpi, dollar, cci), axis = 1)
    macro.columns = ["Unemployment", "GDP", "CPI", "Dollar", "CCI"]
    macro.set_index(pd.PeriodIndex(macro.index, freq='Q'), inplace = True)
    
    return macro

def get_data (ticker, start, end):
    
    company = get_company_data(ticker, start, end)
    macro = get_macroeconomic_data(start, end)
    merged = pd.merge(company, macro, left_index = True, right_index = True)
    return merged.dropna(axis = 0).sort_index()

def forecast (ticker, steps, with_macro = True):
        
    end = datetime.now()
    start = (end - relativedelta(years = 10))
    
    if with_macro:
        data = get_data(ticker, start, end)
        # Add sentiment data
    else:
        data = get_company_data(ticker, start, end).dropna(axis = 0).sort_index()
    
    scaler = StandardScaler()
    data_arr = scaler.fit_transform(data)

    try:
        model = VAR(data_arr)
        results = model.fit()
        results.summary()
    except Exception as e:
        print("There was an issue with the VAR model:", e)

    out = scaler.inverse_transform(results.forecast(data_arr, steps))
    return pd.DataFrame(out, columns = data.columns)