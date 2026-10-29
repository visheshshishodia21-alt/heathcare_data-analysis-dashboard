
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    page_icon="🏥",
    layout="wide"
)

DATA_FILE = Path(__file__).parent / "healthcare_admission.csv"

st.title("🏥 Healthcare Data Analysis Dashboard")
st.caption("Interactive analysis of patient admissions, hospital stays and billing")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_")
    )

    required = [
        "patient_id", "age", "gender", "admission_type",
        "department", "length_of_stay", "billing_amount",
        "outcome", "admission_date"
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["admission_date"] = pd.to_datetime(
        df["admission_date"], errors="coerce"
    )
    for col in ["age", "length_of_stay", "billing_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

if not DATA_FILE.exists():
    st.error(
        "Dataset not found. Keep healthcare_admission.csv "
        "in the same folder as app.py."
    )
    st.stop()

try:
    df = load_data(str(DATA_FILE))
except Exception as error:
    st.error(f"Could not load dataset: {error}")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

departments = sorted(df["department"].dropna().unique())
selected_departments = st.sidebar.multiselect(
    "Department",
    departments,
    default=departments
)

admission_types = sorted(df["admission_type"].dropna().unique())
selected_types = st.sidebar.multiselect(
    "Admission type",
    admission_types,
    default=admission_types
)

valid_dates = df["admission_date"].dropna()

if not valid_dates.empty:
    start_date, end_date = st.sidebar.date_input(
        "Admission date range",
        value=(valid_dates.min().date(), valid_dates.max().date()),
        min_value=valid_dates.min().date(),
        max_value=valid_dates.max().date()
    )
else:
    start_date = end_date = None

filtered = df[
    df["department"].isin(selected_departments)
    & df["admission_type"].isin(selected_types)
].copy()

if start_date is not None and end_date is not None:
    filtered = filtered[
        filtered["admission_date"].dt.date.between(
            start_date, end_date
        )
    ]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# KPI cards
c1, c2, c3, c4 = st.columns(4)

c1.metric("Patient Records", f"{len(filtered):,}")
c2.metric(
    "Average Age",
    f"{filtered['age'].mean():.1f}"
    if filtered["age"].notna().any() else "N/A"
)
c3.metric(
    "Average Stay (days)",
    f"{filtered['length_of_stay'].mean():.1f}"
    if filtered["length_of_stay"].notna().any() else "N/A"
)
c4.metric(
    "Total Recorded Billing",
    f"{filtered['billing_amount'].sum():,.0f}"
)

st.divider()

# Charts
left, right = st.columns(2)

with left:
    dept = filtered["department"].value_counts().rename_axis(
        "Department"
    ).reset_index(name="Patient Records")

    st.plotly_chart(
        px.bar(
            dept, x="Department", y="Patient Records",
            color="Department", title="Patient Records by Department"
        ),
        use_container_width=True
    )

with right:
    types = filtered["admission_type"].value_counts().rename_axis(
        "Admission Type"
    ).reset_index(name="Patient Records")

    st.plotly_chart(
        px.pie(
            types, names="Admission Type", values="Patient Records",
            title="Admission Type Distribution", hole=0.35
        ),
        use_container_width=True
    )

left, right = st.columns(2)

with left:
    billing = filtered.groupby(
        "department", as_index=False
    )["billing_amount"].sum()

    st.plotly_chart(
        px.bar(
            billing, x="department", y="billing_amount",
            title="Recorded Billing by Department",
            labels={
                "department": "Department",
                "billing_amount": "Total Billing"
            }
        ),
        use_container_width=True
    )

with right:
    stay_data = filtered.dropna(subset=["length_of_stay"])

    st.plotly_chart(
        px.histogram(
            stay_data, x="length_of_stay", nbins=15,
            title="Hospital Stay Distribution",
            labels={"length_of_stay": "Length of Stay (days)"}
        ),
        use_container_width=True
    )

# Outcomes
outcomes = filtered["outcome"].value_counts().rename_axis(
    "Outcome"
).reset_index(name="Patient Records")

st.plotly_chart(
    px.bar(
        outcomes, x="Outcome", y="Patient Records",
        color="Outcome", title="Patient Outcome Records"
    ),
    use_container_width=True
)

st.subheader("Filtered Patient Data")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download Filtered Data (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="healthcare_filtered_data.csv",
    mime="text/csv"
)

st.caption(
    "Demo project using synthetic data. Billing totals are illustrative, "
    "not actual hospital revenue. This dashboard is not for clinical decisions."
)
