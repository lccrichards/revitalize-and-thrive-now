#!/usr/bin/env python3
"""
Simple Orchestrator for Revitalize & Thrive Now + Reclaim & Rise

This is a STREAMLINED version that skips metric collection and posts directly.
Used when the full orchestrator metric dependencies are unavailable.

EXECUTION: When a daily trigger fires, Claude executes this script's logic:
1. Determine day/slot from trigger time
2. Load product rotation from config
3. Generate captions (Claude does this inline)
4. Generate images via Higgsfield MCP
5. Post via Composio Instagram
6. Log results

This script is NOT run from terminal. It's documentation + briefing for Claude.
"""

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"


def get_time_slot() -> str:
    """Map ET time to posting slot."""
    now_et = datetime.now(ZoneInfo("America/New_York"))
    hour_et = now_et.hour

    if 6 <= hour_et < 12:
        return "morning"
    elif 12 <= hour_et < 18:
        return "afternoon"
    elif 18 <= hour_et < 22:
        return "evening"
    elif 22 <= hour_et < 24:
        return "night"
    else:
        return "morning"


def get_day_name() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%A").lower()


def load_configs():
    with open(CONFIG_PATH) as f:
        brand_cfg = json.load(f)
    with open(ORCH_CONFIG_PATH) as f:
        orch_cfg = json.load(f)
    return brand_cfg, orch_cfg


def get_product(brand_cfg: dict, brand: str, product_name: str) -> dict:
    """Find a product by name in the brand config."""
    for p in brand_cfg[brand]["products"]:
        if p["name"] == product_name:
            return p
    return brand_cfg[brand]["products"][0]


def _et_date_str() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def already_posted_today(slot: str) -> bool:
    """Check if we already posted this slot today."""
    if not LOG_PATH.exists():
        return False
    try:
        with open(LOG_PATH) as f:
            log = json.load(f)
    except Exception:
        return False
    today = _et_date_str()
    for e in log:
        if e.get("slot") != slot:
            continue
        same_day = today in str(e.get("date", ""))
        ts = str(e.get("timestamp_utc", ""))
        if not same_day and ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
                same_day = dt.strftime("%Y-%m-%d") == today
            except Exception:
                pass
        if same_day:
            rev = e.get("revitalize", {})
            rec = e.get("reclaim", {})
            if (rev.get("verified") is True or rev.get("status") == "posted" or
                rec.get("verified") is True or rec.get("status") == "posted"):
                return True
    return False


def print_daily_brief(day: str, slot: str, brand_cfg: dict, orch_cfg: dict):
    """Print execution brief for Claude."""
    rev_rotation = orch_cfg["revitalize_rotation"][day]
    rec_rotation = orch_cfg["reclaim_rotation"][day]
    rev_product_name = rev_rotation["slot_products"][slot]
    rec_product_name = rec_rotation["slot_products"][slot]
    slot_info = orch_cfg["schedule"][slot]

    print(f"\n{'='*70}")
    print(f"SIMPLE ORCHESTRATOR — {slot.upper()} SLOT")
    print(f"Day: {day.title()}  |  Time: {slot_info['time_et']} ET")
    print(f"Date (ET): {_et_date_str()}")
    print(f"{'='*70}")

    if already_posted_today(slot):
        print("🛑 POST GUARD: ALREADY POSTED TODAY")
        print("   Do not post again. Exit here.\n")
        return
    else:
        print("✅ POST GUARD: OK to proceed — no verified post for this slot today.")

    print(f"\n📲 REVITALIZE AND THRIVE NOW")
    print(f"   Theme   : {rev_rotation['theme']}")
    print(f"   Product : {rev_product_name}")
    print(f"   Angle   : {slot_info['angle']}")

    print(f"\n👨 RECLAIM AND RISE")
    print(f"   Theme   : {rec_rotation['theme']}")
    print(f"   Product : {rec_product_name}")
    print(f"   Angle   : {slot_info['angle']}")

    print(f"\n🎯 Tone: {slot_info['tone']}")
    print(f"{'='*70}\n")

    print("EXECUTION STEPS:")
    print("1. Generate Revitalize caption (use CTA formula from config)")
    print("2. Generate Reclaim caption (use CTA formula from config)")
    print("3. Call Higgsfield to generate 2 images (women for Revitalize, men for Reclaim)")
    print("4. Post to Instagram via Composio (both accounts)")
    print("5. Verify each post is live (INSTAGRAM_GET_IG_MEDIA)")
    print("6. Append to orchestrator-log.json with full metadata")
    print("7. Push changes to branch\n")


if __name__ == "__main__":
    import sys
    slot_arg = sys.argv[1] if len(sys.argv) > 1 else None
    slot = slot_arg if slot_arg in ("morning", "afternoon", "evening", "night") else get_time_slot()
    day = get_day_name()

    brand_cfg, orch_cfg = load_configs()
    print_daily_brief(day, slot, brand_cfg, orch_cfg)
