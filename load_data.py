
import pandas as pd
import pymysql
from decouple import config
from sqlalchemy import create_engine

# Database configuration
DB_USER = config('DB_USER')
DB_PASS = config('DB_PASS')
DB_HOST = 'localhost'
DB_NAME = 'track1_stage3'

# Create a database engine
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}')

def load_csv_to_table(filepath, table_name):
    """Loads a CSV file into a database table."""
    try:
        df = pd.read_csv(filepath)
        # Rename columns to match the database schema
        if table_name == 'sp500_index':
            df = df.rename(columns={'S&P500': 'sp500_value'})
        elif table_name == 'stock_prices':
            df = df.rename(columns={
                'Adj Close': 'adj_close',
                'Close': 'close',
                'High': 'high',
                'Low': 'low',
                'Open': 'open',
                'Volume': 'volume'
            })
        elif table_name == 'companies':
            df = df.rename(columns={
                'Shortname': 'short_name',
                'Longname': 'long_name',
                'Currentprice': 'current_price',
                'Marketcap': 'market_cap',
                'Ebitda': 'ebitda',
                'Revenuegrowth': 'revenue_growth',
                'Fulltimeemployees': 'full_time_employees',
                'Longbusinesssummary': 'long_business_summary',
                'Weight': 'weight'
            })


        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(df)} rows into '{table_name}'.")
    except Exception as e:
        print(f"Error loading data into '{table_name}': {e}")

if __name__ == "__main__":
    # Load the data
    load_csv_to_table('data/sp500_companies.csv', 'companies')
    load_csv_to_table('data/sp500_index.csv', 'sp500_index')
    load_csv_to_table('data/sp500_stocks.csv', 'stock_prices') 