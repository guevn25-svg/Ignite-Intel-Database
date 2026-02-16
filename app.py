import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import feedparser
import time
from datetime import datetime
import altair as alt
import json
import os

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Ignite Consulting | Intelligence Platform",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# 2. ACCESS GATE
# ═══════════════════════════════════════════════════════════════════════════════
# Set your access code here — or load from st.secrets["ACCESS_CODE"] for deployment
# Load access code
ACCESS_CODE = "ignite2026"

def check_access():
    """Renders a login gate. Returns True only when the correct code is entered."""
    if st.session_state.get("authenticated"):
        return True

    # Center the login form
    st.markdown("""
    <style>
    .login-box {
        max-width: 380px; margin: 12vh auto; background: #fff;
        border: 1px solid #e5e5e5; border-radius: 12px;
        padding: 40px 36px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        text-align: center;
    }
    .login-box img { margin-bottom: 16px; }
    .login-box h3 { color: #0a0a0a; margin: 0 0 4px 0; font-size: 1.1rem; }
    .login-box p { color: #8b8b8b; font-size: 0.8rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
        <div class="login-box">
            <img src="https://cdn.prod.website-files.com/6797cb99fc99e75ad2d2c58a/6797ce0427a9531930570745_IC_Full_WT.png"
                 width="160" style="filter: invert(1);">
            <h3>Intelligence Platform</h3>
            <p>Enter your access code to continue</p>
        </div>
        """, unsafe_allow_html=True)

        code = st.text_input("Access Code", type="password", placeholder="Enter code...", label_visibility="collapsed")
        if st.button("Sign In", type="primary", use_container_width=True):
            if code == ACCESS_CODE:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code.")
    return False


if not check_access():
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# 3. COMPANY CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
CO = {
    "name": "Ignite Consulting, LLC",
    "short": "Ignite",
    "web": "ignitena.com",
    "logo_wt": "https://cdn.prod.website-files.com/6797cb99fc99e75ad2d2c58a/6797ce0427a9531930570745_IC_Full_WT.png",
    "substack": "https://igniteconsulting.substack.com/",
    "tagline": "Transform potential into lasting performance.",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. BRAND STYLING
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
:root {
    --ig-black:    #0a0a0a;
    --ig-charcoal: #141414;
    --ig-dark:     #1a1a1a;
    --ig-slate:    #2a2a2a;
    --ig-border:   #333333;
    --ig-muted:    #8b8b8b;
    --ig-light:    #e8e8e8;
    --ig-white:    #fafafa;
    --ig-accent:   #e8622a;
    --ig-accent-lt:#f0845a;
    --ig-blue:     #4a90d9;
    --ig-green:    #3d9970;
    --ig-red:      #cc4444;
    --ig-bg:       #f4f4f5;
}
.stApp { background-color: var(--ig-bg); font-family: 'Helvetica Neue', 'Segoe UI', sans-serif; }
h1, h2, h3, h4 { color: var(--ig-black); }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
}
section[data-testid="stSidebar"] * { color: var(--ig-light) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--ig-border) !important; opacity: 0.4; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.85rem !important; font-weight: 500 !important; padding: 2px 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    font-size: 1.4rem !important; font-weight: 700 !important; color: var(--ig-accent) !important;
}
section[data-testid="stSidebar"] .stMetric label {
    font-size: 0.6rem !important; text-transform: uppercase; letter-spacing: 0.08em;
}

.ig-card {
    background: #fff; border: 1px solid #e5e5e5; border-radius: 10px;
    padding: 22px 26px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); text-align: center;
}
.ig-card .val { font-size: 2.2rem; font-weight: 700; color: var(--ig-accent); line-height: 1.1; }
.ig-card .lbl {
    font-size: 0.7rem; color: var(--ig-muted); text-transform: uppercase;
    letter-spacing: 0.06em; margin-top: 4px;
}

.feed-card {
    background: #fff; padding: 16px 20px; border-radius: 8px;
    border: 1px solid #e5e5e5; margin-bottom: 10px; transition: border-color 0.15s;
}
.feed-card:hover { border-color: var(--ig-accent); }
.feed-card h4 { margin: 6px 0 2px 0; font-size: 0.95rem; color: var(--ig-black); }
.feed-card .meta { font-size: 0.8rem; color: var(--ig-muted); margin-bottom: 4px; }
.feed-card a { font-size: 0.78rem; color: var(--ig-accent); text-decoration: none; font-weight: 600; }
.feed-card a:hover { text-decoration: underline; }

