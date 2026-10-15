import pandas as pd
import re
import ftfy

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

df = pd.read_csv('17-Eccomerce-Orders-data-cleaning/ecommerce_orders_raw.csv',
    engine='python',
    on_bad_lines='skip')

# Cleaning Order ID column
df['Order ID'] = (df['Order ID']
    .str.strip()
    .str.upper())

def normalizing_ids(cell):
    if pd.isna(cell):
        return pd.NA
    check = bool(re.search(r'\w{3}\-\d{6}', cell))
    if check:
        return cell

    if bool(re.search(r'^\d{6}', cell)):
        cell = 'ORD-' + cell
        return cell
    if bool(re.search(r'ORD\d{6}', cell)):
        cell = re.sub(r'ORD', r'ORD-', cell)
        return cell

df['Order ID'] = df['Order ID'].apply(normalizing_ids)

# ...

# ...

# Cleaning Customer ID column
df['Customer ID'] = (df['Customer ID']
    .str.strip()
    .str.upper() 
    .str.replace(
    'CUST','C'))

def normalizing_customers(cell):
    if pd.isna(cell):
        return pd.NA
    if bool(re.search(r'C\-\d{5}', cell)):
        return cell
    if bool(re.search(r'^\d{4}', cell)):
        cell = re.sub(r'(\d{4})', r'C-0\1', cell)
        return cell
    if bool(re.search(r'C\d{4,5}', cell)):
        cell = re.sub(r'C(\d{4,5})', r'C-\1', cell)
        return cell
    if bool(re.search(r'\d{4}', cell)):
        cell = re.sub(r'(\d{4})', r'0\1', cell) # ...
        return cell
    return cell

df['Customer ID'] = df['Customer ID'].apply(normalizing_customers)

# Cleaning Customer Name column
def safe_fix(x):
    if isinstance(x, str):
        return ftfy.fix_text(x)
    return x
df['Customer Name'] = df['Customer Name'].apply(safe_fix)
df['Customer Name'] = (df['Customer Name']
    .str.strip()
    .str.title()
    .str.replace(r'\s{2,}', ' ', regex=True))

def reorder_name(name):
    if pd.isna(name):
        return pd.NA
    if ',' in name:
        last_name, first_name = name.split(',')
        return f'{first_name.strip()} {last_name.strip()}'
    return name

df['Customer Name'] = df['Customer Name'].apply(reorder_name)

# ...

# Cleaning Country column
df['Country'] = df['Country'].str.lower().str.strip()
country_mapping = {
    # United States
    'united states': 'United States',
    'u.s.a.': 'United States',
    'u.s.': 'United States',
    'us': 'United States',
    'united states of america': 'United States',
    'untied states': 'United States',
    'usa': 'United States',

    # United Kingdom
    'united kingdom': 'United Kingdom',
    'uk': 'United Kingdom',
    'u.k.': 'United Kingdom',
    'great britain': 'United Kingdom',
    'england': 'United Kingdom',
    'gb': 'United Kingdom',

    # Germany
    'germany': 'Germany',
    'germny': 'Germany',
    'de': 'Germany',
    'deutschland': 'Germany',

    # Canada
    'canada': 'Canada',
    'canda': 'Canada',
    'can': 'Canada',
    'ca': 'Canada',

    # Australia
    'australia': 'Australia',
    'au': 'Australia',
    'aus': 'Australia',
}

df['Country'] = df['Country'].map(country_mapping)

