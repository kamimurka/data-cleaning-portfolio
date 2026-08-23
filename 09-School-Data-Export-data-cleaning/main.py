import pandas as pd
import re
import numpy as np

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

df_Student_Records_2023_2024 = pd.read_excel('09-School-Data-Export-data-cleaning/School_Data_Export_2023-2024_Raw.xlsx',
                                           engine='openpyxl',
                                           sheet_name='Student_Records_2023-2024')

df_Academic_Grades_Log = pd.read_excel('09-School-Data-Export-data-cleaning/School_Data_Export_2023-2024_Raw.xlsx',
                                       engine='openpyxl',
                                       sheet_name='Academic_Grades_Log')

##################################
# SHEET 1: Student_Records_2023-2024
##################################

# Cleaning Student ID / Reg No column
df_Student_Records_2023_2024['Student ID / Reg No'] = df_Student_Records_2023_2024['Student ID / Reg No'].str.strip().str.upper()
df_Student_Records_2023_2024.loc[127, 'Student ID / Reg No'] = 'STU-1125'

# Cleaning Full Name & Title column
df_Student_Records_2023_2024['Full Name & Title'] = (df_Student_Records_2023_2024['Full Name & Title']
    .str.strip()
    .str.title()
    .str.replace(
    {
        'Mr. ': '',
        'Ms. ': '',
        'Mrs. ': '',
        'Dr. ': '',
        'Miss. ': '',
        'Miss ': '',
        'Mister ': '',
        'Jr. ': '',
        'Sr. ': '',
        'Jr.': '',
        'Sr.': '',
        'R.': '',
    })
    .str.replace(
    {
        r'\'(.*)\'': '',
        r'\s{2,}': ' ',
    }, regex=True)
    .str.strip()
)
df_Student_Records_2023_2024.loc[127, 'Full Name & Title'] = 'Unknown Student'

# Cleaning DOB / Date of Birth column
df_Student_Records_2023_2024['DOB / Date of Birth'] = pd.to_datetime(
    df_Student_Records_2023_2024['DOB / Date of Birth'],
    errors='coerce',
    format='mixed').dt.strftime('%m/%d/%Y')

# Cleaning Grade/Level column
grade_level_mapping = {
  "9": "9",
  "9th": "9",
  "Grade 9": "9",
  "9th Grade": "9",
  "grade 9": "9",
  "10": "10",
  "10th": "10",
  "Grade 10": "10",
  "10th Grade": "10",
  "Tenth Grade": "10",
  "11": "11",
  "11th": "11",
  "Grade 11": "11",
  "11th Grade": "11",
  "12": "12",
  "12th": "12",
  "Grade 12": "12",
  '12th Grade': "12"
}
df_Student_Records_2023_2024['Grade/Level'] = (df_Student_Records_2023_2024['Grade/Level']
    .astype('string')
    .replace(grade_level_mapping)
    .astype("Int16"))

# Cleaning Primary Contact Person & Details column

# Extracting Parent Name from Primary Contact Person & Details column
name_pattern = r'''
^(?:
    (?:Mother:|Mother\s-|Father:|Guardian:|Parent:|Sibling:|Aunt:|Uncle:|Grandparent:|Other:)\s*(.+?)(?=\s\||\s\(|\s\/|\s\-)
    |
    (.+?)(?=\,|\s\(|\/)

)
'''
extracted = df_Student_Records_2023_2024['Primary Contact Person & Details'].str.extract(name_pattern, flags=re.X)
df_Student_Records_2023_2024['Parent Name'] = extracted[0].fillna(extracted[1])
df_Student_Records_2023_2024['Parent Name'] = [cell if pd.isna(cell)
                                               else 'Unknown Parent' if cell.startswith('Contact')
                                               else cell for cell in df_Student_Records_2023_2024['Parent Name']]

# Extracting Parent Phone from Primary Contact Person & Details column
phone_pattern = r'''
(?:
    (?:Contact:\s|Ph:\s|\-\s|\/|mob:\s|ph:\s|\||tel:\s|\(|,|\))\s*(\d[\d\s\-\(\)\.]*\d)
)
'''
extracted = df_Student_Records_2023_2024['Primary Contact Person & Details'].str.extract(phone_pattern, flags=re.X)
df_Student_Records_2023_2024['Parent Phone'] = extracted[0]
df_Student_Records_2023_2024['Parent Phone'] = df_Student_Records_2023_2024['Parent Phone'].str.replace(r'\D', '', regex=True).str.strip()
df_Student_Records_2023_2024['Parent Phone'] = [cell if pd.isna(cell)
                                                 else '+' + cell if cell.startswith('1')
                                                 else '+1' + cell for cell in df_Student_Records_2023_2024['Parent Phone']]

