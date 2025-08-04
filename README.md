# S&P 500 Data Loader

This project loads S&P 500 data from CSV files into a MySQL database.

## Project Structure

- `data/`: Contains the source CSV files (`sp500_companies.csv`, `sp500_index.csv`, `sp500_stocks.csv`).
- `schema.sql`: The SQL script to create the database schema.
- `load_data.py`: The Python script to load the data from the CSV files into the database.
- `requirements.txt`: The Python dependencies for this project.

## Setup Instructions

1.  **Create a `.env` file** in the root of the project with your MySQL database credentials:

    ```
    DB_USER=your_username
    DB_PASS=your_password
    ```

2.  **Create the database** in MySQL:

    ```sql
    CREATE DATABASE track1_stage3;
    ```

3.  **Create the database tables** by running the `schema.sql` script:

    ```bash
    mysql -u your_username -p track1_stage3 < schema.sql
    ```

4.  **Install the Python dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the data loading script**:

    ```bash
    python load_data.py
    ``` 