import pandas as pd
import re
import numpy as np

pd.set_option('display.max_columns', None)

df_orders_dispatch = pd.read_excel('Logistics_Orders_Export_Q1_2024.xlsx', sheet_name='Orders_Dispatch')
df_carrier_directory = pd.read_excel('Logistics_Orders_Export_Q1_2024.xlsx', sheet_name='Carrier_Directory')

############################################################
# SHEET 1: Orders_Dispatch
############################################################

# Cleaning Order_ID column
df_orders_dispatch['Order_ID'] = df_orders_dispatch['Order_ID'].str.strip()
df_orders_dispatch['Order_ID'] = df_orders_dispatch['Order_ID'].str.upper()

df_orders_dispatch['Order_ID'] = df_orders_dispatch['Order_ID'].str.replace(r'ORD\-([^2024])',
                                                                            r'ORD-2024-\1',
                                                                            regex=True)
df_orders_dispatch['Order_ID'] = df_orders_dispatch['Order_ID'].fillna(value='UNKNOWN')
df_orders_dispatch = df_orders_dispatch.drop_duplicates(subset=['Order_ID'])

# Creating columns from Customer_Contact
s = df_orders_dispatch['Customer_Contact']

pattern = r'''
^(?:
    (?P<company1>.+?)\s+Attn:\s*(?P<name1>.+)
    |
    (?P<last>[^,]+),\s*(?P<first>[^|]+)\|\s*(?P<email1>\S+@\S+)
    |
    (?P<name2>[^-(]+)-\s*(?P<phone1>\+?[\d\-]+)\s*-\s*(?P<email2>\S+@\S+)
    |
    (?P<name3>[^(]+)\((?P<company2>[^)]+)\)\s*-\s*(?P<phone2>\+?[\d\-]+)
    |
    (?P<name4>[A-Za-z\s\-\']+)
)$
'''

ext = s.str.extract(pattern, flags=re.X)

full_name = ext['first'].str.strip() + ' ' + ext['last'].str.strip()
df_orders_dispatch['Customer_Name'] = ext['name1'].combine_first(full_name).combine_first(ext['name2']).combine_first(ext['name3']).combine_first(ext['name4'])
df_orders_dispatch['Customer_Name'] = df_orders_dispatch['Customer_Name'].str.strip()
df_orders_dispatch['Company_Name'] = ext['company1'].combine_first(ext['company2'])
df_orders_dispatch['Email'] = ext['email1'].combine_first(ext['email2'])
df_orders_dispatch['Phone'] = ext['phone1'].combine_first(ext['phone2'])

df_orders_dispatch['Customer_Name'] = df_orders_dispatch['Customer_Name'].str.strip()

# Cleaning Delivery_Address column
ZIP_RE = r'\(?(\d{5})\)?'
SUFFIX_RE = r'(?:Blvd|Pkwy|Ave|St|Ln|Rd|Broadway|Dr)'

def parse_address(s):
    zip_m = re.search(ZIP_RE, s)
    zip_code = zip_m.group(1) if zip_m else None
    s_nozip = re.sub(ZIP_RE, '', s).strip().strip(',').strip()

    if '(' in s:
        city, state, street = [p.strip() for p in s_nozip.split(',', 2)]
    else:
        state_m = re.search(r'\b([A-Z]{2})\b', s_nozip)
        state = state_m.group(1) if state_m else None
        rest = (s_nozip[:state_m.start()] + s_nozip[state_m.end():]).strip().strip(',').strip()

        if ',' in rest:
            street, city = [p.strip() for p in rest.split(',', 1)]
        else:
            sfx_m = re.search(r'^(.*?\b' + SUFFIX_RE + r'\b)\s+(.*)$', rest)
            street, city = (sfx_m.group(1), sfx_m.group(2)) if sfx_m else (rest, None)

    return pd.Series([street, city, state, zip_code])

df_orders_dispatch[['Street_Address', 'City', 'State', 'Zip_Code']] = (
    df_orders_dispatch['Delivery_Address'].str.strip().apply(parse_address)
)

# Cleaning Order_Date column
df_orders_dispatch['Order_Date'] = pd.to_datetime(df_orders_dispatch['Order_Date'],
                                                  format='mixed',
                                                  errors='coerce').dt.strftime('%Y-%m-%d')

# Cleaning Weight_kg
df_orders_dispatch['Weight_kg'] = pd.to_numeric(
    df_orders_dispatch['Weight_kg']
    .astype(str)
    .str.replace(' kg', ''),
    errors='coerce'
).fillna(0)

