import re
from pathlib import Path
import ftfy
import pandas as pd
import numpy as np
import phonenumbers
from datetime import datetime, timedelta
import unicodedata

csv_path = Path(__file__).resolve().parent / "marathon_registrations_raw.csv"
df = pd.read_csv(csv_path)


# ── Cleaning Registration ID column ──
def normalize_registration_id(value):
    if pd.isna(value):
        return pd.NA

    match = re.fullmatch(
        r"(?:MAR25[- ]?)?(\d{5})",
        str(value).strip(),
        flags=re.IGNORECASE,
    )
    if match:
        return f"MAR25-{match.group(1)}"
    return pd.NA


original_ids = df["Registration ID"]
normalized_ids = original_ids.apply(normalize_registration_id)
missing_ids = original_ids.isna() | original_ids.astype("string").str.strip().eq("")
junk_rows = ~missing_ids & normalized_ids.isna()

df["Registration ID"] = normalized_ids
df = df.drop(index=df.index[junk_rows])


# ── Cleaning Full Name column ──
NAME_PLACEHOLDERS = {"xxx", "runner", "unknown", "asdf", "??", "?? ???"}
NAME_PARTICLES = {"bin", "da", "de", "del", "den", "der", "di", "do", "dos", "du", "della", "delle", "des", "op", "ter", "van", "von"}
full_name_before = df["Full Name"].copy()


def clean_full_name(value):
    if pd.isna(value):
        return pd.NA

    name = re.sub(r"\s+", " ", ftfy.fix_text(str(value))).strip()
    if not name or name.casefold() in NAME_PLACEHOLDERS:
        return pd.NA

    name = re.sub(r"^(?:Mr|Mrs|Ms|Miss|Dr|Prof|Sr|Sra|Herr|Frau)\.?\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+(?:PhD|M\.?D\.?|MBA|Jr\.?|Sr\.?|II|III|IV)$", "", name, flags=re.IGNORECASE)

    if "," in name:
        surname, given_names = name.split(",", 1)
        name = f"{given_names.strip()} {surname.strip()}"

    words = []
    for word in name.split():
        word = re.sub(
            r"(?<=[a-zà-öø-ÿ])(?=(?:de|del|da|do|dos|op|ter|van|von|bin)[A-Z])",
            " ",
            word,
        )
        word = re.sub(
            r"(?<!Mc)(?<!Mac)(?<=[a-zà-öø-ÿ])(?=[A-Z][a-zà-öø-ÿ])",
            " ",
            word,
        )
        words.extend(word.split())

    words = [word.title() for word in words]
    for index, word in enumerate(words):
        if index > 0 and word.casefold() in NAME_PARTICLES:
            words[index] = word.casefold()
        elif index > 0 and word.casefold() == "la" and words[index - 1].casefold() in NAME_PARTICLES:
            words[index] = word.casefold()
        elif word.casefold().startswith("mc") and len(word) > 2:
            words[index] = "Mc" + word[2:].lower().capitalize()
        elif word.casefold().startswith("mac") and len(word) > 3:
            words[index] = "Mac" + word[3:].lower().capitalize()

    return " ".join(words)


df["Full Name"] = df["Full Name"].apply(clean_full_name)


# ── Cleaning Email column ──
PLACEHOLDERS = {"not provided", "-", "?", "n/a", "na", "none", "null", "nan", "unknown", "no email", "no"}
FORBIDDEN = re.compile(r"[^a-z0-9._%+\-@]")
STRICT = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)+$")
AT_WORD = re.compile(r"\s+at\s+")

DOMAIN_FIX = {
    "gmial.com": "gmail.com", "gmail.con": "gmail.com", "yaho.com": "yahoo.com",
    "iclod.com": "icloud.com", "icloud.con": "icloud.com", "yahoo.con": "yahoo.com",
    "hotmail.con": "hotmail.com", "live.con": "live.com", "outlok.com": "outlook.com",
    "hotmal.com": "hotmail.com", "cedartech.con.mx": "cedartech.com.mx",
}

