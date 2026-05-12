# workflows/04-optimize.md
# Optimization Workflow
# โหลดเฉพาะ MODE 4
# Version 2.0 | May 2026

---

## ลำดับการทำงาน (Overview)

```
PHASE 1 → INTAKE        (เลือก campaign + entry_mode)
PHASE 2 → DIAGNOSE      (ดึง metric + เทียบ benchmark + ระบุปัญหา)
PHASE 3 → RECOMMEND     (เสนอ action 2-3 ทางเลือก พร้อม trade-off)
PHASE 4 → CONFIRM       (user เลือก action + ยืนยันค่าเงินทุกครั้ง)
PHASE 5 → EXECUTE       (snapshot before → ทำ action → snapshot after)
PHASE 6 → FOLLOW-UP     (เสนอดูผลซ้ำใน 24-48 ชม.)
```

---

## Money Safety Rules (ใช้ทุก phase)

```
Hard stop:
- ห้าม assume / default งบใหม่หรือ delta งบ
- ห้าม assume / default bid cap, CPF, CPA, CPC ใหม่
- ทุกค่าเงินที่จะเปลี่ยน ต้องมาจาก user เป็นตัวเลขชัดเจน
- ก่อน execute action ที่กระทบเงิน (เพิ่มงบ, เปลี่ยน bid, pause, restart)
  → ต้อง confirm จำนวนเงิน + ระยะเวลาผลกระทบ ก่อนทุกครั้ง
```

ตัวอย่างคำถามที่ถูก:
> "อยากเพิ่มงบจาก ฿300 → กี่บาทครับ? ระบบจะ start ทันทีหลังบันทึก"

ตัวอย่างที่ผิด:
> "ขอเพิ่มงบ 20% นะครับ" ❌ (Cowork ตัดสินใจ % เอง)

---

## PHASE 1 — INTAKE

### Step 1.1: เลือก campaign

ถาม:
> "อยากปรับ campaign ไหนครับ? หรือดูทั้งหมดก่อน?"

ถ้า user ระบุชื่อ → เปิดเฉพาะ campaign นั้น
ถ้า user บอก "ดูทั้งหมด" → เปิด dashboard summary

### Step 1.2: เลือก entry_mode

```
จะให้ผมช่วยแบบไหนครับ?

1. ผมวิเคราะห์ + เสนอ action, คุณกดปรับเอง — ประหยัด token, control 100%
2. ผมวิเคราะห์ + execute action ให้, คุณยืนยันก่อนทุกครั้ง — สะดวก แต่ใช้ token มากกว่า

แนะนำ: ถ้า familiar กับ LINE Ads แล้ว เลือก 1 ครับ
```

บันทึกเป็น `optimize_entry_mode`:
- `ADVISE_ONLY` = Cowork วิเคราะห์ + แนะนำ user ทำเอง
- `EXECUTE` = Cowork ทำ action หลัง user confirm

Default `ADVISE_ONLY` ถ้า user ไม่แน่ใจ

---

## PHASE 2 — DIAGNOSE

### Step 2.1: ดึงข้อมูล (Token-disciplined)

```
✅ DO:
- ใช้ read_page interactive เพื่อดึงตาราง metrics
- ดึงเฉพาะ columns ที่ต้องใช้:
  Impressions, Clicks, CTR, Spend, CPC/CPM, 
  Conversions/Friends, Status, Budget remaining
- screenshot เฉพาะตอน:
  · chart/visual ที่ DOM อ่านไม่ได้
  · error message เฉพาะที่ user ต้องเห็น
  · ตาราง 7-day trend ที่ต้อง compare visual

❌ DON'T:
- screenshot dashboard ทั้งหน้าทุกครั้ง
- ดึง metric ที่ไม่ relevant กับ objective
```

### Step 2.2: เทียบ benchmark

โหลด `knowledge/kpi-benchmarks.md` ตอนนี้

Common diagnose patterns:

