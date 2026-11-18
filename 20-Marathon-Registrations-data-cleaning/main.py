import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import pandas as pd
    from pathlib import Path

    csv_path = Path(__file__).resolve().parent / "marathon_registrations_raw.csv"
    df = pd.read_csv(csv_path)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.__version__
    return csv_path, df


if __name__ == "__main__":
    app.run()