.tag {
    display: inline-block; padding: 2px 9px; border-radius: 4px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
}
.tag-sec  { background: #e0ecff; color: #1e40af; }
.tag-warn { background: #fee2e2; color: #991b1b; }
.tag-news { background: #dcfce7; color: #166534; }

.section-hdr {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em;
    font-weight: 700; color: var(--ig-muted); padding-bottom: 6px;
    border-bottom: 2px solid #e5e5e5; margin-bottom: 14px;
}

div.stButton > button {
    border-radius: 6px; font-weight: 600; font-size: 0.82rem; transition: all 0.15s ease;
}
div.stButton > button:hover {
    transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stTextInput input {
    background: #fff; border: 1px solid #ddd; border-radius: 6px; font-size: 0.85rem;
}
.stTextInput input:focus {
    border-color: var(--ig-accent); box-shadow: 0 0 0 2px rgba(232,98,42,0.15);
}

section.main { overflow: auto !important; }
section.main > div.block-container { padding-bottom: 4rem; min-height: 100vh; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 4. GOOGLE SHEETS DATABASE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
#
#   SETUP INSTRUCTIONS (see guide below code):
#     1. Place your service account JSON at: credentials/service_account.json
#        OR store its contents in Streamlit secrets as GOOGLE_CREDS
#     2. Share your Google Sheet with the service account email
#     3. Set your SHEET_ID below (the long string from the Sheet URL)
#
# ═══════════════════════════════════════════════════════════════════════════════

# ── CONFIG: Replace this with your actual Google Sheet ID ──
# URL format: https://docs.google.com/spreadsheets/d/<THIS_PART>/edit
SHEET_ID = "1rBJ7i3_XNdXVH4yU4sQ1SLYx3Ds-PnKBvsL2QHMVqB4"
WORKSHEET_NAME = "Leads"  # Name of the tab inside the sheet

# Column headers — must match the first row of your Google Sheet exactly
HEADERS = ["id", "date_found", "company", "source", "event_type", "details", "link", "status"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_gsheet_connection():
    """Authenticate and return the worksheet object. Cached so it only runs once."""

    # Load credentials from local JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_creds_path = os.path.join(script_dir, "credentials", "trans-gate-487602-f9-3de95a294459.json")
    creds = Credentials.from_service_account_file(local_creds_path, scopes=SCOPES)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    # Get or create the worksheet
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(HEADERS))
        worksheet.append_row(HEADERS)  # Write header row

    return worksheet


def _ws():
    """Shortcut to get the cached worksheet."""
    return get_gsheet_connection()


def save_lead(company, source, event_type, details, link):
    """Append a new lead if the link doesn't already exist (dedup)."""
    ws = _ws()
    try:
        existing_links = ws.col_values(HEADERS.index("link") + 1)  # 1-indexed
        if link in existing_links:
            return False
    except Exception:
        pass

    next_id = len(ws.get_all_values())  # row count serves as auto-increment
    row = [
        next_id,
        datetime.now().strftime("%Y-%m-%d"),
        company,
        source,
        event_type,
        details,
        link,
        "New",
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    return True


@st.cache_data(ttl=20)
def get_all_leads():
    """Read entire sheet into a DataFrame. Cached for 20 seconds."""
    ws = _ws()
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return pd.DataFrame(columns=HEADERS)
    # Use first row as headers, normalize to lowercase/stripped
    raw_headers = [h.strip().lower().replace(" ", "_") for h in rows[0]]
    df = pd.DataFrame(rows[1:], columns=raw_headers)
    # Rename common mismatches to expected names
    rename_map = {
        "date": "date_found",
        "date_found": "date_found",
        "event": "event_type",
        "event_type": "event_type",
        "type": "event_type",
        "summary": "details",
        "details": "details",
        "url": "link",
        "link": "link",
        "name": "company",
        "company": "company",
        "source": "source",
        "status": "status",
    }
    df.columns = [rename_map.get(c, c) for c in df.columns]
    # Ensure all expected columns exist
    for col in HEADERS:
        if col not in df.columns:
            df[col] = ""
    return df[HEADERS]


def clear_lead_cache():
    get_all_leads.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. INTELLIGENCE SCANNERS
# ═══════════════════════════════════════════════════════════════════════════════
SCANNERS = {
    "SEC EDGAR": {"icon": "📑", "tag": "tag-sec", "desc": "8-K Executive Change Filings"},
    "Global News": {"icon": "📰", "tag": "tag-news", "desc": "CEO / CFO Appointment Coverage"},
    "WARN Notice": {"icon": "🚨", "tag": "tag-warn", "desc": "Mass Layoff & Plant Closing Alerts"},
}


def scan_sec_edgar():
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&start=0&count=40&output=atom"
    headers = {"User-Agent": "IgniteConsulting/1.0 (intel@ignitena.com)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        feed = feedparser.parse(resp.content)
        count = 0
        for entry in feed.entries:
            if "Item 5.02" in entry.get("title", "") or "Item 5.02" in entry.get("summary", ""):
                company = entry.title.split("(")[0].strip()
                if save_lead(company, "SEC EDGAR", "Executive Change (8-K)", entry.title, entry.link):
                    count += 1
        return count
    except Exception:
        return 0


def scan_google_news():
    query = "appointed%20CEO%20OR%20appointed%20CFO%20when:1d"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
        count = 0
        for entry in feed.entries[:10]:
            src = entry.get("source", {})
            src_title = src.get("title", "Unknown") if isinstance(src, dict) else getattr(src, "title", "Unknown")
            if save_lead(src_title, "Global News", "Press Mention", entry.title, entry.link):
                count += 1
        return count
    except Exception:
        return 0


def scan_warn_notices():
    mock = [
        ("TechFlow Logistics", "WARN Notice", "Mass Layoff (50+)", "Filing date: Today", "http://state.gov/warn/1"),
        ("Omega Manufacturing", "WARN Notice", "Plant Closing", "Filing date: Yesterday", "http://state.gov/warn/2"),
    ]
    return sum(1 for m in mock if save_lead(*m))


SCANNER_FUNCS = {
    "SEC EDGAR": scan_sec_edgar,
    "Global News": scan_google_news,
    "WARN Notice": scan_warn_notices,
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image(CO["logo_wt"], width=180)
    st.caption("Intelligence Platform")
    st.markdown("---")

    menu = st.radio("Navigation", ["Dashboard", "Live Scanner", "Database"], label_visibility="collapsed")

    st.markdown("---")
    df_side = get_all_leads()
    m1, m2 = st.columns(2)
    m1.metric("Total Leads", len(df_side))
    today_count = len(df_side[df_side["date_found"] == datetime.now().strftime("%Y-%m-%d")]) if not df_side.empty else 0
    m2.metric("New Today", today_count)

    st.markdown("---")
    st.caption("SOURCES ACTIVE")
    for name, meta in SCANNERS.items():
        st.markdown(f"{meta['icon']}  **{name}**")
    st.markdown("---")
    st.markdown(f"[🔗 Ignite Insights]({CO['substack']})")
    st.caption(f"© {datetime.now().year} {CO['name']}")
    st.caption("📊 Backend: Google Sheets")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. HELPER
# ═══════════════════════════════════════════════════════════════════════════════
def source_tag(source_name):
    meta = SCANNERS.get(source_name, {"tag": "tag-news"})
    return f'<span class="tag {meta["tag"]}">{source_name}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
# 8. PAGE — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if menu == "Dashboard":
    st.markdown("#### Executive Summary")
    st.caption("Real-time overview of automated lead generation across all active sources.")

    df = get_all_leads()

    if df.empty:
        st.info("No leads yet — head to **Live Scanner** to run your first scan.")
        st.stop()

    today_str = datetime.now().strftime("%Y-%m-%d")
    metrics = [
        ("Total Leads", len(df)),
        ("New Today", len(df[df["date_found"] == today_str])),
        ("SEC 8-K Events", len(df[df["source"] == "SEC EDGAR"])),
        ("WARN Notices", len(df[df["source"] == "WARN Notice"])),
    ]
    cols = st.columns(len(metrics))
    for col, (label, val) in zip(cols, metrics):
        col.markdown(
            f'<div class="ig-card"><div class="val">{val}</div><div class="lbl">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    left, right = st.columns([1.3, 1], gap="large")

    with left:
        st.markdown('<div class="section-hdr">Lead Source Breakdown</div>', unsafe_allow_html=True)
        chart_data = df["source"].value_counts().reset_index()
        chart_data.columns = ["Source", "Count"]
        chart = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Source:N", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Count:Q"),
                color=alt.Color(
                    "Source:N",
                    scale=alt.Scale(
                        domain=["SEC EDGAR", "Global News", "WARN Notice"],
                        range=["#4a90d9", "#3d9970", "#cc4444"],
                    ),
                    legend=None,
                ),
            )
            .properties(height=280)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.markdown('<div class="section-hdr">Latest Activity</div>', unsafe_allow_html=True)
        for _, row in df.head(5).iterrows():
            st.markdown(
                f"""<div class="feed-card">
                    {source_tag(row['source'])}
                    <span style="float:right;color:#999;font-size:0.75rem;">{row['date_found']}</span>
                    <h4>{row['company']}</h4>
                    <div class="meta">{row['event_type']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# 9. PAGE — LIVE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "Live Scanner":
    st.markdown("#### Live Intelligence Scanner")
    st.caption("Trigger automated agents across all registered sources.")

    ctrl, feed = st.columns([1, 2], gap="large")

    with ctrl:
        st.markdown('<div class="section-hdr">Control Center</div>', unsafe_allow_html=True)
        run_choices = {}
        for name, meta in SCANNERS.items():
            run_choices[name] = st.checkbox(f"{meta['icon']}  {name}", value=True, help=meta["desc"])

        st.markdown("")
        if st.button("🚀 Run Selected Scanners", type="primary", use_container_width=True):
            total = 0
            active = {k: v for k, v in run_choices.items() if v}
            if not active:
                st.warning("Select at least one source.")
            else:
                with st.status("Initializing Agents...", expanded=True) as status:
                    for name in active:
                        st.write(f"🔌 Connecting to {name}...")
                        n = SCANNER_FUNCS[name]()
                        st.write(f"✅ {name}: **{n}** new lead(s)")
                        total += n
                    status.update(label="Scan complete", state="complete", expanded=False)
                clear_lead_cache()
                st.success(f"**Done.** {total} new lead(s) captured across {len(active)} source(s).")
                time.sleep(0.8)
                st.rerun()

    with feed:
        st.markdown('<div class="section-hdr">Recent Raw Feed</div>', unsafe_allow_html=True)
        df = get_all_leads()
        if df.empty:
            st.info("No data yet — run a scan.")
        else:
            for _, row in df.head(10).iterrows():
                st.markdown(
                    f"""<div class="feed-card">
                        {source_tag(row['source'])}
                        <span style="float:right;color:#999;font-size:0.75rem;">{row['date_found']}</span>
                        <h4>{row['company']}</h4>
                        <div class="meta">{row['event_type']}</div>
                        <a href="{row['link']}" target="_blank">View source →</a>
                    </div>""",
                    unsafe_allow_html=True,
                )

# ═══════════════════════════════════════════════════════════════════════════════
# 10. PAGE — DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "Database":
    st.markdown("#### Lead Database")
    st.caption("Master registry — editable live at Google Sheets.")

    df = get_all_leads()

    if df.empty:
        st.info("Database is empty — run the scanner to populate.")
        st.stop()

    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search = st.text_input("🔍 Search", placeholder="Company, type, details...")
    with f2:
        sources = ["All"] + sorted(df["source"].unique().tolist())
        src_filter = st.selectbox("Source", sources)
    with f3:
        statuses = ["All"] + sorted(df["status"].unique().tolist())
        stat_filter = st.selectbox("Status", statuses)

    filtered = df.copy()
    if search:
        mask = filtered.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
        filtered = filtered[mask]
    if src_filter != "All":
        filtered = filtered[filtered["source"] == src_filter]
    if stat_filter != "All":
        filtered = filtered[filtered["status"] == stat_filter]

    st.markdown(f"**{len(filtered)}** records")
    st.dataframe(
        filtered,
        use_container_width=True,
        column_config={
            "link": st.column_config.LinkColumn("Source Link"),
            "date_found": "Date",
            "details": "Summary",
        },
        hide_index=True,
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Export CSV",
            csv,
            f"ignite_leads_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
        )
    with c2:
        st.link_button(
            "📊 Open Google Sheet",     
            f"https://docs.google.com/spreadsheets/d/{"1rBJ7i3_XNdXVH4yU4sQ1SLYx3Ds-PnKBvsL2QHMVqB4"}/edit",
        )