median = df_orders_dispatch['Weight_kg'].median()
Q1 = df_orders_dispatch['Weight_kg'].quantile(0.25)
Q3 = df_orders_dispatch['Weight_kg'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
lower = Q1 - 1.5 * IQR

df_orders_dispatch['Weight_kg'] = np.where(df_orders_dispatch['Weight_kg'].between(lower, upper),
                              df_orders_dispatch['Weight_kg'],
                              median)
df_orders_dispatch['Weight_kg'] = np.where(df_orders_dispatch['Weight_kg'] <= 0.0,
                              median,
                              df_orders_dispatch['Weight_kg'])

# Cleaning Shipping_Cost_USD colum
df_orders_dispatch['Shipping_Cost_USD'] = pd.to_numeric(df_orders_dispatch['Shipping_Cost_USD']
                                                        .astype(str)
                                                        .str.replace('$', '', regex=False),
                                                        errors='coerce').fillna(0).abs()

# Cleaning Status column
df_orders_dispatch['Status'] = df_orders_dispatch['Status'].str.strip()
df_orders_dispatch['Status'] = df_orders_dispatch['Status'].str.capitalize()
df_orders_dispatch['Status'] = df_orders_dispatch['Status'].replace({
    'RETURNED': 'Returned',
    'Returned to sender': 'Returned',
    'Return_Processed': 'Return',
    'In-transit': 'In Transit',
    'Return_processed': 'Returned',
    'Cancld': 'Canceled',
    'Shipment complete': 'Delivered',
    'En route': 'In Transit',
    'Dlvrd': 'Delivered',
    'Delivered!': 'Delivered',
    'In_transit': 'In Transit',
    'Cancelled': 'Canceled',
    'Canceled / refunded': 'Canceled',
    'Awaiting pickup': 'Pending',
    'In transit': 'In Transit'
}, regex=True)

# Cleaning Carrier_Code column
df_orders_dispatch['Carrier_Code'] = df_orders_dispatch['Carrier_Code'].str.strip().str.upper()
df_orders_dispatch['Carrier_Code'] = df_orders_dispatch['Carrier_Code'].replace({
    'UPS': 'UPS-GR',
    'UPS_GRND': 'UPS-GR',
    'USPS': 'UPS-GR',
    'DHL': 'DHL-EX',
    'UPS-GROUND': 'UPS-GR',
    'FEDEX': 'FX-EX',
    'FEDEX EX': 'FX-EX',
    'DHL EXPRESS': 'DHL-EX',
    'FEDEX EXPRESS': 'FX-EX',
    'USPS STANDARD': 'USPS-ST',
    'DHL_EXPRESS': 'DHL-EX',
    'USPS POSTAL': 'USPS-ST',
    'FDEX-EX': 'FX-EX',
    'UPS GROUND': 'UPS-GR',
    'USPS-GR': 'UPS-GR'
})

############################################################
# SHEET 2: Carrier_Directory
############################################################

# Creating new columns from Contact_Person
df_carrier_directory['Email'] = df_carrier_directory['Contact_Person'].str.extract(r'([\w.+-]+@[\w.-]+)')
df_carrier_directory['Phone'] = df_carrier_directory['Contact_Person'].str.extract(r'(\d-\d{3}-[A-Z\d]{3,}(?:-[A-Z\d]{3,})*)')
df_carrier_directory['Position'] = df_carrier_directory['Contact_Person'].str.extract(r'\(([^)]+)\)')

df_carrier_directory['Name'] = (df_carrier_directory['Contact_Person']
    .str.replace(r'\(.*?\)', '', regex=True)
    .str.replace(r'[\w.+-]+@[\w.-]+', '', regex=True)
    .str.replace(r'\d-\d{3}-[A-Z\d]{3,}(?:-[A-Z\d]{3,})*', '', regex=True)
    .str.replace(r'[-|]', ' ', regex=True)
    .str.replace(r'\s+', ' ', regex=True)
    .str.replace(' +', '', regex=False)
    .str.strip())
df_carrier_directory['Phone'] = df_carrier_directory['Phone'].str.replace('ASK-USPS', '275-8777')

# Cleaning Base_Rate_Per column
df_carrier_directory['Base_Rate_Per_Kg']= df_carrier_directory['Base_Rate_Per_Kg'].astype(str).str.replace(' USD', '').astype(float)

# Exporting
with pd.ExcelWriter('Logistics_Orders_Export_Q1_2024_cleaned.xlsx', engine='openpyxl') as writer:
    df_orders_dispatch.to_excel(writer, sheet_name='Orders_Dispatch', index=False)
    df_carrier_directory.to_excel(writer, sheet_name='Carrier_Directory', index=False)

print(df_orders_dispatch['Customer_Name'].tolist())
