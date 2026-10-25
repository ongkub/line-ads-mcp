# workflows/07-campaign-planner.md
# Data-driven Campaign Planner Workflow
# Version 1.0 | October 2026 | MCP-first | ไม่อยู่ในเล่มแล้ว (ตัดออก 19 ต.ค. 2026) — เก็บไว้เป็นโหมดเสริม

---

## Overview

MODE 7 วางแผนแคมเปญใหม่จากประวัติในบัญชี ก่อนส่งต่อ MODE 2 เพื่อสร้าง
Trigger: “อยากเปิดแคมเปญใหม่ ช่วยวางแผนจากผลที่ผ่านมา”
เริ่มจากแชทประโยคเดียว AI ดึงประวัติผ่าน MCP เอง ไม่ต้องทำ brief หรือแนบรายงาน

```
PHASE 1 → BUSINESS INTAKE
PHASE 2 → FETCH HISTORY
PHASE 3 → DATA SUFFICIENCY
PHASE 4 → EVIDENCE-BASED PLAN
PHASE 5 → REVIEW + HANDOFF TO MODE 2
```

## Knowledge Loading Gate

อ่านก่อนเริ่ม:
- `knowledge/planning-from-history.md` — ความเพียงพอ, budget split, confidence และข้อห้ามสรุป
- `knowledge/kpi-benchmarks.md` — benchmark ตาม objective เป็นบริบท ไม่แทนข้อมูลจริง
- `knowledge/bidding-strategy.md` — bid/learning และเงื่อนไขก่อนสร้าง
- `knowledge/report-metrics.md` — หน่วย, weighted ratios, results และวัน UTC

เมื่อเลือก targeting อ่าน `knowledge/interest-catalog-INDEX.md` และ detail เฉพาะหมวด
เมื่อวาง creative อ่าน `knowledge/ad-specs.md` ก่อนเสนอข้อกำหนดไฟล์/ข้อความ
ถ้า knowledge ที่จำเป็นยังไม่พร้อม ให้ระบุข้อจำกัด ห้ามแต่งกฎแทน

---

## PHASE 1 — Business Intake

### สิ่งที่ AI ต้องถาม

ถามทีละข้อ และข้ามสิ่งที่ผู้ใช้บอกแล้ว:
1. เป้าหมายธุรกิจใหม่และสินค้า/ข้อเสนอที่ต้องการโปรโมต
2. งบรวมกี่บาท — ต้องเป็นตัวเลขจากผู้ใช้ ห้ามเดาจากงบแคมเปญเก่า
3. วันเริ่ม; ถ้าจะคำนวณงบรายวัน ให้ถามวันจบหรือระยะเวลาที่ต้องการด้วย
4. สิ่งที่ยังไม่แน่ใจ เช่น กลุ่มใหม่, offer, creative หรือ tracking ที่เปลี่ยนไป

อย่าถามตัวเลข performance หรือให้ผู้ใช้รวบรวมไฟล์ที่ MCP อ่านได้
ถ้าผู้ใช้ยังไม่ทราบ budget/date ให้ทำได้เฉพาะวิเคราะห์ประวัติและระบุว่าแผนเงิน/วันยังรอข้อมูล
เป้าหมายใหม่ต้อง map เป็น objective ที่รองรับ ห้ามถือว่าเพิ่มเพื่อนเท่ากับยอดขาย

---

## PHASE 2 — Fetch History

ประกาศช่วงย้อนหลังและวัน UTC ชัดเจน; เริ่ม 4 สัปดาห์เต็มล่าสุดถ้ายังไม่ระบุ
ถ้าประวัติน้อยหรือมี seasonality ให้ขยายช่วงพร้อมบอกเหตุผล ไม่อ้างข้อมูลที่ยังไม่ได้ดึง

```python
list_campaigns(status=None, fetch_all=True)
list_adsets(campaign_id=None, status=None, fetch_all=True)
list_ads(adset_id=None, campaign_id=None, status=None, fetch_all=True)
get_report(level="CAMPAIGN", start_date=start_date, end_date=end_date,
           campaign_id=None, fetch_all=True, by_day=True)
get_report(level="ADGROUP", start_date=start_date, end_date=end_date,
           campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)
get_report(level="AD", start_date=start_date, end_date=end_date,
           campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)
```

- `by_day=True` สูงสุด 93 วันต่อคำขอ; แบ่งช่วงไม่ซ้อนกันเมื่อจำเป็น
- ผูก ID campaign → ad set → ad เพื่อเชื่อม objective/targeting/creative กับผลงาน
- รวมรายการที่ PAUSED/REMOVED ซึ่งอาจมีประวัติ ไม่ใช้ status ปัจจุบันตัดผลเก่า
- ตรวจ `paging.complete` ทุก report/ทุกช่วง, date_basis UTC, หน่วย, currency และวันที่ข้อมูลขาด
- คำนวณอัตราจากผลรวม ไม่เฉลี่ยค่า ratio และไม่บวกยอดข้ามระดับซ้ำ
- `list_ads` ให้ข้อมูลเท่าที่มี; ถ้าไม่เห็นเนื้อหา/ภาพ creative ให้ระบุว่ามุม creative เป็นสมมติฐาน

