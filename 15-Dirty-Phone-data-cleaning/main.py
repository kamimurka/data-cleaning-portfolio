import pandas as pd
import phonenumbers

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('15-Dirty-Phone-data-cleaning/dirty_phone_cleaning_practice.csv', engine='python')

# Cleaning customer_name column
df['customer_name'] = (df['customer_name']
    .str.strip()
    .str.title()
    .str.replace({
        ',': ' ',
        '\t': ' ',
        r'\s{2,}': ' '
    }, regex=True))

# Cleaning email column
df['email'] = (df['email']
    .str.strip()
    .str.lower()
    .str.replace(r'\s+', '', regex=True))

# Cleaning city column
df['city'] = df['city'].str.strip().str.title()

# Cleaning signup_date column
df['signup_date'] = pd.to_datetime(
    df['signup_date'],
    errors='coerce',
    format='mixed').dt.strftime('%Y-%m-%d')


#########
print(df['signup_date'].head(50))