import pandas as pd

df = pd.read_excel('18-fiverr-dirty-sales-data-cleaning/fiverr_dirty_sales_data.xlsx')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Cleaning Customer_Name column
df['Customer_Name'] = (df['Customer_Name']
    .str.strip()
    .str.title()
    .str.replace(r'\s{2,}', ' ', regex=True)
    .replace('Unknown', pd.NA)
)

# Cleaning Contact_Email column
df['Contact_Email'] = (df['Contact_Email']
    .str.strip()
    .str.lower()
    .str.replace({
            r'\.{2,}': '.',
            'gmial': 'gmail',
            'gmailcom': 'gmail.com'
        }, regex=True)
    .replace('no_email@null', pd.NA)
)

# Cleaning Product_Category column
df['Product_Category'] = (df['Product_Category']
    .str.strip()
    .str.title()
    .replace(
        {
            'Home And Kitchen': 'Home & Kitchen',
            'Electrnics': 'Electronics',
            'Sports & Outdoors': 'Sports'
        }
    )
)

# Cleaning Item_Description column
df['Item_Description'] = df['Item_Description'].str.strip().replace('Coffee maker', 'Coffee Maker')

# Cleaning Unit_Price column
df['Unit_Price'] = (df['Unit_Price']
    .astype(str)
    .str.strip()
    .str.replace(
        {
            'USD ': '',
            '$': ''
        }
    )
    .str.strip()
)

df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').abs()
Q1 = df['Unit_Price'].quantile(0.25)
Q3 = df['Unit_Price'].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR

df['Unit_Price'] = df['Unit_Price'].clip(upper=upper_bound)

# Cleaning Quantity column
df['Quantity'] = df['Quantity'].astype(str).str.strip().replace({'one': '1', '-2': '2'}).astype('Int64')

print(df['Quantity'].value_counts())


# Cleaning Country column
df['Country'] = df['Country'].str.strip().str.lower()
country_mapping = {
    'canada': 'Canada',
    'germany': 'Germany',
    'ca': 'Canada',
    'united states of america': 'United States',
    'usa': 'United States',
    'u.s.a.': 'United States',
    'united states': 'United States',
    'us': 'United States',
    'united kingdom': 'United Kingdom',
    'uk': 'United Kingdom',
    'u.k.': 'United Kingdom',
    'de': 'Germany'
}
df['Country'] = df['Country'].map(country_mapping)

# Cleaning Order_Status
df['Order_Status'] = df['Order_Status'].str.strip().str.lower()

status_mapping = {
    'completed': 'Completed',
    'pending': 'Pending',
    'refunded': 'Refunded',
    'succeeded': 'Succeeded',
    'processing': 'Processing',
    'cancelled': 'Cancelled',
    'canceled': 'Cancelled'
}

df['Order_Status'] = df['Order_Status'].map(status_mapping)

# Finalizing

# Exporting
# df.to_excel('18-fiverr-dirty-sales-data-cleaning/fiverr_dirty_sales_data_cleaned.xlsx', index=False)