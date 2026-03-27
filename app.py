import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from agents.orchestrator import Orchestrator

load_dotenv()

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ArthaRakshak",
    page_icon="🛡️",
    layout="wide",
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ ArthaRakshak")
    st.caption("Enterprise Cost Intelligence System")
    st.divider()

    # Paste your NVIDIA API key here — or set NVIDIA_API_KEY in your .env file
    api_key = st.text_input(
        "NVIDIA API Key",
        value=os.getenv("NVIDIA_API_KEY", ""),
        type="password",
        help="Get your key at build.nvidia.com → API Catalog",
    )

    if api_key:
        st.success("API key loaded")
    else:
        st.warning("Paste your NVIDIA API key above")

    st.divider()
    st.markdown("**ET AI Hackathon 2026 — Track 3**")
    st.markdown("Powered by NVIDIA LLaMA-3.1-70B")
    st.markdown("Modules: Vendor Dedup + SLA Risk")

# ─── Session state ────────────────────────────────────────────────────────────
if "vendor_results" not in st.session_state:
    st.session_state.vendor_results = None
if "sla_results" not in st.session_state:
    st.session_state.sla_results = None

tab_dashboard, tab_vendor, tab_sla = st.tabs(
    ["📊 Dashboard", "🔍 Vendor Deduplication", "⏰ SLA Risk Monitor"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dashboard:
    st.header("Cost Intelligence Dashboard")

    if (
        st.session_state.vendor_results is None
        and st.session_state.sla_results is None
    ):
        st.info(
            "Run an analysis in the Vendor or SLA tabs to populate this dashboard."
        )

    vendor_savings = 0
    sla_penalty    = 0
    dup_groups     = 0
    sla_risk       = "N/A"

    if st.session_state.vendor_results:
        vr             = st.session_state.vendor_results
        vendor_savings = vr.get("total_savings", 0)
        dup_groups     = len(vr.get("duplicate_groups", []))

    if st.session_state.sla_results:
        sr          = st.session_state.sla_results
        sla_penalty = sr.get("financial_risk", 0)
        sla_risk    = sr.get("risk_level", "N/A")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendor Savings Found",    f"Rs {vendor_savings:,.0f}")
    c2.metric("Duplicate Vendor Groups", dup_groups)
    c3.metric("SLA Penalty at Risk",     f"Rs {sla_penalty:,.0f}")
    c4.metric("SLA Risk Level",          sla_risk)

    if vendor_savings > 0 or sla_penalty > 0:
        st.divider()
        total_impact = vendor_savings + sla_penalty
        st.success(f"### Total Financial Impact Identified: Rs {total_impact:,.0f}")

    # Savings bar chart
    if st.session_state.vendor_results:
        groups = st.session_state.vendor_results.get("duplicate_groups", [])
        if groups:
            st.subheader("Savings by Vendor Group")
            chart_df = pd.DataFrame(
                [
                    {
                        "Vendor Group":       g["canonical_name"][:30],
                        "Annual Savings (Rs)": g["savings"],
                        "Duplicates":         g["count"],
                    }
                    for g in groups
                ]
            )
            fig = px.bar(
                chart_df,
                x="Vendor Group",
                y="Annual Savings (Rs)",
                color="Annual Savings (Rs)",
                color_continuous_scale="Blues",
                title="Estimated Annual Savings per Vendor Group",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Audit log
    all_logs: list = []
    if st.session_state.vendor_results:
        all_logs.extend(st.session_state.vendor_results.get("audit_log", []))
    if st.session_state.sla_results:
        all_logs.extend(st.session_state.sla_results.get("audit_log", []))

    if all_logs:
        st.subheader("Agent Decision Audit Trail")
        st.caption("Every decision by every agent — timestamped and traceable.")
        st.dataframe(
            pd.DataFrame(all_logs), use_container_width=True, hide_index=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — VENDOR DEDUPLICATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_vendor:
    st.header("Vendor Deduplication Agent")
    st.caption(
        "Upload vendor data → AI detects duplicates → "
        "Calculates savings → Generates action plan"
    )

    uploaded_vendor = st.file_uploader(
        "Upload Vendor CSV",
        type=["csv"],
        key="vendor_upload",
        help="Use data/sample_vendors.csv to test",
    )

    if uploaded_vendor is not None:
        df_vendors = pd.read_csv(uploaded_vendor)
        st.subheader(f"Loaded {len(df_vendors)} vendors")
        st.dataframe(df_vendors, use_container_width=True, hide_index=True)

        if not api_key:
            st.warning("Paste your NVIDIA API key in the sidebar before running.")

        run_vendor = st.button(
            "🔍 Run Vendor Deduplication Analysis", type="primary"
        )

        if run_vendor:
            if not api_key:
                st.error("NVIDIA API key is required. Add it in the sidebar.")
            else:
                try:
                    with st.status("Agents working...", expanded=True) as status:
                        st.write("🤖 Orchestrator: Starting vendor analysis pipeline...")
                        st.write("🔍 Scanner Agent: Running fuzzy name matching...")
                        st.write("💰 Finance Agent: Calculating savings...")
                        st.write(
                            "📋 Advisor Agent: Calling NVIDIA LLaMA API "
                            "for action plan..."
                        )
                        orch    = Orchestrator(api_key)
                        results = orch.run_vendor_analysis(df_vendors)
                        st.session_state.vendor_results = results
                        status.update(label="Analysis complete!", state="complete")

                    groups        = results["duplicate_groups"]
                    total_savings = results["total_savings"]

                    if not groups:
                        st.success(
                            "No duplicate vendors found. Your vendor data looks clean!"
                        )
                    else:
                        st.success(
                            f"## 💰 Total Annual Savings Identified: "
                            f"Rs {total_savings:,.0f}"
                        )
                        col_a, col_b = st.columns(2)
                        col_a.metric("Duplicate Groups Found", len(groups))
                        col_b.metric(
                            "Vendors That Can Be Eliminated",
                            sum(g["count"] - 1 for g in groups),
                        )

                        st.divider()
                        st.subheader("Duplicate Vendor Groups")

                        for i, group in enumerate(groups, 1):
                            with st.expander(
                                f"Group {i}: {group['canonical_name']}  —  "
                                f"Save Rs {group['savings']:,.0f}/year  "
                                f"({group['count']} duplicates)",
                                expanded=(i <= 2),
                            ):
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Vendors in Group",  group["count"])
                                m2.metric(
                                    "Total Spent",
                                    f"Rs {group['total_group_spend']:,.0f}",
                                )
                                m3.metric(
                                    "Estimated Savings",
                                    f"Rs {group['savings']:,.0f}",
                                )
                                vdf      = pd.DataFrame(group["vendors"])
                                show_col = [
                                    c
                                    for c in [
                                        "vendor_id",
                                        "vendor_name",
                                        "service_category",
                                        "annual_spend",
                                    ]
                                    if c in vdf.columns
                                ]
                                st.dataframe(vdf[show_col], hide_index=True)

                        st.divider()
                        st.subheader("AI-Generated Action Plan")
                        st.caption(
                            "Written by NVIDIA LLaMA-3.1-70B based on your findings."
                        )
                        st.markdown(results["action_plan"])

                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    st.info(
                        "Check that your NVIDIA API key is correct and that "
                        "you have credits at build.nvidia.com"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SLA RISK MONITOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_sla:
    st.header("SLA Risk Monitor")
    st.caption(
        "Upload task data → AI predicts breach risk → "
        "Finds bottlenecks → Writes recovery plan"
    )

    uploaded_tasks = st.file_uploader(
        "Upload Task Tracker CSV",
        type=["csv"],
        key="sla_upload",
        help="Use data/sample_tasks.csv to test",
    )

    if uploaded_tasks is not None:
        df_tasks = pd.read_csv(uploaded_tasks)
        st.subheader(f"Loaded {len(df_tasks)} tasks")
        st.dataframe(df_tasks, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("SLA Parameters")
        p1, p2, p3 = st.columns(3)
        with p1:
            contract_tasks = st.number_input(
                "Total tasks contracted",
                min_value=1,
                value=20,
                help="How many tasks were agreed in the contract?",
            )
        with p2:
            days_remaining = st.number_input(
                "Days remaining in SLA",
                min_value=1,
                value=8,
                help="Calendar days left until deadline",
            )
        with p3:
            penalty_per_day = st.number_input(
                "Daily penalty (Rs)",
                min_value=0,
                value=50000,
                help="Rupees charged per day of breach",
            )

        if not api_key:
            st.warning("Paste your NVIDIA API key in the sidebar before running.")

        run_sla = st.button("⚡ Assess SLA Risk", type="primary")

        if run_sla:
            if not api_key:
                st.error("NVIDIA API key is required. Add it in the sidebar.")
            else:
                try:
                    with st.status("Agents working...", expanded=True) as status:
                        st.write("🤖 Orchestrator: Starting SLA analysis pipeline...")
                        st.write("📊 Tracker Agent: Measuring completion rate...")
                        st.write("⚠️  Risk Agent: Predicting SLA breach...")
                        st.write(
                            "📋 Recovery Agent: Calling NVIDIA LLaMA API "
                            "for recovery plan..."
                        )
                        st.write(
                            "📧 Recovery Agent: Generating escalation email..."
                        )
                        orch        = Orchestrator(api_key)
                        sla_results = orch.run_sla_analysis(
                            df_tasks,
                            int(contract_tasks),
                            int(days_remaining),
                            float(penalty_per_day),
                        )
                        st.session_state.sla_results = sla_results
                        status.update(label="Analysis complete!", state="complete")

                    risk_level = sla_results["risk_level"]

                    if risk_level == "HIGH":
                        st.error(f"## 🔴 SLA RISK: {risk_level}")
                    elif risk_level == "MEDIUM":
                        st.warning(f"## 🟡 SLA RISK: {risk_level}")
                    else:
                        st.success(f"## 🟢 SLA RISK: {risk_level}")

                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Tasks Completed",  sla_results["tasks_completed"])
                    r2.metric("Tasks Remaining",  sla_results["tasks_remaining"])
                    r3.metric(
                        "Predicted Miss",
                        f"{sla_results['predicted_miss_days']} days",
                    )
                    r4.metric(
                        "Financial Penalty Risk",
                        f"Rs {sla_results['financial_risk']:,.0f}",
                    )

                    # Gauge chart
                    pct_done = sla_results["tasks_completed"] / max(
                        int(contract_tasks), 1
                    )
                    fig_gauge = go.Figure(
                        go.Indicator(
                            mode="gauge+number+delta",
                            value=round(pct_done * 100, 1),
                            title={"text": "Task Completion %"},
                            delta={"reference": 100},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar":  {"color": "#185FA5"},
                                "steps": [
                                    {"range": [0,  40], "color": "#FCEBEB"},
                                    {"range": [40, 75], "color": "#FAEEDA"},
                                    {"range": [75,100], "color": "#EAF3DE"},
                                ],
                                "threshold": {
                                    "line":      {"color": "#E24B4A", "width": 4},
                                    "thickness": 0.75,
                                    "value":     80,
                                },
                            },
                            number={"suffix": "%"},
                        )
                    )
                    fig_gauge.update_layout(height=280, margin=dict(t=40, b=20))
                    st.plotly_chart(fig_gauge, use_container_width=True)

                    # Pace comparison chart
                    pace_df = pd.DataFrame(
                        {
                            "Metric": ["Current pace", "Required pace"],
                            "Tasks per day": [
                                sla_results["current_rate"],
                                sla_results["required_rate"],
                            ],
                        }
                    )
                    fig_pace = px.bar(
                        pace_df,
                        x="Metric",
                        y="Tasks per day",
                        color="Metric",
                        color_discrete_map={
                            "Current pace":  "#378ADD",
                            "Required pace": "#E24B4A",
                        },
                        title="Current vs Required Completion Rate",
                    )
                    fig_pace.update_layout(showlegend=False)
                    st.plotly_chart(fig_pace, use_container_width=True)

                    # Bottlenecks table
                    bottlenecks = sla_results.get("bottlenecks", [])
                    if bottlenecks:
                        st.subheader(f"Bottlenecks Found ({len(bottlenecks)})")
                        st.caption(
                            "These blocked tasks are slowing delivery."
                        )
                        st.dataframe(
                            pd.DataFrame(bottlenecks),
                            use_container_width=True,
                            hide_index=True,
                        )

                    st.divider()
                    st.subheader("AI Recovery Plan")
                    st.caption(
                        "Generated by NVIDIA LLaMA-3.1-70B based on your project."
                    )
                    st.markdown(sla_results["recovery_plan"])

                    st.divider()
                    st.subheader("Auto-Generated Escalation Email")
                    st.caption("Copy and send this to your manager.")
                    st.code(sla_results["escalation_email"], language=None)

                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    st.info(
                        "Check that your NVIDIA API key is correct and that "
                        "you have credits at build.nvidia.com"
                    )