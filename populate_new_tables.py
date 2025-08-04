import pymysql
from decouple import config
from sqlalchemy import create_engine
import pandas as pd
import random
from datetime import datetime, timedelta

# Database configuration
DB_USER = config('DB_USER')
DB_PASS = config('DB_PASS')
DB_HOST = 'localhost'
DB_NAME = 'track1_stage3'

# Create a database engine
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}')

def populate_data():
    """Populates the new tables with sample data."""
    try:
        # Create Users
        users_data = [{'username': f'user_{i}'} for i in range(1, 11)]
        users_df = pd.DataFrame(users_data)
        users_df.to_sql('user', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(users_df)} rows into 'user'.")

        # Create BrokerAccounts
        accounts_data = [{'user_id': i, 'account_type': random.choice(['taxable', 'ira']), 'provider_ref': f'ref_{i}'} for i in range(1, 11)]
        accounts_df = pd.DataFrame(accounts_data)
        accounts_df.to_sql('broker_account', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(accounts_df)} rows into 'broker_account'.")

        # Create Securities from existing companies
        companies_df = pd.read_sql('SELECT symbol FROM companies', con=engine)
        securities_data = [{'ticker': symbol, 'asset_class': 'stock'} for symbol in companies_df['symbol']]
        securities_df = pd.DataFrame(securities_data)
        securities_df.to_sql('security', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(securities_df)} rows into 'security'.")

        # Get security_ids
        security_ids = pd.read_sql('SELECT security_id FROM security', con=engine)['security_id'].tolist()

        # Create PortfolioHoldings
        holdings_data = []
        for i in range(1, 1001):
            holdings_data.append({
                'account_id': random.randint(1, 10),
                'security_id': random.choice(security_ids),
                'quantity': random.uniform(1, 1000),
                'book_cost': random.uniform(10, 5000)
            })
        holdings_df = pd.DataFrame(holdings_data)
        holdings_df.to_sql('portfolio_holding', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(holdings_df)} rows into 'portfolio_holding'.")

        # Create PriceSnapshots
        snapshots_data = []
        for security_id in security_ids:
            for i in range(5): # 5 snapshots per security
                snapshots_data.append({
                    'security_id': security_id,
                    'price': random.uniform(50, 500),
                    'snapshot_ts': datetime.now() - timedelta(days=i)
                })
        snapshots_df = pd.DataFrame(snapshots_data)
        snapshots_df.to_sql('price_snapshot', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(snapshots_df)} rows into 'price_snapshot'.")

        # Create RiskMetrics
        risk_data = []
        for i in range(1, 11):
            risk_data.append({
                'account_id': i,
                'VaR': random.uniform(0.01, 0.1),
                'Sharpe_ratio': random.uniform(0.5, 2.5),
                'calc_date': datetime.now().date()
            })
        risk_df = pd.DataFrame(risk_data)
        risk_df.to_sql('risk_metric', con=engine, if_exists='append', index=False)
        print(f"Successfully loaded {len(risk_df)} rows into 'risk_metric'.")

    except Exception as e:
        print(f"Error populating data: {e}")

if __name__ == "__main__":
    populate_data() 