MANUAL = {
    "v.melnykharborgroup.com.ua": "v.melnyk@harborgroup.com.ua",
    "zofianowakorbitdesign.pl": "zofianowak@orbitdesign.pl",
    "erikssonlarsmapleconsulting.se": "erikssonlars@mapleconsulting.se",
    "rina.matsumotourbanconsulting.jp": "rina.matsumoto@urbanconsulting.jp",
}


def clean_email_part(part):
    flags = []
    s = part.lower().strip()
    s = re.sub(r"^mailto:\s*", "", s)
    s = re.sub(r"[<>]", "", s).strip()

    if s == "":
        return None, ["blank"]
    if s in PLACEHOLDERS:
        return s, ["placeholder"]

    if "@" not in s and AT_WORD.search(s):
        s = AT_WORD.sub("@", s)

    if "@" in s:
        s = re.sub(r"\s+", "", s)
        s = re.sub(r"@{2,}", "@", s)
        s = FORBIDDEN.sub("", s)
        s = re.sub(r"\.{2,}", ".", s)
    s = s.strip(".")

    if s == "":
        return None, ["blank"]

    if "@" not in s:
        flags.append("no_at")
    elif s.count("@") > 1:
        flags.append("multi_at")
    else:
        local, domain = s.split("@")
        if local == domain.split(".")[0]:
            flags.append("fake_like")
    return s, flags


def clean_email_column(df, col="Email"):
    df = df.copy()
    cleaned, extras = [], []

    for raw in df[col]:
        if pd.isna(raw):
            cleaned.append(np.nan); extras.append(np.nan)
            continue

        results = [clean_email_part(p) for p in str(raw).split(";")]
        good = [(v, f) for v, f in results if v is not None]
        if not good:
            cleaned.append(np.nan); extras.append(np.nan)
            continue

        first_val, first_flags = good[0]
        extra_vals = [v for v, _ in good[1:]]

        if "placeholder" in first_flags or "fake_like" in first_flags:
            first_val = np.nan

        cleaned.append(first_val)
        extras.append("; ".join(extra_vals) if extra_vals else np.nan)

    df[col] = cleaned
    df["Email_extra"] = extras
    return df


df = clean_email_column(df)

dom = df["Email"].str.split("@").str[1]
df.loc[dom.isin(["none.com", "email.com"]), "Email"] = np.nan

dom = df["Email"].str.split("@").str[1]
for bad, good in DOMAIN_FIX.items():
    m = dom == bad
    df.loc[m, "Email"] = df.loc[m, "Email"].str.replace("@" + bad, "@" + good, regex=False)

valid = df["Email"].dropna()
valid = valid[valid.str.match(STRICT)]
known = list(valid.str.split("@").str[1].value_counts().index)

for i, raw in df["Email"].dropna().items():
    if STRICT.match(raw):
        continue
    cands = [d for d in known if raw.endswith(d) and len(raw) > len(d)]
    if len(cands) == 1:
        df.loc[i, "Email"] = raw[:-len(cands[0])] + "@" + cands[0]

m = df["Email"].isin(MANUAL.keys())
df.loc[m, "Email"] = df.loc[m, "Email"].map(MANUAL)


# ── Cleaning Country ──
df['Country'] = df['Country'].str.strip().str.lower()

