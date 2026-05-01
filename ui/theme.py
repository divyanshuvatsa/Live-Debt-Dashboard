"""
JCL Debt Monitoring Dashboard — Theme & Configuration
Centralized color palette, typography, chart defaults.
"""

# =============================================================================
# COLOR PALETTE — Bloomberg-inspired, high-contrast
# =============================================================================
COLORS = {
    # Brand
    "navy":          "#0A2540",
    "navy_light":    "#1F3864",
    "blue":          "#2563EB",
    "blue_light":    "#60A5FA",
    "accent_gold":   "#F59E0B",

    # Status (covenant compliance)
    "compliant":     "#10B981",   # Emerald
    "watch":         "#3B82F6",   # Blue (5–10% headroom)
    "near_breach":   "#F59E0B",   # Amber (<5% headroom)
    "breach":        "#EF4444",   # Red
    "neutral":       "#6B7280",   # Gray

    # Backgrounds
    "bg_primary":    "#0F172A",   # Dark slate
    "bg_secondary":  "#1E293B",   # Card background
    "bg_tertiary":   "#334155",
    "bg_light":      "#F8FAFC",
    "card_dark":     "#1E293B",

    # Text
    "text_primary":   "#F1F5F9",  # Near-white
    "text_secondary": "#94A3B8",  # Muted
    "text_dim":       "#64748B",

    # Lender-specific (consistent across charts)
    "rbl":           "#3B82F6",   # Blue
    "ybl":           "#8B5CF6",   # Purple
    "bajaj":         "#F59E0B",   # Amber
    "icici":         "#EC4899",   # Pink
    "sib":           "#10B981",   # Green

    # Category
    "cat_fb":        "#3B82F6",
    "cat_nfb":       "#8B5CF6",
    "cat_term":      "#F59E0B",
    "cat_hedge":     "#10B981",
}

LENDER_COLORS = {
    "RBL Bank":          COLORS["rbl"],
    "YES Bank":          COLORS["ybl"],
    "Bajaj Finance":     COLORS["bajaj"],
    "ICICI Bank":        COLORS["icici"],
    "South Indian Bank": COLORS["sib"],
}

CATEGORY_COLORS = {
    "FB":            COLORS["cat_fb"],
    "FB-Term":       COLORS["cat_term"],
    "FB-FCY":        COLORS["blue_light"],
    "FB-FDbacked":   "#06B6D4",
    "NFB":           COLORS["cat_nfb"],
    "NFB-FDbacked":  "#A78BFA",
    "Hedge":         COLORS["cat_hedge"],
}

STATUS_COLORS = {
    "Compliant":   COLORS["compliant"],
    "Watch":       COLORS["watch"],
    "Near Breach": COLORS["near_breach"],
    "Breach":      COLORS["breach"],
    "N/A":         COLORS["neutral"],
}

# =============================================================================
# PLOTLY CHART DEFAULTS
# =============================================================================
CHART_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": COLORS["bg_secondary"],
    "plot_bgcolor": COLORS["bg_secondary"],
    "font": {
        "family": "Inter, Segoe UI, system-ui, -apple-system, sans-serif",
        "size": 13,
        "color": COLORS["text_primary"],
    },
}

