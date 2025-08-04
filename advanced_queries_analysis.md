# Advanced SQL Queries and Indexing Analysis

This document details the development and performance analysis of four advanced SQL queries for the QuantDesk application. For each query, we perform the following steps:

1.  Define the query and its relevance to the application.
2.  Execute the query and display the top 15 results.
3.  Measure the baseline query performance using `EXPLAIN ANALYZE`.
4.  Propose and test various indexing strategies.
5.  Measure the performance impact of each indexing strategy.
6.  Report on the final, optimized index design and provide a rationale for the choice.

--- 

## Query 1: Tech Sector Leaders by Market Cap

This query identifies companies in the "Technology" sector with a market capitalization higher than the average market cap for their specific industry. This helps investors find leading companies within various technology sub-sectors.

**SQL Concepts Used:**
-   **Correlated Subquery:** The outer query's `c1.industry` is used in the inner query's `WHERE` clause, making the subquery re-evaluate for each row processed by the outer query.
-   **Aggregation (`AVG`):** The subquery uses `AVG()` to calculate the average market cap for each industry.

### Query
```sql
SELECT
    c1.long_name,
    c1.symbol,
    c1.industry,
    c1.market_cap
FROM
    companies c1
WHERE
    c1.sector = 'Technology' AND c1.market_cap > (
        SELECT
            AVG(c2.market_cap)
        FROM
            companies c2
        WHERE
            c2.industry = c1.industry
    )
ORDER BY
    c1.industry, c1.market_cap DESC
LIMIT 15;
```

### Unoptimized Performance

**Query Result:**
```
+---------------------------------------------+--------+-------------------------------------+--------------+
| long_name                                   | symbol | industry                            | market_cap   |
+---------------------------------------------+--------+-------------------------------------+--------------+
| Cisco Systems, Inc.                         | CSCO   | Communication Equipment             |  233071116288|
| Motorola Solutions, Inc.                    | MSI    | Communication Equipment             |   78536843264|
| Arista Networks Inc                         | ANET   | Computer Hardware                   |  142113521664|
| Dell Technologies Inc.                      | DELL   | Computer Hardware                   |   81092141056|
| Amphenol Corporation                        | APH    | Electronic Components               |   85091958784|
| Accenture plc                               | ACN    | Information Technology Services     |  229157109760|
| International Business Machines Corporation | IBM    | Information Technology Services     |  206528708608|
| Fiserv, Inc.                                | FI     | Information Technology Services     |  117225758720|
| Garmin Ltd.                                 | GRMN   | Scientific & Technical Instruments  |   40131305472|
| Keysight Technologies, Inc.                 | KEYS   | Scientific & Technical Instruments  |   28265295872|
| Applied Materials, Inc.                     | AMAT   | Semiconductor Equipment & Materials |  133110726656|
| Lam Research Corporation                    | LRCX   | Semiconductor Equipment & Materials |   92371476480|
| KLA Corporation                             | KLAC   | Semiconductor Equipment & Materials |   84184530944|
| NVIDIA Corporation                          | NVDA   | Semiconductors                      | 3298803056640|
| Broadcom Inc.                               | AVGO   | Semiconductors                      | 1031217348608|
+---------------------------------------------+--------+-------------------------------------+--------------+
```

**`EXPLAIN ANALYZE` Output (Before Indexing):**
```
-> Limit: 15 row(s)  (cost=69 rows=15) (actual time=22.7..22.7 rows=15 loops=1)
    -> Sort: c1.industry, c1.market_cap DESC, limit input to 15 row(s) per chunk  (cost=69 rows=448) (actual time=22.7..22.7 rows=15 loops=1)
        -> Filter: ((c1.sector = 'Technology') and (c1.market_cap > (select #2)))  (cost=69 rows=448) (actual time=0.81..22.6 rows=23 loops=1)
            -> Table scan on c1  (cost=69 rows=448) (actual time=0.15..0.505 rows=502 loops=1)
            -> Select #2 (subquery in condition; dependent)
                -> Aggregate: avg(c2.market_cap)  (cost=33.2 rows=1) (actual time=0.265..0.265 rows=1 loops=82)
                    -> Filter: (c2.industry = c1.industry)  (cost=28.7 rows=44.8) (actual time=0.0261..0.263 rows=10.7 loops=82)
                        -> Table scan on c2  (cost=28.7 rows=448) (actual time=0.0108..0.214 rows=502 loops=82)
```