COUNTRY_MAP = {
    # Germany
    "germany": "Germany", "germny": "Germany", "de": "Germany", "deu": "Germany",
    "deutschland": "Germany", "allemagne": "Germany",
    # United Kingdom
    "united kingdom": "United Kingdom", "gb": "United Kingdom", "gbr": "United Kingdom",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "great britain": "United Kingdom",
    "britain": "United Kingdom", "england": "United Kingdom", "wales": "United Kingdom",
    "scotland": "United Kingdom",
    # France
    "france": "France", "frnace": "France", "fr": "France", "fra": "France",
    # Spain
    "spain": "Spain", "esp": "Spain", "es": "Spain", "espana": "Spain", "españa": "Spain",
    # Italy
    "italy": "Italy", "itlay": "Italy", "it": "Italy", "ita": "Italy",
    "italia": "Italy",
    # United States
    "united states": "United States", "untied states": "United States", "usa": "United States",
    "u.s.": "United States", "u.s.a.": "United States", "us": "United States",
    "united states of america": "United States",
    # Poland
    "poland": "Poland", "pl": "Poland", "pol": "Poland", "polska": "Poland",
    "polnad": "Poland",
    # Netherlands
    "netherlands": "Netherlands", "netherland": "Netherlands", "the netherlands": "Netherlands",
    "nl": "Netherlands", "nld": "Netherlands", "holland": "Netherlands", "nederland": "Netherlands",
    # Portugal
    "portugal": "Portugal", "portugual": "Portugal", "pt": "Portugal", "prt": "Portugal",
    # Brazil
    "brazil": "Brazil", "brazill": "Brazil", "br": "Brazil", "bra": "Brazil",
    "brasil": "Brazil",
    # India
    "india": "India", "in": "India", "ind": "India", "inida": "India", "bharat": "India",
    # Ukraine
    "ukraine": "Ukraine", "ukrain": "Ukraine", "ukr": "Ukraine", "ua": "Ukraine",
    "україна": "Ukraine",
    # Ireland
    "ireland": "Ireland", "ie": "Ireland", "irl": "Ireland", "republic of ireland": "Ireland",
    "eire": "Ireland",
    # Sweden
    "sweden": "Sweden", "se": "Sweden", "swe": "Sweden", "sverige": "Sweden", "swedan": "Sweden",
    # Mexico
    "mexico": "Mexico", "mex": "Mexico", "mx": "Mexico", "mexcio": "Mexico",
    # China
    "china": "China", "cn": "China", "chn": "China", "p.r. china": "China",
    "people's republic of china": "China", "中国": "China",
    # Turkey
    "turkey": "Turkey", "tr": "Turkey", "tur": "Turkey", "türkiye": "Turkey",
    "turkiye": "Turkey", "turkei": "Turkey",
    # Kenya
    "kenya": "Kenya", "ke": "Kenya", "ken": "Kenya", "kenia": "Kenya",
    # Australia
    "australia": "Australia", "au": "Australia", "aus": "Australia", "austrlia": "Australia",
    # South Korea
    "south korea": "South Korea", "kr": "South Korea", "kor": "South Korea",
    "korea": "South Korea", "s. korea": "South Korea", "대한민국": "South Korea",
    # Canada
    "canada": "Canada", "ca": "Canada", "can": "Canada", "canda": "Canada",
    # Japan
    "japan": "Japan", "jp": "Japan", "jpn": "Japan", "日本": "Japan",
    # Colombia
    "colombia": "Colombia", "co": "Colombia",
    # South Africa
    "south africa": "South Africa", "za": "South Africa", "zaf": "South Africa",
    "rsa": "South Africa", "south afrika": "South Africa",
    # Nigeria
    "nigeria": "Nigeria", "ng": "Nigeria",
    # Israel
    "israel": "Israel", "il": "Israel", "isr": "Israel",
    # United Arab Emirates
    "united arab emirates": "United Arab Emirates", "uae": "United Arab Emirates",
    "ae": "United Arab Emirates", "u.a.e.": "United Arab Emirates", "are": "United Arab Emirates",
    # New Zealand
    "new zealand": "New Zealand", "nz": "New Zealand", "new zeland": "New Zealand",
    # Other
    "allemagne": "Germany",
}

df['Country'] = df['Country'].map(COUNTRY_MAP)

COUNTRY_CODES = {
    "Germany": "DE",
    "United Kingdom": "GB",
    "France": "FR",
    "Spain": "ES",
    "Italy": "IT",
    "United States": "US",
    "Poland": "PL",
    "Netherlands": "NL",
    "Portugal": "PT",
    "Brazil": "BR",
    "India": "IN",
    "Ukraine": "UA",
    "Ireland": "IE",
    "Sweden": "SE",
    "Mexico": "MX",
    "China": "CN",
    "Turkey": "TR",
    "Kenya": "KE",
    "Australia": "AU",
    "South Korea": "KR",
    "Canada": "CA",
    "Japan": "JP",
    "Colombia": "CO",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Israel": "IL",
    "United Arab Emirates": "AE",
    "New Zealand": "NZ",
}

