import pandas as pd
import numpy as np

df: pd.DataFrame = pd.read_csv('06-Property-Listings-data-cleaning/property_listings_raw.csv', engine='python', encoding='utf-8')

# Cleaning Property_Address column
df['Property_Address'] = (df['Property_Address']
    .str.strip()
    .str.title()
    .str.replace(r'\s{2,}', ' ', regex=True)
)

# Cleaning Listing_Price column
df['Listing_Price'] = (df['Listing_Price']
    .astype(str)
    .str.replace(r'[^0-9.]', '', regex=True)
    .astype(float)
)
# Cleaning Square_Feet column
df['Square_Feet'] = (pd.to_numeric(
    df['Square_Feet']
    .astype(str)
    .str.replace(r'[^0-9]', '', regex=True)
    .str.strip()
    , errors='coerce'
)).astype('Int64')
df['Square_Feet'] = np.where((df['Square_Feet'] <= 0).fillna(False),
    np.nan,
    df['Square_Feet'].astype('Int64'))

# Cleaning Propety_Type column
type_mapping = {
    'apt': 'Apartment', 'Apt.': 'Apartment', 'Apartment': 'Apartment',
    'Townhouse': 'Townhouse', 'twnd house': 'Townhouse',
    'House': 'House',
    'Multi-Family': 'Multi-Family',
    'condo': 'Condo', 'Condo': 'Condo',
    'Single Family Home': 'Single Family', 'Single Family': 'Single Family',
}
df['Property_Type'] = df['Property_Type'].str.strip().map(type_mapping)

# Cleaning Listing_Date column
df['Listing_Date'] = pd.to_datetime(df['Listing_Date'],
     errors='coerce',
     format='mixed')

# Creating new columns from Agent_Contact_Info
df['Agent_Name'] = df['Agent_Contact_Info'].str.extract(
    r'([A-za-z]+ [A-Za-z]+)'
)
df['Agent_Name'] = df['Agent_Name'].str.strip()
df['Agent_Phone'] = df['Agent_Contact_Info'].str.extract(r'(\+?\(?\d[\d\-\s()]{6,}\d\)?)')
df['Agent_Phone'] = df['Agent_Phone'].str.replace(r'[^\d+]', '', regex=True)
df['Agent_Phone'] = df['Agent_Phone'].astype(str)
df['Agent_Phone'] = [cell if pd.isna(cell) 
                    else cell if cell.startswith('+1')
                    else '+' + cell if cell.startswith('1')
                    else '+1' + cell
                    for cell in df['Agent_Phone']]



print('-'*200)
print(df['Square_Feet'].head(30))
print('-'*200)
print(df['Agent_Phone'].head(30))
print('-'*200)
print(df['Property_Address'].head(30))