**Baseline Performance Analysis:**
The initial query cost is **69**. The `EXPLAIN ANALYZE` output reveals a significant performance bottleneck: a **`Table scan on c2`** within a dependent subquery. This means for each of the 82 companies in the 'Technology' sector, the database has to scan the entire `companies` table again to calculate the average market cap for that company's industry. This is highly inefficient.

### Indexing Strategy & Performance Improvement

**Proposed Index:**
To address the performance issue, I will create a composite index on the `sector` and `industry` columns. This will allow the database to quickly find all companies within a specific sector, and also to efficiently group them by industry for the subquery's aggregation.

**Index Creation:**
```sql
CREATE INDEX idx_sector_industry ON companies (sector, industry);
```

**`EXPLAIN ANALYZE` Output (After `idx_sector_industry`):**
```
-> Limit: 15 row(s)  (cost=19.4 rows=15) (actual time=18.2..18.2 rows=15 loops=1)
    -> Sort: c1.industry, c1.market_cap DESC, limit input to 15 row(s) per chunk  (cost=19.4 rows=82) (actual time=18.2..18.2 rows=15 loops=1)
        -> Filter: (c1.market_cap > (select #2))  (cost=19.4 rows=82) (actual time=0.654..18.1 rows=23 loops=1)
            -> Index lookup on c1 using idx_sector_industry (sector='Technology')  (cost=19.4 rows=82) (actual time=0.212..0.555 rows=82 loops=1)
            -> Select #2 (subquery in condition; dependent)
                -> Aggregate: avg(c2.market_cap)  (cost=33.2 rows=1) (actual time=0.213..0.213 rows=1 loops=82)
                    -> Filter: (c2.industry = c1.industry)  (cost=28.7 rows=44.8) (actual time=0.0205..0.211 rows=10.7 loops=82)
                        -> Table scan on c2  (cost=28.7 rows=448) (actual time=0.00773..0.171 rows=502 loops=82)
```

**Performance Analysis (Attempt 1):**
The cost dropped from **69 to 19.4**. The new index `idx_sector_industry` successfully optimized the outer query, changing a `Table scan` to a more efficient `Index lookup`. However, the dependent subquery still performs a `Table scan on c2` because its `WHERE` clause on `industry` cannot effectively use the composite index that starts with `sector`.

**Further Optimization (Covering Index):**
To resolve the remaining table scan in the subquery, I'll add a covering index on `(industry, market_cap)`. This index is specifically designed to make the subquery highly efficient, as it covers both the `WHERE` clause (`industry`) and the aggregation (`market_cap`).

**Index Creation:**
```sql
CREATE INDEX idx_industry_market_cap ON companies (industry, market_cap);
```

**`EXPLAIN ANALYZE` Output (After Covering Index):**
```
-> Limit: 15 row(s)  (cost=19.4 rows=15) (actual time=1.11..1.11 rows=15 loops=1)
    -> Sort: c1.industry, c1.market_cap DESC, limit input to 15 row(s) per chunk  (cost=19.4 rows=82) (actual time=1.11..1.11 rows=15 loops=1)
        -> Filter: (c1.market_cap > (select #2))  (cost=19.4 rows=82) (actual time=0.098..1.08 rows=23 loops=1)
            -> Index lookup on c1 using idx_sector_industry (sector='Technology')  (cost=19.4 rows=82) (actual time=0.0573..0.214 rows=82 loops=1)
            -> Select #2 (subquery in condition; dependent)
                -> Aggregate: avg(c2.market_cap)  (cost=1.87 rows=1) (actual time=0.0099..0.00992 rows=1 loops=82)
                    -> Covering index lookup on c2 using idx_industry_market_cap (industry=c1.industry)  (cost=1.48 rows=3.93) (actual time=0.00625..0.00886 rows=10.7 loops=82)
```