df["Country_code"] = df["Country"].map(COUNTRY_CODES)


# ── Cleaning Phone column ──
# df['Phone'] = df['Phone'].str.strip().str.replace(r'[0-9]', '9', regex=True)

def clean_phone(raw, region):
    if pd.isna(raw):
        return np.nan
    s = str(raw).split("/")[0]                  # два номера через "/": берём первый
    s = re.sub(r"(?i)ext\.?.*", "", s)          # срезаем ext и всё после
    s = re.sub(r"[^\d+]", "", s)                # оставляем только цифры и +
    s = re.sub(r"^00", "+", s)                  # ведущий 00 -> +
    if s == "":
        return np.nan
    try:
        n = phonenumbers.parse(s, None if pd.isna(region) else region)
    except phonenumbers.NumberParseException:
        return np.nan
    return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)

df["Phone"] = [clean_phone(p, r) for p, r in zip(df["Phone"], df["Country_code"])]

# ── Cleaning City column ──
df["City"] = df["City"].apply(lambda v: ftfy.fix_text(v) if isinstance(v, str) else v)
df["City"] = df["City"].str.strip().str.lower()

CITY_MAP = {
    "münchen": "Munich", "munchen": "Munich", "muenchen": "Munich", "munich": "Munich",
    "köln": "Cologne", "koeln": "Cologne",
    "kraków": "Kraków", "krakow": "Kraków", "cracow": "Kraków",
    "wrocław": "Wrocław", "wroclaw": "Wrocław",
    "gdańsk": "Gdańsk", "gdansk": "Gdańsk",
    "warszawa": "Warsaw",
    "torino": "Turin", "turin": "Turin",
    "napoli": "Naples", "naples": "Naples",
    "milano": "Milan", "milan": "Milan",
    "roma": "Rome", "rome": "Rome",
    "lisboa": "Lisbon", "lisbon": "Lisbon",
    "sevilla": "Seville", "seville": "Seville",
    "den haag": "The Hague",
    "göteborg": "Gothenburg", "goteborg": "Gothenburg",
    "malmö": "Malmö", "malmo": "Malmö",
    "oporto": "Porto",
    "kyiv": "Kyiv", "kiev": "Kyiv", "київ": "Kyiv",
    "odesa": "Odesa", "odessa": "Odesa",
    "istanbul": "Istanbul", "izmir": "Izmir",
    "seoul": "Seoul", "서울": "Seoul",
    "busan": "Busan", "pusan": "Busan",
    "beijing": "Beijing", "peking": "Beijing",
    "mumbai": "Mumbai", "bombay": "Mumbai",
    "chennai": "Chennai", "madras": "Chennai",
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
    "são paulo": "São Paulo", "sao paulo": "São Paulo", "s. paulo": "São Paulo",
    "rio": "Rio de Janeiro", "rio de janeiro": "Rio de Janeiro",
    "brasília": "Brasília", "brasilia": "Brasília",
    "mexico city": "Mexico City", "ciudad de méxico": "Mexico City",
    "montréal": "Montreal", "montreal": "Montreal",
    "valencia": "Valencia", "valència": "Valencia",
    "abudhabi": "Abu Dhabi",
    "sf": "San Francisco", "nyc": "New York",
}

df["City"] = df["City"].str.replace("\u0307", "", regex=False)
df["City"] = df["City"].replace({"?": np.nan, "not provided": np.nan, "-": np.nan, "": np.nan})
df["City"] = df["City"].map(lambda v: CITY_MAP.get(v, v.title()) if isinstance(v, str) else v)


# ── Cleaning Race column ──
df["Race"] = df['Race'].str.strip().str.lower()

