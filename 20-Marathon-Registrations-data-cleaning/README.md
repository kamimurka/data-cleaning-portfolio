# Marathon Registrations — Data Cleaning

Cleaning work for a raw marathon-registration export.

## Completed columns

### Registration ID

All valid IDs were standardized to `MAR25-12345`.

| Raw value       | Cleaned valuem  |
| --------------- | --------------- |
| `mar25-10001` | `MAR25-10001` |
| `MAR25 10001` | `MAR25-10001` |
| `MAR2510001`  | `MAR25-10001` |
| `10001`       | `MAR25-10001` |

Rows with non-empty junk values such as `not provided`, `?`, `-`, or a repeated CSV header were removed. Rows with a genuinely missing Registration ID were kept.

### Full Name

- Repaired broken text encoding, for example `ThÃ©oLeGall` → `Théo Le Gall`.
- Removed leading, trailing, and repeated spaces.
- Changed surname-first values, for example `Edwards, Katherine` → `Katherine Edwards`.
- Standardized capitalization: `VALENTINA ROSSI` → `Valentina Rossi`.
- Removed titles and credentials: `Herr Daan van den Berg` → `Daan van den Berg`; `Ute Schröder MBA` → `Ute Schröder`.
- Preserved common surname particles in their usual in-name style, including `de la`, `del`, `van der`, `ter`, `op`, and `bin`.
- Replaced clear placeholder names such as `xxx`, `Runner`, `Unknown`, `asdf`, and `??` with missing values. The associated rows remain in the dataset.
- ### Email


  - Cleaned the `Email` column.

    - Standardised format: lowercased, trimmed spaces, removed `mailto:` prefixes and `< >` brackets, collapsed repeated `@` and `.`, removed trailing dots.
    - Split cells with several addresses on `;`: the first stays in `Email`, the rest go to `Email_extra` (21 rows).
    - Replaced `name at domain.com` with `name@domain.com` (17 rows), since `at` was clearly a separator.
    - Fixed 45 domain typos using a small reviewed mapping (`gmial.com`, `gmail.con`, `yaho.com`, etc.). Real domains such as `hotmail.nl` were left alone.
    - Restored `@` in 35 glued values (e.g. `joris_smitgmail.com`): 30 by matching a domain already seen in valid addresses, 5 rows (4 distinct values) by hand.
    - Replaced placeholders (`not provided`, `-`, `?`, blank) and fake addresses (`none@none.com`, `test@test.com`, `noemail@none.com`, `no@email.com`) with missing values. Missing `Email` went from 34 to 76. The rows remain in the dataset.
    - Final check: all non-missing emails pass a strict structure check.

    ### Phone

    Cleaned the `Phone` column.


    - Removed extensions (`ext.`), letters and symbols (e.g. `(WhatsApp)`, `tel.`), keeping only digits and `+`.
    - Converted a leading `00` to `+` (international dialling prefix).
    - Parsed numbers with `phonenumbers`, using the country from `Country` as the region for numbers without a `+`, and standardised them to E.164 (`+4915112345678`).
    - For cells with two numbers separated by `/`, kept the first and dropped the second (about 9 rows).
    - Replaced placeholders and fake values (`not provided`, `-`, `?`, `0`, `000000000`, `+00 000 000`, `999-999-9999`) with missing values.
    - Numbers without a `+` and without a country could not be parsed safely, so they were set to missing (18 rows). The country was not guessed.
    - 1459 of 1660 values are now standardised. 189 of them do not pass `phonenumbers` validity checks but are well-formed, so they were kept. (AI's generation mistake))

  ### Fee Paid (EURO)

  - Deleted everything which isn't a number, and a few other symbols.
  - Converted into **float**.

  ### Registration Date

  - Cleaned `Registration Date` and converted all values to ISO format (`YYYY-MM-DD`).

    - Handled many input formats, including `2026-03-05`, `05/03/2026`, `05.03.2026`, `05-03-2026`, `5 Mar 2026`, `Mar 5, 2026`, `05-Mar-26`, `2026年3月5日`, and Excel serial numbers. Times and time zones were dropped.
    - (MY DECISION!) Ambiguous values (both numbers 12 or less, e.g. `03/04/2026`) were read with the order that most unambiguous values in the same format use: day first for `/`, `.` and `-` with a 4-digit year; month first for 2-digit years. For `/`, 324 unambiguous values were day-first and 40 month-first, so roughly 10% of ambiguous dates may have day and month swapped. This cannot be resolved from the data.
    - Placeholders and impossible dates (`tomorrow`, `see form`, `0000-00-00`, `13/45/2024`, `29/02/2025`, `31/04/2025`, blanks) were set to missing. Dates were not invented.
    - 4 rows already contained `1900-01-01` (3) or `1970-01-01` (1) in the source. Kept as they are.
    - Excluding those, dates range from 2023-10-30 to 2026-01-08. 36 dates fall after 2025-03-01 (20 of them ambiguous). They are treated as genuine late registrations and kept.
    - I decided that everything before 2023-01-01 are placeholders.

    ### Removed duplicate records in four passes, keeping one row per person:
  - Exact duplicate rows: 1660 → 1597.
  - Same `Registration ID`: 1597 → 1514. Empty fields were filled from the second row, the longer name was kept, and the later registration date was used when dates differed.
  - Same `Email`: 1514 → 1503. Rows were merged only when the names matched (one name is an abbreviation of the other, accents ignored) and the race was the same or missing. Different races were kept as separate registrations, and different names (shared family emails) were not merged.
  - Same `Phone`: 1503 → 1495. Fake numbers (e.g. `+3312345678901234567`, `+349999999999`) were set to missing first, so unrelated people sharing them were not merged. Merge rules as for email.
  - When a removed row had a different email, it was kept in `Email_extra`.
  - Known limitations: the Registration ID of a removed row is lost after merging. Three or more rows with the same email were not merged. 30 rows still share a phone number with another row (families or people on two races); they were kept.
