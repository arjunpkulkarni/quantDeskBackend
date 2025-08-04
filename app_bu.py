from flask import Flask, jsonify
from flask_cors import CORS
import pymysql
from decouple import config

app = Flask(__name__)
CORS(app)

# Database connection
try:
    connection = pymysql.connect(
        host='localhost',
        user=config('DB_USER'),
        password=config('DB_PASS'),
        database='track1_stage3',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
    connection = None

@app.route('/api/companies', methods=['GET'])
def get_companies():
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT symbol, long_name, sector, industry, market_cap FROM companies LIMIT 20")
            companies = cursor.fetchall()
            return jsonify(companies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
