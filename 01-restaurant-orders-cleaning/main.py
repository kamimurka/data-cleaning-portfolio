import pandas as pd
import re
pd.set_option('display.max_columns', None)
df_orders_data = pd.read_excel('restaurant_orders.xlsx', sheet_name='Orders_Data')
df_customer_directory = pd.read_excel('restaurant_orders.xlsx', sheet_name='Customer_Directory')
print('-'*200)

############################################################
# SHEET 1 - Orders_Data
############################################################

# Cleaning Order_ID column
df_orders_data = df_orders_data.drop_duplicates(subset=['Order_ID'], keep='first')
df_orders_data

# Cleaning Customer_Ref column
df_orders_data['Customer_Ref'] = df_orders_data['Customer_Ref'].str.strip()
df_orders_data['Customer_Ref'] = df_orders_data['Customer_Ref'].str.upper()
df_orders_data['Customer_Ref'] = df_orders_data['Customer_Ref'].fillna(value='GUEST')

# Cleaning Order_Timestamp column
mask = df_orders_data['Order_Timestamp'].str.fullmatch(r'\d{8}')

df_orders_data.loc[mask, 'Order_Timestamp'] = pd.to_datetime(
    df_orders_data.loc[mask, 'Order_Timestamp'],
    format='%d%m%Y'
).dt.strftime('%Y-%m-%d')

df_orders_data['Order_Timestamp'] = pd.to_datetime(df_orders_data['Order_Timestamp'],
                                                   format='mixed').dt.strftime('%Y-%m-%d %H:%M:%S')

# Cleaning Item_and_Contact_Info column
df_orders_data['QTY'] = df_orders_data['Item_and_Contact_Info'].str.extract(r'(?:QTY:\s?|x|x\[)(\d+)')
df_orders_data['Email'] = df_orders_data['Item_and_Contact_Info'].str.extract(r'([\w.+-]+@[\w.-]+\.\w+)')
df_orders_data['Item_and_Contact_Info'] = df_orders_data['Item_and_Contact_Info'].str.replace(r'ITEM:\s?|ORD:\s?', '', regex=True, case=False)
df_orders_data['Contact'] = df_orders_data['Item_and_Contact_Info'].str.extract(r'(?:Phone|CONTACT|Tel):\s*([\d\+\-\.\(\)\s]+)',
                                                                                flags=re.IGNORECASE)
df_orders_data['Contact'] = df_orders_data['Contact'].str.replace(r'[^\d+]', '', regex=True)
df_orders_data['Contact'] = df_orders_data['Contact'].fillna(value='')
df_orders_data['Contact'] = [cell if cell.startswith('+1') else '+1' + cell for cell in df_orders_data['Contact']]
df_orders_data['Item'] = df_orders_data['Item_and_Contact_Info'].str.extract(r'(.+?)\s?(?:x\d+|X\d+|\[x\d+|\s?\|\s?QTY:\s?\d+)')
df_orders_data = df_orders_data.drop(columns=['Item_and_Contact_Info'])

# Cleaning Total_Amount column
df_orders_data = df_orders_data[df_orders_data['Total_Amount'] > 0]
Q1 = df_orders_data['Total_Amount'].quantile(0.25)
Q3 = df_orders_data['Total_Amount'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 1.5 * IQR
lower = Q1 - 1.5 * IQR
df_orders_data = df_orders_data[(df_orders_data['Total_Amount'] >= lower) & (df_orders_data['Total_Amount'] <= upper)]

# Cleaning Delivery_Status column
df_orders_data['Delivery_Status'] = df_orders_data['Delivery_Status'].str.strip()
df_orders_data['Delivery_Status'] = df_orders_data['Delivery_Status'].str.title()
df_orders_data['Delivery_Status'] = df_orders_data['Delivery_Status'].str.replace(r'In.Transit', 
                                                                                  'In Transit',
                                                                                  regex=True, case=False)
df_orders_data['Delivery_Status'] = df_orders_data['Delivery_Status'].str.replace('Cancelled', 'Canceled')
df_orders_data['Delivery_Status'] = df_orders_data['Delivery_Status'].str.replace('Pending', 'In Transit')

# Cleaning Payment_Method column
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.strip()
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.title()
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('paypal', 'PayPal', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('CC', 'Credit Card', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('Apple_Pay', 'Apple Pay', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('Credit_Card', 'Credit Card', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('Card', 'Credit Card', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].str.replace('Credit Credit Card', 'Credit Card', case=False)
df_orders_data['Payment_Method'] = df_orders_data['Payment_Method'].fillna(value='Unknown')

# Cleaning Branch_Name column
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.strip()
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.title()
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.replace(r'westside.hub', 'Westside Hub', case=False, regex=True)
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.replace(r'uptown.bistro', 'Uptown Bistro', case=False, regex=True)
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.replace(r'downtown.cafe', 'Downtown Cafe', case=False, regex=True)
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.replace(r'downtown', 'Downtown Cafe', case=False, regex=True)
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].str.replace(r'downtown cafe cafe', 'Downtown Cafe', case=False, regex=True)
df_orders_data['Branch_Name'] = df_orders_data['Branch_Name'].fillna(value='Unknown')

############################################################
# SHEET 2 - Customer_Directory
############################################################

# Cleaning Customer_Full_Name column
df_customer_directory['Customer_Full_Name'] = df_customer_directory['Customer_Full_Name'].str.strip()
df_customer_directory['Customer_Full_Name'] = df_customer_directory['Customer_Full_Name'].str.title()

# Cleaning Loyalty_Tier column
df_customer_directory['Loyalty_Tier'] = df_customer_directory['Loyalty_Tier'].fillna(value='Bronze')
df_customer_directory['Loyalty_Tier'] = df_customer_directory['Loyalty_Tier'].str.strip()
df_customer_directory['Loyalty_Tier'] = df_customer_directory['Loyalty_Tier'].str.capitalize()
df_customer_directory['Loyalty_Tier'] = df_customer_directory['Loyalty_Tier'].str.replace('Vip', 'VIP', case=False)

# Cleaning Registration_Date column
df_customer_directory['Registration_Date'] = pd.to_datetime(df_customer_directory['Registration_Date'],
                                                            format='mixed').dt.strftime('%Y-%m-%d %H:%M:%S')
# Merging Two Dataframes
final_df = pd.merge(left=df_orders_data, right=df_customer_directory, left_on='Customer_Ref', right_on='Cust_ID', how='left')
final_df['Loyalty_Tier'] = final_df['Loyalty_Tier'].fillna('Bronze')
final_df = final_df.drop(columns=['Cust_ID'])

# Exporting
final_df.to_excel("restaurant_orders_cleaned.xlsx", index=False)
