# Yin Lab Plotter v2

A browser-based graphing tool for laboratory data using Streamlit.

## Features
- Upload CSV / Excel
- Choose X, Y, and optional Group columns
- Box + raw points / Scatter / Line / Bar / Violin + raw points / Histogram
- Mean / median / n display
- Error bars: SD / SE / 95% CI / Min–Max
- Linear regression for scatter plots
- Continuous numeric X-axis support
- Axis min / max / tick controls
- Export PNG / PDF / SVG / processed CSV
- Summary-statistics table
- Built-in downloadable template CSV
- Crack Healing preset for the current workbook format

## Deploy
Repository structure:

```text
plotter/
├── app.py
├── data_loader.py
├── plotters.py
├── statistics.py
├── requirements.txt
└── README.md
```

In Streamlit Community Cloud select:
- Branch: `main`
- Main file path: `app.py`

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app is designed primarily for tidy / long-form data.
