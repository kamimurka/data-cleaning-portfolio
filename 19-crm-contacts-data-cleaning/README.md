# CRM Contacts Data Cleaning

Cleaning pipeline for a synthetic CRM leads dataset (pandas).

- **Input:** `crm_contacts_raw.csv` (792 rows, 13 columns)
- **Output:** `crm_contacts_cleaned.csv` (618 rows, 13 columns)
- **Script:** `main.py`

## What the pipeline does

| Column                                           | Cleaning                                                                                                                                                                                                                                                         |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lead ID                                          | Normalized to `L-XXXXX` format; unparseable values become NaN                                                                                                                                                                                                  |
| Full Name                                        | Whitespace, titles (Mr/Dr/...), suffixes (Jr/PhD/...) removed; mojibake fixed (`ftfy`); `Last, First` swapped; junk values (`test`, `n/a`, ...) removed; hyphen between first and last name replaced with a space; particles lowercased (`de la Cruz`) |
| Email                                            | Lowercased; separators and typos fixed (`gmial.com`, `hotmal.com`, `outlok.com`, `.con`); placeholder emails (`test`, `none`, `fake`, ...) set to NaN                                                                                              |
| Company, Job Title, Country, Lead Source, Status | Normalized via mapping dictionaries                                                                                                                                                                                                                              |
| Phone                                            | Parsed with `phonenumbers`, stored as E.164 (`+14155550123`); placeholder numbers (`+15551234`, `+10000000000`, 555 exchanges) removed                                                                                                                   |
| Signup Date, Last Contact, Date of Birth         | Many input formats parsed to `YYYY-MM-DD`                                                                                                                                                                                                                      |
| Last Updated                                     | Parsed to ISO datetime                                                                                                                                                                                                                                           |

## Cross-field validation

- `Last Contact` earlier than `Signup Date`: `Last Contact` set to NaN (19 rows).
- Age at signup under 18 (or DOB after signup): `Date of Birth` set to NaN (2 rows).
- `Last Updated` earlier than `Last Contact` or `Signup Date`: **both** dates set to NaN for the `Last Contact` conflict, only `Last Updated` for the `Signup Date` conflict (13 rows total).
- Date of Birth outside 1920 to 2026-05-03 is set to NaN.

## Deduplication

1. Exact duplicate rows are dropped.
2. Rows sharing a `Lead ID` are collapsed into one. Priority: valid email, then phone present, then most recent `Last Updated`.
3. The longest full name among the duplicates is carried over to the surviving row, so a better contact record does not lose a complete name.
4. Rows without a `Lead ID` are handled separately so they do not collapse into a single row. Fully empty rows and rows whose email already exists on a row with an ID are dropped. 8 rows without an ID remain.
5. Three hidden duplicates (same person and email, different or missing ID) were removed manually by index: `394` (Renée Taylor), `446` (Katherine Jackson), `127` (Elizabeth Wilson). Each was verified against a surviving record. Note that this is index-based, so it is only valid for this exact input file and step order. Step 4 removes row `394` automatically, so only `446` and `127` remain in the explicit drop.

## Design decisions and known limitations

- **Phone validation uses `is_possible_number`, not `is_valid_number`.** The strict check rejected about 376 plausible-looking numbers in this synthetic dataset. The trade-off is that numbers which pass the length check may not be real. Numbers without a country code and without a leading `+` cannot be parsed and become NaN.
- **Ambiguous dates (`NN/NN/YYYY` with both parts 12 or less) are read as MM/DD.** In unambiguous rows MM/DD dominates (106 vs 26 for DD/MM), but up to 104 dates could be misread. Formats with dots or dashes use a fixed day/month order based on the separator.
- **Two-digit years:** years that would land after 2026 are shifted back 100 years (`15-Mar-45` becomes 1945, not 2045).
- **Date conflicts are resolved by nulling**, since it is impossible to tell which date is wrong. Original values are not preserved.
- **8 rows without `Lead ID`** are kept as-is. Some may be duplicates with typos in the email (for example `nwilson@globex.com`, `tsmith@umbrella.co`); this was not verified.
- **Shared email** between two different people (the two Dubois records) is kept intentionally.
- **Longest-name rule** is a heuristic and could pick a longer name that is not the correct one.
