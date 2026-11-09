import pandas as pd
import re
import ftfy
from datetime import datetime, timedelta
import phonenumbers
import rapidfuzz

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('19-crm-contacts-data-cleaning/crm_contacts_raw.csv', engine='pyarrow')


# Cleaning Lead ID column
df['Lead ID'] = df['Lead ID'].str.strip()

def clean_lead_id(cell):
    if cell is None:
        return None
    s = str(cell).strip().upper()

    if re.fullmatch(r"[A-Z]-\d{5}", s):
        return s

    m = re.fullmatch(r"([A-Z])(\d{5})", s)
    if m:
        return f"{m[1]}-{m[2]}"

    if re.fullmatch(r"\d{4}", s):
        return f"L-0{s}"

    m = re.fullmatch(r"[A-Z]{4}(\d{4})", s)
    if m:
        return f"L-0{m[1]}"

    return None

df["Lead ID"] = df["Lead ID"].apply(clean_lead_id).replace('NAN', pd.NA)

# Cleaning Full Name column
df['Full Name'] = (df['Full Name']
    .str.strip()
    .str.replace(
        {
            r'\s{2,}': ' ',
            r'\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\b\.?\s*': '',
            r'[\s,]+\b(?:Jr|Sr|II|III|IV|PhD|MD|Esq)\b\.?\s*$': ''
        }
    , regex=True))

def safe_fix(x):
    if isinstance(x, str):
        return ftfy.fix_text(x)
    return x

df['Full Name'] = df['Full Name'].apply(safe_fix)

def main_clean_name(cell):
    if pd.isna(cell):
        return pd.NA
    cell = cell.strip()
    if cell == '':
        return pd.NA
    
    # Swap
    if ',' in cell:
        parts = cell.split(',')
        last_name, first_name = parts[0].strip(), parts[1].strip()
        cell = f"{first_name} {last_name}"
    return cell.title()    

df['Full Name'] = df['Full Name'].apply(main_clean_name)

junk_names = {"test", "asdf", "abcd", "qwerty",
               "n/a", "none", "unknown", "xxx",
               'test test', 'john doe', 'full name'
}

mask = df["Full Name"].str.lower().str.strip().isin(junk_names)
df.loc[mask, "Full Name"] = pd.NA

particles = ["van", "von", "der", "den", "de", "la", "le", "di", "da", "del", "du"]
pattern = r"(?<=\s)(" + "|".join(p.title() for p in particles) + r")(?=\s)"

df["Full Name"] = df["Full Name"].str.strip().str.title()
df["Full Name"] = df["Full Name"].str.replace(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), regex=True)
df["Full Name"] = df["Full Name"].str.replace(pattern, lambda m: m.group(1).lower(), regex=True)

# Cleaning Email column
df['Email'] = (df['Email']
    .str.strip()
    .str.lower() 
    .str.replace({
        r';.*$': '',
        r'[^a-zA-Z0-9._%+-@]': '',
        r'\sat\s': '@',
        r'[<>]': '',
        'con': 'com',
    }, regex=True
    ).str.strip().replace({'': pd.NA, r'^\s+$': pd.NA})
)

parts = df["Email"].str.split("@", expand=True)
local, dom = parts[0], parts[1].str.split(".").str[0]

bad = (
    (local == dom)
    | (local.str.len() < 3)            
    | local.str.contains(r"no.?email|none|^no$|test|fake|dummy|asdf|null|n/?a$", regex=True)
    | dom.str.contains(r"^(none|test|fake|dummy|example|null)$", regex=True)
)

df.loc[bad, "Email"] = None

# Cleaning Company column
df['Company'] = (df['Company'].str.strip())
df.loc[df["Company"].isin(["", "-", "?", 'company']), "Company"] = pd.NA

key = (
    df["Company"]
    .str.lower()
    .str.replace({
        r"[.,()]": " ",
        r"^\s*the\b": "",
        r"\s+formerly\b.*$": "",
        r"\b(llc|gmbh|corp|corporation|inc|incorporated|company|co|ltd|plc|pty)\b": "",  # суффиксы -> убрать
        r"\s+": " ",
    }, regex=True)
    .str.strip()
)
df["Company"] = key.str.title().replace("", pd.NA)

# Cleaning Job Title column
df['Job Title'] = (df['Job Title']
    .str.strip()
    .str.lower()
)

