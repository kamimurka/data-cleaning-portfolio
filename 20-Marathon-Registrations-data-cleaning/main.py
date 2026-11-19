import re
from pathlib import Path
import ftfy
import pandas as pd

csv_path = Path(__file__).resolve().parent / "marathon_registrations_raw.csv"
df = pd.read_csv(csv_path)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

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
email_raw = df["Email"].copy()
email_text = email_raw.astype("string").str.strip()
email_present = email_text.notna() & email_text.ne("").fillna(False)
email_at_count = email_text.str.count("@").fillna(-1)
single_at = email_at_count.eq(1)

email_domains = email_text.loc[single_at].str.rsplit("@", n=1).str[-1]
email_placeholder_values = {"", "-", "?", "not provided", "unknown", "none", "null", "n/a"}
email_strict_pattern = r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$"

email_issues = {
    "Missing values": email_raw.isna(),
    "Blank values": email_text.eq("").fillna(False),
    "No @ symbol": email_at_count.eq(0) & ~email_text.str.casefold().isin(email_placeholder_values) & email_present,
    "More than one @ symbol": email_at_count.gt(1),
    "Multiple emails in one cell": email_text.str.contains(";", regex=False, na=False),
    "Spaces inside the value": email_text.str.contains(r"\s", regex=True, na=False),
    "Envelope brackets <...>": email_text.str.contains(r"[<>]", regex=True, na=False),
    "mailto: prefix": email_text.str.startswith("mailto:", na=False),
    "Trailing full stop": email_text.str.endswith(".", na=False),
    "Repeated dots": email_text.str.contains(r"\.\.", regex=True, na=False),
    "Placeholder text": email_text.str.casefold().isin(email_placeholder_values),
    "Local part matches domain label": email_text.str.fullmatch(r"(?i)([^@.\s]+)@\1(?:\.[a-z]{2,})+", na=False),
    "Fails strict email structure": ~email_text.str.fullmatch(email_strict_pattern, case=False, na=False) & email_present,
}

print("\n" + "─" * 46)
print("EMAIL | RAW COLUMN ANALYSIS")
print("─" * 46)
print(f"Rows: {len(email_raw)}")
print(f"Values with exactly one @: {int(single_at.sum())}")
print("\nIssue counts:")
for issue, mask in email_issues.items():
    print(f"{issue}: {int(mask.sum())}")

print("\nAll raw domains from values with exactly one @:")
print(email_domains.value_counts().to_string())

for issue in (
    "No @ symbol",
    "More than one @ symbol",
    "Multiple emails in one cell",
    "Placeholder text",
    "Local part matches domain label",
    "Fails strict email structure",
):
    values = email_text.loc[email_issues[issue]].value_counts()
    if not values.empty:
        print(f"\n{issue} — values to review:")
        print(values.to_string())


# ── Cleaning Phone column ──


# ── Cleaning Country column ──


# ── Cleaning City column ──


# ── Cleaning Race column ──


# ── Cleaning T-Shirt Size column ──


# ── Cleaning Registration Date column ──


# ── Cleaning Fee Paid (EUR) column ──


# ── Cleaning Payment Status column ──


# ── Cleaning Newsletter Opt-in column ──
