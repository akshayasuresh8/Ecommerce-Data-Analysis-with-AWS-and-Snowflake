# E-commerce Sales Analysis Pipeline

An end-to-end data pipeline built to demonstrate cloud storage, data warehousing,
and business intelligence skills using real-world e-commerce data.

## Tech Stack

| Layer | Tool |
|---|---|
| Cloud Storage | AWS S3 |
| Data Cleaning | Python (pandas, boto3) |
| Data Warehouse | Snowflake |
| Dashboard | Power BI |

## Architecture
```
Raw CSV Files → AWS S3 → Python (Clean & Transform) → Snowflake → Power BI Dashboard
```

## Dataset

[Brazilian E-Commerce (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
— 100,000+ real orders across 4 tables: orders, items, products, and payments.

## Project Structure
```
ecommerce-pipeline/
│
├── Pipeline.py          # Main pipeline — S3 ingestion, cleaning, Snowflake upload
├── requirements.txt     # Python dependencies
├── .gitignore           # Excludes credentials and data files
└── README.md            # Project documentation
```

## Pipeline Steps

### Step 1 — Cloud Storage (AWS S3)
- Created an S3 bucket in eu-central-1 (Frankfurt)
- Uploaded 4 raw CSV files from the Olist dataset
- Configured IAM access keys for secure programmatic access

### Step 2 — Data Cleaning (Python)
- Connected to S3 using `boto3` — no local file storage needed
- Loaded all 4 tables directly into pandas DataFrames
- Cleaning operations performed:
  - Parsed 5 date columns from strings to datetime
  - Filtered to delivered orders only (removed cancelled/unavailable)
  - Engineered `delivered_on_time` flag by comparing actual vs estimated delivery
  - Extracted `order_year`, `order_month`, `order_month_name` for time-series analysis
  - Aggregated split payments into single `total_payment` per order
  - Filled missing product categories and freight values
  - Joined all 4 tables into one flat fact table
- Output: 110,197 rows × 15 columns

### Step 3 — Data Warehouse (Snowflake)
- Created `ECOMMERCE_DB` database and `SALES` schema
- Provisioned `ECOM_WH` X-Small warehouse with auto-suspend (60s)
- Uploaded fact table using `snowflake-connector-python` write_pandas
- Wrote 5 SQL analysis queries:
  - Monthly revenue trend
  - Top 10 product categories by revenue
  - Delivery performance breakdown
  - Average order value by year
  - Total orders and revenue by year

### Step 4 — Dashboard (Power BI)
Connected Power BI to Snowflake via ODBC and built an interactive dashboard with:
- Monthly revenue trend (line chart)
- Top 10 categories by revenue (bar chart)
- Delivery performance — on time vs late (donut chart)
- Total orders by year (column chart)
- KPI cards — Total Revenue, Total Orders, Avg Order Value
- Interactive slicers for year and product category

## Key Findings

- Peak revenue months: **November and December** (holiday season effect)
- Top category by revenue: **bed_bath_table** followed by **health_beauty**
- Delivery performance: ~93% of orders delivered on time
- Average order value: ~R$154 across all years
- Order volume grew significantly from 2017 to 2018

## Setup Instructions

### Prerequisites
- Python 3.8+
- AWS account (Free Tier)
- Snowflake account (Free Trial)
- Power BI Desktop

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/ecommerce-pipeline.git
cd ecommerce-pipeline

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_BUCKET=your_s3_bucket_name

SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_ACCOUNT=your_snowflake_account_identifier
```

### Run the Pipeline
```bash
python Pipeline.py
```

This will:
1. Load all 4 CSVs from S3
2. Clean and join the data
3. Save a local backup CSV
4. Upload 110,197 rows to Snowflake

## SQL Analysis Queries
```sql
-- Monthly revenue trend
SELECT
    ORDER_YEAR, ORDER_MONTH, ORDER_MONTH_NAME,
    ROUND(SUM(PRICE), 2)         AS TOTAL_REVENUE,
    COUNT(DISTINCT ORDER_ID)     AS TOTAL_ORDERS,
    ROUND(AVG(TOTAL_PAYMENT), 2) AS AVG_ORDER_VALUE
FROM ECOM_FACT
GROUP BY ORDER_YEAR, ORDER_MONTH, ORDER_MONTH_NAME
ORDER BY ORDER_YEAR, ORDER_MONTH;

-- Top 10 categories by revenue
SELECT
    PRODUCT_CATEGORY_NAME,
    ROUND(SUM(PRICE), 2)     AS CATEGORY_REVENUE,
    COUNT(DISTINCT ORDER_ID) AS NUM_ORDERS
FROM ECOM_FACT
GROUP BY PRODUCT_CATEGORY_NAME
ORDER BY CATEGORY_REVENUE DESC
LIMIT 10;

-- Delivery performance
SELECT
    DELIVERED_ON_TIME,
    COUNT(*) AS NUM_ORDERS,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS PERCENTAGE
FROM ECOM_FACT
GROUP BY DELIVERED_ON_TIME;
```
