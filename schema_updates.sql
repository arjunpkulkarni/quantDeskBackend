-- =================================================================
-- 1. INDEXING FOR FASTER QUERIES
-- =================================================================

-- Add indexes to the companies table for faster filtering and searching
CREATE INDEX idx_companies_sector ON companies(sector);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_long_name ON companies(long_name);

-- Add a composite index for portfolio holdings for faster lookups
CREATE INDEX idx_portfolio_holding_account_security ON portfolio_holding(account_id, security_id);


-- =================================================================
-- 2. PORTFOLIO SUMMARY TABLE AND TRIGGERS
-- =================================================================

-- Create a table to hold portfolio summary data
CREATE TABLE IF NOT EXISTS portfolio_summary (
    account_id INT PRIMARY KEY,
    total_value DECIMAL(20, 4) DEFAULT 0.00,
    total_book_cost DECIMAL(20, 4) DEFAULT 0.00,
    unique_assets INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES broker_account(account_id) ON DELETE CASCADE
);

-- Stored procedure to recalculate a portfolio's summary
DELIMITER //
CREATE PROCEDURE UpdatePortfolioSummary(IN p_account_id INT)
BEGIN
    DECLARE v_total_value DECIMAL(20, 4);
    DECLARE v_total_book_cost DECIMAL(20, 4);
    DECLARE v_unique_assets INT;

    -- Calculate aggregated values
    SELECT
        SUM(ph.quantity * ps.price),
        SUM(ph.book_cost),
        COUNT(DISTINCT ph.security_id)
    INTO
        v_total_value,
        v_total_book_cost,
        v_unique_assets
    FROM
        portfolio_holding ph
    JOIN
        price_snapshot ps ON ph.security_id = ps.security_id
    WHERE
        ph.account_id = p_account_id;
        
    -- Insert or update the summary table
    INSERT INTO portfolio_summary (account_id, total_value, total_book_cost, unique_assets)
    VALUES (p_account_id, v_total_value, v_total_book_cost, v_unique_assets)
    ON DUPLICATE KEY UPDATE
        total_value = VALUES(total_value),
        total_book_cost = VALUES(total_book_cost),
        unique_assets = VALUES(unique_assets);
END //
DELIMITER ;

-- Triggers to automatically update the summary table
DELIMITER //
CREATE TRIGGER after_holding_insert
AFTER INSERT ON portfolio_holding
FOR EACH ROW
BEGIN
    CALL UpdatePortfolioSummary(NEW.account_id);
END; //

CREATE TRIGGER after_holding_update
AFTER UPDATE ON portfolio_holding
FOR EACH ROW
BEGIN
    CALL UpdatePortfolioSummary(NEW.account_id);
    IF OLD.account_id != NEW.account_id THEN
        CALL UpdatePortfolioSummary(OLD.account_id);
    END IF;
END; //

CREATE TRIGGER after_holding_delete
AFTER DELETE ON portfolio_holding
FOR EACH ROW
BEGIN
    CALL UpdatePortfolioSummary(OLD.account_id);
END; //
DELIMITER ;


-- =================================================================
-- 3. FINANCIAL CALCULATION STORED PROCEDURES
-- =================================================================

-- Note: These are example structures. The financial formulas may need
-- to be adjusted based on the exact data available and desired models.

-- Stored Procedure for Value at Risk (VaR)
DELIMITER //
CREATE PROCEDURE CalculateVaR(IN p_account_id INT)
BEGIN
    -- Placeholder for VaR calculation logic.
    -- This would typically involve fetching historical price data,
    -- calculating daily returns, volatility, and then the VaR value.
    -- For this example, we'll just insert a dummy value.
    
    INSERT INTO risk_metric (account_id, VaR, calc_date)
    VALUES (p_account_id, RAND() * 1000, CURDATE())
    ON DUPLICATE KEY UPDATE VaR = VALUES(VaR), calc_date = VALUES(calc_date);

END //
DELIMITER ;

-- Stored Procedure for Sharpe Ratio
DELIMITER //
CREATE PROCEDURE CalculateSharpeRatio(IN p_account_id INT)
BEGIN
    -- Placeholder for Sharpe Ratio calculation logic.
    -- This would involve calculating portfolio return, volatility,
    -- and using a risk-free rate.
    
    INSERT INTO risk_metric (account_id, Sharpe_ratio, calc_date)
    VALUES (p_account_id, RAND() * 5, CURDATE())
    ON DUPLICATE KEY UPDATE Sharpe_ratio = VALUES(Sharpe_ratio), calc_date = VALUES(calc_date);

END //
DELIMITER ;

-- Stored Procedure for Drawdown (This is more complex and usually done in application code)
-- This is a simplified example.
DELIMITER //
CREATE PROCEDURE CalculateDrawdown(IN p_account_id INT)
BEGIN
    -- Placeholder for Drawdown calculation.
    -- This would require a time series of portfolio values.
    
    -- For demonstration, we'll just log a message or dummy value.
    -- In a real scenario, this would be a more involved calculation.
    SELECT 'Drawdown calculation logic would be executed here.' as status;

END //
DELIMITER ;
