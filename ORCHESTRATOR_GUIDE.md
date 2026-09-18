# Orchestrator Quick Reference

## What It Does

The orchestrator automates daily Instagram posting for Revitalize & Thrive Now and Reclaim & Rise:
- **Frequency**: 4 slots per day × 2 brands = 8 posts daily
- **Slots**: Morning (7 AM), Afternoon (3 PM), Evening (7 PM), Night (10 PM ET)
- **Platforms**: Instagram (primary), Facebook (Revitalize auto-syncs)
- **Status**: Stalled since Jul 28 due to missing API keys in trigger environment

## Architecture

```
Triggers (4)
├── Morning (7:00 AM ET / 11:00 UTC)
├── Afternoon (3:00 PM ET / 19:00 UTC)  
├── Evening (7:00 PM ET / 23:00 UTC)
└── Night (10:00 PM ET / 02:00 UTC next day)
    ↓
Claude Code Remote Session (spawned by trigger)
    ↓
unified_orchestrator.py (or master_orchestrator.py)
    ├── Load brand & orchestrator config
    ├── Check duplicate guard
    ├── Generate captions (Claude API if available)
    ├── Generate images (Higgsfield MCP or placeholder)
    ├── Post via Composio MCP
    ├── Verify via INSTAGRAM_GET_IG_MEDIA
    └── Log to orchestrator-log.json
    ↓
Instagram Business Accounts
├── Revitalize & Thrive Now (ig_user_id: 27164026169935796)
└── Reclaim & Rise (ig_user_id: 27634679816148097)
```

## Files

### Configuration
- `data/brand-config.json` — Product catalog, voice guidelines, hashtag pools
- `data/orchestrator-config.json` — Daily schedule, weekly rotation, Higgsfield/Composio IDs
- `data/triggers.json` — Trigger definitions (3 ACTIVE, 1 PENDING)

### Scripts
- `scripts/master_orchestrator.py` — Print daily brief (what to post today)
- `scripts/unified_orchestrator.py` — Full orchestration (ready to use)
- `scripts/post_direct.py` — Manual posting tool (Composio-based)

### Logs
- `data/orchestrator-log.json` — All posted content (90 entries rolling window)

## Daily Rotation

Each day has a theme and products for each slot:

| Day | Theme | Morning | Afternoon | Evening | Night |
|-----|-------|---------|-----------|---------|-------|
| Mon | Hormone Balance | Hormone Reset | Hormone Meal Plan | Complete Bundle | Sleep Fix |
| Tue | Sleep Optimization | Sleep Fix | Sleep Fix | Sleep Fix | Sleep Fix |
| Wed | Energy Restoration | Energy Guide | Energy Guide | 30-Day Bundle | Sleep Fix |
| Thu | Mindset Reset | Mindset Bundle | Stress Workbook | Revitalize Circle | Stress Workbook |
| Fri | Nutrition | Nutrition Dive | Hormone Meal Plan | Complete Bundle | Revitalize Circle |
| Sat | Skincare & Beauty | Skincare Protocol | Skincare Protocol | Revitalize Circle | Skincare Protocol |
| Sun | Strength & Fitness | Fitness Guide | Fitness Guide | 30-Day Bundle | Revitalize Circle |

(Same structure for Reclaim with different products)

## Key Concepts

### Duplicate Guard
Before posting, the script checks if a post for this slot has already been made today (ET timezone):
```python
if already_posted_today("morning"):
    exit("POST GUARD: ALREADY POSTED TODAY")
```
This prevents accidental re-posting if a trigger fires multiple times.

### Composio Workflow
Posts to Instagram via 2-step process:
1. `INSTAGRAM_POST_IG_USER_MEDIA` — Create media container with image + caption
2. `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` — Publish the container
3. `INSTAGRAM_GET_IG_MEDIA` — Verify the post is live and get permalink

### Account Aliases
Composio uses entity IDs (account aliases) not raw user IDs:
- Revitalize: `instagram_cardin-bulgar` (ig_user_id 27164026169935796)
- Reclaim: `instagram_medlar-slap` (ig_user_id 27634679816148097)

## How to Use

### Run Manual Post (Testing)
```bash
cd /home/user/revitalize-and-thrive-now
export COMPOSIO_API_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"  # optional

python3 scripts/unified_orchestrator.py --slot morning
```

### Print Today's Brief
```bash
python3 scripts/master_orchestrator.py
```

### View Recent Posts
```bash
tail -10 data/orchestrator-log.json
```

## Troubleshooting

### "POST GUARD: ALREADY POSTED TODAY"
Normal behavior - duplicate detection working. The script exits to prevent re-posting.

### "COMPOSIO_API_KEY not set"
Set the environment variable:
```bash
export COMPOSIO_API_KEY="your_composio_key"
```

### "ANTHROPIC_API_KEY not set"
Optional - captions will use a fallback template. For better captions:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Images show as "placeholder"
Higgsfield image generation not wired up in this script version. Deploy through Claude Code Remote for full MCP access, or provide image URLs separately.

### Posts not appearing in log
Check:
1. `data/orchestrator-log.json` exists and is valid JSON
2. Script ran to completion (no errors)
3. `verified: true` field is set (post was confirmed live on Instagram)

## Standing Authorization

Per CLAUDE.md:
- Owner of this repository explicitly authorizes scheduled triggers to publish live to Instagram business accounts
- No per-run confirmation needed
- Account aliases: `instagram_cardin-bulgar` (Revitalize), `instagram_medlar-slap` (Reclaim)

## Next Steps

1. **Resume Posting** → Update trigger prompts to use `unified_orchestrator.py`
2. **Set API Keys** → Configure COMPOSIO_API_KEY + ANTHROPIC_API_KEY in trigger environment
3. **Test Run** → Manual execution in Claude Code session to verify workflow
4. **Backlog** → Optional: re-post missing Jul 28 - Sep 8 content if desired

See `ORCHESTRATOR_STATUS.md` for detailed recovery plan.
