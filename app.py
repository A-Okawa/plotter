import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from data_loader import load_uploaded_file, load_crack_healing_preset, make_template_csv
from plotters import make_plot
from statistics import summary_table

st.set_page_config(page_title="Yin Lab Plotter", page_icon="📊", layout="wide")
st.title("Yin Lab Plotter")
st.caption("Upload CSV / Excel → choose columns → make graphs → export.")

with st.sidebar:
    st.header("1. Data")
    mode = st.radio("Input mode", ["General CSV / Excel", "Crack Healing preset"])
    uploaded = st.file_uploader("Upload data", type=["csv", "xlsx", "xls"])
    st.download_button("Download template CSV", make_template_csv(), "plotter_template.csv", "text/csv", use_container_width=True)

if uploaded is None:
    st.info("Upload a CSV or Excel file to begin.")
    st.stop()

try:
    if mode == "Crack Healing preset":
        df, note = load_crack_healing_preset(uploaded)
        st.success(note)
    else:
        df = load_uploaded_file(uploaded)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

if df.empty:
    st.warning("No usable rows were found.")
    st.stop()

numeric_cols = list(df.select_dtypes(include="number").columns)
all_cols = list(df.columns)
if not numeric_cols:
    st.error("No numeric columns were detected.")
    st.stop()

plot_tab, data_tab, stats_tab = st.tabs(["Plot", "Data", "Statistics"])

with plot_tab:
    left, right = st.columns([1, 2.2], gap="large")
    with left:
        st.subheader("2. Plot settings")
        graph_type = st.selectbox("Graph type", ["Box + raw points", "Scatter", "Line", "Bar", "Violin + raw points", "Histogram"])

        default_x = "grain_size_um" if "grain_size_um" in df.columns else all_cols[0]
        default_y = "healing_pct" if "healing_pct" in df.columns else numeric_cols[0]

        if graph_type == "Histogram":
            x_col = st.selectbox("Value column", numeric_cols, index=numeric_cols.index(default_y) if default_y in numeric_cols else 0)
            y_col = None
        else:
            x_col = st.selectbox("X column", all_cols, index=all_cols.index(default_x) if default_x in all_cols else 0)
            y_col = st.selectbox("Y column", numeric_cols, index=numeric_cols.index(default_y) if default_y in numeric_cols else 0)

        group_options = ["(None)"] + all_cols
        default_group = "condition" if "condition" in df.columns else "(None)"
        group_col = st.selectbox("Group column", group_options, index=group_options.index(default_group))
        group_col = None if group_col == "(None)" else group_col

        st.markdown("**Display**")
        show_raw = st.checkbox("Show raw points", True, disabled=graph_type in ["Scatter", "Line", "Histogram"])
        show_mean = st.checkbox("Show mean", True, disabled=graph_type in ["Scatter", "Line", "Histogram"])
        show_median = st.checkbox("Show median", False, disabled=graph_type in ["Scatter", "Line", "Histogram"])
        show_n = st.checkbox("Show n", True, disabled=graph_type in ["Scatter", "Line", "Histogram"])
        errorbar = st.selectbox("Error bar", ["None", "SD", "SE", "95% CI", "Min–Max"], index=1, disabled=graph_type not in ["Bar", "Scatter", "Line"])
        trendline = st.checkbox("Linear regression line", False) if graph_type == "Scatter" else False
        bins = st.slider("Bins", 5, 80, 20) if graph_type == "Histogram" else 20

        st.markdown("**Axes**")
        continuous_x = st.checkbox("Treat X as continuous numeric axis", value=(x_col in numeric_cols if graph_type != "Histogram" else False), disabled=graph_type in ["Histogram", "Bar"])
        x_min = st.text_input("X min (blank = auto)", "")
        x_max = st.text_input("X max (blank = auto)", "")
        x_tick = st.text_input("X tick interval (blank = auto)", "0.25" if mode == "Crack Healing preset" else "")
        y_min = st.text_input("Y min (blank = auto)", "0" if mode == "Crack Healing preset" and graph_type != "Histogram" else "")
        y_max = st.text_input("Y max (blank = auto)", "100" if mode == "Crack Healing preset" and graph_type != "Histogram" else "")
        y_tick = st.text_input("Y tick interval (blank = auto)", "")

        st.markdown("**Labels**")
        title = st.text_input("Title", "")
        x_label = st.text_input("X-axis label", "As-sintered mean grain size (µm)" if mode == "Crack Healing preset" else "")
        y_label = st.text_input("Y-axis label", "Crack-healing ratio (%)" if mode == "Crack Healing preset" else "")
        point_size = st.slider("Point size", 10, 100, 28)
        alpha = st.slider("Point opacity", 0.1, 1.0, 0.60, 0.05)

    with right:
        try:
            fig, plotted_df = make_plot(
                df, graph_type, x_col, y_col, group_col, show_raw, show_mean, show_median,
                show_n, errorbar, trendline, bins, continuous_x, x_min, x_max, x_tick,
                y_min, y_max, y_tick, title, x_label, y_label, point_size, alpha
            )
            st.pyplot(fig, use_container_width=True)
            st.markdown("### Export")
            c1, c2, c3, c4 = st.columns(4)
            png = io.BytesIO(); fig.savefig(png, format="png", dpi=300, bbox_inches="tight")
            pdf = io.BytesIO(); fig.savefig(pdf, format="pdf", bbox_inches="tight")
            svg = io.BytesIO(); fig.savefig(svg, format="svg", bbox_inches="tight")
            c1.download_button("PNG", png.getvalue(), "plot.png", "image/png", use_container_width=True)
            c2.download_button("PDF", pdf.getvalue(), "plot.pdf", "application/pdf", use_container_width=True)
            c3.download_button("SVG", svg.getvalue(), "plot.svg", "image/svg+xml", use_container_width=True)
            c4.download_button("Processed CSV", plotted_df.to_csv(index=False).encode("utf-8-sig"), "processed_data.csv", "text/csv", use_container_width=True)
            plt.close(fig)
        except Exception as e:
            st.error(f"Plotting error: {e}")

with data_tab:
    st.subheader("Data preview")
    st.dataframe(df, use_container_width=True, height=520)
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

with stats_tab:
    st.subheader("Summary statistics")
    if mode == "Crack Healing preset":
        stats_value = "healing_pct"; stats_group = "condition"
    else:
        stats_value = st.selectbox("Value column", numeric_cols, key="stats_value")
        sg = st.selectbox("Group column", ["(None)"] + all_cols, key="stats_group")
        stats_group = None if sg == "(None)" else sg
    try:
        summary = summary_table(df, stats_value, stats_group)
        st.dataframe(summary, use_container_width=True)
        st.download_button("Download summary CSV", summary.to_csv(index=False).encode("utf-8-sig"), "summary_statistics.csv", "text/csv")
    except Exception as e:
        st.error(f"Statistics error: {e}")