# =============================================================================
# CSS for custom styling
# =============================================================================
CUSTOM_CSS = """
<style>
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main app background gradient */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #0A1628;
        border-right: 1px solid #334155;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #F1F5F9;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #2D3F58 100%);
        border: 1px solid #334155;
        border-left: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #F1F5F9 !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        line-height: 1.1;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    /* Tab styling */
    div[data-testid="stTabs"] button {
        background: transparent;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 20px;
        color: #94A3B8;
        font-weight: 600;
        margin-right: 6px;
        transition: all 0.2s ease;
    }
    div[data-testid="stTabs"] button:hover {
        background: #1E293B;
        color: #F1F5F9;
        border-color: #3B82F6;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
        color: #FFFFFF;
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #F1F5F9 !important;
        font-family: 'Inter', system-ui, sans-serif;
        letter-spacing: -0.02em;
    }
    h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #60A5FA 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    h2 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    h3 {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
    }

    /* Status pills */
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-compliant { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #10B981; }
    .status-watch     { background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid #3B82F6; }
    .status-near      { background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid #F59E0B; }
    .status-breach    { background: rgba(239, 68, 68, 0.15);  color: #EF4444; border: 1px solid #EF4444; }

    /* Custom covenant cards */
    .cov-card {
        background: #1E293B;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
        border-left: 4px solid #10B981;
        transition: transform 0.2s ease;
    }
    .cov-card:hover { transform: translateX(4px); }
    .cov-card.compliant { border-left-color: #10B981; }
    .cov-card.watch     { border-left-color: #3B82F6; }
    .cov-card.near      { border-left-color: #F59E0B; }
    .cov-card.breach    { border-left-color: #EF4444; }
    .cov-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .cov-card-title {
        font-weight: 700;
        color: #F1F5F9;
        font-size: 0.95rem;
    }
    .cov-card-lender {
        font-size: 0.7rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .cov-card-actual {
        font-size: 1.6rem;
        font-weight: 800;
        color: #F1F5F9;
        line-height: 1.1;
    }
    .cov-card-threshold {
        color: #94A3B8;
        font-size: 0.85rem;
        margin-top: 4px;
    }
    .cov-card-headroom {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .headroom-good   { color: #10B981; }
    .headroom-watch  { color: #60A5FA; }
    .headroom-warn   { color: #F59E0B; }
    .headroom-bad    { color: #EF4444; }

    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(59, 130, 246, 0.4);
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
    }

    /* Slider */
    div[data-testid="stSlider"] {
        padding: 8px 0;
    }

    /* Alert banner */
    .alert-banner {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(239, 68, 68, 0.1) 100%);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        color: #F1F5F9;
    }

    /* Logo / brand bar */
    .brand-bar {
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.1) 0%, transparent 100%);
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid #1E293B;
        margin-bottom: 16px;
    }
    .brand-title {
        font-size: 1.7rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60A5FA 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .brand-subtitle {
        color: #94A3B8;
        font-size: 0.85rem;
        margin-top: 4px;
    }

    /* Insight cards */
    .insight-card {
        background: linear-gradient(135deg, #1E293B 0%, #243449 100%);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border-left: 4px solid #3B82F6;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .insight-card:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    }
    .insight-card.good     { border-left-color: #10B981; background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, #1E293B 100%); }
    .insight-card.info     { border-left-color: #3B82F6; }
    .insight-card.neutral  { border-left-color: #6B7280; }
    .insight-card.warning  { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.12) 0%, #1E293B 100%); }
    .insight-card.danger   { border-left-color: #EF4444; background: linear-gradient(135deg, rgba(239,68,68,0.12) 0%, #1E293B 100%); }
    .insight-icon {
        font-size: 1.6rem;
        line-height: 1;
        flex-shrink: 0;
    }
    .insight-content { flex: 1; }
    .insight-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #F1F5F9;
        margin: 0 0 4px 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .insight-body {
        font-size: 0.92rem;
        color: #CBD5E1;
        line-height: 1.5;
        margin: 0;
    }

    /* Health gauge / score */
    .health-gauge {
        background: linear-gradient(135deg, #1E293B 0%, #2D3F58 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid #334155;
    }
    .health-score {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        margin: 8px 0;
    }
    .health-rating {
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .health-component {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        font-size: 0.85rem;
        color: #CBD5E1;
        border-bottom: 1px solid #334155;
    }
    .health-component:last-child { border-bottom: none; }
    .health-component-bar {
        width: 60px;
        height: 6px;
        background: #334155;
        border-radius: 3px;
        margin-left: 8px;
        overflow: hidden;
    }
    .health-component-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
        border-radius: 3px;
    }

    /* Section dividers */
    .section-divider {
        background: linear-gradient(90deg, transparent 0%, #334155 50%, transparent 100%);
        height: 1px;
        margin: 24px 0;
    }

    /* Tooltip on hover */
    .tooltip-icon {
        display: inline-block;
        width: 16px;
        height: 16px;
        line-height: 16px;
        text-align: center;
        background: #334155;
        color: #94A3B8;
        border-radius: 50%;
        font-size: 11px;
        cursor: help;
        margin-left: 4px;
    }
    .tooltip-icon:hover { background: #3B82F6; color: white; }

    /* Quick action buttons (scenario presets) */
    .quick-action {
        display: inline-block;
        padding: 8px 14px;
        margin: 4px 6px 4px 0;
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 999px;
        color: #CBD5E1;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .quick-action:hover {
        background: #2563EB;
        color: white;
        border-color: #3B82F6;
    }

    /* Narrative banner at top of tabs */
    .narrative-banner {
        background: linear-gradient(135deg, rgba(37,99,235,0.12) 0%, rgba(139,92,246,0.08) 100%);
        border: 1px solid rgba(96,165,250,0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 12px 0 20px 0;
    }
    .narrative-banner-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #60A5FA;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .narrative-banner-body {
        color: #E2E8F0;
        font-size: 0.95rem;
        line-height: 1.55;
    }

    /* Glossary entries */
    .glossary-entry {
        padding: 10px 14px;
        margin-bottom: 8px;
        background: #1E293B;
        border-radius: 8px;
        border-left: 3px solid #3B82F6;
    }
    .glossary-name {
        font-weight: 700;
        color: #F1F5F9;
        font-size: 0.95rem;
    }
    .glossary-formula {
        color: #94A3B8;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        margin: 4px 0;
    }
    .glossary-interpretation {
        color: #CBD5E1;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .glossary-rot {
        color: #60A5FA;
        font-size: 0.78rem;
        font-style: italic;
        margin-top: 4px;
    }

    /* Animated counter */
    @keyframes countUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    div[data-testid="stMetric"] {
        animation: countUp 0.5s ease-out;
    }

    /* Callout boxes */
    .callout-good {
        background: rgba(16,185,129,0.1);
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        color: #D1FAE5;
    }
    .callout-warn {
        background: rgba(245,158,11,0.1);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        color: #FED7AA;
    }
    .callout-info {
        background: rgba(59,130,246,0.1);
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        color: #DBEAFE;
    }

    /* Mini-stats inline */
    .mini-stat {
        display: inline-block;
        padding: 2px 10px;
        background: rgba(59,130,246,0.15);
        border-radius: 12px;
        color: #60A5FA;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0 4px;
    }

    /* === SENIOR MANAGEMENT HERO === */
    .hero-section {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #1E2A47 100%);
        border-radius: 20px;
        padding: 32px 36px;
        margin-bottom: 24px;
        border: 1px solid #334155;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(96,165,250,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-verdict-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 16px;
    }
    .hero-narrative {
        font-size: 1.25rem;
        line-height: 1.55;
        color: #F1F5F9;
        font-weight: 400;
        max-width: 780px;
        margin: 0;
    }
    .hero-narrative b { color: #FFFFFF; font-weight: 700; }

    /* === BIG KPI TILES (replace cramped 5-col) === */
    .big-kpi {
        background: linear-gradient(135deg, #1E293B 0%, #243449 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: left;
        border: 1px solid #334155;
        height: 100%;
    }
    .big-kpi-label {
        color: #94A3B8;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .big-kpi-value {
        color: #F1F5F9;
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 4px;
    }
    .big-kpi-sub {
        color: #94A3B8;
        font-size: 0.82rem;
        margin-top: 6px;
    }

    /* === RECOMMENDED ACTIONS === */
    .action-card {
        background: #1E293B;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        border-left: 4px solid #6B7280;
    }
    .action-card.HIGH    { border-left-color: #EF4444; background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, #1E293B 100%); }
    .action-card.MEDIUM  { border-left-color: #F59E0B; background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, #1E293B 100%); }
    .action-card.LOW     { border-left-color: #3B82F6; }
    .action-card.INFO    { border-left-color: #6B7280; }

    .action-priority {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        flex-shrink: 0;
        min-width: 70px;
        text-align: center;
    }
    .action-priority.HIGH    { background: #EF4444; color: white; }
    .action-priority.MEDIUM  { background: #F59E0B; color: #1E293B; }
    .action-priority.LOW     { background: #3B82F6; color: white; }
    .action-priority.INFO    { background: #6B7280; color: white; }

    .action-content { flex: 1; }
    .action-title {
        font-size: 1.0rem;
        font-weight: 700;
        color: #F1F5F9;
        margin-bottom: 4px;
    }
    .action-body {
        font-size: 0.88rem;
        color: #CBD5E1;
        line-height: 1.5;
    }
    .action-owner {
        font-size: 0.72rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 6px;
    }

    /* === STATUS LIGHTS (traffic-light style) === */
    .status-light-container {
        display: flex;
        gap: 16px;
        margin: 16px 0;
    }
    .status-light {
        background: #1E293B;
        border-radius: 12px;
        padding: 16px 20px;
        flex: 1;
        text-align: center;
        border: 1px solid #334155;
    }
    .status-light-dot {
        width: 16px; height: 16px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        vertical-align: middle;
        box-shadow: 0 0 12px currentColor;
    }
    .status-light-label {
        font-size: 0.72rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    .status-light-value {
        font-size: 1.6rem;
        font-weight: 800;
        margin-top: 6px;
    }

    /* === Tab section header (cleaner than markdown ##) === */
    .tab-header {
        margin: 24px 0 16px 0;
    }
    .tab-header-label {
        color: #60A5FA;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
    }
    .tab-header-title {
        color: #F1F5F9;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 4px 0 0 0;
        line-height: 1.2;
    }
    .tab-header-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 6px;
        max-width: 700px;
    }
</style>
"""
