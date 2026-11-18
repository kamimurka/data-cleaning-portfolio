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
NAME_PARTICLES = {"da", "de", "del", "den", "der", "di", "do", "dos", "du", "della", "delle", "des", "van", "von"}
full_name_before = df["Full Name"].copy()


def clean_full_name(value):
    if pd.isna(value):
        return pd.NA

    name = re.sub(r"\s+", " ", ftfy.fix_text(str(value))).strip()
    if not name or name.casefold() in NAME_PLACEHOLDERS:
        return pd.NA

    name = re.sub(r"^(?:Mr|Mrs|Ms|Miss|Dr|Prof|Sr|Sra)\.?\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+(?:PhD|M\.?D\.?|Jr\.?|Sr\.?|II|III|IV)$", "", name, flags=re.IGNORECASE)

    if "," in name:
        surname, given_names = name.split(",", 1)
        name = f"{given_names.strip()} {surname.strip()}"

    words = []
    for word in name.split():
        word = re.sub(
            r"(?<=[a-zà-öø-ÿ])(?=(?:de|del|da|do|dos|van|von)[A-Z])",
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

original_missing = full_name_before.isna() | full_name_before.astype("string").str.strip().eq("")
converted_to_missing = ~original_missing & df["Full Name"].isna()
converted_values = full_name_before.loc[converted_to_missing].value_counts()
expected_placeholders = full_name_before.astype("string").str.strip().str.casefold().isin(NAME_PLACEHOLDERS)
unexpected_missing = converted_to_missing & ~expected_placeholders

print("\n" + "─" * 46)
print("FULL NAME CLEANING | NEW MISSING VALUES")
print("─" * 46)
print(f"NaN before:                    {int(full_name_before.isna().sum())}")
print(f"New non-empty values → NaN:    {int(converted_to_missing.sum())}")
print(f"NaN after:                     {int(df['Full Name'].isna().sum())}")
print(f"Rows removed by name cleaning: 0")
print("\nValues converted to NaN:")
if converted_values.empty:
    print("  None")
else:
    print(f"  {'Original value':<24} {'Count':>5}")
    for value, count in converted_values.items():
        print(f"  {str(value):<24} {count:>5}")

print(f"\nUnexpected non-placeholder values converted to NaN: {int(unexpected_missing.sum())}")
if unexpected_missing.any():
    print(full_name_before.loc[unexpected_missing].value_counts().to_string())