job_title_mapping = {
    'data analyst': 'Data Analyst',
    'analyst, data': 'Data Analyst',

    'hr manager': 'HR Manager',
    'human resources manager': 'HR Manager',
    'h.r. manager': 'HR Manager',

    'ceo': 'CEO',
    'c.e.o.': 'CEO',
    'chief executive officer': 'CEO',
    'founder & ceo': 'Founder & CEO',

    'marketing manager': 'Marketing Manager',
    'marketing mgr.': 'Marketing Manager',
    'marketing mgr': 'Marketing Manager',
    'mktg manager': 'Marketing Manager',

    'account executive': 'Account Executive',
    'acct executive': 'Account Executive',
    'account exec': 'Account Executive',
    'ae': 'Account Executive',

    'software engineer': 'Software Engineer',
    'sw engineer': 'Software Engineer',
    'software eng.': 'Software Engineer',

    'operations director': 'Director of Operations',
    'director, operations': 'Director of Operations',
    'director of operations': 'Director of Operations',
    'ops director': 'Director of Operations',

    'vp of sales': 'VP of Sales',
    'vp, sales': 'VP of Sales',
    'vice president of sales': 'VP of Sales',
    'v.p. sales': 'VP of Sales',
    'vp sales': 'VP of Sales',
}

df['Job Title'] = df['Job Title'].map(job_title_mapping)

# Cleaning Country column
df['Country'] = (df['Country']
    .str.strip()
    .str.lower()
)

country_map = {
    "united states": "United States",
    "untied states": "United States",
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "united states of america": "United States",

    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "gb": "United Kingdom",
    "england": "United Kingdom",

    "australia": "Australia",
    "au": "Australia",
    "aus": "Australia",

    "germany": "Germany",
    "germny": "Germany",
    "deutschland": "Germany",
    "de": "Germany",

    "canada": "Canada",
    "canda": "Canada",
    "can": "Canada",
    "ca": "Canada",
}

df['Country'] = df['Country'].map(country_map)

country_to_code = {
    "United States": "US",
    "United Kingdom": "GB",
    "Australia": "AU",
    "Germany": "DE",
    "Canada": "CA",
}

df['country_code'] = df['Country'].map(country_to_code)

# Cleaning Phone column
df['Phone'] = (df['Phone']
    .str.strip()
    .replace({
        r'^\s+$': pd.NA,
        '': pd.NA
    }, regex=True)
)

df.loc[df['Phone'].isin(['', '-', '?']), 'Phone'] = pd.NA

def clean_phone(row):
    if pd.isna(row['Phone']) or pd.isna(row['country_code']):
        return pd.NA
    number = str(row['Phone']).strip()
    country_code = row['country_code']
    try:
        phone = phonenumbers.parse(number, country_code)
        if phonenumbers.is_valid_number(phone):
            return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return pd.NA

df['Phone'] = df.apply(clean_phone, axis=1)

# Cleaning Signup Date column
df['Signup Date'] = df['Signup Date'].str.strip()
is_garbage = df['Signup Date'].astype(str).str.fullmatch(r"[A-Za-z ]+") & df['Signup Date'].notna()
df.loc[is_garbage, 'Signup Date'] = pd.NA

