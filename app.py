import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinTrack · Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  
  .main { background: #0f1117; }
  
  /* KPI cards */
  .kpi-card {
    background: linear-gradient(135deg, #1e2130 0%, #252836 100%);
    border: 1px solid #2d3148;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
  }
  .kpi-label { color: #8b8fa8; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
  .kpi-value { font-size: 26px; font-weight: 700; }
  .kpi-sub   { font-size: 12px; color: #8b8fa8; margin-top: 4px; }
  .kpi-pos   { color: #22c55e; }
  .kpi-neg   { color: #ef4444; }
  .kpi-neu   { color: #f8fafc; }
  .kpi-warn  { color: #f59e0b; }

  /* Section headers */
  .section-title {
    font-size: 13px; font-weight: 600; color: #8b8fa8;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 28px 0 14px; border-bottom: 1px solid #2d3148; padding-bottom: 8px;
  }

  /* Sidebar */
  [data-testid="stSidebar"] { background: #161826; border-right: 1px solid #2d3148; }
  
  /* Insight box */
  .insight {
    background: #1a2236; border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0; padding: 10px 14px;
    font-size: 13px; color: #a5b4fc; margin: 6px 0;
    line-height: 1.5;
  }
  
  /* Crypto card */
  .crypto-card {
    background: #1e2130; border: 1px solid #2d3148;
    border-radius: 12px; padding: 16px 18px;
  }
  .crypto-name  { font-size: 14px; font-weight: 600; color: #f8fafc; }
  .crypto-price { font-size: 22px; font-weight: 700; color: #f8fafc; margin: 4px 0; }
  .crypto-change-pos { font-size: 13px; color: #22c55e; font-weight: 500; }
  .crypto-change-neg { font-size: 13px; color: #ef4444; font-weight: 500; }
  
  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
COLORS = {
    "income":  "#22c55e",
    "expense": "#ef4444",
    "savings": "#6366f1",
    "neutral": "#64748b",
    "chart":   ["#6366f1","#8b5cf6","#ec4899","#f59e0b","#22c55e","#14b8a6","#3b82f6","#f97316"],
}

def fmt_inr(val):
    val = abs(val)
    if val >= 1e7:  return f"₹{val/1e7:.2f}Cr"
    if val >= 1e5:  return f"₹{val/1e5:.2f}L"
    if val >= 1000: return f"₹{val/1000:.1f}K"
    return f"₹{val:.0f}"

@st.cache_data(ttl=300)
def fetch_crypto():
    """Fetch live prices from CoinGecko (free, no API key)."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana,binancecoin,cardano",
            "vs_currencies": "inr,usd",
            "include_24hr_change": "true",
        }
        r = requests.get(url, params=params, timeout=8)
        return r.json()
    except:
        return None
@st.cache_data
def load_data(uploaded=None):
    if uploaded:
        # Reset file pointer and check if file has content
        uploaded.seek(0)
        content = uploaded.read()
        if not content or len(content.strip()) == 0:
            st.error("❌ The uploaded file is empty. Please upload a valid CSV.")
            return pd.DataFrame()
        
        # Try different separators (comma, semicolon, tab)
        uploaded.seek(0)
        df = None
        for sep in [",", ";", "\t", "|"]:
            try:
                uploaded.seek(0)
                df = pd.read_csv(uploaded, sep=sep)
                if len(df.columns) > 1:
                    break
            except Exception:
                continue
        
        if df is None or df.empty or len(df.columns) < 2:
            st.error("❌ Could not parse this CSV. Make sure it has headers and at least 2 columns.")
            return pd.DataFrame()

        # Auto-detect and rename columns
        col_map = {}
        for col in df.columns:
            c = col.lower().strip()
            if c in ["date", "transaction date", "trans date", "txn date", "value date"]:
                col_map[col] = "date"
            elif c in ["amount", "debit", "credit", "value", "sum", "inr", "rs"]:
                col_map[col] = "amount"
            elif c in ["category", "cat", "expense type", "head"]:
                col_map[col] = "category"
            elif c in ["subcategory", "sub category", "sub-category", "description",
                       "narration", "particulars", "remarks"]:
                col_map[col] = "subcategory"
        df = df.rename(columns=col_map)

        # Add missing columns with safe defaults
        if "date"        not in df.columns: df["date"]        = pd.Timestamp.today()
        if "amount"      not in df.columns: df["amount"]      = 0
        if "category"    not in df.columns: df["category"]    = "Other"
        if "subcategory" not in df.columns: df["subcategory"] = "Other"
        if "type"        not in df.columns:
            df["type"] = df["amount"].apply(lambda x: "income" if float(str(x).replace(",","") or 0) > 0 else "expense")
        
        df["amount"] = pd.to_numeric(
            df["amount"].astype(str).str.replace(",", "").str.replace("₹", "").str.strip(),
            errors="coerce"
        ).abs().fillna(0)

    else:
        df = pd.read_csv("transactions.csv")

    df["date"]      = pd.to_datetime(df["date"], errors="coerce")
    df              = df.dropna(subset=["date"])
    df["month_num"] = df["date"].dt.month
    df["month"]     = df["date"].dt.strftime("%b")
    return df

    if uploaded:
        df = pd.read_csv(uploaded)
        # Auto-detect and rename common column name variations
        col_map = {}
        for col in df.columns:
            c = col.lower().strip()
            if c in ["date", "transaction date", "trans date", "txn date", "value date"]:
                col_map[col] = "date"
            elif c in ["amount", "debit", "credit", "value", "sum", "inr", "rs"]:
                col_map[col] = "amount"
            elif c in ["category", "cat", "type", "expense type", "head"]:
                col_map[col] = "category"
            elif c in ["subcategory", "sub category", "sub-category", "description", "narration", "particulars", "remarks"]:
                col_map[col] = "subcategory"
        df = df.rename(columns=col_map)

        # Add missing columns with defaults so app doesn't crash
        if "date"        not in df.columns: df["date"]        = pd.Timestamp.today()
        if "amount"      not in df.columns: df["amount"]      = 0
        if "category"    not in df.columns: df["category"]    = "Other"
        if "subcategory" not in df.columns: df["subcategory"] = "Other"
        if "type"        not in df.columns:
            df["type"] = df["amount"].apply(lambda x: "income" if x > 0 else "expense")
        df["amount"] = df["amount"].abs()
    else:
        df = pd.read_csv("transactions.csv")

    df["date"]      = pd.to_datetime(df["date"], errors="coerce")
    df              = df.dropna(subset=["date"])
    df["month_num"] = df["date"].dt.month
    df["month"]     = df["date"].dt.strftime("%b")
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 FinTrack")
    st.markdown("<div style='color:#8b8fa8;font-size:12px;margin-bottom:20px'>Personal Finance Dashboard</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("📂 Upload your CSV", type="csv",
                                 help="Upload your own transactions CSV or use the demo data")

    st.markdown("---")
    st.markdown("**📅 Filter by Month**")
    months = ["All", "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    sel_month = st.selectbox("Month", months, index=0)

    st.markdown("**🗂️ Filter by Category**")
    df_raw = load_data(uploaded)
    cat_col = df_raw["category"]
    if isinstance(cat_col, pd.DataFrame):
        cat_col = cat_col.iloc[:, 0]
    if df_raw.empty:
        all_cats = ["All"]
    else:
        cat_col = df_raw["category"]
        if isinstance(cat_col, pd.DataFrame):
            cat_col = cat_col.iloc[:, 0]
        all_cats = ["All"] + sorted(cat_col.dropna().unique().tolist())
    sel_cat = st.selectbox("Category", all_cats)

    st.markdown("---")
    st.markdown("**₿ Crypto Portfolio**")
    btc_qty  = st.number_input("Bitcoin (BTC)",  value=0.05, step=0.01, format="%.4f")
    eth_qty  = st.number_input("Ethereum (ETH)", value=0.5,  step=0.1,  format="%.4f")
    sol_qty  = st.number_input("Solana (SOL)",   value=5.0,  step=1.0,  format="%.2f")
    bnb_qty  = st.number_input("BNB",            value=1.0,  step=0.5,  format="%.2f")

    st.markdown("---")
    st.markdown("<div style='color:#8b8fa8;font-size:11px'>Data refreshes every 5 minutes<br>Prices via CoinGecko API</div>", unsafe_allow_html=True)

# ── Load & filter data ────────────────────────────────────────────────────────
df = load_data(uploaded)
if sel_month != "All":
    month_map = {m: i+1 for i, m in enumerate(months[1:])}
    df = df[df["month_num"] == month_map[sel_month]]
if sel_cat != "All":
    cat_series = df["category"]
    if isinstance(cat_series, pd.DataFrame):
        cat_series = cat_series.iloc[:, 0]
    df = df[cat_series == sel_cat]

income_df  = df[df["type"] == "income"]
expense_df = df[df["type"] == "expense"]

total_income  = income_df["amount"].sum()
total_expense = expense_df["amount"].sum()
net_savings   = total_income - total_expense
savings_rate  = (net_savings / total_income * 100) if total_income > 0 else 0

# ── Header ────────────────────────────────────────────────────────────────────
period = sel_month if sel_month != "All" else "Jan – Dec 2024"
st.markdown(f"## Personal Finance Dashboard")
st.markdown(f"<div style='color:#8b8fa8;font-size:13px;margin-bottom:1.5rem'>Period: {period} &nbsp;·&nbsp; {len(df):,} transactions</div>", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Total Income</div>
      <div class="kpi-value kpi-pos">{fmt_inr(total_income)}</div>
      <div class="kpi-sub">All income sources</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Total Expenses</div>
      <div class="kpi-value kpi-neg">{fmt_inr(total_expense)}</div>
      <div class="kpi-sub">All categories</div>
    </div>""", unsafe_allow_html=True)

with k3:
    color = "kpi-pos" if net_savings >= 0 else "kpi-neg"
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Net Savings</div>
      <div class="kpi-value {color}">{fmt_inr(net_savings)}</div>
      <div class="kpi-sub">Income minus expenses</div>
    </div>""", unsafe_allow_html=True)

with k4:
    rate_color = "kpi-pos" if savings_rate >= 20 else ("kpi-warn" if savings_rate >= 10 else "kpi-neg")
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Savings Rate</div>
      <div class="kpi-value {rate_color}">{savings_rate:.1f}%</div>
      <div class="kpi-sub">Target: 20%+</div>
    </div>""", unsafe_allow_html=True)

# ── Monthly Trend ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Monthly Overview</div>", unsafe_allow_html=True)

monthly = df.groupby(["month_num", "month", "type"])["amount"].sum().reset_index()
monthly_pivot = monthly.pivot_table(index=["month_num","month"], columns="type", values="amount", fill_value=0).reset_index()
monthly_pivot = monthly_pivot.sort_values("month_num")
monthly_pivot["savings"] = monthly_pivot.get("income", 0) - monthly_pivot.get("expense", 0)

fig_trend = go.Figure()
if "income" in monthly_pivot.columns:
    fig_trend.add_trace(go.Scatter(
        x=monthly_pivot["month"], y=monthly_pivot["income"],
        name="Income", line=dict(color="#22c55e", width=2.5),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.08)",
        mode="lines+markers", marker=dict(size=6)
    ))
if "expense" in monthly_pivot.columns:
    fig_trend.add_trace(go.Scatter(
        x=monthly_pivot["month"], y=monthly_pivot["expense"],
        name="Expenses", line=dict(color="#ef4444", width=2.5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.08)",
        mode="lines+markers", marker=dict(size=6)
    ))
if "savings" in monthly_pivot.columns:
    fig_trend.add_trace(go.Bar(
        x=monthly_pivot["month"], y=monthly_pivot["savings"],
        name="Net Savings", marker_color=[
            "#22c55e" if v >= 0 else "#ef4444" for v in monthly_pivot["savings"]
        ], opacity=0.7, yaxis="y2"
    ))

fig_trend.update_layout(
    height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b8fa8", size=12),
    legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, color="#8b8fa8"),
    yaxis=dict(showgrid=True, gridcolor="#2d3148", color="#8b8fa8", title="Amount (₹)"),
    yaxis2=dict(overlaying="y", side="right", showgrid=False, color="#8b8fa8", title="Savings (₹)"),
    margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Expense Breakdown ─────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Expense Breakdown</div>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    cat_exp = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False).reset_index()
    cat_exp["pct"] = (cat_exp["amount"] / cat_exp["amount"].sum() * 100).round(1)

    fig_donut = go.Figure(go.Pie(
        labels=cat_exp["category"], values=cat_exp["amount"],
        hole=0.6, marker_colors=COLORS["chart"],
        textinfo="label+percent", textfont_size=12,
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
    ))
    fig_donut.update_layout(
        height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b8fa8"), showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
        annotations=[dict(text=f"Total<br><b>{fmt_inr(total_expense)}</b>",
                          x=0.5, y=0.5, font_size=13, font_color="#f8fafc", showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    fig_bar = px.bar(
        cat_exp, x="amount", y="category", orientation="h",
        color="pct", color_continuous_scale=["#312e81","#6366f1","#a5b4fc"],
        text=cat_exp["amount"].apply(fmt_inr),
    )
    fig_bar.update_traces(textposition="outside", textfont_size=11)
    fig_bar.update_layout(
        height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b8fa8"), coloraxis_showscale=False,
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, color="#c4c9e0", categoryorder="total ascending"),
        margin=dict(l=10, r=60, t=20, b=10),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Top Spending Subcategories ─────────────────────────────────────────────────
st.markdown("<div class='section-title'>Top Spending Subcategories</div>", unsafe_allow_html=True)

top_sub = expense_df.groupby("subcategory")["amount"].sum().sort_values(ascending=False).head(10).reset_index()
fig_sub = px.bar(
    top_sub, x="subcategory", y="amount",
    color="amount", color_continuous_scale=["#4f46e5","#a855f7","#ec4899"],
    text=top_sub["amount"].apply(fmt_inr),
)
fig_sub.update_traces(textposition="outside", textfont_size=11)
fig_sub.update_layout(
    height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b8fa8"), coloraxis_showscale=False,
    xaxis=dict(showgrid=False, color="#8b8fa8"),
    yaxis=dict(showgrid=True, gridcolor="#2d3148", visible=False),
    margin=dict(l=10, r=10, t=20, b=10),
)
st.plotly_chart(fig_sub, use_container_width=True)

# ── Income vs Expense Waterfall ───────────────────────────────────────────────
st.markdown("<div class='section-title'>Income vs Expense Waterfall</div>", unsafe_allow_html=True)

income_cats = income_df.groupby("subcategory")["amount"].sum().to_dict()
expense_cats = expense_df.groupby("category")["amount"].sum().nlargest(5).to_dict()

labels  = list(income_cats.keys()) + list(expense_cats.keys()) + ["Net Savings"]
measures = ["relative"] * len(income_cats) + ["relative"] * len(expense_cats) + ["total"]
values   = list(income_cats.values()) + [-v for v in expense_cats.values()] + [net_savings]
colors_wf = (["#22c55e"] * len(income_cats) +
             ["#ef4444"] * len(expense_cats) +
             ["#6366f1" if net_savings >= 0 else "#ef4444"])

fig_wf = go.Figure(go.Waterfall(
    name="", orientation="v", measure=measures,
    x=labels, y=values, text=[fmt_inr(abs(v)) for v in values],
    textposition="outside", textfont=dict(size=11, color="#c4c9e0"),
    connector=dict(line=dict(color="#2d3148", width=1, dash="dot")),
    increasing=dict(marker_color="#22c55e"),
    decreasing=dict(marker_color="#ef4444"),
    totals=dict(marker_color="#6366f1"),
))
fig_wf.update_layout(
    height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b8fa8"),
    xaxis=dict(showgrid=False, color="#8b8fa8"),
    yaxis=dict(showgrid=True, gridcolor="#2d3148", visible=False),
    margin=dict(l=10, r=10, t=20, b=10),
    showlegend=False,
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── AI Insights ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Smart Insights</div>", unsafe_allow_html=True)

insights = []
if savings_rate < 10:
    insights.append(f"⚠️ Your savings rate is <b>{savings_rate:.1f}%</b> — below the recommended 20%. Consider reducing your top 2 expense categories.")
elif savings_rate >= 20:
    insights.append(f"✅ Great job! Your savings rate of <b>{savings_rate:.1f}%</b> is above the 20% benchmark.")

if not expense_df.empty:
    top_cat = expense_df.groupby("category")["amount"].sum().idxmax()
    top_amt  = expense_df.groupby("category")["amount"].sum().max()
    pct = top_amt / total_expense * 100
    insights.append(f"🔍 <b>{top_cat}</b> is your biggest expense at {fmt_inr(top_amt)} ({pct:.1f}% of total spending).")

if not income_df.empty:
    top_income = income_df.groupby("subcategory")["amount"].sum().idxmax()
    insights.append(f"💼 <b>{top_income}</b> is your primary income source — consider diversifying with more freelance or passive income.")

if net_savings > 0:
    inv = expense_df[expense_df["category"] == "Investment"]["amount"].sum() if "Investment" in expense_df["category"].values else 0
    inv_pct = inv / total_income * 100 if total_income > 0 else 0
    insights.append(f"📈 You're investing <b>{fmt_inr(inv)}</b> ({inv_pct:.1f}% of income). The 50/30/20 rule recommends at least 20% in savings + investments.")

for ins in insights:
    st.markdown(f'<div class="insight">{ins}</div>', unsafe_allow_html=True)

# ── Crypto Portfolio ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Live Crypto Portfolio</div>", unsafe_allow_html=True)

crypto_data = fetch_crypto()

holdings = {
    "bitcoin":     {"symbol": "BTC", "qty": btc_qty,  "color": "#f7931a"},
    "ethereum":    {"symbol": "ETH", "qty": eth_qty,  "color": "#627eea"},
    "solana":      {"symbol": "SOL", "qty": sol_qty,  "color": "#9945ff"},
    "binancecoin": {"symbol": "BNB", "qty": bnb_qty,  "color": "#f0b90b"},
}

cols = st.columns(4)
total_crypto_inr = 0
crypto_breakdown = []

for i, (coin_id, info) in enumerate(holdings.items()):
    with cols[i]:
        if crypto_data and coin_id in crypto_data:
            price_inr = crypto_data[coin_id].get("inr", 0)
            price_usd = crypto_data[coin_id].get("usd", 0)
            change_24h = crypto_data[coin_id].get("inr_24h_change", 0) or 0
            val_inr = price_inr * info["qty"]
            total_crypto_inr += val_inr
            crypto_breakdown.append({"coin": info["symbol"], "value": val_inr})

            chg_class = "crypto-change-pos" if change_24h >= 0 else "crypto-change-neg"
            chg_icon  = "▲" if change_24h >= 0 else "▼"
            status = "🟢 LIVE" if crypto_data else "🔴 OFFLINE"

            st.markdown(f"""
            <div class="crypto-card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div class="crypto-name">{info['symbol']}</div>
                <div style="font-size:10px;color:#8b8fa8">{status}</div>
              </div>
              <div class="crypto-price">{fmt_inr(price_inr)}</div>
              <div class="{chg_class}">{chg_icon} {abs(change_24h):.2f}% (24h)</div>
              <div style="margin-top:8px;font-size:12px;color:#8b8fa8">{info['qty']} {info['symbol']} = <b style="color:#f8fafc">{fmt_inr(val_inr)}</b></div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="crypto-card">
              <div class="crypto-name">{info['symbol']}</div>
              <div style="color:#8b8fa8;font-size:12px;margin-top:8px">Unable to fetch live price.<br>Check your internet connection.</div>
            </div>""", unsafe_allow_html=True)

# Crypto portfolio chart
if crypto_breakdown:
    st.markdown("")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div class="kpi-card" style="margin-top:8px">
          <div class="kpi-label">Total Crypto Value</div>
          <div class="kpi-value kpi-warn">{fmt_inr(total_crypto_inr)}</div>
          <div class="kpi-sub">Across {len(crypto_breakdown)} assets</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        crypto_df = pd.DataFrame(crypto_breakdown)
        fig_crypto = px.pie(
            crypto_df, names="coin", values="value", hole=0.55,
            color_discrete_sequence=["#f7931a","#627eea","#9945ff","#f0b90b"],
        )
        fig_crypto.update_layout(
            height=160, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b8fa8", size=11),
            legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)", y=-0.1),
            margin=dict(l=0, r=0, t=0, b=10), showlegend=True,
        )
        fig_crypto.update_traces(textinfo="percent", textfont_size=11)
        st.plotly_chart(fig_crypto, use_container_width=True)

# ── Transaction Table ─────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Recent Transactions</div>", unsafe_allow_html=True)

recent = df.sort_values("date", ascending=False).head(20)[
    ["date", "category", "subcategory", "amount", "type"]
].copy()
recent["date"]   = recent["date"].dt.strftime("%d %b %Y")
recent["amount"] = recent["amount"].apply(lambda x: f"₹{x:,.0f}")
recent["type"]   = recent["type"].str.capitalize()
st.dataframe(recent, use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#8b8fa8;font-size:12px'>"
    "FinTrack · Built with Python & Streamlit · Live crypto prices via CoinGecko API"
    "</div>",
    unsafe_allow_html=True
)
