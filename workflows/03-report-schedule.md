# workflows/03-report-schedule.md
# LINE Ads Report + Scheduled Tasks Workflow
# Version 2.0 | May 2026

---

## OVERVIEW

ทำ 2 อย่าง:
1. **Instant Report** — ดึงผลแคมเปญตอนนี้
2. **Schedule** — ให้ Cowork ดึง Report อัตโนมัติตามเวลา

```
TRIGGER:
A) หลังสร้าง Campaign เสร็จ → Cowork เสนอตั้ง Schedule
B) User เรียกเอง → "ดู Report" / "ตั้งรายงานอัตโนมัติ"
```

---

## PHASE 1 — ENTRY POINT

### A) Auto-offer หลังสร้าง Campaign

```
✅ สร้างโฆษณาเสร็จแล้วครับ! LINE กำลังตรวจสอบอยู่ (~24 ชั่วโมง)

อยากให้ผมส่งรายงานผลโฆษณาให้อัตโนมัติไหมครับ?
ตั้งครั้งเดียวแล้วทุกเช้าจะมีสรุปผลให้ดู

[ ✅ ตั้งรายงานอัตโนมัติ ] [ ดูเองเมื่อต้องการ ]
```

### B) User เรียกเอง

```
Trigger phrases:
- "ดู report" / "ดูผลโฆษณา" / "เช็คผล"
- "ตั้งรายงานอัตโนมัติ" / "ส่งรายงานทุกวัน"
- "campaign เป็นยังไงบ้าง"
```

---

## PHASE 2 — SCHEDULE CONFIGURATION (Default + Opt-out)

ใช้ default ก่อน แล้วให้ user แก้เฉพาะที่ไม่ตรง:

```
จะตั้งรายงานทุกวัน 09:00 สำหรับ [campaign ที่เพิ่งสร้าง]
แจ้งเตือนเมื่อ: งบใกล้หมด (<10%), Ad ถูก reject, ไม่มี result 24 ชม.

ยืนยันแบบนี้ไหมครับ? ถ้าอยากแก้ บอกได้เลย
```

ถ้า user รับ default → ข้ามไป PHASE 3
ถ้า user ขอแก้ → ถามเฉพาะข้อที่ต้องแก้ (ไม่ต้องไล่ Q1-Q3 ทั้งหมด)

### Q1 — ความถี่ (ถามเฉพาะถ้า user ขอแก้)

```
[ ทุกวัน ] ⭐ campaign active
[ ทุกสัปดาห์ ] campaign stable
[ กำหนดเอง ] เช่น "จันทร์-ศุกร์ 09:00"
```

### Q2 — Campaign ที่ติดตาม (ถามเฉพาะถ้า user ขอแก้)

```
[ Campaign ที่เพิ่งสร้าง ] ⭐ default
[ ทุก Campaign ในบัญชี ]
[ เลือกเอง ]
```

### Q3 — Alert (ถามเฉพาะถ้า user ขอแก้)

```
Default = งบใกล้หมด + Ad reject + ไม่มี result 24 ชม.

อยากเพิ่ม/ตัดอะไรไหม?
- งบหมด/ใกล้หมด <10%
- Ad ถูก reject
- ไม่มี result 24 ชม.
- CTR ต่ำ <1% (สำหรับ Website Click)
- CPF/CPC สูงกว่า benchmark 50%
```

---

## PHASE 3 — CREATE SCHEDULED TASK

ใช้ `mcp__scheduled-tasks__create_scheduled_task` กรอก:

```
- taskId: kebab-case (e.g. "line-ads-[brand]-daily-report")
- description: หนึ่งบรรทัดบอกหน้าที่
- cronExpression: "0 9 * * *" (ทุกวัน 09:00)
- prompt: ใช้ REPORT PROMPT TEMPLATE ด้านล่าง
```

แนะนำ user คลิก "Run now" รอบแรกใน Sidebar เพื่อ pre-approve tools

