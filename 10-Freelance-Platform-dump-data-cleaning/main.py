import pandas as pd
import numpy as np
import re

# Creating DataFrames & setting options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df_Freelancer_Profiles: pd.DataFrame = pd.read_excel('10-Freelance-Platform-dump-data-cleaning/freelance_platform_raw_dump.xlsx',
                                                    sheet_name='Freelancer_Profiles', engine='openpyxl')

df_Project_Logs: pd.DataFrame = pd.read_excel('10-Freelance-Platform-dump-data-cleaning/freelance_platform_raw_dump.xlsx',
                                            sheet_name='Project_Logs', engine='openpyxl')

# df_Feedback_and_Ratings: pd.DataFrame = pd.read_excel('10-Freelance-Platform-dump-data-cleaning/freelance_platform_raw_dump.xlsx',
#                                                     sheet_name='Feedback_and_Ratings', engine='openpyxl')

###################################
# SHEET 1: Freelancer_Profiles
###################################

# Cleaning Full_Name_&_Title column
df_Freelancer_Profiles['Full_Name_&_Title'] = (
    df_Freelancer_Profiles['Full_Name_&_Title']
    .str.strip() 
    .str.title()
    .str.replace(
        {
            r'\s{2,}': '',
            'Ms.': '',
            'Mr.': '',
            'Mrs.': '',
            'Dr.': '',
            'Eng.': '',
            'Prof.': '',
        },
        regex=True
    )
    .str.strip()
)

# Cleaning Location_Country
country_mapping = {
    "Deutschland": "DE",
    "Germany": "DE",
    "Australia": "AU",
    "India": "IN",
    "Canada": "CA",
    "Ukraine": "UA",
    "Brazil": "BR",
    "United Kingdom": "GB",
    "United States": "US",
    "USA": "US",
    "U.S.A.": "US",
    "UK": "GB",
}

df_Freelancer_Profiles['Location_Country'] = df_Freelancer_Profiles['Location_Country'].replace(country_mapping)

country_phone_codes = {
    "DE": "+49",
    "US": "+1",
    "GB": "+44",
    "AU": "+61",
    "IN": "+91",
    "CA": "+1",
    "UA": "+380",
    "BR": "+55",
}
min_phone_length = {
    "DE": 9,
    "US": 12,
    "GB": 10,
    "AU": 8,
    "IN": 10,
    "CA": 12,
    "UA": 13,
    "BR": 13,
}

### Contact_Details ###

# Creating Email column
email_pattern = r'''
^(?:
    (?:Email:)\s*(\S+@\S+)\s*\|
    |
    (\S+@\S+)\,?
)
'''

extracted_email = df_Freelancer_Profiles['Contact_Details'].str.extract(
    email_pattern,
    flags=re.VERBOSE
)
df_Freelancer_Profiles['Email'] = extracted_email[0].fillna(extracted_email[1])
df_Freelancer_Profiles['Email'] = (df_Freelancer_Profiles['Email']
    .str.strip()
    .str.replace(',', '')
    .str.strip()
    .str.lower()
)

# Creating Phone column
phone_pattern = r'''
(?:
    Tel:\s*(.+)
    |
    \,\s*(.+)
)
'''

extracted_phone = df_Freelancer_Profiles['Contact_Details'].str.extract(
    phone_pattern,
    flags=re.VERBOSE
)
df_Freelancer_Profiles['Phone'] = extracted_phone[0].fillna(extracted_phone[1]) # <-
df_Freelancer_Profiles['Phone'] = (df_Freelancer_Profiles['Phone']
    .str.strip()
    .str.replace(r'[^0-9\+]', '', regex=True)
    .str.strip()
    .astype('string'))


def normalize_phone(row):
    country = row['Location_Country']
    phone = row['Phone']

    if pd.isna(phone):
        return pd.NA

    had_plus = phone.startswith('+')
    digits = phone.lstrip('+')

    if had_plus:
        return '+' + digits

    if pd.isna(country):
        return pd.NA

    code = country_phone_codes.get(country)
    if code is None:
        return phone

    digits = digits.lstrip('0')
    result = code + digits

    min_len = min_phone_length.get(country)
    if min_len and len(result.lstrip('+')) < min_len:
        return pd.NA

    return result

df_Freelancer_Profiles['Phone'] = df_Freelancer_Profiles.apply(normalize_phone, axis=1)

# Cleaning Hourly_Rate_USD column
df_Freelancer_Profiles['Hourly_Rate_USD'] = (df_Freelancer_Profiles['Hourly_Rate_USD']
    .astype('string')
    .str.replace(
        {
            'USD': '',
            'usd': '',
            '$': '',
            '/hr': '',
        },
    )
    .str.strip()
)

df_Freelancer_Profiles['Hourly_Rate_USD'] = pd.to_numeric(
    df_Freelancer_Profiles['Hourly_Rate_USD'],
    errors='coerce'
)
df_Freelancer_Profiles['Hourly_Rate_USD'] = df_Freelancer_Profiles['Hourly_Rate_USD'].abs()

Q1 = df_Freelancer_Profiles['Hourly_Rate_USD'].quantile(0.25)
Q3 = df_Freelancer_Profiles['Hourly_Rate_USD'].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR

mask = df_Freelancer_Profiles['Hourly_Rate_USD'] > upper_bound
df_Freelancer_Profiles.loc[mask, 'Hourly_Rate_USD'] = df_Freelancer_Profiles.loc[mask, 'Hourly_Rate_USD'] / 100

# Cleaning Core_Skills column
df_Freelancer_Profiles['Core_Skills'] = (df_Freelancer_Profiles['Core_Skills']
    .str.strip()
    .str.title()
)

core_skills_mapping = {
    'Js': 'js',
    'Seo': 'SEO',
    'Powerbi': 'Power BI',
    'Sql': 'SQL',
    'Smm': 'SMM',
    'Aws': 'AWS',
    'Devops': 'DevOps',
    'Ui': 'UI',
    'Ux': 'UX',
    ';': ' | ',
    r',(?![^(]*\))': ' | ',
    ' / ': ' | ',
    '  ': ' '
}
df_Freelancer_Profiles['Core_Skills'] = df_Freelancer_Profiles['Core_Skills'].str.replace(core_skills_mapping, regex=True)

# Cleaning Member_Since
df_Freelancer_Profiles['Member_Since'] = pd.to_datetime(
    df_Freelancer_Profiles['Member_Since'],
    errors='coerce',
    format='mixed'
).dt.strftime('%Y-%m-%d')

# Validation 1
df_Freelancer_Profiles = df_Freelancer_Profiles.drop(columns=['Contact_Details'])

###################################
# SHEET 2: Project_Logs
###################################

# Cleaning Assigned_Freelancer_ID column
df_Project_Logs['Assigned_Freelancer_ID'] = df_Project_Logs['Assigned_Freelancer_ID'].replace('UNKNOWN', pd.NA)

# Cleaning Category column


##########
print('-'*120)
print(df_Project_Logs['Assigned_Freelancer_ID'].head(100))
