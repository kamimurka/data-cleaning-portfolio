import pandas as pd
import phonenumbers
import re

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

# Cleaning phone column
def clean_phone(raw, region):
    if pd.isna(raw) or pd.isna(region):
        return None
    
    raw = raw.strip()
    raw = str(raw)
    if raw.startswith('00'):
        raw = '+' + raw[2:]
    raw = re.sub(r'\s*(ext\.?|доб\.?)\s*\d+', '', raw, flags=re.IGNORECASE)

    try:
        phone = phonenumbers.parse(raw, region)
        if phonenumbers.is_valid_number(phone):
            return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        else:
            print(phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164))
    except phonenumbers.NumberParseException:
        return None

df['phone'] = df.apply(lambda row: clean_phone(row['phone'], row['country']), axis=1)

print(f'NA are: {df['phone'].isna().sum()}')

# Cleaning signup_date column
df['signup_date'] = pd.to_datetime(df['signup_date'],
    format='mixed',
    errors='coerce')

df.loc[df["signup_date"] > pd.Timestamp.now(), "signup_date"] = pd.NaT


# print(df['country'].value_counts())
# print('-'*100)

# Finalization
df2 = pd.read_csv('14-Customers-data-cleaning/customers_dirty.csv', engine='python')
print(df2.loc[df['phone'].isna(), 'phone'].tolist())
# Exporting
# pd.to_csv('customers_cleaned.csv', index=False)