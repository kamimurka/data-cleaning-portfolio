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

df_Feedback_and_Ratings: pd.DataFrame = pd.read_excel('10-Freelance-Platform-dump-data-cleaning/freelance_platform_raw_dump.xlsx',
                                                    sheet_name='Feedback_and_Ratings', engine='openpyxl')

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
            r'\s{2,}': ' ',
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

df_Freelancer_Profiles = df_Freelancer_Profiles.drop_duplicates()
df_Freelancer_Profiles = df_Freelancer_Profiles.drop_duplicates(subset=['Freelancer_Ref_No'], keep='first')


###################################
# SHEET 2: Project_Logs
###################################

# Cleaning Assigned_Freelancer_ID column
df_Project_Logs['Assigned_Freelancer_ID'] = df_Project_Logs['Assigned_Freelancer_ID'].replace('UNKNOWN', pd.NA)

# Cleaning Category column
df_Project_Logs['Category'] = (df_Project_Logs['Category']
    .str.strip()
    .str.title()
    .str.replace('Ui', 'UI')
    .replace({
        'Web Dev': 'Web Development',
        'Design': 'Design & UI', 
        'Copywriting / Content': 'Content Writing'
    })
)

# Cleaning Budget_Amount column
df_Project_Logs['Budget_Amount'] = (df_Project_Logs['Budget_Amount']
    .astype('string')
    .str.replace('$', '')
    .str.strip()
)

df_Project_Logs['Budget_Amount'] = pd.to_numeric(df_Project_Logs['Budget_Amount'], errors='coerce')

# Cleaning Project_Status column
df_Project_Logs['Project_Status'] = (df_Project_Logs['Project_Status']
    .str.strip()
    .str.title()
)
status_mapping = {
    'Finished': 'Completed',
    'In-Progress': 'In Progress',
    'Canceled': 'Cancelled'
}

df_Project_Logs['Project_Status'] = df_Project_Logs['Project_Status'].replace(status_mapping)

# Cleaning Start_Date & Completion_Date
def parse_mixed_date(series):
    s = series.astype(str)
    iso_mask = s.str.match(r'^\d{4}-\d{2}-\d{2}$')
    slash_mask = s.str.match(r'^\d{2}/\d{2}/\d{4}$')
    dash_mask = s.str.match(r'^\d{2}-\d{2}-\d{4}$')

    result = pd.Series(pd.NaT, index=series.index, dtype='datetime64[ns]')
    result[iso_mask] = pd.to_datetime(s[iso_mask], format='%Y-%m-%d', errors='coerce')
    result[slash_mask] = pd.to_datetime(s[slash_mask], format='%d/%m/%Y', errors='coerce')
    result[dash_mask] = pd.to_datetime(s[dash_mask], format='%m-%d-%Y', errors='coerce')
    return result.dt.strftime('%Y-%m-%d')

df_Project_Logs['Start_Date'] = parse_mixed_date(df_Project_Logs['Start_Date'])
df_Project_Logs['Completion_Date'] = parse_mixed_date(df_Project_Logs['Completion_Date'])

# Validation 2
df_Project_Logs = df_Project_Logs.drop_duplicates()
df_Project_Logs = df_Project_Logs.drop_duplicates(subset=['Project_Code'], keep='first')

# Assigned_Freelancer_ID не трогаем — один фрилансер может вести много проектов
###################################
# SHEET 3: Feedback_and_Ratings
###################################

# Cleaning Client_Rating column
df_Feedback_and_Ratings['Client_Rating'] = (df_Feedback_and_Ratings['Client_Rating']
    .astype('string')
    .str.strip()
    .str.title()
    .str.replace({
        'Stars': '',
        'Five': '5',
        'Four': '4',
        'Three': '3',
        'Two': '2',
        'One': '1'
    })
    .str.strip()
)
df_Feedback_and_Ratings['Client_Rating'] = pd.to_numeric(df_Feedback_and_Ratings['Client_Rating'], errors='coerce')
df_Feedback_and_Ratings['Client_Rating'] = (df_Feedback_and_Ratings['Client_Rating']
    .where(df_Feedback_and_Ratings['Client_Rating'].between(1.0, 5.0), pd.NA)
)

# Cleaning Feedback_Comment column
df_Feedback_and_Ratings['Feedback_Comment'] = df_Feedback_and_Ratings['Feedback_Comment'].str.strip()

# Cleaning Verified_Review
bool_mapping = {
    'yes': 'Yes', 'Y': 'Yes', 'YES': 'Yes', 'True': 'Yes', 'TRUE': 'Yes',
    'NO': 'No', 'N': 'No', 'FALSE': 'No', 'No': 'No', 'no': 'No'
}

df_Feedback_and_Ratings['Verified_Review'] = df_Feedback_and_Ratings['Verified_Review'].replace(bool_mapping)

# Validation 3
df_Feedback_and_Ratings = df_Feedback_and_Ratings.drop_duplicates()
df_Feedback_and_Ratings = df_Feedback_and_Ratings.drop_duplicates(subset=['Review_ID'], keep='first')


# EXPORTING
with pd.ExcelWriter('10-Freelance-Platform-dump-data-cleaning/freelance_platform_cleaned.xlsx') as writer:
    df_Freelancer_Profiles.to_excel(writer, sheet_name='Freelancer_Profiles', index=False)
    df_Project_Logs.to_excel(writer, sheet_name='Project_Logs', index=False)
    df_Feedback_and_Ratings.to_excel(writer, sheet_name='Feedback_and_Ratings', index=False)
