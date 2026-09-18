import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('12-Customer-data-cleaning/customer_data_cleaning_practice.csv', engine='python')

# Cleaning Customer_ID column
df['Customer_ID'] = (df['Customer_ID']
    .str.strip()
    .str.upper()
)

# Cleaning Signup_Date column
df['Signup_Date'] = pd.to_datetime(
    df['Signup_Date'],
    format='mixed'
).dt.strftime('%Y-%m-%d')

# Cleaning Country column
country_mapping = {
    "FRANCE": "France",
    "uk": "United Kingdom",
    "UK": "United Kingdom",
    "USA": "United States",
    "usa": "United States",
    "germany": "Germany",
    "can": "Canada",
}
df['Country'] = df['Country'].replace(country_mapping)

# Cleaning Age column
Q1 = df['Age'].quantile(0.25)
Q3 = df['Age'].quantile(0.75)

IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
lower = Q1 - 1.5 * IQR

df = df[df['Age'].between(lower, upper)]
df['Age'] = df['Age'].round()
df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
df['Age'] = df['Age'].astype('Int64')

# Cleaning Annual_Income column
df['Annual_Income'] = df['Annual_Income'].str.replace(r'[^0-9]', '', regex=True)
df['Annual_Income'] = df['Annual_Income'].astype('Int64')
# Cleaning Purchase_Status
status_mapping = {
    "active": "Active",
    "inactive": "Inactive",
    "pend.": "Pending",
    "ACTIVE": "Active",
}

df['Purchase_Status'] = df['Purchase_Status'].replace(status_mapping)

################
df = df.drop_duplicates()
print(len(df))
df = df.drop_duplicates(subset=['Customer_ID'])
print(len(df))

# Exporting
df.to_csv('12-Customer-data-cleaning/customer_data_cleaned.csv', index=False)

# print(df['Signup_Date'].head(200))
# print(df['Country'].value_counts())
# print(df['Age'].head(200))
# print(df['Annual_Income'].head(200))
# print(df['Purchase_Status'].value_counts())python $ZED_FILE
print('Hello')
print('чтобы ты сдох гемини , ты мне ничем не помог, а тебя  удаляю, гори в аду мразь')
