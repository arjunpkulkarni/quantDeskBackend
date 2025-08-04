
CREATE TABLE IF NOT EXISTS companies (
    exchange VARCHAR(255),
    symbol VARCHAR(255) PRIMARY KEY,
    short_name VARCHAR(255),
    long_name VARCHAR(255),
    sector VARCHAR(255),
    industry VARCHAR(255),
    current_price DECIMAL(10, 2),
    market_cap BIGINT,
    ebitda BIGINT,
    revenue_growth DECIMAL(5, 3),
    city VARCHAR(255),
    state VARCHAR(255),
    country VARCHAR(255),
    full_time_employees INT,
    long_business_summary TEXT,
    weight DECIMAL(18, 16)
);

CREATE TABLE IF NOT EXISTS sp500_index (
    date DATE PRIMARY KEY,
    sp500_value DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    date DATE,
    symbol VARCHAR(255),
    adj_close DECIMAL(10, 2),
    close DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    open DECIMAL(10, 2),
    volume BIGINT,
    PRIMARY KEY (date, symbol),
    FOREIGN KEY (symbol) REFERENCES companies(symbol)
);

-- New tables from Stage 2 Design
CREATE TABLE IF NOT EXISTS user (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS broker_account (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    account_type VARCHAR(20),
    provider_ref VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS security (
    security_id INT PRIMARY KEY AUTO_INCREMENT,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    asset_class VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS portfolio_holding (
    holding_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    security_id INT,
    quantity DECIMAL(18,8),
    book_cost DECIMAL(12,2),
    FOREIGN KEY (account_id) REFERENCES broker_account(account_id),
    FOREIGN KEY (security_id) REFERENCES security(security_id)
);

CREATE TABLE IF NOT EXISTS price_snapshot (
    snapshot_id INT PRIMARY KEY AUTO_INCREMENT,
    security_id INT,
    price DECIMAL(12,4),
    snapshot_ts TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES security(security_id)
);

CREATE TABLE IF NOT EXISTS risk_metric (
    metric_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    VaR DECIMAL(12,4),
    Sharpe_ratio DECIMAL(6,3),
    calc_date DATE,
    FOREIGN KEY (account_id) REFERENCES broker_account(account_id)
); 