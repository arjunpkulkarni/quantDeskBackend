-- Stored Procedure to get portfolio holdings for a given account
DELIMITER //
CREATE PROCEDURE GetPortfolioHoldings(IN p_account_id INT)
BEGIN
    SELECT s.ticker, ph.quantity, ph.book_cost
    FROM portfolio_holding ph
    JOIN security s ON ph.security_id = s.security_id
    WHERE ph.account_id = p_account_id;
END //
DELIMITER ;

-- Audit table for company insertions
CREATE TABLE IF NOT EXISTS company_audit (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(255),
    action VARCHAR(50),
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to log new company insertions
DELIMITER //
CREATE TRIGGER AfterCompanyInsert
AFTER INSERT ON companies
FOR EACH ROW
BEGIN
    INSERT INTO company_audit (symbol, action)
    VALUES (NEW.symbol, 'INSERT');
END //
DELIMITER ;
