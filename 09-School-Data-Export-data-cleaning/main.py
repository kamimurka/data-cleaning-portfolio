import pandas as pd
import re
import numpy as np

pd.set_option('display.max_rows', None)

df_Student_Records_2023_2024 = pd.read_excel('09-School-Data-Export-data-cleaning/School_Data_Export_2023-2024_Raw.xlsx',
                                           engine='openpyxl',
                                           sheet_name='Student_Records_2023-2024')

# df_Academic_Grades_Log = pd.read_excel('09-School-Data-Export-data-cleaning/Academic_Grades_Log.xlsx',
#                                        engine='openpyxl',
#                                        sheet_name='Academic_Grades_Log')

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
    format='mixed').dt.strftime('%d-%m-%Y')

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
                                               else 'Unknown Student' if cell.startswith('Contact')
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




print('-'*120)
print(df_Student_Records_2023_2024[['Student ID / Reg No', 'Full Name & Title']].head(130))
print('-'*120)
print(df_Student_Records_2023_2024['DOB / Date of Birth'].head(130))
print('-'*120)
print(df_Student_Records_2023_2024['Grade/Level'].value_counts())
print(df_Student_Records_2023_2024[['Parent Name', 'Relationship']].head(130))