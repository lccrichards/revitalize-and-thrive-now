# Orchestrator Status & Recovery Plan

**Date**: Sep 18, 2026  
**Current Status**: Posting pipeline stalled since Jul 28 (52 days)  
**Last Verified Posts**: Jul 28, 2026 (Composio-based, working)

## Problem Summary

The daily posting orchestrator (4 triggers × 2 brands = 8 daily posts) stopped publishing after Jul 28, 2026, despite:
- ✓ Schedule firing reliably on time (confirmed by Sep 8 commits)
- ✓ Captions being generated correctly
- ✗ API keys missing from trigger environment

## Root Causes

### 1. Buffer API Key Missing (Jul 26 - Aug 6)
- **When**: Jul 26 - Aug 6
- **What happened**: Workflow switched to `scripts/auto_post_cross_platform.py` (Buffer-based)
- **Why it failed**: `BUFFER_API_KEY` not set in cron environment
- **Last attempted**: Aug 6 evening/afternoon slots
- **Evidence**: 50+ log entries with "BUFFER_API_KEY is not set" error

### 2. Higgsfield API Key Missing (Sep 7 - present)
- **When**: Sep 7 - present (Sep 8 commits show this)
- **What happened**: Workflow changed to use Higgsfield API directly instead of MCP
- **Why it failed**: `HIGGSFIELD_API_KEY` not set in environment
- **Status**: Triggers still firing, all blocked on same error
- **Evidence**: Sep 8 commits show "HIGGSFIELD_API_KEY not configured"

### 3. Orchestrator-log.json Corruption
- **Issue**: File has multiple JSON arrays concatenated (malformed)
- **Fixed**: Removed corrupted portion, restored 90 valid entries
- **Impact**: New entries can be appended normally going forward

## Working Components

### ✓ What's Ready to Use

1. **Composio Instagram Posting** (tested & working Jul 28)
   - Direct REST API integration
   - No Meta tokens needed
   - Account aliases confirmed:
     - Revitalize: `instagram_cardin-bulgar` (ig_user_id 27164026169935796)
     - Reclaim: `instagram_medlar-slap` (ig_user_id 27634679816148097)

2. **Master Orchestrator Script** (`scripts/master_orchestrator.py`)
   - Generates daily brief
   - Lists products for today's slots
   - Implements POST GUARD (duplicate prevention)

3. **Post Direct Script** (`scripts/post_direct.py`)
   - Generates AI content
   - Posts via Composio REST API
   - Requires: ANTHROPIC_API_KEY, COMPOSIO_API_KEY

4. **Unified Orchestrator** (`scripts/unified_orchestrator.py`) — NEW
   - Composio-based workflow (no Buffer)
   - Generates captions via Claude API
   - Posts to both brands
   - Logs results properly
   - Ready for trigger deployment

## Recovery Steps

### Immediate (Restore Posting)

1. **Deploy new trigger prompts** that use `unified_orchestrator.py`
   - Replace the current triggers (or create new ones) with prompts that:
     - Call `python3 scripts/unified_orchestrator.py --slot <slot>`
     - Require ENV: `ANTHROPIC_API_KEY`, `COMPOSIO_API_KEY`
     - Use the existing Higgsfield MCP for image generation (instead of API key)

2. **Environment Setup** (in trigger cron environment)
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export COMPOSIO_API_KEY="..."
   # HIGGSFIELD_API_KEY — not needed if using MCP
   # BUFFER_API_KEY — not needed if using Composio
   ```

3. **Test with manual run** (in a Claude Code session)
   ```bash
   cd /home/user/revitalize-and-thrive-now
   python3 scripts/unified_orchestrator.py --slot morning
   ```

### Backlog Recovery (Optional)

To post the missing Jul 28 - Sep 8 content:
- Review the orchestrator-config.json rotation for those dates
- Generate captions for each missing day/slot
- Use unified_orchestrator.py or post_direct.py to publish
- Update orchestrator-log.json with historical timestamps

### Long-term (Architecture)

The current trigger model (Claude Code spawning sessions) should:
1. Use MCP tools (Higgsfield, Composio) not API keys
2. Have Claude generate captions inline (not via external API)
3. Log results with proper JSON structure (no malformed concatenation)
4. Include duplicate guards and verification steps

## Files to Monitor

- `data/orchestrator-log.json` — append-only log (now healthy)
- `data/triggers.json` — current trigger definitions
- `scripts/unified_orchestrator.py` — ready for deployment
- `CLAUDE.md` — standing authorization for publishing

## Next Action

When API keys are available in the trigger environment, the unified_orchestrator.py is ready to use. Triggers can resume immediately with a prompt update pointing to this script.