# Cleaning State/Prov column
df['State/Prov'] = df['State/Prov'].str.lower().str.strip()
region_mapping = {
    # US states
    'co': 'Colorado', 'colorado': 'Colorado',
    'wa': 'Washington', 'washington': 'Washington',
    'az': 'Arizona', 'arizona': 'Arizona',
    'il': 'Illinois', 'illinois': 'Illinois',
    'ma': 'Massachusetts', 'massachusetts': 'Massachusetts',
    'ct': 'Connecticut', 'connecticut': 'Connecticut',
    'pa': 'Pennsylvania', 'pennsylvania': 'Pennsylvania',
    'oh': 'Ohio', 'ohio': 'Ohio',
    'nc': 'North Carolina', 'north carolina': 'North Carolina',
    'ga': 'Georgia', 'georgia': 'Georgia',
    'ny': 'New York', 'new york': 'New York',
    'fl': 'Florida', 'florida': 'Florida',
    'ca': 'California', 'california': 'California',
    'tx': 'Texas', 'texas': 'Texas',
    'nj': 'New Jersey', 'new jersey': 'New Jersey',

    # Canadian provinces
    'on': 'Ontario', 'ontario': 'Ontario',
    'ab': 'Alberta', 'alberta': 'Alberta',
    'bc': 'British Columbia', 'british columbia': 'British Columbia',
    'qc': 'Quebec', 'quebec': 'Quebec',
    'nsw': 'New South Wales',
    'qld': 'Queensland',
    'vic': 'Victoria',

    # UK constituent countries
    'england': 'England',
    'wales': 'Wales',
    'scotland': 'Scotland',

    # German federal states
    'hesse': 'Hesse',
    'saxony': 'Saxony',
    'bavaria': 'Bavaria',
    'hamburg': 'Hamburg',
    'berlin': 'Berlin',
}

df['State/Prov'] = df['State/Prov'].map(region_mapping)

# Cleaning Zip/Postal
df['Zip/Postal'] = (df['Zip/Postal']
    .str.upper()
    .str.strip()
    .str.replace(r'\s{1,}', '', regex=True)
    .str.replace('.0', '')
)

def fix_us_codes(row):
    zip_code = str(row['Zip/Postal']).strip()
    country = row['Country']

    if country == 'United States' and zip_code.isdigit() and len(zip_code) < 5:
        return zip_code.zfill(5)
    return zip_code

df['Zip/Postal'] = df.apply(fix_us_codes, axis=1)

# Cleaning SKU column
df['SKU'] = df['SKU'].str.strip().str.upper()

def splitting_sku(cell):
    if pd.isna(cell):
        return cell
    if bool(re.match(r'\w\w\d{4}', cell)):
        cell = re.sub(r'(\w\w)(\d{4})', r'\1-\2', cell)
        return cell
    if not bool(re.match(r'\w\w\-\d{4}', cell)):
        cell = pd.NA
    return cell

df['SKU'] = df['SKU'].apply(splitting_sku)

# Cleaning Product Name column
df['Product Name'] = (df['Product Name'].str.strip().str.replace(
    {
        r'\s{2,}': ' ',
        r'^[?!-]': '',
    }, regex=True)
    .replace('', pd.NA))

# Cleaning Category column
df['Category'] = df['Category'].str.strip()
category_map = {
    'Toys & Games': 'Toys & Games',
    'Toys and Games': 'Toys & Games',
    'Toys & games': 'Toys & Games',
    'toys & games': 'Toys & Games',
    'Toys': 'Toys & Games',

    'Sports & Outdoors': 'Sports & Outdoors',
    'sports & outdoors': 'Sports & Outdoors',
    'Sports & Outdoor': 'Sports & Outdoors',
    'Sports and Outdoors': 'Sports & Outdoors',
    'Sports': 'Sports & Outdoors',

    'Electronics': 'Electronics',
    'electronics': 'Electronics',
    'ELECTRONICS': 'Electronics',
    'Electronic': 'Electronics',

    'Office Supplies': 'Office Supplies',
    'Office supplies': 'Office Supplies',
    'office supplies': 'Office Supplies',
    'OFFICE SUPPLIES': 'Office Supplies',
    'Office Supply': 'Office Supplies',

    'Beauty': 'Beauty',
    'BEAUTY': 'Beauty',
    'beauty': 'Beauty',
    'Beauty & Personal Care': 'Beauty',

    'Home & Kitchen': 'Home & Kitchen',
    'home & kitchen': 'Home & Kitchen',
    'Home&Kitchen': 'Home & Kitchen',
    'Home and Kitchen': 'Home & Kitchen',
}

