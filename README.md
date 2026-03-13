# Overview

End-to-end retail analytics project in collaboration with Quantium — a global leader in data science and AI — focused on the chips category for a major Australian supermarket chain.

The work spans the full analytics lifecycle : raw messy transactional data, customer behaviour analysis, controlled experiment evaluation, boardroom ready strategic presentation.

Business question: Who is buying chips, what drives their spend, and did a new in-store layout actually move the needle?

 **Live Dashboard →** : https://quantium-dashboard.onrender.com

[![Live Demo](https://img.shields.io/badge/Live%20Demo-quantium--dashboard-F28C28?style=flat-square&logo=render&logoColor=white)](https://quantium-dashboard.onrender.com)
---

## Project Structure

Quantium/
├── data/
│   ├── QVI_transaction_data.xlsx      # 264K+ raw transactions
│   ├── QVI_purchase_behaviour.csv     # Customer loyalty segmentation
│   └── QVI_data.csv                   # Cleaned & merged output
├── notebooks/
│   ├── Task1_Category_Analysis.ipynb  # EDA, segmentation, affinity
│   └── Task2_Uplift_Testing.ipynb     # Control matching & significance
├── reports/
│   ├── Chips_Category_Review.pptx     # 12-slide client deck
│   └── Chips_Category_Review.pdf
└── README.md

---

## Work Summary 

The raw data needed serious cleaning before any analysis could begin — dates were stored as Excel integers and had to be converted correctly, non-chip products like salsa were filtered out, a loyalty card buying 200 units per visit was flagged as a commercial buyer and removed, and both pack size and brand name had to be pulled out of messy product name strings using pattern matching. Once clean, customers were grouped into 21 segments based on life stage and spending tier, revealing that Mainstream Young Singles & Couples are the top revenue segment at $179K — they pay significantly more per unit than any other group (confirmed with a statistical test), and strongly prefer premium brands like Kettle and Tyrrells with a clear preference for the 270g sharing pack.

To evaluate a new in-store chip aisle layout trialled across three stores, each trial store was carefully matched to the most similar non-trial store using a combination of sales trend correlation and volume similarity. The results were then tested for statistical significance month by month. Stores 77 and 88 showed clear, significant uplift in both sales and customer numbers. Store 86 was a mixed result — it brought in more customers but didn't see a matching revenue increase, pointing to a possible pricing or product issue during the trial period.

All findings were packaged into a 12-slide boardroom presentation built on the Pyramid Principles storytelling framework — starting from the business situation, identifying the key tension, and landing on four concrete recommendations for where and how to roll out the new layout chain-wide.

## Skills Demonstrated

- Data Wrangling : Datetime parsing, regex extraction, outlier detection, multi-dataset joins. 
- Feature Engineering : Pack size & brand name from unstructured text
- Statistical Testing : Welch's t-test, Pearson correlation, one-sided significance thresholds
- Experimental Design : Pre/post control matching, composite similarity scoring, scaling
- Visualization : matplotlib + seaborn — time-series, segmented bars, affinity charts
- Business Communication :  CommunicationPyramid Principles, KPI framing, data-backed recommendations


## How to Run

` bashgit clone https://github.com/YOUR_USERNAME/Quantium-Portfolio.git `
` cd Quantium-Portfolio/Quantium `

` pip install pandas numpy matplotlib seaborn scipy openpyxl jupyter`

## Category analysis

`jupyter notebook notebooks/Transaction_I.ipynb`

## Uplift testing (requires QVI_data.csv output from above)
`Jupyter notebook notebooks/Transaction_II.ipynb`


## Built as a Part of : 

Quantium Data Analysis — Forage Program

This project is extended with full DS Plus ML Engineering : quantium-extended
