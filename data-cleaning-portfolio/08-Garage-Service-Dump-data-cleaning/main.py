import pandas as pd
import numpy as np

pd.set_option('display.max_rows', None)

df = pd.read_csv('08-Garage-Service-Dump-data-cleaning/garage_service_dump.csv')

# Cleaning Customer_Details column
df['Customer_Details'] = (df['Customer_Details']
    .str.replace(r'(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sir)\s+', '', regex=True)
    .str.strip()
)
df['Phone_Number'] = df['Phone_Number'].combine_first(df['Customer_Details'].str.extract(
    r'Tel:\s*(.+?)\s(?:\||ext)', expand=False
))

# Creating & Cleaning Phone_Number column
df['Phone_Number'] = (df['Phone_Number']
    .astype('string')
    .str.replace(r'\D', '', regex=True)
    .replace(r'', np.nan, regex=True)
)
df['Phone_Number'] = [cell if pd.isna(cell)
                      else cell if cell.startswith('+1')
                      else '+' + cell if cell.startswith('1')
                      else '+1' + cell for cell in df['Phone_Number']]
df['Phone_Number'] = df['Phone_Number'].where(df['Phone_Number'].str.len() == 12, np.nan)

# Creating & Extracting from Customer_Details column
df['Email_Address'] = df['Customer_Details'].str.extract(
    r'Mail:\s*(.+)'
)
df['Email_Address'] = (df['Email_Address']
                       .astype('string')
                       .str.replace(r'\.{2,}', '.', regex=True)
                       .str.replace('-', '')
                       .replace('', np.nan)
                       .str.lower()
                       .replace('invalidemail@', np.nan)
)

# Cleaning Customer_Details (removing phone numbers and email addresses)
df['Customer_Details'] = df['Customer_Details'].str.extract(
    r'([^|]+)'
)
df['Customer_Details'] = (df['Customer_Details']
    .str.strip()
    .str.title()
    .str.replace(r'\s{2,}', ' ', regex=True)
)
df = df.rename(columns={'Customer_Details': 'Customer_Name'})

# Creating & Cleaning Year column
df['Year'] = df['Vehicle_Description'].str.extract(
    r'(^\d{2,4})'
)
df['Vehicle_Description'] = df['Vehicle_Description'].str.replace(r'(^\d{2,4})', '', regex=True).str.strip()

df['Year'] = df['Year'].astype('string').str.strip()
df['Year'] = df['Year'].apply(lambda x: x if pd.isna(x) or len(x) == 4 else '20' + x)

# Creating & Cleaning Make column
df['Make'] = (df['Vehicle_Description'].str.extract(
    r'^(?:N/A\s*)?(Alfa Romeo|Aston Martin|Land Rover|Rolls Royce|Mercedes Benz|\w+)',
    expand=False
))
make_mapping = {
    "Bmw": "BMW",
    "Honda": "Honda",
    "Toyota": "Toyota",
    "Ford": "Ford",
    "Audi": "Audi",
    "Mercedes": "Mercedes-Benz",
    "Hyundai": "Hyundai",
    "Kia": "Kia",
    "Merc": "Mercedes-Benz",
    "Volkswagen": "Volkswagen",
    "Vw": "Volkswagen",
}
df['Make'] = df['Make'].str.title().map(make_mapping)
df['Vehicle_Description'] = df['Vehicle_Description'].str.replace(r'(^\w+)(?:\s|\-)', '', regex=True).str.strip()

# Creating & Cleaning Model column
df['Model'] = df['Vehicle_Description'].str.extract(
    r'^(?:N/A\s*)?(?:[A-Za-z-]+?\s+)?([^(]+)'
)
df['Model'] = df['Model'].str.strip().str.title()
model_mapping = {
    "Cr-V": "CR-V",
    "Crv": "CR-V",
    "328I": "3 Series",
    "F150": "F-150",
    "E200": "E-Class",
}
df['Model'] = df['Model'].replace(model_mapping)

# Creating & Cleaning License_Plate column
df['License_Plate'] = df['License_Plate'].combine_first(df['Vehicle_Description'].str.extract(
    r'Plate:\s*(.+)\)', expand=False
))

df['License_Plate'] = (df['License_Plate']
    .astype('string')
    .str.strip()
    .str.upper()
    .str.replace('-', '')
    .replace(r'\s+', '', regex=True)
    .replace({'NONE': np.nan,
              'UNREGISTERED': np.nan,
              'NEW CAR': np.nan,
              'NEWCAR': np.nan,
              'NOPLATE': np.nan,})
)
df = df.drop(columns=['Vehicle_Description'])

# Cleaning Service_Type column
df['Service_Type'] = df['Service_Type'].str.strip().str.title()
service_mapping = {
    "Ac Refill": "Air Conditioning",
    "Oil Change & Filter": "Oil Change",
    "Brake Pads Replacement": "Brake Pad Change",
    "Diag": "Diagnostics",
    "Engine Diagnostics": "Diagnostics",
    "Brakes Front": "Brake Pad Change",
    "Battery Replacement": "Battery",
    "Alignment": "Wheel Alignment",
    "Ac Service": "Air Conditioning",
}
df['Service_Type'] = df['Service_Type'].replace(service_mapping)

# Cleaning Date_Of_Service column
df['Date_Of_Service'] = pd.to_datetime(df['Date_Of_Service'],
                                        errors='coerce',
                                        format='mixed'
).dt.strftime('%d-%m-%Y')

# Cleaning Total_Cost column
df['Total_Cost'] = (df['Total_Cost']
    .astype('string')
    .str.strip()
    .str.replace('$', '')
    .str.replace(',', '')
    .str.replace('USD', '')
    .str.replace('FREE / WARRANTY', '0')
    .str.strip()
    .astype('float')
)
Q1 = df['Total_Cost'].quantile(0.25)
Q3 = df['Total_Cost'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
median_cost = df['Total_Cost'].median()
df['Total_Cost'] = np.where(df['Total_Cost'].between(lower_bound, upper_bound), df['Total_Cost'], median_cost)
df['Total_Cost'] = df['Total_Cost'].where(df['Total_Cost'] >= 0, df['Total_Cost'].abs())

# Cleaning Payment_Status column
df['Payment_Status'] = df['Payment_Status'].str.strip().str.title()
payment_mapping = {
    "Done": "Paid",
    "Completed": "Paid",
    "Pndg": "Pending",
    "In Progress": "Pending",
}
df['Payment_Status'] = df['Payment_Status'].replace(payment_mapping)

# Cleaning Internal_Notes column
df['Internal_Notes'] = df['Internal_Notes'].str.strip()

# Validating the cleaned data
print(len(df))
df = df.drop_duplicates()
print(len(df))
df = df.drop_duplicates(
    subset=['Customer_Name', 'Date_Of_Service', 'License_Plate', 'Service_Type', 'Make', 'Model']
)
print(len(df))

# Exporting
df.to_csv('garage_service_dump_cleaned.csv', index=False)