RACE_MAP = {
    "5k": "5K", "5km": "5K", "5 km": "5K", "5 k": "5K", "5000m": "5K", "5k fun run": "5K",
    "10k": "10K", "10 k": "10K", "10 km": "10K", "10km": "10K", "10k run": "10K",
    "half marathon": "Half Marathon", "half-marathon": "Half Marathon", "half": "Half Marathon",
    "hm": "Half Marathon", "halbmarathon": "Half Marathon", "semi-marathon": "Half Marathon",
    "1/2 marathon": "Half Marathon", "21k": "Half Marathon", "21.1 km": "Half Marathon",
    "marathon": "Marathon", "full marathon": "Marathon", "full": "Marathon", "fm": "Marathon",
    "42k": "Marathon", "42 km": "Marathon", "42.195 km": "Marathon",
}

df['Race'] = df['Race'].map(RACE_MAP)


# ── Cleaning T-Shirt Size column ──

df['T-Shirt Size'] = df['T-Shirt Size'].str.strip().str.lower()
SIZE_MAPPING = {
    # Extra Small
    "xs": "XS",
    "x-small": "XS",
    "extra small": "XS",
    # Small
    "s": "S",
    "small": "S",
    "women's s": "S",
    "w-s": "S",
    # Medium
    "m": "M",
    "m (unisex)": "M",
    "medium": "M",
    "men's m": "M",
    "women's m": "M",
    # Large
    "l": "L",
    "large": "L",
    "men's l": "L",
    # Extra Large
    "xl": "XL",
    "extra large": "XL",
    "x-large": "XL",
    "1xl": "XL",
    # 2X Large
    "xxl": "XXL",
    "2xl": "XXL",
    "2x": "XXL",
    "xx-large": "XXL",
    # 3X Large
    "xxxl": "XXXL",
    # Unknown / Missing
    "": None,
    "-": None,
    "?": None,
}

df['T-Shirt Size'] = df['T-Shirt Size'].map(SIZE_MAPPING)


# ── Cleaning Registration Date column ──
df = df.rename(columns={"Registration Date ": "Registration Date"})

RULES = [
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    (r"\d{4}\.\d{2}\.\d{2}", "%Y.%m.%d"),
    (r"[A-Za-z]{3} \d{1,2}, \d{4}", "%b %d, %Y"),
    (r"\d{1,2} [A-Za-z]{3} \d{4}", "%d %b %Y"),
    (r"\d{2}-[A-Za-z]{3}-\d{2}", "%d-%b-%y"),
    (r"\d{4}年\d{1,2}月\d{1,2}日", "%Y年%m月%d日"),
]

AMB = {
    "/": (r"\d{2}/\d{2}/\d{4}", "{}/{}/%Y"),
    ".": (r"\d{2}\.\d{2}\.\d{4}", "{}.{}.%Y"),
    "-": (r"\d{2}-\d{2}-\d{4}", "{}-{}-%Y"),
    "yy": (r"\d{2}-\d{2}-\d{2}", "{}-{}-%y"),
}

TIME_RE = r"[T\s]\d{1,2}:\d{2}(:\d{2})?\s*([APap][Mm])?\s*(Z|[+-]\d{2}:\d{2})?$"


def _try(v, fmt):
    try:
        d = datetime.strptime(v, fmt)
    except ValueError:
        return None
    if "%y" in fmt and d.year > 2026:
        d = d.replace(year=d.year - 100)
    return d


def parse_dates(col):
    s = col.astype("string").str.strip()
    s = s.str.replace(TIME_RE, "", regex=True).str.strip()

    # порядок день/месяц для каждого разделителя по однозначным значениям
    order = {}
    for k, (pat, _) in AMB.items():
        x = s[s.str.fullmatch(pat).fillna(False)]
        a, b = x.str[:2].astype(int), x.str[3:5].astype(int)
        order[k] = "dmy" if (a > 12).sum() >= (b > 12).sum() else "mdy"

    out, amb = [], []
    for v in s:
        r, flag = None, False
        if pd.isna(v):
            pass
        elif re.fullmatch(r"\d{5}", v):
            r = datetime(1899, 12, 30) + timedelta(days=int(v))
        else:
            for pat, fmt in RULES:
                if re.fullmatch(pat, v):
                    r = _try(v, fmt)
                    break
            else:
                for k, (pat, base) in AMB.items():
                    if re.fullmatch(pat, v):
                        first, second = ("%d", "%m") if order[k] == "dmy" else ("%m", "%d")
                        r = _try(v, base.format(first, second))
                        if r is None:
                            r = _try(v, base.format(second, first))
                        flag = int(v[:2]) <= 12 and int(v[3:5]) <= 12
                        break
        out.append(r)
        amb.append(flag)
    return pd.to_datetime(pd.Series(out, index=col.index)), pd.Series(amb, index=col.index)


