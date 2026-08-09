import pandas as pd
import numpy as np

df_visits_data = pd.read_excel('hospital_data_raw.xlsx', sheet_name='Visits_Data')
df_patients_directory = pd.read_excel('hospital_data_raw.xlsx', sheet_name='Patients_Directory')

##################################################
#           SHEET 1: Visits_Data
##################################################

# Cleaning Patient_ID column
df_visits_data = df_visits_data.dropna(subset=['Patient_ID'])

# Cleaning Visit_Date column
df_visits_data = df_visits_data[df_visits_data['Visit_Date'] != 'INVALID_DATE']
df_visits_data = df_visits_data.dropna(subset=['Visit_Date'])

mask = df_visits_data['Visit_Date'].str.fullmatch(r'\d{8}')

df_visits_data.loc[mask, 'Visit_Date'] = pd.to_datetime(
    df_visits_data.loc[mask, 'Visit_Date'],
    format='%d%m%Y'
).dt.strftime('%Y-%m-%d')

df_visits_data['Visit_Date'] = pd.to_datetime(df_visits_data['Visit_Date'],
                                format='mixed')

# Cleaning Department column
df_visits_data['Department'] = df_visits_data['Department'].str.capitalize()
df_visits_data['Department'] = df_visits_data['Department'].str.replace({
    'Ortho': 'Orthopedia',
    'Orthopediapedics': 'Orthopedia',
    'Cardio': 'Cardiology',
    'Cardiologylogy': 'Cardiology',
    'Peds': 'Pediatria',
    'Pediatrics': 'Pediatria',
    'Neuro': 'Neurology',
    'Neurologylogy': 'Neurology',
    'Gen_Med': 'General Medicine',
    'General_medicine': 'General Medicine',
    'General medicine': 'General Medicine',
    'Gen Med': 'General Medicine',
    'Oncol': 'Oncology',
    'Oncologyogy': 'Oncology'
}, case=False)

# Cleaning Doctor_Name column
df_visits_data['Doctor_Name'] = df_visits_data['Doctor_Name'].fillna(value='Unknown')

# Cleaning Lab_Glucose_mgdL column
Q1_lab = df_visits_data['Lab_Glucose_mgdL'].quantile(0.25)
Q3_lab = df_visits_data['Lab_Glucose_mgdL'].quantile(0.75)

IQR_lab = Q3_lab - Q1_lab

upper_lab = Q3_lab + 1.5 * IQR_lab
lower_lab = Q1_lab - 1.5 * IQR_lab

df_visits_data['Lab_Glucose_mgdL'] = np.where(df_visits_data['Lab_Glucose_mgdL'] <= upper_lab,
                          df_visits_data['Lab_Glucose_mgdL'],
                          df_visits_data['Lab_Glucose_mgdL'].median())

df_visits_data['Lab_Glucose_mgdL'] = np.where(df_visits_data['Lab_Glucose_mgdL'] >= lower_lab,
                          df_visits_data['Lab_Glucose_mgdL'],
                          df_visits_data['Lab_Glucose_mgdL'].median())

# Cleaning Billing_Amount_USD column
Q1_USD = df_visits_data['Billing_Amount_USD'].quantile(0.25)
Q3_USD = df_visits_data['Billing_Amount_USD'].quantile(0.75)

IQR_USD = Q3_USD - Q1_USD

upper_USD = Q3_USD + 1.5 * IQR_USD
lower_USD = Q1_USD - 1.5 * IQR_USD

df_visits_data['Billing_Amount_USD'] = np.where(df_visits_data['Billing_Amount_USD'] <= upper_USD,
                          df_visits_data['Billing_Amount_USD'],
                          df_visits_data['Billing_Amount_USD'].median())

df_visits_data['Billing_Amount_USD'] = np.where(df_visits_data['Billing_Amount_USD'] >= lower_USD,
                          df_visits_data['Billing_Amount_USD'],
                          df_visits_data['Billing_Amount_USD'].median())

df_visits_data['Billing_Amount_USD'] = np.where(df_visits_data['Billing_Amount_USD'] > 0, df_visits_data['Billing_Amount_USD'], df_visits_data['Billing_Amount_USD'].median())

# Cleaning Status column
df_visits_data['Status'] = df_visits_data['Status'].str.strip()
df_visits_data['Status'] = df_visits_data['Status'].str.title()

##################################################
#           SHEET 2: Patients_Directory
##################################################

# Cleaning First_Name column
df_patients_directory['First_Name'] = df_patients_directory['First_Name'].str.strip()
df_patients_directory['First_Name'] = df_patients_directory['First_Name'].str.capitalize()

# Cleaning Last_Name column
df_patients_directory['Last_Name'] = df_patients_directory['Last_Name'].str.strip()
df_patients_directory['Last_Name'] = df_patients_directory['Last_Name'].str.capitalize()

# Cleaning Gender column
df_patients_directory['Gender'] = df_patients_directory['Gender'].str.strip()
df_patients_directory['Gender'] = df_patients_directory['Gender'].str.capitalize()
df_patients_directory['Gender'] = df_patients_directory['Gender'].replace({
    'M': 'Male',
    'F': 'Female'
})
df_patients_directory['Gender'] = df_patients_directory['Gender'].fillna(value='Unknown')

# Cleaning Contact_Details column

df_patients_directory['Phone'] = df_patients_directory['Contact_Details'].str.extract(r'(?:TEL:|Phone:|Ph:)\s*([+\-\d\(\)]+)')
df_patients_directory['Phone'] = df_patients_directory['Phone'].str.replace(r'[^\d+]', '', regex=True)
df_patients_directory['Phone'] = df_patients_directory['Phone'].fillna(value='Unknown')

df_patients_directory['Email'] = df_patients_directory['Contact_Details'].str.extract(r'([\w+\.\_\-]+@[\w+\.\_\-]+)')
df_patients_directory['Email'] = df_patients_directory['Email'].str.strip()
df_patients_directory['Email'] = df_patients_directory['Email'].fillna(value='example@example.com')

df_patients_directory = df_patients_directory.drop(columns=['Contact_Details'])

# Merging
df_visits_data = df_visits_data.drop_duplicates(subset=['Visit_ID'])
df_visits_data['Visit_Date'] = df_visits_data['Visit_Date'].dt.strftime('%Y-%m-%d')
df_patients_directory = df_patients_directory.drop_duplicates(subset=['Patient_ID'])
final_df = pd.merge(left=df_visits_data, right=df_patients_directory, on='Patient_ID', how='left')
final_df = final_df.dropna(subset=['First_Name'])

# Exporting
final_df.to_excel('hospital_data_cleaned.xlsx', index=False)
