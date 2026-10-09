import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def catch_bad_lines(bad_line):
    # bad_line — это список элементов, как их распарсил Pandas
    print(f"Проблема в строке! Вот её содержимое: {bad_line}")
    return None # None означает "пропустить эту строку и идти дальше"

df = pd.read_csv('17-Eccomerce-Orders-data-cleaning/ecommerce_orders_raw.csv',
    engine='python',
    on_bad_lines=catch_bad_lines)

