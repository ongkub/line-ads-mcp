# workflows/05-dashboard.md
# Ads Dashboard Workflow
# Version 1.0 | October 2026 | MCP-first | บทที่ 4

---

## Overview

MODE 5 เปลี่ยนผลจากบัญชี LINE Ads เป็น Claude Artifact สำหรับดูภาพรวม
เริ่มได้ด้วยประโยคเดียว เช่น “ทำ dashboard ผลโฆษณา 4 สัปดาห์ล่าสุด”
AI ดึงข้อมูลเองผ่าน MCP; ผู้ใช้ไม่ต้องเตรียมหรือแนบไฟล์รายงาน

```
PHASE 1 → INTAKE
PHASE 2 → FETCH REPORTS
PHASE 3 → VALIDATE + NORMALIZE
PHASE 4 → BUILD ARTIFACT
PHASE 5 → REVIEW + REFRESH
```

## Knowledge Loading Gate

ก่อนเริ่ม อ่าน:
- `knowledge/report-metrics.md` — ชื่อ metric, หน่วย, weighted ratios และวันรายงาน UTC
- `knowledge/dashboard-spec.md` — KPI ตาม objective, chart และ unknown vs 0
- `workflows/05-dashboard.md` — ขั้นตอน MODE 5 แบบอ่านอย่างเดียว

ถ้าไฟล์ที่ต้องใช้อ่านไม่ได้ ให้แจ้งข้อจำกัด ห้ามแต่งนิยาม metric แทน

---

## PHASE 1 — Intake

### สิ่งที่ AI ต้องถาม

ถามทีละเรื่อง เฉพาะที่ยังไม่ทราบ:
1. ช่วงวันที่ต้องการ ถ้าบอก “4 สัปดาห์ล่าสุด” แล้ว ให้ใช้ 28 วันเต็มก่อนวันนี้บนฐาน UTC และแจ้งวันที่ชัดเจน
2. “มีตัวชี้วัดที่อยากดูเป็นพิเศษไหมครับ? ถ้าไม่มี ผมเลือกตามเป้าหมายแคมเปญให้ครับ”

ไม่ถาม objective, campaign ID หรือผลย้อนหลังที่อ่านจากบัญชีได้เอง
ถ้าระบุชื่อ campaign ให้หา ID ด้วย `list_campaigns(status=None, fetch_all=True)`
ช่วงวันที่ใช้ `YYYY-MM-DD`; แสดงว่าเป็น **UTC** รวมถึงวันที่บางส่วนถ้าผู้ใช้ขอรวมวันนี้

---

## PHASE 2 — Fetch Reports

เรียกทั้งสองระดับสำหรับช่วงเดียวกัน:

```python
get_report(level="CAMPAIGN", start_date=start_date, end_date=end_date,
           campaign_id=None, fetch_all=True, by_day=True)
get_report(level="AD", start_date=start_date, end_date=end_date,
           campaign_id=None, fetch_all=True, by_day=False)
```

- ถ้าดูเฉพาะ campaign ให้แทน `campaign_id=None` ด้วย ID ที่ตรวจแล้ว
- `by_day=True` จำกัด 93 วันต่อคำขอ; ช่วงยาวกว่านั้นแบ่งช่วงไม่ซ้อนกันแล้วรวมตามวัน×ID
- โหลด `list_campaigns(status=None, fetch_all=True)` เพื่อผูก objective/name เมื่อ report ไม่มี
- ถ้าข้อมูลโฆษณาขาดชื่อหรือ parent ID ใช้ `list_ads(campaign_id=None, status=None, fetch_all=True)` เพิ่มเท่าที่จำเป็น
- ไม่กรองเฉพาะ ACTIVE: รายการ PAUSED/REMOVED อาจมีผลงานในช่วงที่ดู

### ประวัติจากบทที่ 5 (optional)

ถ้ามี `line-ads-data/ad_daily.csv` อยู่แล้วใน workspace ที่เข้าถึงได้ ให้ AI อ่านเองเพื่อเสริมช่วงเก่า
ถ้าไม่มี ให้ใช้ MCP ต่อ ไม่ขอให้ผู้ใช้เตรียม/แนบ/เขียนไฟล์ และไม่เรียก `sync_ad_daily_csv`

- ตรวจ schema, currency, objective, date basis และความครบของช่วงก่อนรวม
- รวมเฉพาะข้อมูลที่เข้ากันได้; ถ้าวันใน CSV ไม่ใช่ UTC ห้ามเปลี่ยนชื่อวันแล้วนำมารวม
- ใช้ key `date + ad_id` ป้องกันซ้ำ; ช่วงซ้อนใช้ MCP ที่ดึงล่าสุดแทน ไม่บวกซ้ำ
- แยกแหล่งข้อมูล/เวลาที่ดึง; อย่าบวก campaign totals กับ ad totals เพราะเป็นเงินก้อนเดียวกัน
- ถ้าจะใช้ CSV สร้าง daily trend ต้องมีข้อมูลรายวันครบและ reconcile กับ MCP ได้; ส่วนที่ยืนยันไม่ได้ให้แยกแสดงพร้อมหมายเหตุ

---

## PHASE 3 — Validate + Normalize