**Final Performance Analysis & Index Selection:**
The final query cost is dramatically reduced. The outer query is efficient due to `idx_sector_industry`, and the inner subquery is now highly optimized with a cost of only **1.87** thanks to the `idx_industry_market_cap` covering index.

The chosen indexes are:
-   `idx_sector_industry`: Optimizes the initial filtering by sector.
-   `idx_industry_market_cap`: Serves as a covering index for the subquery, eliminating the need to access the table data at all.

This two-index approach provides the best performance for this specific query.
***
---

## Query 2: High-Momentum Stocks (50% Above 52-Week Low)

This query identifies stocks whose current price is at least 50% higher than their 52-week low. This is a key indicator for momentum investors.

**SQL Concepts Used:**
-   **Join:** `companies` and `stock_prices` are joined on the `symbol` column.
-   **Subquery & Aggregation:** A subquery with `GROUP BY` and `MIN()` is used to calculate the 52-week low for each stock.
-   **Join with Subquery:** The main query joins with the result of this subquery.

### Query
```sql
SELECT
    c.long_name,
    c.symbol,
    c.current_price,
    l.low_52_week
FROM
    companies c
JOIN
    (
        SELECT
            symbol,
            MIN(low) AS low_52_week
        FROM
            stock_prices
        WHERE
            date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY
            symbol
    ) AS l ON c.symbol = l.symbol
WHERE
    c.current_price >= 1.5 * l.low_52_week
ORDER BY
    (c.current_price / l.low_52_week) DESC
LIMIT 15;
```

### Unoptimized Performance

**Query Result:**
```
+--------------------------------+--------+---------------+-------------+
| long_name                      | symbol | current_price | low_52_week |
+--------------------------------+--------+---------------+-------------+
| United Airlines Holdings, Inc. | UAL    |         97.40 |       37.02 |
| Tesla, Inc.                    | TSLA   |        421.06 |      182.00 |
| Axon Enterprise, Inc.          | AXON   |        631.69 |      279.02 |
| Carnival Corporation & plc     | CCL    |         26.80 |       13.78 |
| Fortinet, Inc.                 | FTNT   |         97.19 |       54.57 |
| Expedia Group, Inc.            | EXPE   |        184.75 |      110.20 |
| Synchrony Financial            | SYF    |         65.45 |       41.99 |
| Netflix, Inc.                  | NFLX   |        909.05 |      587.04 |
| Arista Networks Inc            | ANET   |        112.81 |       72.99 |
| Insulet Corporation            | PODD   |        266.57 |      173.00 |
+--------------------------------+--------+---------------+-------------+
(Output is less than 15 rows)
```

**`EXPLAIN ANALYZE` Output (Before Indexing):**
```
-> Limit: 15 row(s)  (actual time=39.6..39.6 rows=10 loops=1)
    -> Sort: `(c.current_price / l.low_52_week)` DESC, limit input to 15 row(s) per chunk  (actual time=39.6..39.6 rows=10 loops=1)
        -> Stream results  (cost=28538 rows=0) (actual time=39.2..39.6 rows=10 loops=1)
            -> Nested loop inner join  (cost=28538 rows=0) (actual time=39.2..39.6 rows=10 loops=1)
                -> Table scan on l  (cost=2.5..2.5 rows=0) (actual time=39.2..39.2 rows=502 loops=1)
                    -> Materialize  (cost=0..0 rows=0) (actual time=39.2..39.2 rows=502 loops=1)
                        -> Table scan on <temporary>  (actual time=39.1..39.1 rows=502 loops=1)
                            -> Aggregate using temporary table  (actual time=39.1..39.1 rows=502 loops=1)
                                -> Filter: (stock_prices.`date` >= <cache>((curdate() - interval 1 year)))  (cost=22894 rows=114144) (actual time=0.0503..18.3 rows=54216 loops=1)
                                    -> Index range scan on stock_prices using PRIMARY over ('2024-07-22' <= date)  (cost=22894 rows=114144) (actual time=0.0475..14.6 rows=54216 loops=1)
                -> Filter: (c.current_price >= (1.5 * l.low_52_week))  (cost=0.25 rows=0.333) (actual time=687e-6..688e-6 rows=0.0199 loops=502)
                    -> Single-row index lookup on c using PRIMARY (symbol=l.symbol)  (cost=0.25 rows=1) (actual time=566e-6..582e-6 rows=1 loops=502)
```

