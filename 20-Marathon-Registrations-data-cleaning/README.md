# Marathon Registrations — Data Cleaning

Cleaning work for a raw marathon-registration export.

## Completed columns

### Registration ID

All valid IDs were standardized to `MAR25-12345`.

| Raw value | Cleaned value |
| --- | --- |
| `mar25-10001` | `MAR25-10001` |
| `MAR25 10001` | `MAR25-10001` |
| `MAR2510001` | `MAR25-10001` |
| `10001` | `MAR25-10001` |

Rows with non-empty junk values such as `not provided`, `?`, `-`, or a repeated CSV header were removed. Rows with a genuinely missing Registration ID were kept.

### Full Name

- Repaired broken text encoding, for example `ThÃ©oLeGall` → `Théo Le Gall`.
- Removed leading, trailing, and repeated spaces.
- Changed surname-first values, for example `Edwards, Katherine` → `Katherine Edwards`.
- Standardized capitalization: `VALENTINA ROSSI` → `Valentina Rossi`.
- Removed titles and credentials: `Herr Daan van den Berg` → `Daan van den Berg`; `Ute Schröder MBA` → `Ute Schröder`.
- Preserved common surname particles in their usual in-name style, including `de la`, `del`, `van der`, `ter`, `op`, and `bin`.
- Replaced clear placeholder names such as `xxx`, `Runner`, `Unknown`, `asdf`, and `??` with missing values. The associated rows remain in the dataset.

## Next

Email cleaning has been analysed but has not yet been applied. The remaining columns will be cleaned next.