ก่อนแสดง KPI:
1. ตรวจ `paging.complete` ทุก response และทุกช่วงย่อย; false/ไม่มีค่า = ยังยืนยันความครบไม่ได้
2. ตรวจ `date_basis: "UTC"`, วันที่ครอบคลุม, ID ซ้ำ, currency และหน่วยเงินตาม `knowledge/report-metrics.md`
3. แยก campaign ตาม objective ก่อนเลือก result และ cost per result
4. คำนวณอัตรารวมจากผลรวมตัวตั้ง/ตัวหาร ไม่เฉลี่ย CTR/CPC/CPA รายแถว
5. ค่า `None`, metric ที่ API ไม่คืน และตัวหาร 0 แสดง “ไม่มีข้อมูล/คำนวณไม่ได้”; 0 ใช้เฉพาะค่าศูนย์ที่ยืนยันได้

สูตรที่ใช้เมื่อหน่วยผ่านการตรวจแล้ว:

```
CTR (%) = sum(clicks) / sum(impressions) × 100
CPC = sum(spend) / sum(clicks)
CPM = sum(spend) / sum(impressions) × 1,000
Cost per result = sum(spend) / sum(results ของ objective เดียวกัน)
```

`summary.avg_ctr` เป็นเปอร์เซ็นต์แล้ว ห้ามคูณ 100 ซ้ำ
ไม่รวม Friends, Clicks, Installs และ Conversions เป็น “ผลลัพธ์รวม” เดียวกัน
ไม่ใช้ CV/CPA/ROAS กับ objective ที่ไม่ใช่ CONVERSIONS
Reach เป็น unique metric ห้ามบวกรายวัน/รายแคมเปญเพื่ออ้างว่าเป็น unique reach ทั้งบัญชี
ถ้าข้อมูลไม่ครบ แสดงได้เฉพาะยอดที่ดึงได้พร้อมคำเตือนชัดเจน ห้ามเรียกว่า total ทั้งบัญชี

---

## PHASE 4 — Build Claude Artifact

Claude สร้าง Artifact เองตาม `knowledge/dashboard-spec.md` ไม่มี dashboard MCP tool
จัดให้อ่านง่ายและมีส่วนต่อไปนี้:

| ส่วน | เนื้อหา |
|---|---|
| Header | ช่วงวันที่ UTC, เวลา refresh, แหล่งข้อมูล, สถานะความครบ |
| KPI tiles | Spend/Impressions และ KPI ตาม objective แยกกลุ่ม |
| Daily trend | Spend และผลลัพธ์ตาม objective จากวัน×campaign; ไม่ปนหน่วยบนแกนเดียว |
| Campaign table | ชื่อ, objective, spend, results และ cost/ratio ที่เกี่ยวข้อง |
| Ad table | ชื่อ/ID, campaign, spend และ KPI ตาม objective; ไม่แต่ง creative preview |
| Data gaps | วันที่/metric ที่ขาด, paging ไม่ครบ, unknown และข้อจำกัดการรวม CSV |

- ระบุหน่วยบาท/สกุลเงินจริง, %, จำนวนครั้ง หรือจำนวนคนให้ตรง metric
- แสดงช่องว่างในกราฟเมื่อไม่ทราบค่า; วันไม่มีแถวไม่เท่ากับ spend=0 โดยอัตโนมัติ
- แยกตารางตาม objective ถ้าการเทียบแถวเดียวกันทำให้เข้าใจผิด
- ถ้า Artifact ใช้งานไม่ได้ ให้สรุปตารางในแชทและบอกข้อจำกัด ไม่อ้างว่าสร้างแล้ว

---

## PHASE 5 — Review + Refresh

สรุปข้อค้นพบที่มีหลักฐาน พร้อมจุดที่ยังสรุปไม่ได้
Dashboard เป็น **snapshot** ณ เวลาที่ดึงข้อมูล ไม่อัปเดตเอง
เมื่อผู้ใช้ขอ “รีเฟรช dashboard” ให้เรียก MCP ใหม่และตรวจความครบซ้ำ
ถ้าขอตั้งเวลา ให้ส่งต่อ MODE 3; MODE 5 ไม่สร้าง scheduled task

### ตัวอย่างผลลัพธ์ (ตัวอย่างสมมติ)

```
Dashboard: 1–28 ก.ย. 2026 (UTC), ข้อมูลครบ ณ เวลาที่ดึง
GAIN_FRIENDS: ใช้ ฿6,000 / เพื่อนใหม่ 400 / CPF ฿15
WEBSITE_TRAFFIC: ใช้ ฿2,000 / คลิก 1,000 / CPC ฿2
กราฟรายวัน + ตาราง campaign/ad อยู่ใน Artifact
ROAS: ไม่มีข้อมูลรายได้ จึงไม่แสดงค่า 0
นี่เป็น snapshot; พิมพ์ “รีเฟรช dashboard” เมื่อต้องการข้อมูลใหม่ครับ
```

## ห้าม

- ห้ามใช้ MCP write tools รวมถึง create/update/pause/resume/upload หรือ sync CSV
- ห้ามสร้างเครื่องมือ dashboard/scheduler ที่ไม่มีจริง
- ห้ามขอให้ผู้อ่านเตรียมไฟล์รายงาน หรือถือว่ามีประวัติบทที่ 2 เสมอ
- ห้ามซ่อนข้อมูลไม่ครบ, เติม unknown เป็น 0 หรือรวม KPI ต่าง objective
- ห้ามสรุปว่าเป็นข้อมูลสดต่อเนื่อง หรือรายงานวัน UTC เป็นวันไทยโดยไม่แปลงข้อมูล
