"""
analysis_rules.py

Rule-based analysis for Google Ads performance data stored in SQLite.
Outputs a structured JSON with recommended actions for:
- Search terms (negative keyword candidates)
- Campaign scaling candidates (winners)
- Campaign pause/restructure candidates (losers)

Assumptions (per your project):
- SQLite file is at repo root: data.sqlite
- Tables: campaign_daily, search_term_daily
- Conversion value column in DB: conversions_value
"""

import sqlite3
from pathlib import Path
from datetime import date, timedelta
import json

# =========================
# MODE CONFIGURATION
# =========================
# Switch between:
# - "HISTORICAL": for initial/baseline evaluation using long window + stricter thresholds
# - "LIVE": for weekly ops (7-day decision window) + more aggressive thresholds
MODE = "HISTORICAL"  # "HISTORICAL" or "LIVE"

CONFIG = {
    "HISTORICAL": {
        "window_days": 180,
        "search_terms": {
            "min_clicks": 20,
            "min_cost": 30.0,  # BRL
        },
        "campaign_winners": {
            "min_roas": 1.2,
            "min_conversions": 2,
            "min_cost": 200.0,  # BRL
        },
        "campaign_losers": {
            "min_cost": 300.0,  # BRL
            "conversions_equals": 0,
        },
    },
    "LIVE": {
        "window_days": 7,
        "search_terms": {
            "min_clicks": 10,
            "min_cost": 20.0,  # BRL
        },
        "campaign_winners": {
            "min_roas": 1.2,
            "min_conversions": 2,
            "min_cost": 200.0,  # BRL
        },
        "campaign_losers": {
            "min_cost": 300.0,  # BRL
            "conversions_equals": 0,
        },
    },
}

# =========================
# PATHS
# =========================
DB_PATH = Path("data.sqlite")


def run_analysis() -> dict:
    if MODE not in CONFIG:
        raise ValueError(f"Invalid MODE={MODE}. Must be one of: {list(CONFIG.keys())}")

    cfg = CONFIG[MODE]
    window_days = int(cfg["window_days"])

    # Decision window start date (ISO)
    since = (date.today() - timedelta(days=window_days)).isoformat()

    # Read thresholds
    st_min_clicks = int(cfg["search_terms"]["min_clicks"])
    st_min_cost = float(cfg["search_terms"]["min_cost"])

    win_min_roas = float(cfg["campaign_winners"]["min_roas"])
    win_min_conv = float(cfg["campaign_winners"]["min_conversions"])
    win_min_cost = float(cfg["campaign_winners"]["min_cost"])

    lose_min_cost = float(cfg["campaign_losers"]["min_cost"])
    lose_conv_eq = float(cfg["campaign_losers"]["conversions_equals"])

    result = {
        "mode": MODE,
        "window_days": window_days,
        "generated_at": date.today().isoformat(),
        "thresholds": {
            "search_terms": {"min_clicks": st_min_clicks, "min_cost": st_min_cost, "conversions": 0},
            "campaign_winners": {"min_roas": win_min_roas, "min_conversions": win_min_conv, "min_cost": win_min_cost},
            "campaign_losers": {"min_cost": lose_min_cost, "conversions_equals": lose_conv_eq},
        },
        "campaign_actions": [],
        "search_term_actions": [],
    }

    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite DB not found at: {DB_PATH.resolve()}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # =========================
    # 1) SEARCH TERMS – NEGATIVES
    # =========================
    # Note: conversions_value isn't used for negative suggestion; we care about spend w/ 0 conv in window.
    cur.execute(
        """
        SELECT
          search_term,
          SUM(clicks) AS clicks,
          SUM(cost_micros) / 1e6 AS cost
        FROM search_term_daily
        WHERE date >= ?
          AND conversions = 0
        GROUP BY search_term
        HAVING clicks >= ? AND cost >= ?
        ORDER BY cost DESC
        """,
        (since, st_min_clicks, st_min_cost),
    )

    for term, clicks, cost in cur.fetchall():
        result["search_term_actions"].append(
            {
                "type": "ADD_NEGATIVE",
                "search_term": term,
                "clicks": int(clicks or 0),
                "cost": round(float(cost or 0.0), 2),
                "why": f"Spend with zero conversions in last {window_days} days (thresholds: clicks>={st_min_clicks}, cost>={st_min_cost})",
            }
        )

    # =========================
    # 2) CAMPAIGNS – WINNERS (SCALE)
    # =========================
    # ROAS = conversions_value / cost
    # We compute ROAS in SQL to filter winners efficiently.
    cur.execute(
        """
        SELECT
          campaign_name,
          SUM(cost_micros) / 1e6 AS cost,
          SUM(conversions) AS conv,
          SUM(conversions_value) AS conv_value,
          CASE
            WHEN SUM(cost_micros) > 0
            THEN (SUM(conversions_value) / (SUM(cost_micros) / 1e6))
            ELSE 0
          END AS roas
        FROM campaign_daily
        WHERE date >= ?
        GROUP BY campaign_name
        HAVING roas >= ?
           AND conv >= ?
           AND cost >= ?
        ORDER BY roas DESC
        """,
        (since, win_min_roas, win_min_conv, win_min_cost),
    )

    for name, cost, conv, conv_value, roas in cur.fetchall():
        result["campaign_actions"].append(
            {
                "type": "SCALE_WINNER",
                "campaign": name,
                "cost": round(float(cost or 0.0), 2),
                "conversions": round(float(conv or 0.0), 2),
                "conversions_value": round(float(conv_value or 0.0), 2),
                "roas": round(float(roas or 0.0), 2),
                "suggestion": "Increase budget gradually (+10–20%) or duplicate into a tighter structure (more specific keywords/ad groups).",
            }
        )

    # =========================
    # 3) CAMPAIGNS – LOSERS (PAUSE / RESTRUCTURE)
    # =========================
    cur.execute(
        """
        SELECT
          campaign_name,
          SUM(cost_micros) / 1e6 AS cost,
          SUM(conversions) AS conv
        FROM campaign_daily
        WHERE date >= ?
        GROUP BY campaign_name
        HAVING cost >= ?
           AND conv = ?
        ORDER BY cost DESC
        """,
        (since, lose_min_cost, lose_conv_eq),
    )

    for name, cost, conv in cur.fetchall():
        result["campaign_actions"].append(
            {
                "type": "PAUSE_OR_RESTRUCTURE",
                "campaign": name,
                "cost": round(float(cost or 0.0), 2),
                "conversions": round(float(conv or 0.0), 2),
                "why": f"High spend with zero conversions in last {window_days} days (threshold: cost>={lose_min_cost})",
            }
        )

    con.close()
    return result


if __name__ == "__main__":
    actions = run_analysis()
    with open("analysis_output.json", "w", encoding="utf-8") as f:
        json.dump(actions, f, indent=2, ensure_ascii=False)

    print(json.dumps(actions, indent=2, ensure_ascii=False))