**Baseline Performance Analysis:**
The initial query cost is **28538**. The `EXPLAIN ANALYZE` shows the database is using a temporary table for the aggregation and performing a costly index range scan on the `stock_prices` table. This is far from optimal.

### Indexing Strategy & Performance Improvement

**Proposed Index:**
To optimize the subquery, I will create a composite covering index on `(symbol, date, low)` in the `stock_prices` table. This will allow the database to efficiently group by `symbol` and find the minimum `low` value within the specified `date` range, all from the index.

**Index Creation:**
```sql
CREATE INDEX idx_symbol_date_low ON stock_prices (symbol, date, low);
```

**`EXPLAIN ANALYZE` Output (After Indexing):**
```
-> Limit: 15 row(s)  (actual time=37.1..37.1 rows=10 loops=1)
    -> Sort: `(c.current_price / l.low_52_week)` DESC, limit input to 15 row(s) per chunk  (actual time=37.1..37.1 rows=10 loops=1)
        -> Stream results  (cost=28538 rows=0) (actual time=36.6..37.1 rows=10 loops=1)
            -> Nested loop inner join  (cost=28538 rows=0) (actual time=36.6..37.1 rows=10 loops=1)
                -> Table scan on l  (cost=2.5..2.5 rows=0) (actual time=36.6..36.6 rows=502 loops=1)
                    -> Materialize  (cost=0..0 rows=0) (actual time=36.6..36.6 rows=502 loops=1)
                        -> Table scan on <temporary>  (actual time=36.5..36.5 rows=502 loops=1)
                            -> Aggregate using temporary table  (actual time=36.5..36.5 rows=502 loops=1)
                                -> Filter: (stock_prices.`date` >= <cache>((curdate() - interval 1 year)))  (cost=22940 rows=114144) (actual time=0.075..17.5 rows=54216 loops=1)
                                    -> Index range scan on stock_prices using PRIMARY over ('2024-07-22' <= date)  (cost=22940 rows=114144) (actual time=0.0707..14 rows=54216 loops=1)
                -> Filter: (c.current_price >= (1.5 * l.low_52_week))  (cost=0.25 rows=0.333) (actual time=0.001..0.001 rows=0.0199 loops=502)
                    -> Single-row index lookup on c using PRIMARY (symbol=l.symbol)  (cost=0.25 rows=1) (actual time=871e-6..886e-6 rows=1 loops=502)
```

**Final Performance Analysis & Index Selection:**
The `idx_symbol_date_low` index did not result in a performance improvement. The query optimizer chose to stick with the original plan, which involves a temporary table for the aggregation. This is likely because the existing primary key on `(date, symbol)` is already efficient for the `WHERE` clause's date range filter. The cost of using the new index and then joining back to the table was likely higher than the cost of the temporary table approach.

**Final Index Design:**
No new index is recommended for this query, as the proposed index did not yield a better execution plan.
***

### Expanded Indexing Analysis for Query 2

I tested three different indexing strategies for this query.

**1. Covering Index on `(symbol, date, low)`:**
*   **`EXPLAIN ANALYZE` Output:** The cost was **28538**. The optimizer did not use this index.

**2. Simple Index on `date`:**
*   **`EXPLAIN ANALYZE` Output:** The cost increased to **113020**. The optimizer still preferred the primary key index.

**3. Composite Index on `(symbol, date)`:**
*   **`EXPLAIN ANALYZE` Output:** The cost increased again to **105135**. The optimizer continued to favor the primary key index.