---

## REPORT PROMPT TEMPLATE

```
คุณคือ LINE Ads Report Agent

# Campaign Context
- Ad Account: [ID + ชื่อ]
- Campaign: [ชื่อ + ID]
- Objective: [Friend Added / Website Click / Reach / ...]
- Daily Budget: ฿[X]/วัน
- Bid/Cost cap: ฿[Y] ([CPF/CPC/CPA])
- Targeting: [summary]

# งานของคุณ
1. เปิด admanager.line.biz/adaccount/[ID]/campaign/
2. ถ้าต้อง login → แจ้ง user แล้ว pause
3. คลิก campaign → เลือก date range "เมื่อวาน"
4. อ่าน metrics ด้วย read_page interactive (ห้าม screenshot ถ้า DOM อ่านได้)
5. ถ้า DOM อ่านไม่ได้ ค่อย screenshot ตาราง

# ข้อมูลที่ต้องดึง
- Impressions, Clicks (CTR%)
- Spend / Budget remaining
- CPM, CPC
- Friend Added (สำหรับ Friend Added objective) หรือ Conversions
- Status

# Format Output (ภาษาไทย)
📊 รายงาน LINE Ads — [Brand]
วันที่: [DD/MM/YYYY]
Campaign: [ชื่อ]

ผลลัพธ์:
• 👀 Impressions: [X]
• 👥 [Result metric]: [X] [unit]
• 💸 ใช้งบไป: ฿[X] / ฿[Budget] (เหลือ [%])
• 💰 [Cost metric]: ฿[X] (cap ฿[Y])
• 📈 Status: [Active/Paused/Rejected]

การประเมิน:
[ดี/ปานกลาง/ต้องปรับ] — [เหตุผล]

สิ่งที่ควรทำต่อ:
• [action]

# Alert Rules (ตรวจทุกครั้ง)

🚨 ถ้าเข้าเงื่อนไขใดเงื่อนไขหนึ่ง → แจ้งในแชท:

1. งบใกล้หมด — Spend > Budget × 0.9
   "🚨 งบใกล้หมด ([X]% เหลือ) — ถ้าผลดีอาจอยากเพิ่มงบ"

2. Ad Reject — Status = Rejected
   "🚨 Ad ถูก Reject! Reason: [reason] — ต้องแก้และ resubmit"

3. ไม่มี result 24 ชม. — Result = 0 + Impressions > 0
   "🚨 ไม่ได้ result เลย — bid cap อาจต่ำเกิน หรือ creative ไม่ดึงดูด"

4. ไม่มี Impressions — Impressions = 0
   "🚨 Ad ไม่ deliver — เช็ค approve / bid / targeting"

# Money Safety
- ห้ามแนะนำตัวเลขใหม่ (เพิ่มงบ ฿X) — แค่ flag ปัญหา
- การปรับเงินทุกครั้งต้องผ่าน MODE 4 (Optimize) ที่ user confirm จำนวนเงิน

# Token Discipline
- ใช้ read_page interactive แทน screenshot
- screenshot เฉพาะ chart/visual ที่ DOM อ่านไม่ได้
- ถ้า login session หมด → หยุดและ notify user (ห้าม login แทน)

# บันทึก
บันทึกผลที่: reports/LINE-ads-[YYYY-MM-DD].md
ถ้าโฟลเดอร์ reports/ ยังไม่มี → สร้างก่อน

# หมายเหตุ
- Campaign อายุ < 7 วัน: ระบุว่าข้อมูลยัง limited (LINE ยัง learning)
- หลัง 14 วัน: เสนอเปลี่ยนเป็น weekly schedule
- ถ้าตรวจไม่ได้ (Chrome ปิด, login expire) → notify user สั้นๆ ไม่ retry หลายครั้ง
```

---

## PHASE 4 — CONFIRMATION TO USER

