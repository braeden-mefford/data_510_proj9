import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")
st.title("National Labor Statistics Dashboard")


df = pd.read_csv("nls97b.csv")


weeks_cols = []
for c in df.columns:
    if str(c).startswith("weeksworked"):
        weeks_cols.append(c)

year_map = {}
for c in weeks_cols:
    suf = str(c).replace("weeksworked", "")
    try:
        suf_int = int(suf)
        year_map[c] = 1996 + suf_int
    except:
        pass

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
bar_numeric_cols = [c for c in numeric_cols if c not in weeks_cols]

cat_cols = []
for c in df.columns:
    if df[c].dtype == "object":
        cat_cols.append(c)


st.sidebar.header("Filters")

if "highestdegree" in df.columns:
    deg_options = df["highestdegree"].dropna().unique().tolist()
    selected_degrees = st.sidebar.multiselect(
        "Highest degree",
        options=deg_options,
        default=deg_options
    )
else:
    selected_degrees = []

if "gender" in df.columns:
    gender_options = df["gender"].dropna().unique().tolist()
    selected_genders = st.sidebar.multiselect(
        "Gender",
        options=gender_options,
        default=gender_options
    )
else:
    selected_genders = []

if "nightlyhrssleep" in df.columns:
    sleep_min = float(np.nanmin(df["nightlyhrssleep"]))
    sleep_max = float(np.nanmax(df["nightlyhrssleep"]))
    selected_sleep = st.sidebar.slider(
        "Nightly hours of sleep (range)",
        min_value=float(np.floor(sleep_min)),
        max_value=float(np.ceil(sleep_max)),
        value=(float(np.floor(sleep_min)), float(np.ceil(sleep_max)))
    )
else:
    selected_sleep = None


st.sidebar.header("Visualization Options")

if len(bar_numeric_cols) > 0:
    bar_metric = st.sidebar.selectbox(
        "Bar chart numeric metric",
        options=bar_numeric_cols,
        index=0
    )
else:
    bar_metric = None

if len(cat_cols) > 0:
    default_pie = None
    if "gender" in cat_cols:
        default_pie = "gender"
    elif "highestdegree" in cat_cols:
        default_pie = "highestdegree"
    else:
        default_pie = cat_cols[0]

    pie_category = st.sidebar.selectbox(
        "Pie chart category",
        options=cat_cols,
        index=cat_cols.index(default_pie)
    )
else:
    pie_category = None

if "highestdegree" in df.columns:
    ts_deg_options = df["highestdegree"].dropna().unique().tolist()
    ts_selected_degrees = st.sidebar.multiselect(
        "Time series: degrees to display",
        options=ts_deg_options,
        default=ts_deg_options
    )
else:
    ts_selected_degrees = []

if len(year_map) > 0:
    all_years = sorted(list(set(year_map.values())))
    ts_selected_years = st.sidebar.multiselect(
        "Time series: years",
        options=all_years,
        default=all_years
    )
else:
    ts_selected_years = []


df2 = df.copy()

if "highestdegree" in df2.columns and len(selected_degrees) > 0:
    df2 = df2[df2["highestdegree"].isin(selected_degrees)]

if "gender" in df2.columns and len(selected_genders) > 0:
    df2 = df2[df2["gender"].isin(selected_genders)]

if (selected_sleep is not None) and ("nightlyhrssleep" in df2.columns):
    low, high = selected_sleep
    df2 = df2[(df2["nightlyhrssleep"] >= low) & (df2["nightlyhrssleep"] <= high)]


col1, col2 = st.columns(2)

with col1:
    st.subheader("Bar Chart")
    if bar_metric is None:
        st.info("No numeric columns available for the bar chart.")
    else:
        if "highestdegree" in df2.columns:
            group_col = "highestdegree"
        else:
            group_col = pie_category

        if group_col is None:
            st.info("No grouping column found for the bar chart.")
        else:
            bar_data = df2.groupby(group_col)[bar_metric].mean().reset_index()
            bar_data.columns = [group_col, f"mean_{bar_metric}"]

            fig_bar = px.bar(
                bar_data,
                x=group_col,
                y=f"mean_{bar_metric}"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.write("Bar chart data")
            st.dataframe(bar_data, use_container_width=True)
            st.download_button(
                label="Download bar data (CSV)",
                data=bar_data.to_csv(index=False).encode("utf-8"),
                file_name="bar_chart_data.csv",
                mime="text/csv"
            )

with col2:
    st.subheader("Pie Chart")
    if pie_category is None:
        st.info("No categorical column available for the pie chart.")
    else:
        pie_counts = df2[pie_category].value_counts(dropna=False).reset_index()
        pie_counts.columns = [pie_category, "count"]

        fig_pie = px.pie(
            pie_counts,
            names=pie_category,
            values="count",
            hole=0.25
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.write("Pie chart data")
        st.dataframe(pie_counts, use_container_width=True)
        st.download_button(
            label="Download pie data (CSV)",
            data=pie_counts.to_csv(index=False).encode("utf-8"),
            file_name="pie_chart_data.csv",
            mime="text/csv"
        )


st.subheader("Time Series of Weeks Worked")

if len(year_map) == 0:
    st.info("No weeksworked columns found for a time series.")
else:
    df_years = df2.rename(columns=year_map)

    selected_years = []
    for y in year_map.values():
        if (len(ts_selected_years) == 0) or (y in ts_selected_years):
            selected_years.append(y)
    selected_years = sorted(list(set(selected_years)))

    if len(selected_years) == 0:
        st.info("No years selected.")
    else:
        id_vars = []
        if "highestdegree" in df_years.columns:
            id_vars = ["highestdegree"]

        ts_long = pd.melt(
            df_years,
            id_vars=id_vars,
            value_vars=selected_years,
            var_name="year",
            value_name="weeksworked"
        )

        if ("highestdegree" in ts_long.columns) and (len(ts_selected_degrees) > 0):
            ts_long = ts_long[ts_long["highestdegree"].isin(ts_selected_degrees)]

        if "highestdegree" in ts_long.columns:
            ts_grouped = ts_long.groupby(["year", "highestdegree"])["weeksworked"].mean().reset_index()
            color_col = "highestdegree"
        else:
            ts_grouped = ts_long.groupby(["year"])["weeksworked"].mean().reset_index()
            color_col = None

        fig_line = px.line(
            ts_grouped,
            x="year",
            y="weeksworked",
            color=color_col,
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

        st.write("Time series data")
        st.dataframe(ts_grouped, use_container_width=True)
        st.download_button(
            label="Download time series data (CSV)",
            data=ts_grouped.to_csv(index=False).encode("utf-8"),
            file_name="time_series_data.csv",
            mime="text/csv"
        )


st.subheader("Filtered Dataset")
st.caption("Rows shown reflect the filters chosen in the sidebar.")
st.dataframe(df2, use_container_width=True, height=400)
st.download_button(
    label="Download filtered dataset (CSV)",
    data=df2.to_csv(index=False).encode("utf-8"),
    file_name="filtered_dataset.csv",
    mime="text/csv"
)
