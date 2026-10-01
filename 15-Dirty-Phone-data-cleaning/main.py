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

# Cleaning phone column
def clean_phone(phone_raw):

    print(f'BEFORE: {phone_raw}')

    if pd.isna(phone_raw):
        print('AFTER:  ❌ empty')
        print('-' * 40)
        return pd.NA

    try:
        phone = phonenumbers.parse(phone_raw, 'US')

        print(f'PARSED: {phone}')
        print(f'VALID:  {phonenumbers.is_valid_number(phone)}')

        if not phonenumbers.is_valid_number(phone):
            print('AFTER:  ❌ invalid')
            print('-' * 40)
            return pd.NA

        cleaned = phonenumbers.format_number(
            phone,
            phonenumbers.PhoneNumberFormat.E164
        )

        print(f'AFTER:  {cleaned}')
        print('-' * 40)

        return cleaned

    except phonenumbers.NumberParseException as e:
        print(f'AFTER:  ❌ parse error: {e}')
        print('-' * 40)
        return pd.NA

df['phone'] = df['phone'].apply(clean_phone)


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

# Exporting
df.to_csv('15-Dirty-Phone-data-cleaning/dirty_phone_cleaned.csv', index=False)

#########