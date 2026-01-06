import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    stayers = pd.read_csv("casino_stayers_clustered.csv")
    migration = pd.read_csv("phase2_persona_migration_scored.csv")
    queue = pd.read_csv("phase2_host_queue.csv")
    return stayers, migration, queue

stayers, migration, queue = load_data()

st.set_page_config(page_title="Casino Stayer Intelligence", layout="wide")

st.title("🎰 Casino Stayer Intelligence Dashboard")

# -----------------------------
# Sidebar navigation
# -----------------------------
page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Persona Performance",
        "Migration Dynamics",
        "Host Queue",
        "Lift Simulator"
    ]
)

# -----------------------------
# PAGE 1 — Executive Overview
# -----------------------------
if page == "Executive Overview":
    st.header("Executive Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Active Stayers", len(migration))
    col2.metric("HIGH %", f"{(migration['pms_bucket']=='HIGH').mean():.1%}")
    col3.metric("Upgrade Risk (avg)", f"{migration['P_UPGRADE'].mean():.2f}")
    col4.metric("Downgrade Risk (avg)", f"{migration['P_DOWNGRADE'].mean():.2f}")

    st.subheader("PMS Distribution")
    st.bar_chart(migration["pms_bucket"].value_counts(normalize=True))

    st.subheader("Persona Size")
    st.bar_chart(
        stayers["cluster_hdbscan"].value_counts().sort_index()
    )

# -----------------------------
# PAGE 2 — Persona Performance
# -----------------------------
elif page == "Persona Performance":
    st.header("Persona Performance")

    persona_summary = (
        migration
        .groupby("cluster_hdbscan")
        .agg(
            players=("user_id", "count"),
            avg_ADT=("ADT_recent", "mean"),
            pct_high=("pms_bucket", lambda x: (x=="HIGH").mean()),
            upgrade_rate=("migration_label", lambda x: (x=="UPGRADE").mean()),
            downgrade_rate=("migration_label", lambda x: (x=="DOWNGRADE").mean())
        )
        .round(3)
    )

    st.dataframe(persona_summary, use_container_width=True)

# -----------------------------
# PAGE 3 — Migration Dynamics
# -----------------------------
elif page == "Migration Dynamics":
    st.header("Migration Dynamics")

    high = migration[migration["pms_bucket"]=="HIGH"]
    non_high = migration[migration["pms_bucket"]!="HIGH"]

    col1, col2 = st.columns(2)

    col1.metric(
        "HIGH Upgrade Rate",
        f"{(high['migration_label']=='UPGRADE').mean():.1%}"
    )

    col2.metric(
        "Non-HIGH Upgrade Rate",
        f"{(non_high['migration_label']=='UPGRADE').mean():.1%}"
    )

    st.subheader("PMS vs ΔADT")
    st.scatter_chart(
        migration[["pms_score", "delta_ADT"]].dropna()
    )

# -----------------------------
# PAGE 4 — Host Queue
# -----------------------------
elif page == "Host Queue":
    st.header("Host Queue")

    persona_filter = st.multiselect(
        "Persona",
        sorted(queue["cluster_hdbscan"].unique()),
        default=sorted(queue["cluster_hdbscan"].unique())
    )

    lane_filter = st.multiselect(
        "Lane",
        queue["host_lane"].unique(),
        default=queue["host_lane"].unique()
    )

    filtered = queue[
        (queue["cluster_hdbscan"].isin(persona_filter)) &
        (queue["host_lane"].isin(lane_filter))
    ]

    st.dataframe(filtered, use_container_width=True)

    st.download_button(
        "Download Queue",
        filtered.to_csv(index=False),
        file_name="host_queue_filtered.csv"
    )

# -----------------------------
# PAGE 5 — Lift Simulator
# -----------------------------
elif page == "Lift Simulator":
    st.header("Expected Lift Simulator")

    target_group = st.selectbox(
        "Target Group",
        ["HIGH only", "Growth Lane only", "HIGH + Growth"]
    )

    intervention_rate = st.slider(
        "Host Intervention Rate",
        0.1, 1.0, 0.5, 0.05
    )

    horizon = st.selectbox(
        "Time Horizon (months)",
        [3, 6, 12],
        index=1
    )

    if target_group == "HIGH only":
        target = migration[migration["pms_bucket"]=="HIGH"]
    elif target_group == "Growth Lane only":
        target = migration[migration["user_id"].isin(queue["user_id"])]
    else:
        target = migration[
            (migration["pms_bucket"]=="HIGH") &
            (migration["user_id"].isin(queue["user_id"]))
        ]

    baseline_upgrade = (migration["migration_label"]=="UPGRADE").mean()
    target_upgrade = (target["migration_label"]=="UPGRADE").mean()

    incremental_prob = max(target_upgrade - baseline_upgrade, 0)
    avg_delta_adt = target["delta_ADT"].mean()

    expected_lift = (
        len(target)
        * intervention_rate
        * incremental_prob
        * avg_delta_adt
        * horizon
    )

    st.metric(
        "Estimated Incremental Value",
        f"PhP{expected_lift:,.0f}"
    )

    st.caption(
        "Scenario-based estimate. Actual lift depends on execution quality."
    )