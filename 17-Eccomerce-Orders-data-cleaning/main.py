import pandas as pd
import re
import ftfy
import phonenumbers

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

df = pd.read_csv('17-Eccomerce-Orders-data-cleaning/ecommerce_orders_raw.csv',
    engine='python',
    on_bad_lines='skip')

orig = df[["Order Date ", "ship_date"]].copy()


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

# Cleaning Order Date (& Ship Date) columns
x = df["Order Date "].astype(str).str.strip()
p = x[x.str.match(r"^\d{2}-\d{2}-\d{2}$")].str.split("-", expand=True).astype(int)

def prep(col):
    s = col.astype(str).str.strip()
    s = s.str.replace(r"\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?$", "", regex=True)
    return s.str.replace(r"^(\d{1,2})[.\-](\d{1,2})[.\-](\d{4})$", r"\1/\2/\3", regex=True)

def row_format(s):
    parts = s.str.extract(r"^(\d{1,2})/(\d{1,2})/\d{4}$").astype(float)
    fmt = pd.Series("", index=s.index)
    fmt[parts[0] > 12] = "dmy"
    fmt[parts[1] > 12] = "mdy"
    return fmt

def parse_dates(s, fmt):
    result = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    for f in ("%Y/%m/%d", "%b %d, %Y", "%d-%b-%y", "%d %b %Y", "%m-%d-%y"):
        result = result.fillna(pd.to_datetime(s, format=f, errors="coerce"))
    num = pd.to_numeric(s, errors="coerce")
    result = result.fillna(pd.to_datetime(num.where(num.between(40000, 50000)), unit="D", origin="1899-12-30"))
    dmy = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    mdy = pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
    result = result.fillna(dmy.where(fmt == "dmy", mdy)).fillna(mdy.where(fmt == "dmy", dmy))
    return result.where(result >= "2000-01-01")

a = prep(df["Order Date "])
b = prep(df["ship_date"])

fmt = pd.Series("", index=df.index)

df["Order Date "] = parse_dates(a, fmt)
df["ship_date"] = parse_dates(b, fmt)

both = df["Order Date "].notna() & df["ship_date"].notna()
bad = both & (df["ship_date"] < df["Order Date "])

df = df.rename(columns={"ship_date": "Ship Date", 'Order Date ': 'Order Date'})

######################

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

junk_names = [
    'test', 'testing', 'dummy', 'unknown', 'Test Test'
    'n/a', 'na', 'none', 'null', 'nil',
    'undefined', 'not available', 'not applicable',
    'no name', 'no customer', 'guest', 'anonymous',
    'asdf', 'qwerty', 'xxx', 'xxxx', '123', '12345',
    '-', '?', '.', 'sample', 'example', 'placeholder'
]

mask = (
    df['Customer Name']
    .astype('string')
    .str.strip()
    .str.lower()
    .isin(junk_names)
)

df.loc[mask, 'Customer Name'] = None

# Cleaning E-mail column
df['E-mail'] = df['E-mail'].str.strip().str.lower()
df['E-mail'] = df['E-mail'].str.replace(r'\sat\s', '@', regex=True)
df[["E-mail", "email_extra"]] = df["E-mail"].str.split(r"\s*[;,]\s*", n=1, expand=True)

parts = df["E-mail"].str.split("@", expand=True)
local, dom = parts[0], parts[1].str.split(".").str[0]

bad = (
    (local == dom)
    | (local.str.len() < 3)            
    | local.str.contains(r"no.?email|none|^no$|test|fake|dummy|asdf|null|n/?a$", regex=True)
    | dom.str.contains(r"^(none|test|fake|dummy|example|null)$", regex=True)
)

df.loc[bad, "E-mail"] = None

df.loc[~df["E-mail"].str.contains("@", na=False), "E-mail"] = None

short = df["E-mail"].dropna()

# Cleaning Phone Number column
phone_mapping = {'United States': 'US', 'United Kingdom': 'GB', 'Canada': 'CA', 'Germany': 'DE', 'Australia': 'AU'}

df['country_code'] = df['Country'].map(phone_mapping)

def clean_phones(row):
    if pd.isna(row['Phone Number']):
        return pd.NA

    number = str(row['Phone Number'])
    code = str(row['country_code'])

    try:
        if code == "nan":
            phone = phonenumbers.parse(number, code)
            if phonenumbers.is_possible_number(phone):
                return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        else:
            phone = phonenumbers.parse(number, code)
            if phonenumbers.is_possible_number(phone):
                return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        return pd.NA
    except phonenumbers.NumberParseException:
        return pd.NA

