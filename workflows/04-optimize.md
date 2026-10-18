# workflows/04-optimize.md
# Optimization Workflow
# Version 4.0 | October 2026 | MCP-first + verified before/after

---

## Overview

MODE 4 ใช้ MCP tools เป็น default สำหรับ diagnose และ execute หลัง user confirm

```
PHASE 1 → INTAKE
PHASE 2 → SNAPSHOT BEFORE (MCP read)
PHASE 3 → DIAGNOSE
PHASE 4 → RECOMMEND
PHASE 5 → CONFIRM
PHASE 6 → EXECUTE (MCP dry-run → confirm → dry_run=False)
PHASE 7 → SNAPSHOT AFTER
PHASE 8 → FOLLOW-UP
```

Browser fallback ใช้เฉพาะ visual QA, API missing feature, หรือ account/login/payment issue

---

## Money Safety Rules

```
Hard stop:
- ห้าม assume งบใหม่หรือ bid/cost cap ใหม่
- ห้ามคำนวณ +20% หรือเลือกเลขแทน user
- ทุก action ที่เปลี่ยนเงินต้องมีตัวเลขจาก user
- ทุก write action ต้อง dry-run ก่อน
- ก่อน dry_run=False ต้องได้คำว่า "ยืนยัน"
- Pause/resume ก็ต้อง confirm เพราะมีผลกับ spend
```

ตัวอย่างที่ถูก (ตัวอย่างสมมติ):
> "อยากเพิ่ม budget จาก ฿100/วัน เป็นกี่บาทครับ?"

ตัวอย่างที่ผิด (ตัวอย่างสมมติ):
> "เพิ่มเป็น ฿150/วันนะครับ" ถ้า user ไม่ได้บอกเลข

---

## MCP Tools

| Action | Tool |
|---|---|
| Diagnose campaign metrics | `get_report`, `get_weekly_report` |
| ดู campaign/adset/ad | `list_campaigns`, `list_adsets`, `list_ads`, `get_ad_status` |
| Pause/resume campaign | `pause_campaign`, `resume_campaign` |
| Pause/resume adset | `pause_adset`, `resume_adset` |
| Pause/resume ad | `pause_ad`, `resume_ad` |
| Snapshot exact entity | `get_entity` |
| ตรวจยอดใช้จ่ายกับ owner cap | `check_spend_cap` |
| ประเมิน reach/click min–max (ไม่สร้างอะไร) | `estimate_adset_reach` |
| Change campaign budget/status | `update_campaign` |
| Change adset budget/bid/targeting/status | `update_adset` |
| Upload new creative | `upload_media` |
| Create new ad | `create_ad` |
| Interest targeting codes | `list_advanced_targeting_codes` |

ไม่มี delete tools ใช้ pause แทน

---

## Knowledge Loading Gate

ก่อนเริ่ม MODE 4 ต้องอ่าน:
- `knowledge/kpi-benchmarks.md` — ใช้ diagnose metric เช่น CTR, CPC, CPM, budget pacing
- `knowledge/bidding-strategy.md` — ใช้แนะนำ bid strategy/learning phase โดยไม่เดาเลขเงิน
- `workflows/04-optimize.md` — ใช้ยืนยัน dry-run/confirm/snapshot rules

โหลดเพิ่มตามจังหวะ:
- ถ้าจะปรับ targeting/interest: อ่าน `knowledge/interest-catalog-INDEX.md` ก่อน แล้วค่อยโหลด `knowledge/interest-detail-*.md` เฉพาะหมวดหรือเรียก code lookup เฉพาะจำเป็น
- ถ้าจะเปลี่ยน creative/upload media: อ่าน `knowledge/ad-specs.md` ก่อน

Rule สำคัญ:
- ต้อง snapshot before ด้วย MCP read tools ก่อน recommend action
- ทุก write action ต้อง dry-run แล้วรอ user ยืนยัน
- ห้ามคำนวณตัวเลขใหม่แทน user แม้จะเป็น +20%; ให้ถาม user ระบุตัวเลขเอง

