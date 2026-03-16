### Part 2: Understand What Each Library Does

Before writing code, it helps to know why each library is there:

| Library | What it does in this project |
|---|---|
| `boto3` | AWS SDK for Python — lets you talk to S3, read files, list buckets |
| `pandas` | Data manipulation — cleaning nulls, merging tables, transforming columns |
| `snowflake-connector-python` | Connects Python to your Snowflake warehouse to upload data |
| `python-dotenv` | Reads your `.env` file so credentials never get hardcoded in your script |

---

### Part 3: Understand the Raw Data Before Cleaning

Open the CSVs locally and look at them first. Here is what each file contains and what problems you'll encounter:

**`olist_orders_dataset.csv`** — one row per order
```
order_id | customer_id | order_status | order_purchase_timestamp | order_approved_at |
order_delivered_carrier_date | order_delivered_customer_date | order_estimated_delivery_date
```
Problems you'll fix: date columns stored as plain text strings, some orders never delivered (status = cancelled/unavailable), missing delivery dates.

**`olist_order_items_dataset.csv`** — one row per item within an order (an order can have multiple items)
```
order_id | order_item_id | product_id | seller_id | shipping_limit_date | price | freight_value
```
Problems you'll fix: occasional nulls in price, need to link to product categories.

**`olist_products_dataset.csv`** — one row per product
```
product_id | product_category_name | product_name_length | product_description_length | ...
```
Problems you'll fix: missing category names.

**`olist_order_payments_dataset.csv`** — one row per payment (an order can have split payments)
```
order_id | payment_sequential | payment_type | payment_installments | payment_value