# pipeline.py — run this once from your terminal

import boto3
import pandas as pd
import io
import os
from dotenv import load_dotenv
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

# ── Helper ───────────────────────────────────────────────────
def read_s3_csv(filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='eu-central-1'
    )
    obj = s3.get_object(Bucket=os.getenv('AWS_BUCKET'), Key=filename)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    print(f"  Loaded '{filename}': {df.shape[0]} rows")
    return df

# ── Load from S3 ─────────────────────────────────────────────
print("\nLoading raw data from S3...")
orders   = read_s3_csv('olist_orders_dataset.csv')
items    = read_s3_csv('olist_order_items_dataset.csv')
products = read_s3_csv('olist_products_dataset.csv')
payments = read_s3_csv('olist_order_payments_dataset.csv')

# ── Clean orders ─────────────────────────────────────────────
print("\nCleaning orders...")
date_cols = [
    'order_purchase_timestamp', 'order_approved_at',
    'order_delivered_carrier_date', 'order_delivered_customer_date',
    'order_estimated_delivery_date'
]
for col in date_cols:
    orders[col] = pd.to_datetime(orders[col], errors='coerce')

orders.dropna(subset=['order_purchase_timestamp'], inplace=True)
orders['order_year']       = orders['order_purchase_timestamp'].dt.year
orders['order_month']      = orders['order_purchase_timestamp'].dt.month
orders['order_month_name'] = orders['order_purchase_timestamp'].dt.strftime('%b')

orders['delivered_on_time'] = (
    orders['order_delivered_customer_date'] <= orders['order_estimated_delivery_date']
).map({True: 'On Time', False: 'Late'})
orders.loc[
    orders['order_delivered_customer_date'].isna() |
    orders['order_estimated_delivery_date'].isna(),
    'delivered_on_time'
] = 'Unknown'

orders_delivered = orders[orders['order_status'] == 'delivered'].copy()

# ── Clean items ──────────────────────────────────────────────
print("Cleaning items...")
items.dropna(subset=['order_id', 'price'], inplace=True)
items['price']         = pd.to_numeric(items['price'], errors='coerce')
items['freight_value'] = pd.to_numeric(items['freight_value'], errors='coerce').fillna(0)

# ── Clean products ───────────────────────────────────────────
print("Cleaning products...")
products['product_category_name'] = products['product_category_name'].fillna('unknown')
products = products[['product_id', 'product_category_name']]

# ── Clean payments ───────────────────────────────────────────
print("Cleaning payments...")
payments.dropna(subset=['order_id', 'payment_value'], inplace=True)
payments['payment_value'] = pd.to_numeric(payments['payment_value'], errors='coerce')
order_payments = (
    payments.groupby('order_id')['payment_value']
    .sum()
    .reset_index()
    .rename(columns={'payment_value': 'total_payment'})
)

# ── Join into fact table ─────────────────────────────────────
print("Joining tables...")
fact = orders_delivered.merge(items, on='order_id', how='inner')
fact = fact.merge(products[['product_id', 'product_category_name']], on='product_id', how='left')
fact = fact.merge(order_payments, on='order_id', how='left')
fact['product_category_name'] = fact['product_category_name'].fillna('unknown')
fact['total_payment']         = fact['total_payment'].fillna(0)

# ── Final cleanup ────────────────────────────────────────────
print("Finalising...")
fact.columns = [c.lower().replace(' ', '_') for c in fact.columns]

columns_to_keep = [
    'order_id', 'customer_id', 'order_status',
    'order_purchase_timestamp', 'order_delivered_customer_date',
    'order_estimated_delivery_date', 'delivered_on_time',
    'order_year', 'order_month', 'order_month_name',
    'product_id', 'product_category_name',
    'price', 'freight_value', 'total_payment'
]
fact = fact[columns_to_keep]

print(f"\nDone. Fact table: {len(fact):,} rows, {len(fact.columns)} columns")
fact.to_csv('ecommerce_fact_cleaned.csv', index=False)
print("Saved to ecommerce_fact_cleaned.csv")

# ── Upload to Snowflake ──────────────────────────────────────
print("\nConnecting to Snowflake...")
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse='ECOM_WH',
    database='ECOMMERCE_DB',
    schema='SALES'
)

print("Connected! Uploading data...")

fact.columns = [c.upper() for c in fact.columns]
success, nchunks, nrows, _ = write_pandas(
    conn,
    fact,
    'ECOM_FACT',
    auto_create_table=False
)

print(f"Upload complete! {nrows:,} rows loaded in {nchunks} chunks. Success: {success}")
conn.close()
print("Snowflake connection closed.")