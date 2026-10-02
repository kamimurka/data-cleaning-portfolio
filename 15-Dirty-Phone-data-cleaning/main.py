import pandas as pd
import phonenumbers

df = pd.read_csv('15-Dirty-Phone-data-cleaning/dirty_phone_cleaning_practice.csv')

# Cleaning customer_name column
df['customer_name'] = df['customer_name'].str.strip()
def split_first_last_names(cell):
    if pd.isna(cell):
        return pd.NA
    if not ', ' in cell:
        return cell
    else:
        last_n, first_n = cell.split(', ')
        return f'{first_n} {last_n}'

df['customer_name'] = df['customer_name'].apply(split_first_last_names)

df['customer_name'] = (df['customer_name']
    .str.strip()
    .str.title()
    .str.replace({
        ',': ' ',
        '\t': ' ',
        r'\s{2,}': ' '
    }, regex=True))

# Cleaning phone column
df['phone_status'] = pd.NA
def clean_phone(row):
    phone_raw = row['phone']
    if pd.isna(phone_raw):
        row['phone'] = pd.NA
        row['phone_status'] = 'missing'
        return row

    try:
        phone = phonenumbers.parse(phone_raw, 'US')

    except phonenumbers.NumberParseException as e:
        row['phone'] = pd.NA
        row['phone_status'] = 'unparseable'
        return row
    
    pretty = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    if phonenumbers.is_possible_number(phone):
        row['phone'] = pretty
        row['phone_status'] = 'invalid_prefix'
        
    if not phonenumbers.is_possible_number(phone):
       row['phone'] = pd.NA
       row['phone_status'] = 'unparseable'
       return row

    if phonenumbers.is_valid_number(phone):
        row['phone'] = pretty
        row['phone_status'] = 'valid'
    return row

df = df.apply(clean_phone, axis=1)


# Cleaning email column
df['email'] = (df['email']
    .str.strip()
    .str.lower()
    .str.replace(r'\s+', '', regex=True))

# Cleaning city column
df['city'] = df['city'].str.strip().str.title()

# Cleaning signup_date column

def parse_date(s):
    if pd.isna(s):
        return pd.NaT
    s = s.strip()
    if '-' in s and len(s.split('-')[0]) <= 2:
        return pd.to_datetime(s, format='%d-%m-%Y', errors='coerce')
    if '/' in s and len(s.split('/')[0]) <= 2:
        return pd.to_datetime(s, format='mixed', dayfirst=False, errors='coerce')
    return pd.to_datetime(s, errors='coerce')

df['signup_date'] = df['signup_date'].apply(parse_date).dt.strftime('%Y-%m-%d')

# Finalizing
df = df.drop_duplicates()

# Exporting
df.to_csv('15-Dirty-Phone-data-cleaning/dirty_phone_cleaned.csv', index=False)