---

## Phase 1 — Intake

เริ่มจากประโยคเดียว เช่น “ช่วยดูโฆษณาที่เปิดอยู่และแนะนำว่าควรปรับอะไร” AI ดึงบัญชีเอง ไม่ให้ผู้อ่านเตรียม/แนบ/เขียนไฟล์ ยกเว้นรูป creative ถามทีละเรื่องเฉพาะเป้าหมายธุรกิจ, งบ/bid/cap, วันเริ่มถ้าสร้างใหม่, ข้อเท็จจริงสินค้า และ approval ที่ขาด

```text
list_campaigns(status="ACTIVE", fetch_all=True)
list_adsets(campaign_id=[ID], status="ACTIVE", fetch_all=True)
list_ads(campaign_id=[ID], status="ACTIVE", fetch_all=True)
get_report(level="ADGROUP", start_date=..., end_date=..., campaign_id=[ID], fetch_all=True)
get_report(level="AD", start_date=..., end_date=..., campaign_id=[ID], fetch_all=True)
```

ดึงทุกหน้าเป็น default; `list_adsets`/`list_ads` ไม่ส่ง parent ก็อ่านทั้งบัญชีได้ `list_ads` กรอง `adset_id` ได้ หาก user ขอ resume หรือระบุ entity ที่พักไว้ ให้ค้นเพิ่มด้วย `status="PAUSED"` ไม่สรุปว่าไม่มีเพียงเพราะไม่อยู่ใน ACTIVE

รายงานใช้ช่วงวันที่ **UTC** (`date_basis="UTC"`) ตรวจ `paging.complete` ก่อนวิเคราะห์ หากอยากเห็นแนวโน้มรายวันใช้ `by_day=True` (วัน×entity สูงสุด 93 วันต่อคำขอ) ค่าเฉลี่ยที่ไม่มีตัวหารเป็น `None` ไม่ใช่ศูนย์ ข้อมูลไม่ครบให้บอกข้อจำกัด

---

## Phase 2 — Snapshot Before

ก่อนเสนอ action หรือ execute ต้องเก็บ snapshot:

```
- Campaign ID/name/status/objective
- Budget
- Adset ID/name/status/bid/budget/targeting
- Ads + creative review status
- 7-day metrics หรือช่วงที่ user ขอ
```

ใช้ `get_entity(entity_type="campaign"|"adset"|"ad", entity_id=...)` กับเป้าหมายแต่ละตัว เก็บ configured_status, delivery_status, budget, bid, targeting และ raw ในบริบทแชท พร้อม `get_ad_status(ad_id)` แบบ exact ID เมื่อต้องดู review

ก่อน write แต่ละรายการ ให้ดึง `get_entity` อีกครั้งเป็น before snapshot แล้วจึง dry-run หากค่าปัจจุบันต่างจากแผนที่อนุมัติ ให้ทบทวนแผน/ขอ “ยืนยัน” ใหม่ ห้ามใช้ snapshot เก่าทับการเปลี่ยนแปลงล่าสุด

---

## Phase 3 — Diagnose

โหลด `knowledge/kpi-benchmarks.md` เฉพาะตอนวิเคราะห์ benchmark

วิเคราะห์ตาม objective เท่านั้น: GAIN_FRIENDS ใช้ CPF/Friends, WEBSITE_TRAFFIC ใช้ CTR/CPC, VIDEO_VIEW ใช้ VTR/CPV, REACH ใช้ CPM/Reach/Frequency, APP_INSTALL ใช้ CPI ส่วน CV/CPA/ROAS ใช้เฉพาะ CONVERSIONS และเฉพาะ metrics ที่ response มีจริง

### Sequential Check

เช็คตามลำดับนี้ก่อน pattern matching เสมอ เพื่อไม่วิเคราะห์ metric ที่ยังไม่ควรถูกใช้:

```
Step 1: Campaign/adset status
  - ถ้า PAUSED/ENDED/REMOVED → หยุดที่ status issue ก่อน

Step 2: Creative review status
  - ถ้า IN_REVIEW → แจ้งว่ายังประเมิน performance ไม่ได้
  - ถ้า NOT_APPROVED (= review rejected) → อ่าน reason; ถ้า POLICY_VIOLATION ต้องแก้ copy/image ใหม่ ไม่ใช่ resubmit เดิม

Step 3: Impressions
  - ถ้า Impressions = 0 → ตรวจ bid, targeting, account/payment, review, audience size

Step 4: Results
  - ถ้า Results = 0 แต่ Impressions > 0 → ตรวจ creative, offer, bid cap, targeting fit

Step 5: Cost + quality
  - ถ้า cost สูงและ result ดี → เสนอ scale up แต่ให้ user ระบุตัวเลขเอง
  - ถ้า cost สูงและ result แย่ → เสนอ creative/targeting/bid diagnosis
```

Patterns:

```
GAIN_FRIENDS:
- ⚠️ cv = 0 → ปกติสำหรับ GAIN_FRIENDS เสมอ อย่า flag เป็น pixel/tracking issue
  ใช้ Friends/result ที่ response ระบุว่าเป็น Friend จริง; ถ้าไม่มีให้บอกว่าคำนวณ CPF ไม่ได้ ห้ามถือว่าทุก click เป็น Friend
- ไม่มี Friend result แต่มี impressions → ตรวจ creative/bid/targeting ตามหลักฐานจริง ไม่ใช้ cv=0 เป็นเหตุ
- Impressions = 0 → paused, review, bid ต่ำ, targeting แคบ
- CPF สูงใกล้ cap → อาจต้องปรับ bid หรือ creative แต่ห้ามเลือกเลขเอง

Website:
- CTR ต่ำกว่า benchmark ที่เหมาะกับข้อมูล → ตรวจ creative/headline และจำนวน impressions ก่อนสรุป
- CPC สูง → bid/competition/targeting

All objectives:
- Campaign/adset paused → ไม่ deliver
- Creative IN_REVIEW/NOT_APPROVED → ยังไม่ deliver หรือแก้ creative
- Budget ใช้น้อยมาก → bid ต่ำ/targeting แคบ/review
```

สรุปเป็นไทย:

```
Diagnosis:
- ปัญหา: [what]
- หลักฐาน: [metric/status reason]
- ความเสี่ยง: [LOW/MEDIUM/HIGH]
```

---

## Phase 4 — Recommend

เสนอ 2-3 ทางเลือก พร้อม trade-off:

```
A) เปลี่ยน creative / เพิ่ม ad ใหม่
   Risk: MEDIUM, ไม่เปลี่ยนเงินโดยตรง

B) ปรับ targeting / เพิ่ม interest / broadening
   Risk: MEDIUM, กระทบ delivery/learning

C) ปรับ budget หรือ bid cap
   Risk: HIGH, ต้องให้ user ระบุเลขเงินเอง

D) Pause/resume campaign/adset/ad
   Risk: MEDIUM/HIGH เพราะมีผลกับ spend
```

เพิ่มข้อเสนอจากข้อมูลจริง:

- ถ้ามี owner cap ให้เรียก `check_spend_cap(cap_amount=..., start_date=..., end_date=..., campaign_id=..., period_end=...)` เทียบ cap ที่เจ้าของระบุ (ไม่ใช้ daily budget แทน cap) ถ้ายังไม่มีให้ถามทีละเรื่อง ห้ามเดาเงิน
- `exceeded` เฉพาะ spend > cap; เท่ากับ cap เป็น `within_cap`; `indeterminate` = ข้อมูลไม่ครบ ห้ามสรุปว่าเกิน/ไม่เกิน ใช้ per-campaign spend และ optional projection ตาม response โดยแยกประมาณการจากยอดจริง
- เปรียบเทียบ creative ระดับ AD ภายใน objective/ช่วงวัน UTC เดียวกัน ใช้ spend, impressions, results/ต้นทุนตาม objective และ review/delivery ประกอบ ไม่ฟันธงผู้ชนะจากข้อมูลน้อยหรือบริบท targeting ต่างกัน; แสดงสิ่งที่รู้/ยังไม่รู้ก่อนเสนอ refresh หรือ pause ad