```
✅ ตั้ง Schedule เรียบร้อยครับ

📅 ทุกวัน 09:00 — Campaign: [ชื่อ]
📁 บันทึกที่: reports/LINE-ads-YYYY-MM-DD.md

⚠️ Schedule ทำงานได้เมื่อ:
- เปิดคอม + Claude Desktop
- ปิดเครื่อง → catch-up ตอนเปิดใหม่

แนะนำ: คลิก "Run now" ที่ sidebar เพื่อ pre-approve Chrome
```

---

## PHASE 5 — INSTANT REPORT (ดูทันที)

ใช้ flow เดียวกับ REPORT PROMPT TEMPLATE แต่ทำในแชทตอนนี้เลย:

```
1. read_page dashboard (interactive view)
2. ดึง metrics ตาม template
3. เทียบ benchmark (โหลด kpi-benchmarks.md)
4. แสดงผลในแชท + บันทึก reports/
```

---

## ERROR HANDLING

```
[Chrome ปิด / extension disconnect]
→ "ผมเข้า admanager ไม่ได้ตอนนี้ — เปิด Chrome แล้วบอกผมอีกทีครับ"
→ ไม่ retry อัตโนมัติ

[Login session หมด]
→ "session login หมด — login ใหม่ที่ admanager.line.biz แล้วบอกผมอีกที"
→ ห้าม Cowork login แทน

[Campaign ถูกลบ / ID ไม่มีแล้ว]
→ แจ้ง user → เสนอเลือก campaign อื่น หรือลบ schedule

[Date range ไม่มีข้อมูล]
→ "Campaign ยังไม่มี data ใน [วันที่] — รอข้อมูล approve/run ก่อน"
```

---

## BENCHMARK REFERENCE

(โหลด `knowledge/kpi-benchmarks.md` เพื่อใช้ใน analysis)

ค่าหลักที่ใช้ใน MODE 3:
```
CTR (Website Click):
- < 1.0%: ต้องปรับ creative
- 1.0-2.0%: ปกติ
- 2.0-3.5%: ดี
- > 3.5%: ดีมาก

CPF (Friend Added) — ตลาดไทย:
- < ฿15: ดีมาก
- ฿15-25: ดี
- ฿25-40: ปานกลาง
- > ฿40: ต้องปรับ

Budget pacing:
- ใช้ < 50%/วัน: bid ต่ำเกิน หรือ audience แคบ
- ใช้ 80-100%: balanced
- ใช้ 100% ก่อน 9 โมง: oversubscribed (อาจอยากเพิ่มงบ — ห้าม Cowork ตัดสินใจ)
```

---

## MANAGE SCHEDULE

```
"หยุดรายงานชั่วคราว"   → pause schedule
"เปลี่ยนเป็นทุกสัปดาห์"  → update cronExpression
"ยกเลิกรายงานอัตโนมัติ" → delete schedule
"ดูรายงานย้อนหลัง"     → เปิด reports/ folder
"รายงานตอนนี้เลย"      → manual run (PHASE 5)
```

---

## NOTES สำหรับ Cowork Agent

1. **Default + opt-out** — ใช้ค่ามาตรฐานก่อน ให้ user แก้เฉพาะที่ไม่ตรง
2. **Money Safety** — Report Agent flag ปัญหาได้ แต่ห้ามแนะนำตัวเลขใหม่ ส่งต่อ MODE 4
3. **Token discipline** — read_page interactive ก่อน screenshot
4. **No retry** — ถ้า login/Chrome fail แจ้ง user แล้วหยุด
5. **Pre-approve tools** — แนะนำ user คลิก "Run now" ครั้งแรกใน Sidebar

---

*Version 2.0 | May 2026*
*Updated:*
*- Default + opt-out flow ลดรอบถาม*
*- Money Safety: Report flag ปัญหา ไม่แนะนำตัวเลขใหม่*
*- Token Discipline ใน prompt template*
*- Error handling: Chrome/login/missing data*
