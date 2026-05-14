# workflows/03-report-schedule.md
# LINE Ads Report + Scheduled Tasks Workflow
# Version 3.0 | May 2026 | MCP-first

---

## Overview

MODE 3 ใช้ MCP report tools เป็น default ไม่ใช้ browser dashboard ยกเว้นต้องตรวจ visual/chart ที่ API ไม่มี

```
Instant Report  → get_report / get_daily_report / get_weekly_report
Scheduled Report → scheduled task เรียก MCP report tools
Status Check → list_campaigns / list_adsets / list_ads / get_ad_status
Browser Fallback → ใช้เฉพาะ API error, login/account issue, หรือ visual QA
```

---

## Entry Point

Trigger:
- หลังสร้าง campaign/ad/adset เสร็จ
- "ดู report"
- "ดูผลโฆษณา"
- "campaign เป็นยังไงบ้าง"
- "ตั้งรายงานอัตโนมัติ"

หลังสร้าง campaign เสร็จ ให้เสนอ:

```
ตั้งรายงานอัตโนมัติไหมครับ?
ค่าเริ่มต้น: ทุกวัน 09:00 ดึงผ่าน MCP API ไม่ต้องเปิด Chrome
แจ้งเตือนเมื่อ ad reject, ไม่มี delivery, CPF/CPC สูงผิดปกติ, หรือใช้งบผิด pace
```

---

## MCP Tools

| งาน | Tool |
|---|---|
| รายงานตามช่วงวันที่ | `get_report` |
| รายงานเมื่อวาน | `get_daily_report` |
| รายงาน 7 วันล่าสุด | `get_weekly_report` |
| ดู campaigns | `list_campaigns` |
| ดู adsets | `list_adsets` |
| ดู ads | `list_ads` |
| ดู creative/ad review | `get_ad_status` |

Read-only tools เรียกได้เลย ไม่ต้อง confirm เพราะไม่กระทบเงิน

---

## Knowledge Loading Gate

ก่อนเริ่ม MODE 3 ต้องอ่าน:
- `knowledge/kpi-benchmarks.md` — ใช้ตีความ CTR, CPC, CPM, budget alerts และ diagnosis rules
- `workflows/03-report-schedule.md` — ใช้ยืนยันว่า report ใช้ MCP-first ไม่ใช่ browser dashboard เป็น default

โหลดเพิ่มตามจังหวะ:
- ถ้าจะเสนอ action ปรับ bid/budget/status ให้หยุดที่ recommendation แล้วส่งต่อ `workflows/04-optimize.md`
- ถ้าจะวิเคราะห์ creative/media issue ให้ดู `knowledge/ad-specs.md`

Rule สำคัญ:
- MODE 3 เป็น read-only; ห้าม pause/resume/update budget จาก report workflow
- ต้องบอกช่วงวันที่ของ report ทุกครั้ง
- ต้องระบุ timezone เป็น Asia/Bangkok/+07:00 ทุกครั้ง เพื่อกัน report date คลาดจาก GMT
- ถ้า data น้อยหรือ campaign อายุ < 7 วัน ต้องแจ้งว่า insight ยัง limited

---

## Phase 1 — Instant Report

ถ้า user ขอ report ตอนนี้:

```
1. ระบุ level: CAMPAIGN / ADGROUP / AD
2. ระบุ date range หรือใช้ default:
   - เมื่อวาน → get_daily_report
   - 7 วันล่าสุด → get_weekly_report
3. ถ้ามี campaign_id ให้ส่ง filter
4. สรุป metrics เป็นภาษาไทย
5. ถ้ามี status issue ให้ดึง list_ads/get_ad_status เพิ่ม
```

Output format:

```
รายงาน LINE Ads — [ช่วงวันที่]

Campaign: [ชื่อ/ID]
- Spend: ฿[X]
- Impressions: [X]
- Clicks/Friends/Conversions: [X]
- CTR: [X]%
- CPC/CPF/CPA/CPM: ฿[X]
- Status: [ACTIVE/PAUSED/IN_REVIEW/etc.]

ประเมิน:
[ดี/ปานกลาง/ต้องปรับ] — [เหตุผล]

สิ่งที่ควรดูต่อ:
- [action]
```

Money safety:
- Report Agent flag ปัญหาได้
- ห้ามเปลี่ยน budget/bid เอง
- ห้ามเสนอเลขใหม่แบบฟันธง ให้ส่งต่อ MODE 4 เพื่อ confirm

---

## Phase 2 — Scheduled Report Configuration

ใช้ default + opt-out:

```
จะตั้งรายงานทุกวัน 09:00 สำหรับ [campaign]
ใช้ MCP API ดึงข้อมูล ไม่ต้องเปิด Chrome

แจ้งเตือน:
- Ad ถูก reject / creative in review นาน
- ไม่มี impression หรือไม่มี result
- CPF/CPC/CPA สูงกว่า benchmark
- ใช้งบเร็วหรือช้าเกินไป

ยืนยันแบบนี้ไหมครับ? ถ้าอยากเปลี่ยนเวลา/ความถี่บอกได้เลย
```