ห้าม execute จาก recommendation ทันที และ **ห้าม auto-pause** ไม่ว่า cap เกิน, creative แพ้ หรือ KPI แย่ ทุกการหยุด/เปิดต้องผ่าน dry-run → สรุป → “ยืนยัน” ก่อน

---

## Phase 5 — Confirm

ก่อน write action ใช้ before snapshot จาก `get_entity` แล้ว dry-run ด้วย tool/args เดียวกับที่จะ execute:

```
สรุปก่อนทำ:
- Action: [pause/update/create]
- Target: [campaign/adset/ad ID]
- ค่าเดิม: [old]
- ค่าใหม่: [new from user]
- ผลกระทบ: [delivery/spend/learning]
- Risk: [level]

ผมจะทำ dry-run เพื่อตรวจแผนก่อน ยังไม่ส่งจริงครับ
```

หลัง dry-run:

```
นี่คือ payload ที่จะส่งจริง:
[compact payload]

พิมพ์ "ยืนยัน" เพื่อส่งจริง
```

---

## Phase 6 — Execute With MCP

### Pause/Resume

```
pause_campaign / resume_campaign
pause_adset / resume_adset
pause_ad(ad_id=..., dry_run=True) / resume_ad(ad_id=..., dry_run=True)
```

Rules:
- dry-run ก่อน
- confirm ก่อน write จริง
- หลัง “ยืนยัน” จึงเรียก tool เดิมด้วย `dry_run=False` แล้วแสดง `before`, `readback`, `readback_ok`; ไม่ผ่านต้องแจ้งว่ายังยืนยันผลไม่ได้

### Change Budget

```
update_campaign(daily_budget=...)
update_adset(daily_budget=...)
```

Rules:
- daily_budget ต้องมาจาก user
- แสดงบาท ไม่พูดแต่ micro

### Change Bid Cap

```
update_adset(bid_amount=...)
```

Rules:
- bid_amount ต้องมาจาก user
- สำหรับ CPF/COST_CAP ต้องทวนว่าเป็นเพดานต่อ friend

### Change Targeting / Interest

```
อ่าน knowledge/interest-catalog-INDEX.md → detail file เฉพาะหมวด → list_advanced_targeting_codes เฉพาะเมื่อ cache ไม่พอ
update_adset(interest_groups=[[Need...], [Ability...], [Life Stage...]], targeting fields...)
```

Rules:
- ต้องใช้ official code เท่านั้น
- ถ้า adset เดิมยังไม่มี App Behavior (หมวดหมู่แอป / ความมั่งคั่ง / ราคามือถือ) ให้เสนอเติมในชั้นที่เกี่ยวข้องเป็นตัวเลือกหนึ่งของการปรับ — ดู `knowledge/interest-detail-app-behavior.md`
- ถ้ามี `interest_codes` ต้องเป็น `targetingMode=MANUAL`
- บันทึก targeting เดิมก่อน เผื่อ rollback

### Change Creative

```
upload_media
create_ad
```

Rules:
- upload media ต้อง confirm เพราะเป็น write action
- create ad ต้อง dry-run + confirm
- สร้าง ad ใหม่เป็น `status="PAUSED"` default; แสดง `readback`/`readback_ok` แล้วตรวจ `get_entity` และ `get_ad_status`; resume เป็น approval แยกต่างหาก

---

## Phase 7 — Snapshot After

หลัง `dry_run=False` ทุกครั้ง:

1. แสดง `readback` / `readback_ok` จาก response; update/pause/resume มี `before` snapshot ด้วย
2. เรียก `get_entity` ของ exact target ตรวจ configured_status กับ delivery_status แยกกัน และใช้ `get_ad_status(ad_id)` สำหรับ review; `NOT_APPROVED` คือถูกปฏิเสธ, `IN_REVIEW` ยังรอ
3. เทียบ before/after กับสิ่งที่ยืนยัน หาก readback ไม่ครบ/ไม่ตรง/`readback_ok=false` ห้ามบอกว่าสำเร็จหรือ retry write ซ้ำทันที ให้ตรวจข้อมูลล่าสุดก่อน
4. ถ้ามี `workspace_dir` ส่งกับ write tool เพื่อ append before/after/time ใน `line-ads-data/change_log.jsonl`; fallback env `LINE_ADS_WORKSPACE_DIR` ไม่ให้ผู้อ่านเตรียมไฟล์ ถ้าไม่ตั้ง path อย่าอ้างว่ามี log ถ้า log ล้มเหลวให้แยกจากผล API และแจ้งตามจริง

| รายการ | ก่อน | หลังที่อ่านกลับ |
|---|---|---|
| [entity ID / field] | [ค่าจาก before] | [ค่าจริงจาก readback/get_entity] |
| configured_status / delivery_status | [ค่าจริง] | [ค่าจริง + เหตุผลถ้ามี] |

ตารางใช้ค่าจริงเท่านั้น ถ้ายัง process/review ให้บอกว่า pending ไม่รับประกันว่าจะ deliver ทันที

---

## Phase 8 — Follow-up

```
สรุปวันติดตามผล: [วัน/เวลา + timezone ที่คำนวณจริง 24–48 ชั่วโมงหลังปรับ]
บอกช่วงรายงานที่จะตรวจเป็น UTC และ metrics ตาม objective
หากต้องการรายงานอัตโนมัติ ให้ไป MODE 3 ไม่อ้างว่าตั้งแล้ว
```

ถ้า user ขอ schedule → switch to `03-report-schedule.md`

---

## Rollback Plan

ทุก action ต้องมี rollback concept:

| Action | Rollback |
|---|---|
| เพิ่ม budget | update กลับค่าเดิม หลัง user confirm |
| เพิ่ม bid | update กลับค่าเดิม หลัง user confirm |
| pause | resume หลัง user confirm |
| resume | pause หลัง user confirm |
| targeting change | update targeting กลับ snapshot เดิม หลัง dry-run + “ยืนยัน” |
| creative change | pause_ad หรือสร้าง creative ใหม่ หลัง dry-run + “ยืนยัน”; ห้าม delete |

Rollback ทุก write ต้อง dry-run → สรุป → “ยืนยัน” → execute → readback ใหม่เสมอ

---

## Browser Fallback

ใช้ browser เฉพาะเมื่อ:
- MCP API ไม่มีข้อมูล rejection reason ที่ต้องดูใน UI
- ต้องตรวจ creative preview/crop จริง
- ต้องทำ payment/account setting
- API permission ไม่พอและ user เลือก self-fill

Token discipline:
- DOM/interactive ก่อน screenshot
- screenshot เฉพาะ chart/preview/error
- ไม่ login/password/OTP/card แทน user

---

## Notes

1. MCP-first สำหรับ diagnose และ execute
2. Read-only tools ไม่ต้อง confirm
3. Write tools dry-run + confirm เสมอ
4. Money inputs จาก user เท่านั้น
5. Snapshot before/after ทุก write action
6. No delete, use pause
7. ถ้า method endpoint error ให้เช็ค spec ก่อนสรุป permission เช่น update adgroup ใช้ POST

---

*Version 4.0 | October 2026*
*Updated: MCP-first optimization, dry-run execute flow, targeting/creative update via MCP, browser fallback scope*
