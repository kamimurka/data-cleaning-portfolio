import pandas as pd

df_1 = pd.read_csv('16-3-contacts-duplication/1_customers.csv')
df_2 = pd.read_csv('16-3-contacts-duplication/2_order_lines.csv')
df_3 = pd.read_csv('16-3-contacts-duplication/3_contacts.csv')

# df_1
df_1 = df_1.drop_duplicates(subset=['email'])

df_1.to_csv("16-3-contacts-duplication/1_customers_cleaned.csv", index=False)

# df_2
df_2 = df_2.drop_duplicates()
df_2 = df_2.sort_values(by='updated_at')
df_2 = df_2.drop_duplicates(subset=['order_id', 'product_sku'], keep='last')

df_2.to_csv('16-3-contacts-duplication/2_order_lines_cleaned.csv', index=False)

# df_3
df_3 = df_3.sort_values("created_at", ascending=False).groupby("email", as_index=False).first()
df_3 = df_3.sort_values("created_at", ascending=False).groupby("phone", as_index=False).first()
print(df_3.shape)

print(df_3.shape, df_3["job_title"].isna().sum(), df_3.duplicated(subset=["email"]).sum(), df_3.duplicated(subset=["phone"]).sum())