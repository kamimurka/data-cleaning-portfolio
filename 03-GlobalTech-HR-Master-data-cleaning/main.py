import pandas as pd
import numpy as np
import re

# Preparing
pd.set_option('display.max_columns', None)
df_employee_records = pd.read_excel('GlobalTech_HR_Master_Export_2026.xlsx', sheet_name='Employee_Records')
df_dept_reference = pd.read_excel('GlobalTech_HR_Master_Export_2026.xlsx', sheet_name='Dept_Reference')

# Cleaning Employee_ID column
df_employee_records['Employee_ID'] = df_employee_records['Employee_ID'].str.strip()
df_employee_records['Employee_ID'] = df_employee_records['Employee_ID'].str.upper()
df_employee_records['Employee_ID'] = df_employee_records['Employee_ID'].str.replace('_','-')
df_employee_records = df_employee_records.drop_duplicates(subset=['Employee_ID'])

# Cleaning First_Name column
df_employee_records['First_Name'] = df_employee_records['First_Name'].str.strip()
df_employee_records['First_Name'] = df_employee_records['First_Name'].str.capitalize()

# Cleaning Last_Name column
df_employee_records['Last_Name'] = df_employee_records['Last_Name'].str.strip()
df_employee_records['Last_Name'] = df_employee_records['Last_Name'].str.capitalize()

# Creating Email & Phone & Adress columns
df_employee_records['Email'] = df_employee_records['Contact_Details'].str.extract(r'Email:\s*([\w@#_\-\+\.]+)', flags=re.IGNORECASE)
df_employee_records['Email'] = df_employee_records['Email'].str.replace({'#': '.',
                                                                         'at': '@'})
df_employee_records['Email'] = df_employee_records['Email'].fillna(value='Not Provided')

df_employee_records['Phone'] = df_employee_records['Contact_Details'].str.extract(r'(?:Phone:|Tel:)\s*([\d\-\(\)\_\.\+\s{1}]+)')
df_employee_records['Phone'] = df_employee_records['Phone'].str.replace(r'[\-\.\(\)\s]', '', regex=True)
df_employee_records['Phone'] = df_employee_records['Phone'].fillna(value='Not Provided')
df_employee_records['Phone'] = [
    cell if cell.startswith('+1')
    else '+' + cell if cell.startswith('1')
    else '+1' + cell
    for cell in df_employee_records['Phone']
]
df_employee_records['Address'] = df_employee_records['Contact_Details'].str.extract(r'(?:Loc:|Addr:)\s*([\w\,\s]+)')
df_employee_records['Address'] = df_employee_records['Address'].str.strip()

# Cleaning Department column & Merging
df_employee_records['Department'] = df_employee_records['Department'].str.strip()
df_employee_records['Department'] = df_employee_records['Department'].str.title()

df_employee_records['Department'] = df_employee_records['Department'].replace({
    'H.R.': 'Human Resources',
    'Hr': 'Human Resources',
    'Finance & Accounting': 'Finance',
    'Fin': 'Finance',
    'Mktg': 'Marketing',
    'Sales Dept': 'Sales',
    'Software Engineering': 'Engineering',
    'Eng.': 'Engineering'
})

df_employee_records = pd.merge(left=df_employee_records,
                               right=df_dept_reference,
                               left_on='Department',
                               right_on='Department_Name',
                               how='left').drop(columns=['Department_Name'])

# Cleaning Annual_Salary column
Q1 = df_employee_records['Annual_Salary'].quantile(0.25)
Q3 = df_employee_records['Annual_Salary'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
lower = Q1 - 1.5 * IQR
median = df_employee_records['Annual_Salary'].median()

df_employee_records['Annual_Salary'] = df_employee_records['Annual_Salary'].fillna(median)
df_employee_records['Annual_Salary'] = np.where(df_employee_records['Annual_Salary'].between(lower, upper),
                                                df_employee_records['Annual_Salary'],
                                                median)

# Cleaning Hire_Data column
mask = df_employee_records['Hire_Date'].str.fullmatch(r'\d{8}')
df_employee_records.loc[mask, 'Hire_Date'] = pd.to_datetime(df_employee_records.loc[mask, 'Hire_Date'],
                                                             format='%d%m%Y').dt.strftime('%d-%m-%Y')
df_employee_records['Hire_Date'] = pd.to_datetime(df_employee_records['Hire_Date'],
                                                  format='mixed')

# Cleaning Employment_Status column
df_employee_records['Employment_Status'] = df_employee_records['Employment_Status'].str.strip()
df_employee_records['Employment_Status'] = df_employee_records['Employment_Status'].replace({
    'full_time': 'Full-Time',
    'full time': 'Full-Time',
    'FT': 'Full-Time',
    'contract': 'Contractor',
    'PT': 'Part-Time',
    'part time': 'Part-Time',
    'ACTIVE': 'Active'
})

# Exporting
df_employee_records = df_employee_records.drop(columns=['Contact_Details'])
df_employee_records['Hire_Date'] = df_employee_records['Hire_Date'].dt.strftime('%d-%m-%Y')
df_employee_records['Phone'] = df_employee_records['Phone'].astype(str)
df_employee_records.to_excel('GlobalTech_HR_Master_Export_2026_cleaned.xlsx', index=False)