```
[Friend Added Campaign]
Friend = 0 + Impression > 1,000
  → CPF cap ต่ำเกิน (bid ไม่ชนะ) หรือ targeting แคบ
  
Friend = 0 + Impression < 100
  → Ad ยังไม่ approve หรือ targeting ใหญ่เกินจน LINE หา audience ไม่เจอ

CPF จริง > CPF cap × 0.9
  → ใกล้ ceiling — ขยับ cap ขึ้นจะได้ friend เพิ่มเร็ว

[Website Click Campaign]
CTR < 1.0% + Impression > 5,000
  → Creative/Headline ไม่ดึงดูด → เปลี่ยน creative
  
CTR ปกติ + CPC สูง > ฿10
  → Bidding หรือ competition สูง → ลอง auto bid

[ทุก objective]
Budget หมดก่อนเที่ยง 3 วันติด
  → audience ตอบสนองดี → user อาจอยากเพิ่มงบ (ห้ามเพิ่มเอง)

Budget ใช้ < 50% ของวัน 3 วันติด
  → bid ต่ำเกิน หรือ audience แคบเกิน → ขยับ bid หรือขยาย targeting
  
Status = Rejected
  → ดู rejection reason → แปลไทย → แนะนำวิธีแก้
```

### Step 2.3: สรุป diagnosis ให้ user

```
📊 [ชื่อ Campaign] — [วันที่เก็บข้อมูล]

ผลลัพธ์:
• [metric หลัก]: [ค่า] ([ดี/ปานกลาง/ต้องปรับ])
• [metric รอง]: [ค่า]

ปัญหาที่เจอ:
1. [ปัญหา] — [reason]
2. [ปัญหา] — [reason]
```

---

## PHASE 3 — RECOMMEND ACTION

เสนอ 2-3 ทางเลือก พร้อม trade-off ชัดเจน:

```
แนะนำ 3 ทางครับ เลือกได้:

[A] [Action เร็ว แก้ symptom] — เช่น "ขยับ CPF cap จาก ฿15 → ฿25"
    Trade-off: เพิ่ม cost/friend แต่ได้ friend เร็วขึ้น
    Risk: HIGH (กระทบเงิน) — ต้อง confirm จำนวนเงิน

[B] [Action กลางๆ แก้ root cause] — เช่น "เปลี่ยน creative ให้ชัดเจนกว่าเดิม"
    Trade-off: ใช้เวลา 1-2 วัน learning ใหม่ แต่ CPF จะถูกลงระยะยาว
    Risk: MEDIUM — ใช้เวลา ไม่กระทบเงินทันที

[C] [Action ระยะยาว แก้กลยุทธ์] — เช่น "เพิ่ม Ad Set ใหม่ targeting ละเอียด"
    Trade-off: ต้องสร้างใหม่ 1 set + creative
    Risk: HIGH (เพิ่มงบ) — ต้องตกลง budget ใหม่
    
ห้ามทำทันที: ผมจะรอให้คุณเลือกและยืนยันตัวเลขก่อน
```

---

## PHASE 4 — CONFIRM

หลัง user เลือก action:

```
สรุปก่อนทำ:
• Action: [ชื่อ]
• Campaign/Ad Set: [ชื่อ]
• ค่าเดิม: [old value]
• ค่าใหม่: [new value — มาจาก user]
• ผลกระทบทันที: [Impressions/Spend จะเปลี่ยนยังไง]
• Risk level: [Low/Medium/High]

ยืนยันให้ผมทำเลยไหมครับ?
```

ถ้า Risk = HIGH (กระทบเงิน): ต้องได้คำว่า "ยืนยัน"/"โอเค" ชัดเจน
ถ้า Risk = MEDIUM: bundle confirm ได้

---

## PHASE 5 — EXECUTE

### Step 5.1: Snapshot ก่อนทำ

บันทึกค่า metric + setting ปัจจุบัน:
```
- Campaign Budget: ฿X/วัน
- CPF cap: ฿Y
- Status: Active
- 7-day metrics: [Impressions, Friends, Spend, CPF avg]
```

