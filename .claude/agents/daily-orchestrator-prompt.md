# Daily Campaign Orchestrator — Execution Prompt

**When a scheduled trigger fires at 7 AM, 3 PM, 7 PM, or 10 PM ET, execute this workflow.**

---

## STEP 0: Pre-Flight Check

Run `python3 scripts/simple_orchestrator.py <slot>` to print today's brief and verify you're not double-posting.

If output says "🛑 POST GUARD: ALREADY POSTED TODAY" → **STOP. Exit. Do not proceed.**

Otherwise, continue to Step 1.

---

## STEP 1: Load Configuration & Determine Today's Post

1. Load `data/orchestrator-config.json` and `data/brand-config.json`
2. Determine today's day name and time slot
3. Get the product rotation for today:
   - Revitalize: `orchestrator-config.revitalize_rotation[day][slot_products][slot]`
   - Reclaim: `orchestrator-config.reclaim_rotation[day][slot_products][slot]`
4. Get the slot's angle and tone from `orchestrator-config.schedule[slot]`

---

## STEP 2: Generate Captions

### Revitalize Caption
Use the **CTA Formula** from `orchestrator-config.cta_formula.revitalize.templates`:
- Look up the template matching today's theme (sleep, hormone, energy)
- If template exists:
  - `[hook] + [product + $price] + [shop_url] + [urgency] + [hashtags]`
- If no template, generate an on-brand variant using the tone and theme

**Example:**
```
💤 Better sleep tonight → better everything tomorrow.

Get the Midlife Sleep Fix for $39
👇
https://lccrichards.github.io/revitalize-and-thrive-now/shop.html

Start tonight.

#HormoneBalance #WomenOver45 #MidlifeWellness
```

### Reclaim Caption
Use the **CTA Formula** from `orchestrator-config.cta_formula.reclaim.templates`:
- Look up the template matching today's theme (testosterone, mindset, bundle)
- Same structure as Revitalize

**Example:**
```
Your testosterone didn't disappear. You just stopped doing what makes it rise.

Get the Testosterone & Stamina Meal Plan for $39
👇
https://reclaimandrisenow.com/shop.html

Science-based. No fluff. Results.

#MensHealth #Testosterone #MidlifeMen #PerformanceEdge #MenOver45
```

---

## STEP 3: Generate Images via Higgsfield

Call `mcp__higgsfield__generate_image` with:

### For Revitalize
- **Prompt Template** (from `orchestrator-config.higgsfield.revitalize_image_prompt_template`):
  ```
  Professional woman aged 45-65, {mood}, {setting}, warm natural light, 
  photorealistic portrait, confident and radiant expression, wellness lifestyle, 
  clean composition. STRICTLY WOMEN ONLY — no men in frame.
  ```
- **Mood** (from `orchestrator-config.higgsfield.moods[slot]`): morning, afternoon, evening, or night mood text
- **Setting** (from `orchestrator-config.higgsfield.revitalize_settings[today_theme]`): theme-specific background
- **Model**: `gpt_image_2` (photorealistic)
- **Style**: Professional wellness portrait

**Example filled prompt:**
```
Professional woman aged 45-65, energized and focused morning light fresh start energy, 
bright kitchen with herbal teas and whole foods on counter, warm natural light, 
photorealistic portrait, confident and radiant expression, wellness lifestyle, 
clean composition. STRICTLY WOMEN ONLY — no men in frame.
```

### For Reclaim
- **Prompt Template** (from `orchestrator-config.higgsfield.reclaim_image_prompt_template`):
  ```
  Professional man aged 45-55, {mood}, {setting}, clean modern environment, 
  photorealistic, sharp focused expression, high-performance lifestyle. 
  STRICTLY MEN ONLY — no women in frame.
  ```
- **Mood**: Same as Revitalize (from moods[slot])
- **Setting**: (from `orchestrator-config.higgsfield.reclaim_settings[today_theme]`)
- **Model**: `gpt_image_2`

### Execution
- Call `generate_image` for each brand
- Wait for both to complete (use `job_display` to poll)
- Store image URLs

---

## STEP 4: Post to Instagram via Composio

For **EACH brand** (Revitalize, then Reclaim):