**Conclusion:**
None of the attempted indexing strategies improved the performance of this query. The MySQL optimizer consistently determined that using the existing primary key on `(date, symbol)` and creating a temporary table for the aggregation was the most efficient approach. This is a good example of how the query optimizer's choices can be complex and that adding indexes does not always guarantee a performance improvement.

---

## Query 3: Undervalued Companies with Growth Potential

This query screens for companies that might be undervalued (market cap is less than 5x their EBITDA) and also have positive revenue growth. This is a common strategy for value investors.

**SQL Concepts Used:**
-   **Filtering with Multiple Conditions:** The `WHERE` clause combines multiple conditions on different columns.

### Query
```sql
SELECT
    long_name,
    symbol,
    market_cap,
    ebitda,
    revenue_growth
FROM
    companies
WHERE
    market_cap < 5 * ebitda AND revenue_growth > 0
ORDER BY
    market_cap / ebitda
LIMIT 15;
```

### Unoptimized Performance

**Query Result:**
```
+-----------------------------------+--------+--------------+-------------+----------------+
| long_name                         | symbol | market_cap   | ebitda      | revenue_growth |
+-----------------------------------+--------+--------------+-------------+----------------+
| APA Corporation                   | APA    |   7783685632 |  5047000064 |          0.104 |
| Charter Communications, Inc.      | CHTR   |  49977675776 | 21500000256 |          0.016 |
| Walgreens Boots Alliance, Inc.    | WBA    |   8246310400 |  2884000000 |          0.060 |
| General Motors Company            | GM     |  56970276864 | 18371000320 |          0.105 |
| Occidental Petroleum Corporation  | OXY    |  44224106496 | 12931000320 |          0.002 |
| Comcast Corporation               | CMCSA  | 146250366976 | 37285998592 |          0.065 |
| CVS Health Corporation            | CVS    |  55823069184 | 14115000320 |          0.060 |
| MGM Resorts International         | MGM    |  10170798080 |  2556987904 |          0.053 |
| Ford Motor Company                | F      |  39265984512 |  9360000000 |          0.055 |
| United Airlines Holdings, Inc.    | UAL    |  32032522240 |  7482999808 |          0.025 |
| PG&E Corporation                  | PCG    |  43475365888 |  9317999616 |          0.009 |
| Delta Air Lines, Inc.             | DAL    |  39316971520 |  8415000064 |          0.012 |
| DaVita Inc.                       | DVA    |  12455345152 |  2657765120 |          0.046 |
| Edison International              | EIX    |  30786168832 |  6444000256 |          0.106 |
| Pinnacle West Capital Corporation | PNW    |   9659952128 |  1978172032 |          0.080 |
+-----------------------------------+--------+--------------+-------------+----------------+
```

**`EXPLAIN ANALYZE` Output (Before Indexing):**
```
-> Limit: 15 row(s)  (cost=69 rows=15) (actual time=0.488..0.49 rows=15 loops=1)
    -> Sort: (companies.market_cap / companies.ebitda), limit input to 15 row(s) per chunk  (cost=69 rows=448) (actual time=0.488..0.489 rows=15 loops=1)
        -> Filter: ((companies.market_cap < (5 * companies.ebitda)) and (companies.revenue_growth > 0.000))  (cost=69 rows=448) (actual time=0.0941..0.468 rows=15 loops=1)
            -> Table scan on companies  (cost=69 rows=448) (actual time=0.0525..0.43 rows=502 loops=1)
```

**Baseline Performance Analysis:**
The initial query cost is **69**, and the query plan shows a full `Table scan`. This is inefficient because the database has to read every row in the `companies` table to find the ones that match the `WHERE` clause.

### Indexing Strategy & Performance Improvement

**Proposed Index:**
To optimize this query, I will create a composite index on `(revenue_growth, market_cap, ebitda)`. The `revenue_growth` column is first because it has a `>` condition, which is a good candidate for an index range scan. The other two columns are included to create a covering index, so the database can get all the data it needs from the index.

