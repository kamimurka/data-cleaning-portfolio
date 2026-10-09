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
df['Country'] = df['Country'].str.lower()
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

    # pd.NA

}

df['Country'] = df['Country'].map(country_mapping)


print(df['Country'].value_counts())

print(df['Country'].isna().sum())
unmapped = df[df['Country'].isna()]['Country'].unique()
print(unmapped)