ถ้า user ขอแก้ ให้ถามเฉพาะ:
- ความถี่
- campaign scope
- alert rules

---

## Phase 3 — Scheduled Task Prompt Template

### Session Context Capture

ก่อนสร้าง scheduled task หลัง campaign/adset/ad สร้างเสร็จ ให้บันทึก context ลง prompt ทันทีเพื่อไม่ต้องถาม user ใหม่ใน scheduled run:

```
- ad_account_id
- campaign_id + campaign name + objective
- daily_budget (บาท)
- bid_strategy + bid_amount/cost cap ถ้ามี
- adset_id/name + targeting summary
- age range, gender, location, interest codes/interest groups
- ad_id/name + creative status ถ้ามี
- start date/time + timezone
- reporting objective metric เช่น Friends, Clicks, Conversions, Views
```

Prompt สำหรับ scheduled task:

```text
คุณคือ LINE Ads Report Agent

ใช้ MCP tools เท่านั้นเป็น default:
- get_daily_report หรือ get_weekly_report
- list_campaigns
- list_adsets
- list_ads
- get_ad_status

ห้ามเปิด browser เว้นแต่ MCP API ใช้งานไม่ได้หรือ user ขอ visual dashboard โดยตรง

Campaign Context:
- Ad Account: [ID]
- Campaign: [name/id]
- Objective: [objective]
- Budget: ฿[X]/วัน
- Bid strategy/cost cap: [strategy + ฿Y หรือ none]
- Adsets: [adset_id/name/status]
- Targeting summary: [age, gender, location, interest codes/groups]
- Ads: [ad_id/name/review status]
- Start date/timezone: [YYYY-MM-DD HH:mm +07:00]
- Primary metric: [Friends/Clicks/Conversions/Views]

งาน:
1. ดึง report ตาม schedule
2. ดึง status ของ campaign/adset/ad ที่เกี่ยวข้อง
3. สรุปผลเป็นภาษาไทยแบบ compact
4. แจ้ง alert ถ้าเข้าเงื่อนไข
5. ห้ามเปลี่ยน budget/bid/status เอง

Alert Rules:
- Impressions = 0 → ไม่ deliver
- Result = 0 และ Impressions > 0 → creative/bid/targeting อาจมีปัญหา
- Creative review rejected → แปล reason และเสนอวิธีแก้
- Campaign/adset paused → แจ้งว่าไม่ delivery เพราะ paused
- CPF/CPC/CPA สูงกว่า benchmark → flag ให้เข้า MODE 4

Output:
รายงาน LINE Ads — [date]
- Spend
- Impressions
- Results
- CTR/CPC/CPF/CPM ตาม objective
- Status + reasons
- Assessment
- Suggested next step
```

---

## Phase 4 — Confirmation to User

```
ตั้ง Schedule เรียบร้อยครับ

- ความถี่: [daily/weekly/custom]
- เวลา: [HH:mm]
- Campaign: [name/id]
- Data source: MCP API
- Browser required: ไม่ต้องใช้ เว้นแต่ API error
```

---

## Error Handling

| Error | Action |
|---|---|
| Missing credentials | แจ้งให้ตั้ง `.env` |
| 401 | ตรวจ Access Key/Secret/signature |
| 403 | แจ้ง permission/feature อาจไม่เปิด |
| 404 | ตรวจ campaign/adset/ad id |
| 429 | retry ตาม client แล้วแจ้งถ้ายัง rate limit |
| 5xx | แจ้ง LINE API ชั่วคราว |
| ไม่มีข้อมูล | บอกว่า campaign ยังไม่ run/ยัง review/ช่วงวันที่ไม่มี delivery |

Browser fallback ใช้เมื่อ:
- user ต้องการดู chart/visual จริง
- API response ไม่พอสำหรับ diagnosis
- ต้องแก้ account/login/payment

---

## Benchmarks

โหลด `knowledge/kpi-benchmarks.md` เฉพาะตอนต้องวิเคราะห์ performance

หลักคิด:
- Campaign อายุ < 7 วัน ให้บอกว่า data ยัง limited
- หลัง 14 วัน ค่อยเสนอ weekly report ถ้า stable
- การเปลี่ยนเงินหรือสถานะต้องไป MODE 4

---

## Manage Schedule

```
"หยุดรายงานชั่วคราว"   → pause schedule
"เปลี่ยนเป็นทุกสัปดาห์"  → update schedule
"ยกเลิกรายงานอัตโนมัติ" → delete schedule
"รายงานตอนนี้เลย"      → run instant report ผ่าน MCP
```

---

## Notes

1. MCP report tools เป็น default
2. Read-only ไม่ต้อง confirm
3. ห้ามแก้เงิน/status จาก MODE 3
4. Browser เป็น fallback เท่านั้น
5. Report ต้องบอก status reasons เช่น `CAMPAIGN_PAUSED`, `ADGROUP_PAUSED`, `CREATIVE_REVIEW_IN_REVIEW`

---

*Version 3.0 | May 2026*
*Updated: MCP-first reporting, scheduled MCP prompt, browser fallback scope*
