import pandas as pd
import phonenumbers

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('14-Customers-data-cleaning/customers_dirty.csv', engine='python')

# Cleaning full_name column
df['full_name'] = (df['full_name']
    .str.strip()
    .str.title())

# Clenaing country column
df['country'] = df['country'].str.strip().str.title()
country_mapping = {
    "Ukraine": "UA",
    "Ua": "UA",

    "Poland": "PL",
    "Pl": "PL",

    "Germany": "DE",
    "Deutschland": "DE",
    "De": "DE",

    "Us": "US",
    "United States": "US",
    "United States Of America": "US",
    "Usa": "US",

    "Uk": "GB",
    "Gb": "GB",
    "England": "GB",
    "United Kingdom": "GB",
}

df['country'] = df['country'].replace(country_mapping)


# Cleaning signup_date column
idx = pd.to_datetime(df['signup_date'],
    format='mixed',
    errors='coerce').idxmax()

print(df.loc[idx])


# print(df['country'].value_counts())
# print('-'*100)
# print(df['signup_date'].max())