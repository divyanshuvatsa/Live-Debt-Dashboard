"""
JCL Debt Monitoring Dashboard — AI Analyst (Groq Powered)
===========================================================


Setup:
  1. Go to https://console.groq.com/keys
  2. Sign up with email (no Google account needed, no credit card)
  3. Copy your API key
  4. Add to .streamlit/secrets.toml:
     GROQ_API_KEY = "gsk_..."
  5. Restart the app
"""

import json
import logging
import os
from typing import Generator, List

logger = logging.getLogger(__name__)

_CLIENT = None
_API_KEY: str = ""
_INIT_ATTEMPTED = False


def _get_api_key() -> str:
    """Read API key from env var first, then Streamlit secrets."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass
    return key


def _ensure_client():
    """Lazy-initialise the Groq client on first use."""
    global _CLIENT, _API_KEY, _INIT_ATTEMPTED
    if _INIT_ATTEMPTED:
        return _CLIENT
    _INIT_ATTEMPTED = True

    _API_KEY = _get_api_key()
    if not _API_KEY:
        logger.info("No GROQ_API_KEY found — AI features disabled")
        return None

    try:
        import groq
        _CLIENT = groq.Groq(api_key=_API_KEY)
        logger.info("Groq client initialised (Mixtral-8x7B)")
        return _CLIENT
    except Exception as e:
        logger.warning(f"Groq init failed: {e}")
        return None


def is_ai_available() -> bool:
    """Quick check whether AI is available."""
    return _ensure_client() is not None


def _build_portfolio_context(logic, controls) -> str:
    """Build a comprehensive context string for the LLM."""
    import pandas as pd

    ls = logic.lender_summary()
    cov_df = logic.calculate_covenants(controls.get("ebitda_change", 0))
    interest = logic.calculate_annual_interest(
        controls.get("rate_shock", 0),
        controls.get("spread_shock", 0),
    )
    f = logic.financials[logic.basis]
    breaches = cov_df[cov_df["Status"] == "Breach"]
    near = cov_df[cov_df["Status"] == "Near Breach"]
    watch = cov_df[cov_df["Status"] == "Watch"]

    breach_text = (
        ", ".join(f"{r['Lender']} {r['Covenant']}"
                  for _, r in breaches.iterrows())
        if len(breaches) > 0 else "None"
    )

    near_text = "None"
    if len(near) > 0:
        near_text = ", ".join(
            f"{r['Lender']} {r['Covenant']} ({r['Headroom_Pct']:.1f}% headroom)"
            for _, r in near.iterrows()
        )

    watch_text = "None"
    if len(watch) > 0:
        watch_text = ", ".join(
            f"{r['Lender']} {r['Covenant']}"
            for _, r in watch.iterrows()
        )

    lender_summary_text = ls[
        ["Lender", "Total_Sanction", "FB_Sanction", "NFB_Sanction",
         "TL_Sanction", "Weighted_Avg_Cost"]
    ].to_string(index=False, float_format=lambda x: f"{x:.2f}")

    stress_active = (
        controls.get("rate_shock", 0) != 0
        or controls.get("spread_shock", 0) != 0
        or controls.get("ebitda_change", 0) != 0
    )

    context = f"""You are an expert credit analyst for Jindal Coke Limited (JCL), a leading Indian coke manufacturer with CARE A+; Stable / A1 rating. You answer questions accurately based ONLY on the data below. If something isn't in the data, say "this is not in my context" and suggest where the user could look.

═══════════════════════════════════════════════════════════
CURRENT PORTFOLIO STATE — As of {logic.as_of_date.strftime('%d-%b-%Y')}
Financial Basis: {logic.basis}  |  FX: ₹{logic.fx_rate}/USD
═══════════════════════════════════════════════════════════

PORTFOLIO TOTALS
- Total Sanctioned: ₹{ls['Total_Sanction'].sum():,.1f} Cr across 34 facilities, 5 lenders
- FB Sanctioned: ₹{ls['FB_Sanction'].sum():,.1f} Cr  |  NFB: ₹{ls['NFB_Sanction'].sum():,.1f} Cr  |  TL: ₹{ls['TL_Sanction'].sum():,.1f} Cr
- Annual Run-Rate Cost: ₹{interest['fb_interest']:.1f} Cr (FB interest) + ₹{interest['nfb_commission']:.1f} Cr (NFB commission)
- Weighted Avg Cost (FB only): {logic.weighted_avg_cost()*100:.2f}%

LENDER BREAKDOWN
{lender_summary_text}

FINANCIALS ({logic.basis})
- EBITDA: ₹{f['EBITDA']:.2f} Cr
- Total Debt: ₹{f['Total Debt']:.2f} Cr  |  Term Debt: ₹{f['Term Debt']:.2f} Cr
- TNW: ₹{f['TNW']:.2f} Cr  |  ATNW: ₹{f['ATNW']:.2f} Cr
- Interest Expense (P&L): ₹{f['Interest Expense']:.2f} Cr
- Net Fixed Assets: ₹{f['Fixed Assets']:.2f} Cr
- Current Assets: ₹{f['Current Assets']:.2f} Cr  |  Current Liabilities: ₹{f['Current Liabilities']:.2f} Cr
- TOL: ₹{f['TOL']:.2f} Cr