# Extracting Parent Email from Primary Contact Person & Details column
email_pattern = r'''
(?:
    (?:Email:\s|E:\s|e:\s|e-mail:\s|e-mail\s-|email:\s|\-|\/|\,|\|)\s*(\S+@\S+)
)
'''
extracted = df_Student_Records_2023_2024['Primary Contact Person & Details'].str.extract(email_pattern, flags=re.X)
df_Student_Records_2023_2024['Parent Email'] = extracted[0]
df_Student_Records_2023_2024['Parent Email'] = (df_Student_Records_2023_2024['Parent Email']
                                                .str.lower()
                                                .str.replace(
                                                {
                                                    ',': '',
                                                    r'@{2,}': '@'
                                                }, regex=True)
                                                .str.strip())

# Extracting Relationship from Primary Contact Person & Details column
relationship_pattern = r'''
(?:
    ^(Father\:?|Mother\:?|Guardian\:?|Sibling\:?|Aunt\:?|Uncle\:?|Other\:?|Parent\:?)
    |
    \((Father|Mother|Guardian|Sibling|Aunt|Uncle|Other|Parent)\)
)
'''
extracted = df_Student_Records_2023_2024['Primary Contact Person & Details'].str.extract(relationship_pattern, flags=re.X)
df_Student_Records_2023_2024['Relationship'] = extracted[0].fillna(extracted[1])
df_Student_Records_2023_2024['Relationship'] = df_Student_Records_2023_2024['Relationship'].str.replace(':', '').str.strip()

# Cleaning Home Address column
df_Student_Records_2023_2024['Home Address'] = (df_Student_Records_2023_2024['Home Address']
                                                .str.replace(
                                                {
                                                    'Street': 'St',
                                                    'Avenue': 'Ave',
                                                    'Road': 'Rd',
                                                    'Lane': 'Ln',
                                                    'Drive': 'Dr',
                                                    'Springfield': '',
                                                    'Springfield IL': '',
                                                    'Springield, IL': '',
                                                    '  ': ' ',
                                                    ',': '',
                                                    'IL': '',
                                                    r'\s{2,}': ' '
                                                }, regex=True)
                                                )
# Cleaning Tuition Fee Paid ($) column
df_Student_Records_2023_2024['Tuition Fee Paid ($)'] = pd.to_numeric(df_Student_Records_2023_2024['Tuition Fee Paid ($)']
                                                                      .astype('string')
                                                                      .str.replace('$', '')
                                                                      .str.replace(',', '')
                                                                      , errors='coerce')