เก็บใน context หรือบันทึกที่ `reports/optimization-[YYYY-MM-DD]-before.md`

### Step 5.2: ทำ action

```
Action types + execution rules:

[Pause Ad Set/Campaign]
- Risk: MEDIUM (หยุด spend แต่ไม่กลับมาอัตโนมัติ)
- Step: Navigate → Ad Set → toggle status PAUSED
- ต้อง confirm ก่อนทำ

[Restart paused]
- Risk: MEDIUM (เริ่ม spend อีกครั้ง)
- Step: toggle status ACTIVE
- ต้อง confirm + ทวน budget เดิม

[Change Budget]
- Risk: HIGH (เงิน)
- Rule: ต้องมีตัวเลขใหม่จาก user เท่านั้น
- ห้าม Cowork คำนวณ % เอง (เช่น +20%)
- Step: Edit campaign → ใส่ตัวเลขใหม่ → save

[Change Bid Cap (CPF/CPC/CPA)]
- Risk: HIGH (เงิน)
- Rule: ต้องมีตัวเลขใหม่จาก user เท่านั้น
- Step: Edit ad set → bid section → ใส่ค่าใหม่ → save

[Change Creative]
- Risk: MEDIUM (กระทบ learning phase)
- Rule: ใช้ creative ใหม่ที่ user ยืนยันแล้ว
- ระวัง: pause learning 24-48 ชม.

[Change Targeting]
- Risk: MEDIUM (กระทบ delivery)
- Rule: บันทึก targeting เดิมก่อน เผื่อต้อง revert
```

⚠️ **ห้าม delete campaign/ad set/ad** ถ้า user ไม่สั่งชัดเจน — ใช้ pause แทน

### Step 5.3: Snapshot หลังทำ

อ่าน metric หลัง save 2-3 นาที (ถ้าระบบยังไม่ update ให้ note ว่า "รอ LINE process")

---

## PHASE 6 — FOLLOW-UP

```
✅ ปรับเรียบร้อยครับ

ก่อนปรับ → หลังปรับ:
• [metric]: [old] → [new]

เสนอตามดูผลใน 24-48 ชม.:
[ ตั้ง schedule report เพิ่ม ] [ จะเรียกผมดูผลเองทีหลัง ]
```

ถ้า user ตอบ "ตั้ง schedule" → switch ไป MODE 3

---

## ROLLBACK PLAN

ถ้าหลังปรับแล้วผลแย่ลง (CPF พุ่ง / Friends ลด > 30%):

```
ผลหลังปรับ 24 ชม. แย่กว่าเดิม:
• [metric]: [old] → [new] = [delta]

แนะนำ rollback กลับค่าเดิม:
• [setting]: [new] → [old]

ยืนยันให้ revert ไหมครับ? (Risk: HIGH — กระทบเงิน)
```

ทำ revert เป็น action ใหม่ ผ่าน PHASE 4-5 ปกติ (ต้อง confirm)

---

## NOTES สำหรับ Cowork Agent

1. **Money inputs จาก user เท่านั้น** — ห้าม Cowork ตัดสินใจ % หรือจำนวนเงินเอง
2. **Snapshot before/after** ทุกครั้งที่ทำ action ที่กระทบ metrics
3. **Pause ก่อน Delete** — ถ้าไม่แน่ใจให้ pause ก่อน delete ไม่ได้
4. **Rollback plan** — ทุก action ต้องคิดล่วงหน้าว่า revert ยังไงถ้าผลแย่
5. **Token discipline** — โหลด kpi-benchmarks.md เฉพาะ Phase 2; screenshot เฉพาะ chart/error
6. **Risk-based confirm** — ทุก action ที่เป็น HIGH risk ต้อง confirm จำนวนเงินชัดเจน

---

*Version 2.0 | May 2026*
*Updated: Money Safety + entry_mode + snapshot before/after + rollback plan + risk-based confirm*
