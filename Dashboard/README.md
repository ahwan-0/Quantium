# Quantium Analytics Dashboard

Interactive Plotly Dash dashboard exploring the Quantium chips category dataset — customer segments, brand affinity, pack size preferences, and trial store uplift results.

## Run Locally

```bash
cd dashboard
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:8050** in your browser.

## Tabs

| Tab | What it shows |
|---|---|
| **Overview** | Monthly sales trend, KPI cards, pack size distribution |
| **Segments** | Revenue, customers, units, and price — filterable by tier |
| **Brand & Pack Affinity** | Affinity scores per segment vs population baseline |
| **Trial Stores** | Trial vs control store chart + month-by-month significance table |

## Data

Reads `../Data/QVI_data.csv` — the cleaned merged output from the category analysis notebook.
