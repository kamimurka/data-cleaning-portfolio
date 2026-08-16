import pandas as pd
import numpy as np

df_appointments_export: pd.DataFrame = pd.read_excel('Clinic_Export_Q1_Q2_2024.xlsx', engine='openpyxl', sheet_name='Appointments_Export_2024')
df_doctor_directory: pd.DataFrame = pd.read_excel('Clinic_Export_Q1_Q2_2024.xlsx', engine='openpyxl', sheet_name='Doctor_Directory')

###################################
# SHEET 1: Appointments_Export_2024
###################################

# Deleting duplicates
df_appointments_export = df_appointments_export.drop_duplicates(subset=['Patient_Ref', 'Visit_Date', 'Doctor_ID'],
                                                                    keep='first')

# Creating new columns from Patient_Details
df_appointments_export['Patient_Details'] = df_appointments_export['Patient_Details'].str.strip().str.title()
df_appointments_export['Patient_Name'] = df_appointments_export['Patient_Details'].str.extract(r'([\w\s]+)\(')
df_appointments_export['Patient_DOB'] = df_appointments_export['Patient_Details'].str.extract(r'Dob:\s?([\d\-]+)\)')
df_appointments_export['Patient_Phone'] = (
    df_appointments_export['Patient_Details']
    .str.extract(r'\)\s*-\s*(?:Ph:\s*)?(.+)$')
)
df_appointments_export['Patient_Phone'] = df_appointments_export['Patient_Phone'].str.replace(r'[()\s\-\.]',
                                                                                              '',
                                                                                              regex=True)
df_appointments_export['Patient_Phone'] = [cell if cell.startswith('+1')
                                           else '+' + cell if cell.startswith('1')
                                           else '+1' + cell
                                           for cell in df_appointments_export['Patient_Phone']]

# Cleaning Visit_Date column
df_appointments_export['Visit_Date'] = pd.to_datetime(df_appointments_export['Visit_Date'],
                                                      format='mixed',
                                                      errors='coerce')

# Cleaning Doctor_ID
df_appointments_export['Doctor_ID'] = (
    df_appointments_export['Doctor_ID']
    .str.strip()
    .str.upper()
    .fillna('UNKNOWN')
    .str.replace('-', '', regex=False)
)

# Cleaning Primary_Diagnosis
diagnosis_mapping = {
    'Migraine without aura': 'Migraine',
    'Essential (primary) hypertension': 'Hypertension',
    'Asthma, unspecified': 'Asthma',
    'Generalized anxiety disorder': 'Anxiety',
    'Type 2 diabetes mellitus': 'Type 2 diabetes',
    'T2dm': 'Type 2 diabetes',
    'General checkup': 'Checkup',
    'Routine medical examination': 'Checkup',
    'Knee pain / osteoarthritis': 'Osteoarthritis of knee',
    'Low back pain': 'Back pain - lower',
    'Lumbar pain': 'Back pain - lower',
    'Uri': 'Upper respiratory infection',
    'Acute upper respiratory infection': 'Upper respiratory infection'
}
df_appointments_export['Primary_Diagnosis'] = (df_appointments_export['Primary_Diagnosis']
    .str.strip()
    .str.capitalize()
    .replace(diagnosis_mapping)
    .fillna('Unspecified')
)

# Cleaning Service_Fee & IQR
df_appointments_export['Service_Fee'] = (df_appointments_export['Service_Fee']
    .astype(str)
    .str.replace('$', '', regex=False)
    .astype(float)
)
Q1 = df_appointments_export['Service_Fee'].quantile(0.25)
Q3 = df_appointments_export['Service_Fee'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
lower = Q1 - 1.5 * IQR
median = df_appointments_export['Service_Fee'].median()
df_appointments_export['Service_Fee'] = np.where(df_appointments_export['Service_Fee'].between(lower, upper),
                                                 df_appointments_export['Service_Fee'],
                                                 median)
df_appointments_export['Service_Fee'] = np.where(df_appointments_export['Service_Fee'] >= 0,
                                                 df_appointments_export['Service_Fee'],
                                                 median)

# Cleaning Payment_Status column
df_appointments_export['Payment_Status'] = (df_appointments_export['Payment_Status']
                                            .str.strip()
                                            .str.capitalize()
                                            .fillna('UNKNOWN')
)
payment_status_mapping = {
    'Cleared': 'Paid',
    'Ins. pending': 'Pending',
    'Insurance processing': 'Pending',
    'Overdue': 'Unpaid'
}
df_appointments_export['Payment_Status'] = df_appointments_export['Payment_Status'].replace(payment_status_mapping)

# Cleaning Contact_Notes
visit_status_mapping = {
    'First visit': 'First visit',
    'Patient arrived 15 mins late': 'Arrived late',
}
tasks_reminders_mapping = {
    'Call back regarding lab results': 'Call back regarding lab results',
    'Follow-up in 3 months': 'Follow-up in 3 months',
    'Referred to specialist': 'Referred to specialist',
    'Requested email receipt': 'Requested email receipt',
}
df_appointments_export['Visit_Status'] = df_appointments_export['Contact_Notes'].map(visit_status_mapping)
df_appointments_export['Tasks_Reminder'] = df_appointments_export['Contact_Notes'].map(tasks_reminders_mapping)

###################################
# SHEET 2: Doctor_Directory
###################################

# Cleaning Full_Name
df_doctor_directory['Full_Name'] = df_doctor_directory['Full_Name'].str.strip().str.title()
# Exporting
df_appointments_export = df_appointments_export.drop(columns=['Patient_Details', 'Contact_Notes'])
with pd.ExcelWriter('Clinic_Export_Q1_Q2_2024_cleaned.xlsx', engine='openpyxl') as writer:
    df_appointments_export.to_excel(writer, sheet_name='Appointments_Export_2024', index=False)
    df_doctor_directory.to_excel(writer, sheet_name='Doctor_Directory', index=False)