---

## PHASE 3 — Data Sufficiency

ใช้เกณฑ์ใน `knowledge/planning-from-history.md` ก่อนแนะนำ budget split
เช็กอย่างน้อย:

| เรื่อง | หลักฐานที่ต้องแสดง |
|---|---|
| ความครบ | ช่วง UTC, จำนวนวันที่มีข้อมูล, paging และช่องว่าง |
| ความเกี่ยวข้อง | objective, สินค้า/offer, tracking และฤดูกาลใกล้กับแผนใหม่แค่ไหน |
| ปริมาณ | spend, impressions, results และวันทำงานจริงของแต่ละกลุ่ม |
| ความเสถียร | ผลรายวัน/ช่วงที่ผันผวน, learning และการเปลี่ยนแปลงที่ทราบ |
| สิ่งที่ยังแยกไม่ได้ | ผลจาก creative/bid/offer กับ targeting ที่เปลี่ยนพร้อมกัน |

- เปรียบเทียบต้นทุนเฉพาะ objective/result type เดียวกัน
- WEBSITE_CONVERSION ใช้ CPA; GAIN_FRIENDS ใช้ CPF ตาม metric dictionary
- Traffic/Reach/Video/App ใช้ CPC/CPM/CPV/CPI ตาม objective ไม่บังคับแปลงเป็น CPA
- ผลลัพธ์ 0/unknown คำนวณ cost per result ไม่ได้ ห้ามจัดให้เป็นต้นทุนศูนย์
- อย่ากำหนด sample threshold ใหม่เอง ถ้า knowledge ไม่รองรับ ให้บอกข้อจำกัด

### ถ้าข้อมูลไม่เพียงพอ

บอกตรง ๆ ว่าขาดอะไร เช่น “มีเพียง 3 ผลลัพธ์ ยังใช้แบ่งงบจากประวัติอย่างมั่นใจไม่ได้”
เสนอ **Basic Campaign Planner skill** สำหรับเริ่มจากข้อมูลธุรกิจและแผนทดสอบ
อย่าอ้างว่ามี MCP tool นี้ หรือว่าได้เรียก skill แล้วถ้ายังเข้าถึงไม่ได้
ไม่ต้องให้ผู้ใช้เตรียมไฟล์ และไม่แต่ง CPA/CPF เพื่อเติมแผน
ถ้ามีประวัติเพียงบางส่วน ให้เสนอแผนทดสอบ confidence ต่ำ โดยแยกสมมติฐานจากหลักฐาน

---

## PHASE 4 — Evidence-based Plan

แผนต้องมี:
1. Objective ที่สอดคล้องกับเป้าหมายใหม่ พร้อมเหตุผลจากประวัติที่เกี่ยวข้อง
2. โครงสร้าง campaign/ad set/ad และจำนวนที่เสนอ; แยกกลุ่มใช้ต่อกับกลุ่มทดลอง
3. Budget split เป็น % และบาทภายในงบรวมที่ผู้ใช้ให้ พร้อมเหตุผลจากต้นทุนจริง
4. Targeting: กลุ่มเดิมที่มีหลักฐาน + กลุ่มใหม่ที่ต้องทดสอบ; codes/Custom IDs ต้องตรวจจริง
5. Creative angles จากข้อความ/ภาพหรือ offer ที่มีหลักฐาน; ส่วนที่คิดใหม่ระบุว่าเป็นสมมติฐาน
6. Confidence high/medium/low ของแต่ละข้อเสนอ พร้อมตัวเลขและข้อจำกัด
7. วิธีประเมินหลังเริ่ม: KPI ตาม objective, ช่วงทบทวน และสิ่งที่ต้องเรียนรู้

### Budget Safety

- การเสนอ split ทำได้จากงบรวมที่ผู้ใช้ระบุ; เป็น **ข้อเสนอรออนุมัติ** ยังไม่ใช่ค่า write
- อธิบายด้วย spend/results จริง เช่น CPF = spend/friends; ไม่ใช้ benchmark เป็น “ผลบัญชีนี้”
- แสดงยอดแต่ละกลุ่มรวมเท่ากับงบรวม; แยกงบรวมออกจาก daily_budget อย่างชัดเจน
- คำนวณงบต่อวันเฉพาะเมื่อทราบระยะเวลาจากผู้ใช้ และให้ผู้ใช้ยืนยันเลขก่อนส่งต่อ dry-run
- ต้นทุนย้อนหลังไม่ใช่ bid cap อัตโนมัติ; ถ้าต้องใช้ cap ให้ถามตัวเลขผู้ใช้แยกต่างหาก
- คาดการณ์ผลได้เมื่อข้อมูลพอ โดยแสดงสูตร/สมมติฐาน ไม่รับประกันว่าจะได้ต้นทุนเดิมเมื่อเพิ่มงบ

### Confidence