parsed, amb = parse_dates(df["Registration Date"])
df["Registration Date"] = parsed

df.loc[df['Registration Date'] < '2023-01-01', 'Registration Date'] = None

# ── Cleaning Fee Paid (EUR) column ──
df['Fee Raw'] = df['Fee Paid (EUR)']
raw = df['Fee Raw'].astype(str)

neg = raw.str.contains(r'-\s*\d')
s = raw.str.extract(r'(\d[\d.,]*)')[0].str.rstrip('.,')

after = s.str.extract(r'[.,](\d+)$')[0].str.len()
mixed = s.str.contains(',') & s.str.contains('.', regex=False)
is_dec = after.notna() & ((after != 3) | mixed)

as_dec = (s.str.replace(r'[.,](\d+)$', r'#\1', regex=True)
            .str.replace(r'[.,]', '', regex=True)
            .str.replace('#', '.', regex=False))
as_int = s.str.replace(r'[.,]', '', regex=True)

df['Fee Paid (EUR)'] = pd.to_numeric(as_dec.where(is_dec, as_int), errors='coerce')
df['Fee Paid (EUR)'] = df['Fee Paid (EUR)'].where(~neg & (df['Fee Paid (EUR)'] > 0))


q1 = df['Fee Paid (EUR)'].quantile(0.25)
q3 = df['Fee Paid (EUR)'].quantile(0.75)
upper = q3 + 1.5 * (q3 - q1)

df['Fee Paid (EUR)'] = df['Fee Paid (EUR)'].where(df['Fee Paid (EUR)'] <= 1000)

# ── Cleaning Payment Status column ──
df['Payment Status'] = df['Payment Status'].str.strip().str.lower()
PAYMENT_STATUS_MAPPING = {
    "paid": "Paid",
    "paid in full": "Paid",
    "succeeded": "Paid",
    "completed": "Paid",
    "pending": "Pending",
    "in progress": "Pending",
    "awaiting payment": "Pending",
    "refunded": "Refunded",
    "partially refunded": "Refunded",
    "refund issued": "Refunded",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "failed": "Failed",
    "payment failed": "Failed",
    "declined": "Failed",
    "-": None,
    "": None,
    "not provided": None,
}

df['Payment Status'] = df['Payment Status'].map(PAYMENT_STATUS_MAPPING)

# ── Cleaning Newsletter Opt-in column ──
df['Newsletter Opt-in'] = df['Newsletter Opt-in'].str.strip().str.lower()
YES_NO_MAPPING = {
    "yes": "Yes",
    "true": "Yes",
    "y": "Yes",
    "1": "Yes",
    "x": "Yes",
    "tak": "Yes",
    "oui": "Yes",
    "ja": "Yes",
    "sí": "Yes",
    "sim": "Yes",
    "no": "No",
    "n": "No",
    "false": "No",
    "0": "No",
    "nein": "No",
    "non": "No",
    "não": "No",
    "nie": "No",
    "": None,
    "-": None,
    "not provided": None,
    "?": None,
}

df['Newsletter Opt-in'] = df['Newsletter Opt-in'].map(YES_NO_MAPPING)

# ── Finalizing ──
df = df.drop_duplicates()

# Reg. ID

dup = df["Registration ID"].notna() & df.duplicated("Registration ID", keep=False)
part = df[dup].sort_values("Registration Date", na_position="first")
merged = part.groupby("Registration ID", as_index=False).last()[df.columns]