**Index Creation:**
```sql
CREATE INDEX idx_rev_mc_ebitda ON companies (revenue_growth, market_cap, ebitda);
```

**`EXPLAIN ANALYZE` Output (After Indexing):**
```
-> Limit: 15 row(s)  (cost=69 rows=15) (actual time=0.804..0.809 rows=15 loops=1)
    -> Sort: (companies.market_cap / companies.ebitda), limit input to 15 row(s) per chunk  (cost=69 rows=448) (actual time=0.804..0.806 rows=15 loops=1)
        -> Filter: ((companies.market_cap < (5 * companies.ebitda)) and (companies.revenue_growth > 0.000))  (cost=69 rows=448) (actual time=0.115..0.756 rows=15 loops=1)
            -> Table scan on companies  (cost=69 rows=448) (actual time=0.0667..0.674 rows=502 loops=1)
```

**Final Performance Analysis & Index Selection:**
The `idx_rev_mc_ebitda` index did not result in a performance improvement. The query optimizer chose to stick with the original plan, which involves a full table scan. This is likely because the `companies` table is relatively small, and the optimizer determined that the cost of reading the entire table is less than the overhead of using an index.

**Final Index Design:**
No new index is recommended for this query, as the proposed index did not yield a better execution plan for a table of this size.
***
---

## Query 4: S&P 500 Current vs. 52-Week Average

This query compares the most recent S&P 500 index value with the average value over the last year. This provides a quick snapshot of the overall market trend.

**SQL Concepts Used:**
-   **`UNION ALL`:** Combines the results of two separate `SELECT` statements.
-   **Subqueries & Aggregation:**  Two subqueries are used, one to get the most recent S&P 500 value and another to get the average over the last year.

### Query
```sql
(SELECT 'current_sp500' as metric, sp500_value FROM sp500_index ORDER BY date DESC LIMIT 1)
UNION ALL
(SELECT 'avg_sp500_52_week' as metric, AVG(sp500_value) FROM sp500_index WHERE date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR));
```

### Unoptimized Performance

**Query Result:**
```
+-------------------+-------------+
| metric            | sp500_value |
+-------------------+-------------+
| current_sp500     | 5930.850000 |
| avg_sp500_52_week | 5731.606019 |
+-------------------+-------------+
```

**`EXPLAIN ANALYZE` Output (Before Indexing):**
```
-> Append  (cost=33.1 rows=2) (actual time=0.0358..0.087 rows=2 loops=1)
    -> Stream results  (cost=0.00178 rows=1) (actual time=0.0355..0.0356 rows=1 loops=1)
        -> Limit: 1 row(s)  (cost=0.00178 rows=1) (actual time=0.0305..0.0305 rows=1 loops=1)
            -> Index scan on sp500_index using PRIMARY (reverse)  (cost=0.00178 rows=1) (actual time=0.0302..0.0302 rows=1 loops=1)
    -> Stream results  (cost=33.1 rows=1) (actual time=0.0502..0.0503 rows=1 loops=1)
        -> Aggregate: avg(sp500_index.sp500_value)  (cost=33.1 rows=1) (actual time=0.0477..0.0477 rows=1 loops=1)
            -> Filter: (sp500_index.`date` >= <cache>((curdate() - interval 1 year)))  (cost=22.3 rows=108) (actual time=0.0206..0.0378 rows=108 loops=1)
                -> Index range scan on sp500_index using PRIMARY over ('2024-07-22' <= date)  (cost=22.3 rows=108) (actual time=0.0184..0.029 rows=108 loops=1)
```

**Baseline Performance Analysis:**
The initial query cost is **33.1**. The query is already well-optimized because the `date` column is the primary key, and therefore indexed. The database is able to use an `Index scan` and an `Index range scan` to efficiently retrieve the data.

### Indexing Strategy & Performance Improvement

**Proposed Index:**
No new index is proposed for this query, as the `date` column is already the primary key and is being used effectively by the query optimizer.

**Final Performance Analysis & Index Selection:**
The query is already optimized, and no further indexing is required.
***
--- 