ยึดเกณฑ์ `knowledge/planning-from-history.md`:
- **high** — หลักฐานครบและเกี่ยวข้อง ปริมาณ/ความเสถียรผ่านเกณฑ์ พร้อมแสดงตัวเลข
- **medium** — มีหลักฐานใช้ประกอบได้ แต่มีข้อจำกัดที่ระบุชัด
- **low** — ข้อมูลน้อย/เปลี่ยนบริบท/เป็นแนวคิดใหม่ ต้องทดสอบก่อนขยาย

ห้ามใช้ confidence สูงทั้งแผนเพียงเพราะกลุ่มเดิมกลุ่มเดียวเคยได้ผลดี
ไม่มี creative breakdown หรือยอดขายจริง ห้ามสรุป creative ชนะ/ROAS ดี

### ตัวอย่างแผน (ตัวอย่างสมมติ)

```
เป้าหมาย: เพิ่มเพื่อน → GAIN_FRIENDS; งบรวมที่ผู้ใช้ให้ ฿18,000
เริ่ม 1 พ.ย. 2026; ระยะเวลา 30 วันตามผู้ใช้
ข้อมูล 1–28 ก.ย. (UTC), paging ครบ:
กลุ่ม A ฿6,000 / 400 เพื่อน → CPF ฿15
กลุ่ม B ฿3,600 / 180 เพื่อน → CPF ฿20
ข้อเสนอ: 1 campaign / 2 ad sets / 4 ads
A ฿12,600 (70%, ฿420/วัน), B ฿5,400 (30%, ฿180/วัน)
ให้น้ำหนัก A เพราะ CPF ต่ำกว่า แต่ยังเก็บ B ทดสอบ; ไม่รับประกัน CPF เดิม
Targeting: ใช้กลุ่มเดิมที่ตรวจ ID/เงื่อนไขแล้ว พร้อมยกเว้นเพื่อน OA
Creative: ทดสอบมุมประโยชน์กับมุมข้อเสนอ เป็นสมมติฐานใหม่
Confidence: medium — มี 580 ผลลัพธ์ แต่ offer ใหม่และการแบ่งงบยังต้องทดสอบ
Bid cap: ยังรอผู้ใช้ระบุ; ยังไม่สร้างหรือแก้บัญชีครับ
```

---

## PHASE 5 — Review + Handoff to MODE 2

ปิดแผนด้วย:

```
ถ้าต้องการไปขั้นสร้าง พิมพ์ “สร้างตามแผนนี้” ครับ
ผมจะใช้แผนในแชทนี้ต่อ แล้วทำ dry-run ให้ตรวจ ก่อนรอคำว่า “ยืนยัน” เพื่อส่งจริง
```

เมื่อผู้ใช้พิมพ์ **“สร้างตามแผนนี้”**:
1. เปิด `workflows/02-campaign.md` ในแชทเดิม ไม่สร้าง brief file และไม่ขอให้ผู้ใช้แนบไฟล์แผน
2. ส่งต่อ objective, จำนวน entity/creative, targeting, exclusions, budget split,
   วันเริ่ม/ระยะเวลา, bid ที่ผู้ใช้ให้, confidence และข้อมูลที่ยังขาดจากแผนในแชท
3. ใช้ข้อมูลที่ตอบแล้ว ไม่ถามซ้ำ; ให้ MODE 2 ตรวจ method/duplicate/ข้อกำหนดที่ยังไม่ครบ
4. ทุก write: `dry_run=True` → สรุปชื่อ/ID/จำนวน/ตัวเลข → ผู้ใช้พิมพ์ “ยืนยัน” → `dry_run=False`
5. สร้างด้วย `status="PAUSED"` เป็นค่าเริ่มต้น; การ resume ต้อง dry-run + “ยืนยัน” แยก
6. ตรวจ `readback`, `readback_ok`; ถ้าไม่ยืนยันให้ใช้ `get_entity(entity_type=entity_type, entity_id=entity_id)`
   แล้วเทียบค่าที่ตกลง ห้ามรายงานสำเร็จถ้า readback ยังไม่ตรง

“สร้างตามแผนนี้” เป็นคำขอเข้าสู่ขั้นสร้าง ไม่ใช่อนุญาตข้าม dry-run/confirmation

## ห้าม

- ห้ามใช้ MCP write tools ภายใน MODE 7; ส่งต่อ MODE 2 ก่อนเสมอ
- ห้ามเดางบรวม/งบรายวัน/bid/วันเริ่ม หรือเอาเงินเก่ามาใช้เป็นคำอนุมัติใหม่
- ห้ามสรุปยอดขาย/ROAS จากเพื่อนหรือคลิก และห้ามรับประกันผลลัพธ์ในอนาคต
- ห้ามใช้ข้อมูลไม่ครบหรือ sample น้อยตัดสินผู้ชนะโดยไม่บอกข้อจำกัด
- ห้ามสร้างไฟล์ brief/ขอไฟล์รายงานจากผู้อ่าน หรือเรียก skill/tool ที่ไม่มีจริง