COVENANT STATUS ({len(cov_df)} total)
- Compliant: {(cov_df['Status']=='Compliant').sum()}
- Watch (5–10% headroom): {len(watch)}  →  {watch_text}
- Near Breach (<5% headroom): {len(near)}  →  {near_text}
- Breach: {len(breaches)}  →  {breach_text}

TERM LOANS
1. RBL Bank: ₹200 Cr @ ~9.75% indicative | 24m moratorium | Matures Oct-2029 | DSCR>1.25x
2. YES Bank: ₹320.7 Cr @ 7.70% (3M T-Bill + 252bps) | Matures Sep-2036 | DSCR>1.20x
3. Bajaj Finance: ₹150 Cr @ 8.60% (BFRR + 10bps) | 12m moratorium | Matures Aug-2033

KEY WATCH ITEMS
- SIB Current Ratio: 1.386x vs >1.33x threshold (4.2% headroom)
- RBL is largest lender at 43.5% — concentration to watch
"""

    if stress_active:
        context += f"""
⚠ STRESS SETTINGS CURRENTLY APPLIED
- Rate shock: {controls.get('rate_shock', 0):+d} bps
- Spread shock: {controls.get('spread_shock', 0):+d} bps
- EBITDA change: {controls.get('ebitda_change', 0):+d}%
The numbers above reflect these stress overlays.
"""

    context += """
═══════════════════════════════════════════════════════════

INSTRUCTIONS:
- Be concise and quantitative. Use ₹ Cr for amounts, x for ratios.
- Link every number to the data above.
- If speculating, clearly mark assumptions.
- Don't make up sanction terms — only cite what's listed above.
- Format with headers and bullets for multi-part answers.
"""
    return context


def stream_ai_response(prompt: str, logic, controls) -> Generator[str, None, None]:
    """
    Generator that yields text chunks. Use with st.write_stream().
    """
    client = _ensure_client()
    if client is None:
        yield (
            "🔌 **AI not configured.**\n\n"
            "To enable the AI Analyst, get a free Groq API key:\n\n"
            "1. Go to https://console.groq.com/keys\n"
            "2. Sign up with email (no credit card needed)\n"
            "3. Copy your API key\n"
            "4. Add to `.streamlit/secrets.toml`: `GROQ_API_KEY = \"gsk_...\"`\n\n"
            "Free tier: 14,400 requests/day (more than enough)"
        )
        return

    context = _build_portfolio_context(logic, controls)
    full_prompt = f"{context}\n\nUSER QUESTION:\n{prompt}"

    try:
        response = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": full_prompt}],
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "429" in err:
            yield (
                "⚠ **Groq quota exceeded.** "
                "Free tier allows 14,400 requests/day. Wait a moment and try again."
            )
        elif "api key" in err.lower() or "401" in err or "403" in err:
            yield (
                "⚠ **API key issue.** "
                "Verify your GROQ_API_KEY is correct at https://console.groq.com/keys"
            )
        else:
            yield f"⚠ Groq error: {err}"


def get_proactive_insights(logic, controls) -> List[dict]:
    """
    Generate 3 non-obvious insights about the portfolio.
    Returns [] if AI isn't available.
    """
    client = _ensure_client()
    if client is None:
        return []

    context = _build_portfolio_context(logic, controls)
    prompt = f"""{context}

GENERATE 3 NON-OBVIOUS INSIGHTS

Each insight must be something a CFO would not immediately spot from the raw numbers. Cover:
1. A risk the headline numbers might be UNDERSTATING.
2. An OPTIMISATION OPPORTUNITY (cost reduction, refinancing, restructuring).
3. A FORWARD-LOOKING concern (12-24 months out).

Respond ONLY with a JSON array, no prose or markdown fences. Schema:
[
  {{"title": "Short 4-7 word title", "body": "1-2 sentence explanation with specific numbers"}},
  {{"title": "...", "body": "..."}},
  {{"title": "...", "body": "..."}}
]"""

    try:
        response = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=800,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.lstrip().startswith("json"):
                text = text.split("\n", 1)[1]
        text = text.strip().rstrip("`").strip()

        insights = json.loads(text)
        if not isinstance(insights, list):
            return []
        clean = []
        for ins in insights[:3]:
            if isinstance(ins, dict) and "title" in ins and "body" in ins:
                clean.append({"title": str(ins["title"]), "body": str(ins["body"])})
        return clean
    except Exception as e:
        logger.warning(f"Proactive insights failed: {e}")
        return []


SUGGESTED_QUESTIONS = [
    "What is the biggest risk in this portfolio right now?",
    "Which covenant is most likely to breach if EBITDA drops 15%?",
    "How does JCL's leverage compare to industry norms for coke manufacturers?",
    "What should we prioritise in the next lender review meeting?",
    "Explain the SIB Current Ratio issue and how to fix it.",
    "What is the impact of a 50bps RBI rate hike on our annual interest bill?",
    "Which term loan should we consider prepaying first, and why?",
    "How does our RBL concentration risk affect us if they tighten lending?",
    "What is our refinancing risk profile over the next 3 years?",
    "Give me a 5-bullet summary for a board presentation tomorrow.",
]