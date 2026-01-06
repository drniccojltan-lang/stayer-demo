# ============================================
# STAYER INTELLIGENCE DASHBOARD
# app.py
# ============================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Stayer Intelligence Dashboard",
    layout="wide"
)

# --------------------------------------------
# DATA LOADERS
# --------------------------------------------

@st.cache_data
def load_data():
    return {
        "clustered": pd.read_csv("casino_stayers_clustered.csv"),
        "behavior": pd.read_csv("casino_stayers_behavioral_analysis.csv"),
        "cluster_desc": pd.read_csv("HDBSCAN_ClusterDescriptions.csv"),
        "scored": pd.read_csv("step2_stayers_scored.csv"),
        "host_queue": pd.read_csv("step2_stayers_host_queue.csv"),
        "emerging": pd.read_csv("casino_emerging_stayers.csv"),
    }

data = load_data()

df_behavior = data["behavior"]
df_clusters = data["cluster_desc"]
df_host = data["host_queue"]
df_emerging = data["emerging"]

# --------------------------------------------
# SIDEBAR
# --------------------------------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Executive Overview",
        "Personas & Clusters",
        "Behavioral Progression",
        "Host Target List",
        "Emerging Stayers"
    ]
)

# --------------------------------------------
# EXECUTIVE OVERVIEW
# --------------------------------------------

if page == "Executive Overview":
    st.title("Stayer Executive Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Stayers", f"{len(df_behavior):,}")
    c2.metric("Upgrade %", f"{(df_behavior['progression_flag']=='UPGRADE').mean()*100:.1f}%")
    c3.metric("Downgrade %", f"{(df_behavior['progression_flag']=='DOWNGRADE').mean()*100:.1f}%")
    c4.metric("Avg ADT (L12M)", f"{df_behavior['ADT'].mean():,.0f}")

    st.subheader("Stayer Distribution by Cluster")
    st.bar_chart(df_behavior["cluster_hdbscan"].value_counts().sort_index())

    st.subheader("Progression Breakdown")
    st.bar_chart(df_behavior["progression_flag"].value_counts())

# --------------------------------------------
# PERSONAS & CLUSTERS
# --------------------------------------------

elif page == "Personas & Clusters":
    st.title("Personas & Clusters")

    st.dataframe(
        df_clusters.sort_values("cluster_hdbscan"),
        use_container_width=True
    )

    st.subheader("Cluster Size")
    st.bar_chart(df_behavior["cluster_hdbscan"].value_counts().sort_index())

    st.subheader("Upgrade / Downgrade by Cluster")
    pivot = (
        df_behavior
        .pivot_table(
            index="cluster_hdbscan",
            columns="progression_flag",
            values="user_id",
            aggfunc="count",
            fill_value=0
        )
    )
    st.dataframe(pivot, use_container_width=True)

# --------------------------------------------
# BEHAVIORAL PROGRESSION
# --------------------------------------------

elif page == "Behavioral Progression":
    st.title("Behavioral Progression")

    cluster = st.selectbox(
        "Cluster",
        sorted(df_behavior["cluster_hdbscan"].unique())
    )

    subset = df_behavior[df_behavior["cluster_hdbscan"] == cluster]

    c1, c2 = st.columns(2)

    c1.subheader("Progression")
    c1.bar_chart(subset["progression_flag"].value_counts())

    c2.subheader("Hours Change")
    c2.bar_chart(subset["hours_change"].value_counts())

    st.subheader("ADT vs Hours Played (Movement Insight)")
    st.scatter_chart(
        subset[["ADT", "L12M_hourplayed"]]
    )

    st.dataframe(subset.head(200), use_container_width=True)

# --------------------------------------------
# HOST TARGET LIST
# --------------------------------------------

elif page == "Host Target List":
    st.title("Host Target List")

    c1, c2, c3 = st.columns(3)

    lane = c1.selectbox("Host Lane", ["ALL"] + sorted(df_host["host_lane"].unique()))
    prog = c2.selectbox("Progression", ["ALL"] + sorted(df_host["progression_flag"].unique()))
    clus = c3.selectbox("Cluster", ["ALL"] + sorted(df_host["cluster_hdbscan"].unique()))

    filt = df_host.copy()
    if lane != "ALL":
        filt = filt[filt["host_lane"] == lane]
    if prog != "ALL":
        filt = filt[filt["progression_flag"] == prog]
    if clus != "ALL":
        filt = filt[filt["cluster_hdbscan"] == clus]

    filt = filt.sort_values("priority_score", ascending=False)

    st.dataframe(filt, use_container_width=True)

    st.subheader("ROI Concentration Curve")
    tmp = filt.copy()
    tmp["cum_value"] = tmp["expected_dollars_per_hour"].cumsum()
    st.line_chart(tmp["cum_value"])

    st.download_button(
        "Download Target List",
        filt.to_csv(index=False),
        "stayer_host_targets.csv",
        "text/csv"
    )

# --------------------------------------------
# EMERGING STAYERS
# --------------------------------------------

elif page == "Emerging Stayers":
    st.title("Emerging Stayers (Upsell & Cross-Sell Experiments)")

    c1, c2 = st.columns(2)
    c1.metric("Emerging Stayers", f"{len(df_emerging):,}")
    c2.metric("Eligible for Host %", f"{df_emerging['eligible_for_host'].mean()*100:.1f}%")

    st.subheader("Experiment Types")
    st.bar_chart(df_emerging["experiment_type"].value_counts())

    st.dataframe(df_emerging.head(200), use_container_width=True)
