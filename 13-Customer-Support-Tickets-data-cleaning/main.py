import pandas as pd
import phonenumbers
import re

df = pd.read_csv('13-Customer-Support-Tickets-data-cleaning/customer_support_tickets_messy.csv', engine='python')

# Cleaning created_at column
df['created_at'] = pd.to_datetime(df['created_at'], format='mixed')

# Cleaning customer_name column
df['customer_name'] = df['customer_name'].str.strip()

# Cleaning email column
df['email'] = (df['email']
    .str.strip()
    .str.lower()
    .str.replace(' ', ''))
# Cleaning phone column
df['phone'] = df['phone'].str.replace(r'[^\d+]', '', regex=True)

raw = df['phone'].copy()

def clean_phone(raw, region="US"):
    if pd.isna(raw):
        return pd.NA
    s = re.sub(r'[^\d+]', '', str(raw))
    if s.startswith('00'):
        s = '+' + s[2:]
    try:
        num = phonenumbers.parse(s, region)
    except phonenumbers.NumberParseException:
        return pd.NA
    if phonenumbers.is_possible_number(num):
        return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    return pd.NA

df['phone'] = df['phone'].apply(clean_phone)

# Cleaning city column
df['city'] = (df['city']
    .str.strip()
    .str.title())

# Cleaning issue_category column
df['issue_category'] = (df['issue_category']
    .str.strip()
    .str.title())
issue_mapping = {
    "Feature_Request": "Feature Request",
    "Account_Access": "Account Access",
    "Technical_Issue": "Technical Issue"
}

df['issue_category'] = df['issue_category'].replace(issue_mapping)

# Cleaning priority column
df['priority'] = (df['priority']
    .str.strip()
    .str.title()
)

# Cleaning channel column
df['channel'] = (df['channel']
    .str.strip()
    .str.title())

channel_mapping = {
    "Social Media": "Social",
    "Chat": "Live Chat",
    "Web Form": "Web-Form"
}
df['channel'] = df['channel'].replace(channel_mapping)

# Cleaning status column
df['status'] = (df['status']
    .str.strip()
    .str.title()
    .replace("Pending_Customer", "Pending Customer"))

# Cleaning customer_tier column
df['customer_tier'] = (df['customer_tier']
    .str.strip()
    .str.title())

# Cleaning satisfaction_rating column
df['satisfaction_rating'] = (df['satisfaction_rating']
    .astype('string')
    .str.strip()
    .replace({'four': '4', '6': pd.NA, '0': pd.NA}))
df['satisfaction_rating'] = pd.to_numeric(df['satisfaction_rating'], errors='coerce')

# Cleaning first_response_minutes column
df['first_response_minutes'] = (df['first_response_minutes']
    .str.strip()
    .str.lower()
    .replace('unknown', pd.NA))
df['first_response_minutes'] = pd.to_numeric(df['first_response_minutes'], errors='coerce')
df['first_response_minutes'] = df['first_response_minutes'].where(
    (pd.isna(df['first_response_minutes'])) | (df['first_response_minutes'] >= 0), pd.NA)

# Cleaning resolution_time_hours column
df['resolution_time_hours'] = (df['resolution_time_hours']
    .str.strip()
    .str.replace(r'[^\d\.\-]', '', regex=True))
df['resolution_time_hours'] = pd.to_numeric(df['resolution_time_hours'], errors='coerce')
df['resolution_time_hours'] = df['resolution_time_hours'].where(
    (pd.isna(df['resolution_time_hours'])) | (df['resolution_time_hours'] >= 0), pd.NA
)
df['resolution_time_hours'] = df['resolution_time_hours'].round()
df['resolution_time_hours'] = df['resolution_time_hours'].astype('Int64')

# Cleaning refund_amount column
df['refund_amount'] = df['refund_amount'].str.replace(r'[^\d\.]', '', regex=True)


# Cleaning tags column
df['tags'] = (df['tags']
    .str.strip()
    .str.title()
    .str.replace({';': ' | ', ',': ' | '}))

# Finalization
df['ticket_id'] = df['ticket_id'].str.strip().str.upper()
df = df.drop_duplicates(subset='ticket_id')

# Exporting
df.to_csv('13-Customer-Support-Tickets-data-cleaning/customer_support_tickets_cleaned.csv', index=False)