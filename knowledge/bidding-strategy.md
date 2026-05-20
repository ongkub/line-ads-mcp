# knowledge/bidding-strategy.md
# Bidding Strategy Decision Tree
# โหลดเฉพาะ PATH B ของ 02-campaign.md

---

## Objective → Recommended Bidding

| Objective | Bid Type | Bid Strategy | Budget ขั้นต่ำ/วัน |
|---|---|---|---|
| GAIN_FRIENDS | CPF | COST_CAP / LOWEST_COST | ฿100 |
| WEBSITE_TRAFFIC | CPC | COST_CAP / LOWEST_COST | ฿100 |
| CONVERSIONS | CPC | COST_CAP | ฿300 |
| REACH | CPM | LOWEST_COST | ฿50 |
| APP_INSTALL | CPC | COST_CAP / LOWEST_COST | ฿100 |
| VIDEO_VIEW | CPV | LOWEST_COST | ฿50 |

## Real Cost Reference (ข้อมูลจริงจาก LINE Ads TH)

> ดูตาราง CPC × Industry และ CPC × Ad Format ฉบับเต็มได้ที่ `knowledge/kpi-benchmarks.md`

Cost สำหรับ objective ยอดนิยม (ช่วงกลาง อ้างอิง):

| Objective | Cost ปกติ |
|---|---|
| GAIN_FRIENDS | CPF ฿10-22 (ขึ้นกับ industry) |
| WEBSITE_TRAFFIC (VISIT_MY_WEBSITE) | CPC ฿1.70-3.50 |
| REACH | CPM ฿6-8 |
| VIDEO_VIEW | CPV ฿0.02-0.09 |
| APP_INSTALL | CPC ฿0.90-3.70 |
| WEBSITE_CONVERSION | CPC ฿1.90-3.40 |

หมายเหตุ: GAIN_FRIENDS มี CPF สูงที่สุดในกลุ่ม fitnessAndMedicalService (฿22.58) และต่ำที่สุดใน lawAndGovernment (฿10.34)

## เมื่อไรใช้ Manual Bid

```
ใช้ Auto ก่อนเสมอ (2–3 วันแรก)
Switch ไป Manual ถ้า:
  - Spend < 60% ของ daily budget ติดต่อกัน 3 วัน (underspend)
  - CPF/CPC/CPA สูงกว่า benchmark tier สูงสุด ติดต่อกัน > 2 วัน
  - Learning phase เสร็จ (> 14 วัน) แล้ว result ยังไม่ดีเมื่อเทียบ benchmark
  - ต้องการ control ราคาเพดาน
```

ก่อน switch:
- โหลด `knowledge/kpi-benchmarks.md` เพื่อเทียบ objective + industry tier
- ห้ามเลือกตัวเลข manual bid แทน user ให้เสนอช่วงอ้างอิง แล้วถาม user ระบุเลขเอง
- ถ้า campaign อายุ < 3 วัน ให้ระวังการสรุป เพราะยังอยู่ช่วง learning/early delivery

## Learning Phase

```
ช่วง Learning: 7–14 วันแรก
ระหว่าง Learning:
  - ห้ามเปลี่ยน targeting / bidding บ่อย
  - ห้ามเพิ่ม budget เกิน 20%/วัน
  - ผลลัพธ์อาจผันผวน — ปกติ

สถานะ "กำลังเรียนรู้" ใน LINE Ads → รอ 14 วันก่อนตัดสิน
```
