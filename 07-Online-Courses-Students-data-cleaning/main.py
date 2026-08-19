import pandas as pd
import numpy as np

df: pd.DataFrame = pd.read_csv('online_course_students_raw.csv', engine='python')

# Cleaning Full Name column
df['Full Name'] = (df['Full Name']
    .str.strip()
    .str.title()
    .str.replace('  ', ' ')
    .str.replace(r'(Ms\.|Mr\.|Dr\.)', '', regex=True)
    .str.strip()
)

# Cleaning Email Address column
srs = df['Email Address'].str.extract(r'@([^;\s]+)')[0]
df['Email Address'] = df['Email Address'].str.split(';').str[0].str.strip()
df['Email Address'] = (df['Email Address']
    .str.strip()
    .str.lower()
    .str.replace({
    'outlook': '@outlook',
    'gmail': '@gmail',
    'yahoo': '@yahoo',
    'hotmail': '@hotmail',
    'company': '@company',
    'edu': '@edu',
})
    .str.replace(r'@{2,}', '@', regex=True)
)

# Enrolled Course
enrolled_course_mapping = {
    'Digital Marketing': 'Digital Marketing',
    'Digital Marketing Essentials': 'Digital Marketing',
    'Marketing 101': 'Digital Marketing',
    'UX/UI Design Fundamentals': 'UX/UI Design',
    'UI/UX Basics': 'UX/UI Design',
    'UX/UI Design': 'UX/UI Design',
    'python for beginners': 'Python for Beginners',
    'Python for beginners': 'Python for Beginners',
    'Python for Beginners': 'Python for Beginners',
    'Web Development': 'Web Development',
    'Web Development Bootcamp': 'Web Development',
    'Web Dev Bootcamp': 'Web Development',
    'Data Science - Intro': 'Data Science',
    'Data Science 101': 'Data Science',
    'DS 101': 'Data Science'
}
df['Enrolled Course'] = df['Enrolled Course'].map(enrolled_course_mapping).str.strip()

# Cleaning Registration Date
df['Registration Date'] = pd.to_datetime(df['Registration Date'],
                                         format='mixed',
                                         errors='coerce').dt.strftime('%d-%m-%Y')

df['Final Score'] = (df['Final Score']
                     .astype(str)
                     .str.replace('%', '')
                     .astype('Int64')
                     .abs()
)

df['Final Score'] = df['Final Score'].where(df['Final Score'].between(0, 100), np.nan)

# Amount Paid
df['Amount Paid'] = (df['Amount Paid']
    .astype(str)
    .str.strip()
    .str.replace(r'(\$|USD)', '', regex=True)
    .str.strip()
    .astype('Int64') #####
)
Q1 = df['Amount Paid'].quantile(0.25)
Q3 = df['Amount Paid'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

df['Amount Paid'] = df['Amount Paid'].where(
    df['Amount Paid'].between(lower, upper),
    np.nan
)

# Cleaning Payment Status
payment_status_mapping = {
    "No": "Unpaid",
    "Unpaid": "Unpaid",
    "Yes": "Paid",
    "Paid": "Paid",
    "Pending": "Pending",
    "Failed": "Failed",
    "Refunded": "Refunded",
    "Completed": "Paid",
}

df['Payment Status'] = (df['Payment Status']
    .str.strip()
    .str.title()
    .map(payment_status_mapping)
) ###########

# Validation
course_prices = df.groupby(df['Enrolled Course'])['Amount Paid'].first().to_dict()
df['Amount Paid'] = df['Amount Paid'].fillna(df['Enrolled Course'].map(course_prices))

df['Amount Paid'] = np.where(
    df['Payment Status'] == 'Refunded',
    0,
    df['Amount Paid']
)
print(f'df len: {len(df)}')
df = df.drop_duplicates(subset=['Full Name', 'Enrolled Course'], keep='first')
print(f'df len: {len(df)}')
print('-'*90)

# Exporting
df.to_csv('online_courses_cleaned.csv', index=False,)

# print('-'*90)
# print(df['Full Name'].head(30))
# print('-'*90)
# print(df['Email Address'].head(30))
# print('-'*90)
# print(df['Payment Status'].value_counts())
# print('-'*90)
# print(df['Registration Date'].head(30))
# print(f'total nans: {df['Registration Date'].isna().sum()}')
# print('-'*90)
# print(df['Amount Paid'].head(30))