### 4a. Create Media Container
```
Call: mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL

Action: INSTAGRAM_POST_IG_USER_MEDIA
Params:
  - account: (revitalize_thrive_now_real OR reclaim_and_rise_now)
  - image_url: (from Higgsfield result)
  - caption: (from Step 2)
```

Response: `media_container_id`

### 4b. Publish the Post
```
Call: mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL

Action: INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH
Params:
  - account: (same as above)
  - media_id: (media_container_id from 4a)
```

Response: `ig_post_id`, `ig_permalink`

### 4c. Verify Post is Live (MANDATORY)
```
Call: mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL

Action: INSTAGRAM_GET_IG_MEDIA
Params:
  - account: (same account)
  - media_id: (ig_post_id from 4b)
```

Verify response includes:
- `caption`: matches your caption
- `media_type`: IMAGE
- `timestamp`: recent
- `like_count`: exists (0 is OK, not 0-available yet)

**If verification fails:** Alert user, do NOT log as "posted"

---

## STEP 5: Log Results to orchestrator-log.json

Create entry:
```json
{
  "date": "YYYY-MM-DD (Day Name) ET",
  "slot": "morning|afternoon|evening|night",
  "timestamp_utc": "ISO format UTC timestamp",
  "revitalize": {
    "product": "Product Name",
    "price": "$XX",
    "theme": "theme name",
    "image_job_id": "Higgsfield job ID",
    "ig_media_id": "media container ID",
    "ig_post_id": "Instagram post ID",
    "ig_permalink": "https://www.instagram.com/p/...",
    "posted_via": "composio",
    "status": "posted",
    "verified": true,
    "verified_at": "ISO timestamp"
  },
  "reclaim": {
    "product": "Product Name",
    "price": "$XX",
    "theme": "theme name",
    "image_job_id": "Higgsfield job ID",
    "ig_media_id": "media container ID",
    "ig_post_id": "Instagram post ID",
    "ig_permalink": "https://www.instagram.com/p/...",
    "posted_via": "composio",
    "status": "posted",
    "verified": true,
    "verified_at": "ISO timestamp"
  },
  "note": "Campaign continuation — posts generating and publishing via simplified orchestrator (metrics collection deferred)"
}
```

Append to `data/orchestrator-log.json`. Keep last 90 entries only.

---

## STEP 6: Commit & Push

```bash
git add data/orchestrator-log.json
git commit -m "Daily orchestration: $(date +%Y-%m-%d) $(slot) posts

Revitalize: [product name], [price]
Reclaim: [product name], [price]

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KtEKoXe1JymUGnZV1FbjFV"

git push -u origin claude/product-conversion-analysis-5sd1jm
```

---

## SUCCESS CRITERIA

✅ **Post published when:**
- Both captions generated correctly
- Both images created via Higgsfield
- Both posts published via Composio
- Both posts verified live (INSTAGRAM_GET_IG_MEDIA confirms)
- Entry appended to orchestrator-log.json with `verified: true`
- Changes committed and pushed

✅ **Daily cadence when:**
- 7 AM: 2 posts (Revitalize + Reclaim)
- 3 PM: 2 posts
- 7 PM: 2 posts
- 10 PM: 2 posts
- **Total: 8 posts per day (4 slots × 2 brands)**

---

## TROUBLESHOOTING

**If Higgsfield image generation hangs:**
- Wait up to 2 minutes for reconnection
- If still disconnected: Alert user, retry in next trigger cycle

**If Composio fails to create/publish:**
- Check account name matches config (revitalize_thrive_now_real, reclaim_and_rise_now)
- Check image URL is valid and publicly accessible
- If persistent: Alert user, do NOT mark as posted

**If verification fails (INSTAGRAM_GET_IG_MEDIA returns error):**
- Post may still exist but IG API lag
- Wait 5 seconds, retry once
- If still fails: Do NOT mark verified=true, alert user

**If already_posted_today() returns True:**
- STOP. Do not post again today. Exit cleanly.

---

**This workflow is METRIC-INDEPENDENT. It requires only:**
- Higgsfield MCP (image generation)
- Composio MCP (Instagram posting)
- Local config files (orchestrator-config.json, brand-config.json)

**No external API calls to analytics/metrics required.**