df['Phone Number'] = df.apply(clean_phones, axis=1)
df = df.drop(columns=['country_code'])

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
df['Zip/Postal'] = df['Zip/Postal'].replace(
    {
        '?': None,
        'nan': None,
        '-': None,
        '': None
    },
)

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
    "delivered": "Delivered",
    "deliverd": "Delivered",
    "returned": "Returned",
    "return": "Returned",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "shipped": "Shipped",
    "refunded": "Refunded",
    "refund issued": "Refunded",
    "processing": "Processing",
    "in progress": "Processing",
    "in transit": "In Transit",
    "pending": "Pending",
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
df['Sales Rep'] = df['Sales Rep'].str.strip().str.title().replace({'Sales Rep': pd.NA})

sales_rep_mapping = {
    "Web": "Web",
    "Web Store": "Web Store",
    "Online": "Online",
    "Website": "Website",
    "J. Smith": "John Smith",
    "S. Martin": "Sophie Martin",
    "M. Lopez": "Maria Lopez",
    "K. O'Neil": "Kyle O'Neil",
    "R. Mehta": "Raj Mehta",
    "E. Carter": "Emily Carter",
    "A. Hassan": "Ahmed Hassan",
    "O. Petrova": "Olga Petrova",
    "T. Becker": "Tom Becker",
    "Raj Mehta": "Raj Mehta",
    "Tom Becker": "Tom Becker",
    "Kyle O'Neil": "Kyle O'Neil",
    "Maria Lopez": "Maria Lopez",
    "John Smith": "John Smith",
    "Emily Carter": "Emily Carter",
    "Sophie Martin": "Sophie Martin",
    "Ahmed Hassan": "Ahmed Hassan",
    "Olga Petrova": "Olga Petrova",
    "Mehta, Raj": "Raj Mehta",
    "Becker, Tom": "Tom Becker",
    "Hassan, Ahmed": "Ahmed Hassan",
    "Petrova, Olga": "Olga Petrova",
    "O'Neil, Kyle": "Kyle O'Neil",
    "Rmehta": "Raj Mehta",
    "Lopez, Maria": "Maria Lopez",
    "Smith, John": "John Smith",
    "Martin, Sophie": "Sophie Martin",
    "Carter, Emily": "Emily Carter",
    "Ecarter": "Emily Carter",
    "Jsmith": "John Smith",
    "Mlopez": "Maria Lopez",
    "Tbecker": "Tom Becker",
    "Ko'Neil": "Kyle O'Neil",
    "Opetrova": "Olga Petrova",
    "Smartin": "Sophie Martin",
    "Ahassan": "Ahmed Hassan",
}

df['Sales Rep'] = df['Sales Rep'].map(sales_rep_mapping)

# Cleaning Notes column
df['Notes'] = df['Notes'].str.strip()

# Cleaning Last Updated column
mask = df['Last Updated'].str.match(r'\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}\s\w{2}')

parts = df.loc[mask, 'Last Updated'].str.split('/')

first = pd.to_numeric(parts.str[0], errors='coerce')
second = pd.to_numeric(parts.str[1], errors='coerce')

def parse_last_updated(col):
    s = col.astype(str).str.strip()
    iso_text = s.str.replace(r"(\d)T(\d)", r"\1 \2", regex=True).str.replace(r"Z$", "", regex=True)
    iso = pd.to_datetime(iso_text, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    us = pd.to_datetime(s, format="%m/%d/%Y %I:%M %p", errors="coerce")
    return iso.fillna(us)

df["Last Updated"] = parse_last_updated(df["Last Updated"])

# Finalizing
df = df.drop_duplicates()
df = df.sort_values('Last Updated', na_position='first')
df = df.drop_duplicates(subset=['Order ID', 'SKU'])

d = df[df["Order ID"].duplicated(keep=False)].sort_values("Order ID")

df = df.drop(0)
 
df = df[df['Product Name'] != 'Product Name']

has_twin = df['Order ID'].notna() & df['Order ID'].duplicated(keep=False)
df = df[~(has_twin & df["SKU"].isna())]

for col in ['Qty', 'Unit Price', 'Discount', 'Total']:
    df[col] = pd.to_numeric(
        df[col],
        errors='coerce'
    )

print(df.dtypes)

# Exporting
df.to_csv('17-Eccomerce-Orders-data-cleaning/eccomerce_orders_cleaned.csv', index=False)