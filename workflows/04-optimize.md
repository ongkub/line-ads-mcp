# workflows/04-optimize.md
# Optimization Workflow
# Version 3.0 | May 2026 | MCP-first

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
- ก่อน dry_run=False ต้องได้คำว่า "ยืนยัน" หรือ "ทำได้เลย"
- Pause/resume ก็ต้อง confirm เพราะมีผลกับ spend
```

ตัวอย่างที่ถูก:
> "อยากเพิ่ม budget จาก ฿100/วัน เป็นกี่บาทครับ?"

ตัวอย่างที่ผิด:
> "เพิ่มเป็น ฿150/วันนะครับ" ถ้า user ไม่ได้บอกเลข

---

## MCP Tools

| Action | Tool |
|---|---|
| Diagnose campaign metrics | `get_report`, `get_weekly_report` |
| ดู campaign/adset/ad | `list_campaigns`, `list_adsets`, `list_ads`, `get_ad_status` |
| Pause/resume campaign | `pause_campaign`, `resume_campaign` |
| Pause/resume adset | `pause_adset`, `resume_adset` |
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

ถาม:

```
อยาก optimize campaign ไหนครับ?
หรือให้ผมดูทั้งหมดก่อนด้วย MCP report?
```

ถ้า user ระบุชื่อ/ID:
- `list_campaigns` เพื่อหา campaign
- `list_adsets`
- `list_ads`
- `get_report` ตามช่วงที่เกี่ยวข้อง

ถ้า user บอก "ดูทั้งหมด":
- `list_campaigns`
- `get_weekly_report(level="CAMPAIGN")`

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

ใช้ MCP read tools เท่านั้นก่อน

---

## Phase 3 — Diagnose

โหลด `knowledge/kpi-benchmarks.md` เฉพาะตอนวิเคราะห์ benchmark

### Sequential Check

เช็คตามลำดับนี้ก่อน pattern matching เสมอ เพื่อไม่วิเคราะห์ metric ที่ยังไม่ควรถูกใช้:

```
Step 1: Campaign/adset status
  - ถ้า PAUSED/ENDED/REMOVED → หยุดที่ status issue ก่อน

Step 2: Creative review status
  - ถ้า IN_REVIEW → แจ้งว่ายังประเมิน performance ไม่ได้
  - ถ้า REJECTED → อ่าน reason; ถ้า POLICY_VIOLATION ต้องแก้ copy/image ใหม่ ไม่ใช่ resubmit เดิม

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
- Friends = 0 + Impressions > 1,000 → bid cap ต่ำ / creative / targeting
- Impressions = 0 → paused, review, bid ต่ำ, targeting แคบ
- CPF สูงใกล้ cap → อาจต้องปรับ bid หรือ creative แต่ห้ามเลือกเลขเอง

Website:
- CTR < 1% + Impressions > 5,000 → creative/headline
- CPC สูง → bid/competition/targeting

All objectives:
- Campaign/adset paused → ไม่ deliver
- Creative IN_REVIEW/REJECTED → ยังไม่ deliver หรือแก้ creative
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

D) Pause/resume campaign/adset
   Risk: MEDIUM/HIGH เพราะมีผลกับ spend
```

ห้าม execute จาก recommendation ทันที

---

## Phase 5 — Confirm

ก่อน write action:

```
สรุปก่อนทำ:
- Action: [pause/update/create]
- Target: [campaign/adset/ad ID]
- ค่าเดิม: [old]
- ค่าใหม่: [new from user]
- ผลกระทบ: [delivery/spend/learning]
- Risk: [level]

ผมจะทำ dry-run ก่อน ยังไม่ส่งจริง ยืนยันให้ทำ preview ไหมครับ?
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
```

Rules:
- dry-run ก่อน
- confirm ก่อน write จริง
- read back หลังทำ

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
update_adset(interest_codes=[...], targeting fields...)
```

Rules:
- ต้องใช้ official code เท่านั้น
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
- read back ด้วย list_ads/get_ad_status

---

## Phase 7 — Snapshot After

หลัง write จริง:

```
1. read back target ด้วย MCP
2. เทียบ before/after
3. แจ้ง status reasons
4. ถ้า LINE ยัง process/review ให้บอกว่า pending
```

ตัวอย่าง:

```
ปรับเรียบร้อยครับ
- ก่อน: targetingMode=AUTO
- หลัง: targetingMode=MANUAL + interest code 4
- Delivery ยังไม่รัน เพราะ CAMPAIGN_PAUSED / CREATIVE_REVIEW_IN_REVIEW
```

---

## Phase 8 — Follow-up

```
อยากให้ผมตามดูผลใน 24-48 ชม.ไหมครับ?
ถ้าตั้ง report ให้ไป MODE 3
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
| targeting change | update targeting กลับ snapshot เดิม |
| creative change | pause ad ใหม่ หรือสร้าง creative ใหม่ ห้าม delete |

Rollback ที่กระทบเงินต้อง confirm ใหม่เสมอ

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

*Version 3.0 | May 2026*
*Updated: MCP-first optimization, dry-run execute flow, targeting/creative update via MCP, browser fallback scope*