rules = [
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    (r"[A-Za-z]{3} \d{1,2}, \d{4}", "%b %d, %Y"),
    (r"\d{1,2} [A-Za-z]{3} \d{4}", "%d %b %Y"),
    (r"\d{2}-[A-Za-z]{3}-\d{2}", "%d-%b-%y"),
    (r"\d{2}-\d{2}-\d{2}", "%m-%d-%y"),
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
    (r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
]

def parse_date(v):
    if pd.isna(v):
        return None, False
    s = str(v).strip()
    s = re.sub(r"\s+\d{2}:\d{2}(:\d{2})?(\s*[APap][Mm])?$", "", s)

    if re.fullmatch(r"\d{5}", s):
        d = datetime(1899, 12, 30) + timedelta(days=int(s))
        return d.strftime("%Y-%m-%d"), False

    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        a, b = int(s[:2]), int(s[3:5])
        fmt = "%d/%m/%Y" if a > 12 else "%m/%d/%Y"
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d"), (a <= 12 and b <= 12)
        except ValueError:
            return None, False

    for pattern, fmt in rules:
        if re.fullmatch(pattern, s):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d"), False
            except ValueError:
                return None, False

    return None, False

res = df["Signup Date"].apply(parse_date)

df["Signup Date"] = res.str[0]
df["ambiguous"] = res.str[1]

junk = ["-", "?", "0000-00-00", "2022-00-10", "31/04/2022", ""]
df.loc[df["Signup Date"].astype(str).str.strip().isin(junk), "Signup Date"] = pd.NA

df.loc[df["Signup Date"].str[:4] < "2000", "Signup Date"] = pd.NA

# Cleaning Last Contact column
df["Last Contact"] = df["Last Contact"].str.strip()
is_garbage = df["Last Contact"].astype(str).str.fullmatch(r"[A-Za-z ]+") & df["Last Contact"].notna()
df['Last Contact'] = df['Last Contact'].replace({
    '': pd.NA,
    '?': pd.NA,
    '-': pd.NA
})

df.loc[is_garbage, "Last Contact"] = pd.NA

df["Last Contact"] = df["Last Contact"].apply(lambda v: parse_date(v)[0])



# Cleaning Date of Birth column
df["Date of Birth"] = df["Date of Birth"].str.strip()
df.loc[df["Date of Birth"].isin(["", "-", "?"]) | (df["Date of Birth"].astype(str).str.fullmatch(r"[A-Za-z ]+") & df["Date of Birth"].notna()), "Date of Birth"] = pd.NA

df["Date of Birth"] = df["Date of Birth"].apply(lambda v: parse_date(v)[0])
df.loc[(df["Date of Birth"] < "1920") | (df["Date of Birth"] > "2026-05-03"), "Date of Birth"] = pd.NA


df["Date of Birth"] = df["Date of Birth"].str.strip().str.replace({
    r'[A-Za-z]': 'X',
    r'[0-9]': '0'
}, regex=True)










# Cleaning Lead Source column
lead_source_mapping = {
    'Linked In': 'LinkedIn',
    'Linkedin': 'LinkedIn',
    'linkedin': 'LinkedIn',
    'LINKEDIN': 'LinkedIn',

    'cold email': 'Cold Email',
    'Cold email': 'Cold Email',

    'partner referral': 'Partner Referral',

    'Trade-show': 'Trade Show',
    'trade show': 'Trade Show',
    'Tradeshow': 'Trade Show',
    'tradeshow': 'Trade Show',

    'Outbound': 'Outbound',
    'outbound email': 'Outbound Email',
}

df['Lead Source'] = df['Lead Source'].map(lead_source_mapping)

# ...

# Cleaning Status column
status_mapping = {
    'Contacted': 'Contacted',
    'contacted': 'Contacted',

    'Qualified': 'Qualified',
    'qualified': 'Qualified',
    'QUALIFIED': 'Qualified',
    'Qualifed': 'Qualified',

    'New': 'New',
    'NEW': 'New',
    'new': 'New',
    'New Lead': 'New',

    'Lost': 'Lost',
    'LOST': 'Lost',
    'lost': 'Lost',
    'Closed Lost': 'Lost',

    'Customer': 'Customer',
    'CUSTOMER': 'Customer',
    'customer': 'Customer',

    'Unsubscribed': 'Unsubscribed',
    'unsubscribed': 'Unsubscribed',
    'Unsub': 'Unsubscribed',
    'opted out': 'Unsubscribed',

    'In Contact': 'Contacted',

    'SQL': 'SQL',

    'Won': 'Won',
    'Closed Won': 'Won',
}

df['Status'] = df['Status'].map(status_mapping)

# Cleaning Last Updated column
df = df.rename(columns={'Last Updated ': 'Last Updated'})
df['Last Updated'] = df['Last Updated'].str.strip().replace('Last Updated', pd.NA)

def to_iso(value):
    if pd.isna(value):
        return value

    s = str(value).strip()
    formats = (
        '%Y-%m-%d %H:%M:%S',     # 2022-03-18 12:23:00
        '%Y-%m-%dT%H:%M:%S',     # 2022-03-18T12:23:00
        '%Y-%m-%dT%H:%M:%SZ',    # 2022-03-18T12:23:00Z (UTC)
        '%m/%d/%Y %I:%M %p',     # 03/18/2022 12:23 PM (MDY)
        '%m/%d/%Y %I:%M:%S %p',  # 03/18/2022 12:23:00 PM
    )

    for fmt in formats:
        try:
            return pd.to_datetime(s, format=fmt).strftime('%Y-%m-%dT%H:%M:%S')
        except ValueError:
            continue

df['Last Updated'] = df['Last Updated'].apply(to_iso)
df['Last Updated'] = pd.to_datetime(df['Last Updated'], errors='coerce')

print(df['Last Updated'].head(300))

print(df['Last Updated'].dtype)


# Finalizing
df = df.drop(['country_code'], axis=1)