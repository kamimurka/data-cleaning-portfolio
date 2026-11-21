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
  - Converted into int.