Q1 = df_Student_Records_2023_2024['Tuition Fee Paid ($)'].quantile(0.25)
Q3 = df_Student_Records_2023_2024['Tuition Fee Paid ($)'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df_Student_Records_2023_2024['Tuition Fee Paid ($)'] = df_Student_Records_2023_2024['Tuition Fee Paid ($)'].clip(lower=lower_bound, upper=upper_bound)

# Cleaning Status / Remarks column
df_Student_Records_2023_2024['Status / Remarks'] = df_Student_Records_2023_2024['Status / Remarks'].str.strip().str.title()
status_mapping = {
    'Active': 'Enrolled',
    'Enrolled': 'Enrolled',
    'Active - Full Scholarship?': 'Enrolled',
    'Suspended': 'Enrolled',
    'Graduating': 'Graduating',
    'Withdrawn': 'Withdrawn',
    'Inactive': 'Withdrawn',
    'Pending': 'Withdrawn',
}

df_Student_Records_2023_2024['Status / Remarks'] = df_Student_Records_2023_2024['Status / Remarks'].map(status_mapping)

##################################
# SHEET 2: Academic_Grades_Log
##################################

# Cleaning Subject / Course Code column

# Creating Subject column
df_Academic_Grades_Log['Subject'] = (df_Academic_Grades_Log['Subject / Course Code']
    .str.strip()
    .str.extract(r'([A-Za-z\s]+)')[0]
    .str.strip())
subject_mapping = {
    'SCI': 'Science',
    'ENG': 'English',
    'Math': 'Math',
    'Mathematics': 'Math',
    'HIST': 'History',
    'World History': 'History',
    'BIO': 'Biology',
    'Biology Lab': 'Biology',
    'English Literature': 'English',
    'Physics': 'Physics',
}

df_Academic_Grades_Log['Subject'] = df_Academic_Grades_Log['Subject'].map(subject_mapping)

# Creating Course Code column
df_Academic_Grades_Log['Course Code'] = (df_Academic_Grades_Log['Subject / Course Code']
    .str.strip()
    .str.extract(r'(\d{3})'))

# Cleaning Exam Date column
df_Academic_Grades_Log['Exam Date'] = pd.to_datetime(df_Academic_Grades_Log['Exam Date'],
                                                     format='mixed',
                                                     errors='coerce').dt.strftime('%m/%d/%Y')




# Cleaning Score / Grade column
letter_grade_mapping = {
    'A+': 98,
    'A': 95,
    'A-': 92,
    'B+': 88,
    'B': 85,
    'B-': 82,
    'C+': 78,
    'C': 75,
    'C-': 72,
    'D+': 68,
    'D': 65,
    'D-': 62,
    'F': 50,
}

def parse_score(value):
    if pd.isna(value):
        return np.nan
    if value in letter_grade_mapping:
        return letter_grade_mapping[value]
    if value == 'EXEMPT':
        return np.nan
    if '/' in value:
        return float(value.split('/')[0])
    try:
        return float(value)
    except ValueError:
        return np.nan
df_Academic_Grades_Log['Score / Grade'] = df_Academic_Grades_Log['Score / Grade'].apply(parse_score)

# Cleaning Attendance (%) column
df_Academic_Grades_Log['Attendance (%)'] = pd.to_numeric(df_Academic_Grades_Log['Attendance (%)']
                                            .astype('string')
                                            .str.strip()
                                            .str.replace('%', '')
                                            , errors='coerce')
def parse_attendance(value):
    if pd.isna(value):
        return np.nan
    if value <= 1.00:
        return str(value * 100) + '%'
    if value > 100.0:
        value = 100.0
        return str(value) + '%'
    return str(value) + '%'

df_Academic_Grades_Log['Attendance (%)'] = df_Academic_Grades_Log['Attendance (%)'].apply(parse_attendance)

######## Validation of Student Records ########
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop_duplicates()
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop_duplicates(subset=['Student ID / Reg No'],
                                                                            keep='first')

df_Student_Records_2023_2024['Full Name & Title'] = df_Student_Records_2023_2024['Full Name & Title'].str.strip()
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop_duplicates(subset=['Full Name & Title'],
                                                                            keep='first')
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.sort_values(by=['Full Name & Title'])

df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop(columns=['Primary Contact Person & Details'])

df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop_duplicates(subset=['Student ID / Reg No'], keep='first')

######## Validation of Academic Grades Log ########
df_Academic_Grades_Log = df_Academic_Grades_Log.drop(columns=['Subject / Course Code'])

# Exporting
df_Student_Records_2023_2024 = pd.merge(left=df_Student_Records_2023_2024,
                                        right=df_Academic_Grades_Log,
                                        left_on=['Full Name & Title'],
                                        right_on='Student Name',
                                        how='left')
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop(columns=['Student ID', 'Student Name'])
df_Student_Records_2023_2024 = df_Student_Records_2023_2024.drop_duplicates(subset=['Student ID / Reg No'], keep='first')


df_Student_Records_2023_2024.to_excel('09-School-Data-Export-data-cleaning/School_Data_Export_2023-2023_cleaned.xlsx', index=False)

print(df_Student_Records_2023_2024['Full Name & Title'].duplicated().sum())
print(df_Student_Records_2023_2024['Status / Remarks'].value_counts())
print(df_Student_Records_2023_2024['Parent Email'].head(100))

print(len(df_Student_Records_2023_2024))
print(df_Student_Records_2023_2024.isna().sum())
print(df_Student_Records_2023_2024[['Parent Name', 'Parent Phone', 'Parent Email']].sample(20))