def longest(s):
    s = s.dropna()
    return s.loc[s.str.len().idxmax()] if len(s) else np.nan

merged["Full Name"] = merged["Registration ID"].map(part.groupby("Registration ID")["Full Name"].agg(longest))

def phone_ok(p, cc):
    try:
        return phonenumbers.region_code_for_number(phonenumbers.parse(p)) == cc
    except Exception:
        return False

def pick_phone(g):
    ok = g[[pd.notna(p) and phone_ok(p, cc) for p, cc in zip(g["Phone"], g["Country_code"])]]
    return ok["Phone"].iloc[-1] if len(ok) else np.nan

phones = part.groupby("Registration ID").apply(pick_phone)
merged["Phone"] = merged["Registration ID"].map(phones).fillna(merged["Phone"])
df = pd.concat([df[~dup], merged], ignore_index=True)

# Emails

def toks(n):
    n = unicodedata.normalize("NFKD", str(n).lower())
    n = "".join(c for c in n if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", " ", n.replace("-", " ")).split()

def names_match(a, b):
    if pd.isna(a) or pd.isna(b):
        return False
    ta, tb = toks(a), toks(b)
    def fits(x, y):
        return all(any(w.startswith(p) for w in y) for p in x)
    return fits(ta, tb) or fits(tb, ta)

dups = df[df["Email"].notna() & df.duplicated("Email", keep=False)]
drop_idx = []
for email, g in dups.groupby("Email"):
    if len(g) != 2:
        continue
    a, b = g.iloc[0], g.iloc[1]
    same_race = a["Race"] == b["Race"] or pd.isna(a["Race"]) or pd.isna(b["Race"])
    if names_match(a["Full Name"], b["Full Name"]) and same_race:
        keep, drop = (a, b) if pd.notna(a["Registration ID"]) or pd.isna(b["Registration ID"]) else (b, a)
        for c in df.columns:
            if pd.isna(keep[c]):
                df.at[keep.name, c] = drop[c]
        if len(str(drop["Full Name"])) > len(str(keep["Full Name"])):
            df.at[keep.name, "Full Name"] = drop["Full Name"]
        drop_idx.append(drop.name)
df = df.drop(index=drop_idx)

# Phones

def fake_phone(p):
    if pd.isna(p):
        return False
    d = re.sub(r"\D", "", p)
    return len(d) > 15 or len(set(d[3:])) <= 2 or "1234567" in d

fk = df["Phone"].map(fake_phone)
df.loc[fk, "Phone"] = np.nan

dups = df[df["Phone"].notna() & df.duplicated("Phone", keep=False)]
drop_idx = []
for phone, g in dups.groupby("Phone"):
    rows = list(g.index)
    for x in range(len(rows)):
        for y in range(x + 1, len(rows)):
            i, j = rows[x], rows[y]
            if i in drop_idx or j in drop_idx:
                continue
            a, b = df.loc[i], df.loc[j]
            same_race = a["Race"] == b["Race"] or pd.isna(a["Race"]) or pd.isna(b["Race"])
            if names_match(a["Full Name"], b["Full Name"]) and same_race:
                keep, drop = (i, j) if pd.notna(a["Registration ID"]) or pd.isna(b["Registration ID"]) else (j, i)
                ke, de = df.at[keep, "Email"], df.at[drop, "Email"]
                if pd.notna(de) and de != ke:
                    old = df.at[keep, "Email_extra"]
                    df.at[keep, "Email_extra"] = de if pd.isna(old) else old + "; " + de
                for c in df.columns:
                    if pd.isna(df.at[keep, c]):
                        df.at[keep, c] = df.at[drop, c]
                if len(str(df.at[drop, "Full Name"])) > len(str(df.at[keep, "Full Name"])):
                    df.at[keep, "Full Name"] = df.at[drop, "Full Name"]
                drop_idx.append(drop)
df = df.drop(index=drop_idx)


# Deleting
df = df.drop(columns=["Country_code"])
df.to_csv('20-Marathon-Registrations-data-cleaning/marathon_registrations_cleaned.csv',
           index=False)