df['Category'] = df['Category'].map(category_map)

# Cleaning Qty column
df['Qty'] = df['Qty'].str.replace({r'[^\d]': '', '.0': ''}, regex=True).replace(
{'': pd.NA,
 '999': pd.NA,
 '0': pd.NA})

# Cleaning Unit Price column (...)
df['Unit Price'] = (df['Unit Price']
.str.strip()
.str.replace(r'[^\d\.]', '', regex=True)
.replace('', '0.00')
.fillna('0.00'))


# Cleaning Discount column
df['Discount'] = (df['Discount']
    .str.strip()
    .str.replace(
        {
            '%': '',
            r'\s{1,}': '',
            r'\.\d{1,}': '',
            r'[^\d\.]': ''
        },
        regex=True)
        .replace({r'\s{1,}': '0', '': '0'}, regex=True)
        .fillna('0')
        .str.strip())

# Cleaning Total column
df['Total'] = (df['Total']
.str.strip()
.str.replace(r'[^\d\.]', '', regex=True)
.replace('', '0.00')
.fillna('0.00'))

# Cleaning Currency column
df['Currency'] = df['Currency'].str.strip()
currency_mapping = {
    "USD": "USD",
    "US$": "USD",
    "usd": "USD",
    "$": "USD",
    "CAD": "CAD",
    "cad": "CAD",
    "C$": "CAD",
    "CA$": "CAD",
    "GBP": "GBP",
    "£": "GBP",
    "gbp": "GBP",
    "EUR": "EUR",
    "€": "EUR",
    "eur": "EUR",
    "AUD": "AUD",
    "A$": "AUD",
    "AU$": "AUD",
    "aud": "AUD"
}

df['Currency'] = df['Currency'].map(currency_mapping)

# Cleaning Payment Method
df['Payment Method'] = df['Payment Method'].str.strip().str.lower()

payment_mapping = {
    "credit card": "Credit Card",
    "credit-card": "Credit Card",
    "credit_card": "Credit Card",
    "cc": "Credit Card",
    "mastercard": "Credit Card",
    "visa": "Credit Card",

    "paypal": "PayPal",
    "pay pal": "PayPal",

    "debit card": "Debit Card",
    "debit": "Debit Card",

    "apple pay": "Apple Pay",
    "applepay": "Apple Pay",

    "bank transfer": "Bank Transfer",
    "wire transfer": "Bank Transfer",
    "wire": "Bank Transfer",
    "ach": "Bank Transfer",

    "gift card": "Gift Card",
    "giftcard": "Gift Card",
}

df['Payment Method'] = df['Payment Method'].map(payment_mapping)

# Cleaning Status column
df['Status'] = df['Status'].str.strip().str.lower()

status_mapping = {
    "shipped": "Shipped",
    "refunded": "Refunded",
    "deliverd": "Delivered",
    "processing": "Processing",
    "return": "Returned",
    "canceled": "Canceled",
    "in transit": "In Transit",
    "refund issued": "Refunded",
    "pending": "Pending",
    "in progress": "Processing",
}

df['Status'] = df['Status'].map(status_mapping)

# Cleaning Gift coolumn
gift_mapping = {
    "N": "No",
    "No": "No",
    "no": "No",
    "FALSE": "No",
    "0": "No",
    "false": "No",
    "Yes": "Yes",
    "Y": "Yes",
    "yes": "Yes",
    "TRUE": "Yes",
    "1": "Yes",
    "true": "Yes",
}

df['Gift'] = df['Gift'].map(gift_mapping)

# Cleaning Sales Rep

print(df['Sales Rep'].value_counts())