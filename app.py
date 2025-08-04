from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
from decouple import config
import yfinance as yf

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user=config('DB_USER'),
        password=config('DB_PASS'),
        database='track1_stage3',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True  # Autocommit changes
    )

# Get all companies
@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT symbol, long_name, sector, industry, market_cap, current_price FROM companies")
                companies = cursor.fetchall()
                return jsonify(companies)
    except Exception as e:
        print(f"Error in get_companies: {e}")
        return jsonify({"error": "An error occurred while fetching companies."}), 500

# Get a single company by symbol
@app.route('/api/companies/<string:symbol>', methods=['GET'])
def get_company(symbol):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM companies WHERE symbol = %s", (symbol,))
                company = cursor.fetchone()
                if company:
                    return jsonify(company)
                else:
                    return jsonify({"error": "Company not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create a new company using yfinance
@app.route('/api/companies', methods=['POST'])
def create_company():
    data = request.get_json()
    if not data or 'ticker' not in data:
        return jsonify({"error": "Ticker symbol is required"}), 400
    
    ticker_symbol = data['ticker']
    
    try:
        # Fetch data from yfinance
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        if not info or info.get('trailingPegRatio') is None:
             return jsonify({"error": f"Could not find data for ticker: {ticker_symbol}"}), 404

        # Prepare data for insertion
        company_data = {
            'exchange': info.get('exchange'),
            'symbol': info.get('symbol'),
            'short_name': info.get('shortName'),
            'long_name': info.get('longName'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'current_price': info.get('currentPrice'),
            'market_cap': info.get('marketCap'),
            'ebitda': info.get('ebitda'),
            'revenue_growth': info.get('revenueGrowth'),
            'city': info.get('city'),
            'state': info.get('state'),
            'country': info.get('country'),
            'full_time_employees': info.get('fullTimeEmployees'),
            'long_business_summary': info.get('longBusinessSummary'),
            'weight': info.get('weight')
        }

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO companies (exchange, symbol, short_name, long_name, sector, industry, 
                                     current_price, market_cap, ebitda, revenue_growth, city, state, 
                                     country, full_time_employees, long_business_summary, weight)
                VALUES (%(exchange)s, %(symbol)s, %(short_name)s, %(long_name)s, %(sector)s, %(industry)s,
                        %(current_price)s, %(market_cap)s, %(ebitda)s, %(revenue_growth)s, %(city)s,
                        %(state)s, %(country)s, %(full_time_employees)s, %(long_business_summary)s, %(weight)s)
                ON DUPLICATE KEY UPDATE
                    exchange=VALUES(exchange), short_name=VALUES(short_name), long_name=VALUES(long_name),
                    sector=VALUES(sector), industry=VALUES(industry), current_price=VALUES(current_price),
                    market_cap=VALUES(market_cap), ebitda=VALUES(ebitda), revenue_growth=VALUES(revenue_growth),
                    city=VALUES(city), state=VALUES(state), country=VALUES(country),
                    full_time_employees=VALUES(full_time_employees), 
                    long_business_summary=VALUES(long_business_summary), weight=VALUES(weight);
                """
                cursor.execute(sql, company_data)
        
        return jsonify({"message": f"Company {ticker_symbol} added/updated successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a company
@app.route('/api/companies/<string:symbol>', methods=['PUT'])
def update_company(symbol):
    try:
        data = request.get_json()
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                sql = "UPDATE companies SET short_name = %s, long_name = %s, sector = %s, industry = %s WHERE symbol = %s"
                cursor.execute(sql, (data['short_name'], data['long_name'], data['sector'], data['industry'], symbol))
            return jsonify({"message": "Company updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a company
@app.route('/api/companies/<string:symbol>', methods=['DELETE'])
def delete_company(symbol):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM companies WHERE symbol = %s", (symbol,))
            return jsonify({"message": "Company deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Keyword search for companies
@app.route('/api/companies/search', methods=['GET'])
def search_companies():
    try:
        keyword = request.args.get('keyword', '')
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM companies WHERE long_name LIKE %s OR short_name LIKE %s"
                cursor.execute(sql, (f"%{keyword}%", f"%{keyword}%"))
                companies = cursor.fetchall()
                return jsonify(companies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Update a portfolio asset
@app.route('/api/portfolio/<string:ticker>', methods=['PUT'])
def update_portfolio_asset(ticker):
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        # Assuming a fixed account_id for now
        account_id = 1
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Get security_id from ticker
                cursor.execute("SELECT security_id FROM security WHERE ticker = %s", (ticker,))
                security = cursor.fetchone()
                if not security:
                    return jsonify({"error": "Security not found"}), 404
                security_id = security['security_id']

                # Update portfolio_holding
                cursor.execute("""
                    UPDATE portfolio_holding 
                    SET quantity = %s 
                    WHERE account_id = %s AND security_id = %s
                """, (quantity, account_id, security_id))
                
                return jsonify({"message": "Asset updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Transaction: Transfer a security between two accounts
@app.route('/api/transactions/transfer', methods=['POST'])
def transfer_security():
    try:
        data = request.get_json()
        from_account = data['from_account']
        to_account = data['to_account']
        security_id = data['security_id']
        quantity = data['quantity']
        
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    connection.begin()
                    # Check if the 'from' account has the security
                    cursor.execute("SELECT quantity FROM portfolio_holding WHERE account_id = %s AND security_id = %s", (from_account, security_id))
                    holding = cursor.fetchone()
                    if not holding or holding['quantity'] < quantity:
                        raise Exception("Insufficient quantity to transfer")

                    # Debit from the 'from' account
                    cursor.execute("UPDATE portfolio_holding SET quantity = quantity - %s WHERE account_id = %s AND security_id = %s", (quantity, from_account, security_id))

                    # Credit to the 'to' account
                    cursor.execute("INSERT INTO portfolio_holding (account_id, security_id, quantity, book_cost) VALUES (%s, %s, %s, 0) ON DUPLICATE KEY UPDATE quantity = quantity + %s", (to_account, security_id, quantity, quantity))
                    
                    connection.commit()
                    return jsonify({"message": "Transfer successful"})
                except Exception as e:
                    connection.rollback()
                    return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Stored Procedure: Get portfolio holdings for an account
@app.route('/api/procedures/portfolio-holdings/<int:account_id>', methods=['GET'])
def get_portfolio_holdings(account_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.callproc('GetPortfolioHoldings', (account_id,))
                holdings = cursor.fetchall()
                return jsonify(holdings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/securities', methods=['GET'])
def get_securities():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM security")
                securities = cursor.fetchall()
                return jsonify(securities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    try:
        # Assuming a fixed account_id for now
        account_id = 1
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    SELECT 
                        s.ticker, 
                        c.short_name as name,
                        ph.quantity,
                        c.current_price as price,
                        (ph.quantity * c.current_price) as value
                    FROM 
                        portfolio_holding ph
                    JOIN 
                        security s ON ph.security_id = s.security_id
                    JOIN
                        companies c ON s.ticker = c.symbol
                    WHERE 
                        ph.account_id = %s
                """
                cursor.execute(sql, (account_id,))
                portfolio = cursor.fetchall()
                return jsonify(portfolio)
    except Exception as e:
        print(f"Error in get_portfolio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio/add', methods=['POST'])
def add_portfolio_asset():
    try:
        data = request.get_json()
        ticker = data.get('ticker')
        quantity = data.get('quantity')
        
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Get security_id from ticker
                cursor.execute("SELECT security_id FROM security WHERE ticker = %s", (ticker,))
                security = cursor.fetchone()
                if not security:
                    return jsonify({"error": "Security not found"}), 404
                security_id = security['security_id']
                
                # Insert into portfolio_holding, assuming account_id = 1 and book_cost = 0 for now
                cursor.execute("""
                    INSERT INTO portfolio_holding (account_id, security_id, quantity, book_cost)
                    VALUES (1, %s, %s, 0)
                """, (security_id, quantity))
                
                return jsonify({"message": "Asset added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/<string:ticker>', methods=['DELETE'])
def delete_portfolio_asset(ticker):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # First, get the security_id from the ticker
                cursor.execute("SELECT security_id FROM security WHERE ticker = %s", (ticker,))
                security = cursor.fetchone()
                if not security:
                    return jsonify({"error": "Security not found"}), 404
                security_id = security['security_id']

                # Delete the holding, assuming account_id = 1
                result = cursor.execute("DELETE FROM portfolio_holding WHERE account_id = 1 AND security_id = %s", (security_id,))
                
                if result > 0:
                    return jsonify({"message": "Asset deleted successfully"}), 200
                else:
                    return jsonify({"error": "Asset not found in portfolio"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/summary/<int:account_id>', methods=['GET'])
def get_portfolio_summary(account_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM portfolio_summary WHERE account_id = %s", (account_id,))
                summary = cursor.fetchone()
                if summary:
                    return jsonify(summary)
                else:
                    return jsonify({"error": "No summary data found for this account."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk/var/<int:account_id>', methods=['POST'])
def calculate_var_route(account_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.callproc('CalculateVaR', (account_id,))
        return jsonify({"message": "VaR calculation initiated."}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk/sharpe/<int:account_id>', methods=['POST'])
def calculate_sharpe_route(account_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.callproc('CalculateSharpeRatio', (account_id,))
        return jsonify({"message": "Sharpe Ratio calculation initiated."}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk/drawdown/<int:account_id>', methods=['GET'])
def get_drawdown_route(account_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.callproc('CalculateDrawdown', (account_id,))
                result = cursor.fetchall()
                return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
