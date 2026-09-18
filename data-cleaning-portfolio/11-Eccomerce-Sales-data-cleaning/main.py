import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('11-Eccomerce-Sales-data-cleaning/dirty_ecommerce_sales.csv', engine='python')


# Cleaning Customer_ID column
df['Customer_ID'] = (df['Customer_ID']
    .str.strip()
    .str.upper()
    .str.replace('_', '-')
)

# Cleaning Date column
df['Date'] = pd.to_datetime(df['Date'],
    format='mixed',
    errors='coerce'
).dt.strftime('%Y-%m-%d')

# Cleaning Customer_Age column
df['Customer_Age'] = df['Customer_Age'].str.replace(r'[^0-9]', '', regex=True)
df['Customer_Age'] = pd.to_numeric(df['Customer_Age'], errors='coerce')
df['Customer_Age'] = df['Customer_Age'].round().astype('Int64')

age_median = df['Customer_Age'].median()

df['Customer_Age'] = df['Customer_Age'].where(df['Customer_Age'].between(18, 100), age_median)

# Cleaning Gender column
df['Gender'] = (df['Gender']
    .str.strip()
    .replace(
    {
        'Female': 'Female',
        'Femal': 'Female',
        'female': 'Female',
        'F': 'Female',
        'M': 'Male',
        'male': 'Male',
        'Male': 'Male',
        'MALE': 'Male',
        'Other': 'Other'
    })
)

# Cleaning Country column
mapping_country = {
    'Uk': 'United Kingdom',
    'United Kingdom': 'United Kingdom',
    'Great Britain': 'United Kingdom',
    'France': 'France',
    'Fr': 'France',
    'Canada': 'Canada',
    'Ca': 'Canada',
    'Usa': 'United States',
    'Us': 'United States',
    'United States': 'United States',
    'U.S.A.': 'United States',
    'Germany': 'Germany',
    'Deutschland': 'Germany',
    'De': 'Germany'
}
df['Country'] = (df['Country']
    .str.strip()
    .str.title()
    .replace(mapping_country)
)

# Cleaning Product_Category column
df['Product_Category'] = (df['Product_Category']
    .str.strip()
    .str.title()
    .replace({
        'Electronics': 'Electronics',
        'Home & Kitchen': 'Home & Kitchen',
        'Beauty': 'Beauty',
        'Clothing': 'Clothing',
        'Books': 'Books',
        'electronics': 'Electronics',
        'home': 'Home',
        'Apparel': 'Apparel',
        'Beauty & Health': 'Beauty & Health',
        'books': 'Books',
        'Beauty & Health': 'Beauty',
        'Apparel': 'Clothing',
        'Home & Kitchen': 'Home'
    })
)

# Cleaning Purchase_Amount column
df['Purchase_Amount'] = (df['Purchase_Amount']
    .str.strip()
    .str.replace(r'[^0-9\.]', '', regex=True)
)
df['Purchase_Amount'] = pd.to_numeric(df['Purchase_Amount'], errors='coerce')
df = df[(df['Purchase_Amount'] > 0) | df['Purchase_Amount'].isna()]

# Cleaning Quantity column
df['Quantity'] = df['Quantity'].str.strip().replace(
    {
        'one': '1',
        'two': '2',
        'three': '3'
    }
)

df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
df['Quantity'] = df['Quantity'].abs().astype('Int64')

# Cleaning Rating column
df['Rating'] = df['Rating'].where(df['Rating'].between(1.0, 5.0), pd.NA)

# Cleaning Payment_Method column
mapping_payment = {
    'CC': 'Credit Card',
    'credit_card': 'Credit Card',
    'paypal': 'PayPal',
    'bank_transfer': 'Bank Transfer',
    'Wire Transfer': 'Bank Transfer'
}

df['Payment_Method'] = df['Payment_Method'].replace(mapping_payment)

# Cleaning Order_Status
mapping_status = {
    'canceled': 'Cancelled',
    'COMPLETE': 'Completed',
    'pending': 'Pending',
    'completed': 'Completed'
}

df['Order_Status'] = df['Order_Status'].replace(mapping_status)

# ...
total_missing = df['Transaction_ID'].isna().sum()

placeholders = [f'UNKNOWN_TXN_{i}' for i in range(total_missing)]

df.loc[df['Transaction_ID'].isna(), 'Transaction_ID'] = placeholders

df = df.drop_duplicates(subset=['Transaction_ID'], keep='first')

# Exporting
df.to_csv('11-Eccomerce-Sales-data-cleaning/ecommerce_sales_cleaned.csv', index=False)
