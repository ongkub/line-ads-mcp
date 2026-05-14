# knowledge/kpi-benchmarks.md
# KPI Benchmarks สำหรับ LINE Ads ไทย
# โหลดเฉพาะ MODE 3 (Report) และ MODE 4 (Optimize)

---

## CTR Benchmark

ใช้ตาราง objective-specific ก่อน generic benchmark เสมอ เพราะแต่ละ objective มี metric หลักต่างกัน

## Objective Benchmarks

| Objective | CTR ดี | Cost ปกติ | Metric หลัก |
|---|---:|---:|---|
| GAIN_FRIENDS | > 1.5% | CPF ฿8-20/friend | Friends, CPF |
| WEBSITE_TRAFFIC | > 0.8% | CPC ฿2-6/click | Clicks, CPC, CTR |
| CONVERSIONS | > 0.8% | CPA ขึ้นกับ margin | Conversions, CPA, CVR |
| REACH | > 0.5% | CPM ฿20-80 | Reach, CPM, Frequency |
| APP_INSTALL | > 0.8% | CPI ขึ้นกับ app category | Installs, CPI |
| VIDEO_VIEW | > 3.0% video engagement | CPV ฿0.5-2/view | Views, CPV, completion |

## Industry Tier Adjustments

| Industry Tier | ใช้กับ | Cost Expectation |
|---|---|---|
| Competitive/high intent | Healthcare, beauty clinic, insurance, finance, B2B lead | CPF/CPC/CPA มักสูงกว่า baseline 1.5-3x |
| Commerce/SME | Ecommerce, retail, restaurant, local service, agency for SMEs | ใช้ baseline objective เป็นหลัก |
| Mass awareness | FMCG, entertainment, video, reach campaign | CPM/CPV ต่ำกว่า baseline ได้ แต่ conversion intent ต่ำกว่า |

ถ้า industry อยู่ tier แข่งขันสูง อย่าสรุปว่า campaign แย่จาก cost สูงอย่างเดียว ให้ดู result quality, conversion intent, และ audience size ประกอบ

## Generic CTR Benchmark

| ระดับ | CTR | ความหมาย |
|---|---|---|
| ต่ำกว่า 1.0% | ต้องปรับ | Creative หรือ targeting มีปัญหา |
| 1.0%–2.0% | ปกติ | อยู่ในเกณฑ์มาตรฐาน |
| 2.0%–3.5% | ดี | ทำงานได้ดี |
| สูงกว่า 3.5% | ดีมาก | Excellent |

## CPC Benchmark (ประมาณการ)

| ระดับ | CPC | ความหมาย |
|---|---|---|
| ต่ำกว่า ฿2 | ประหยัดมาก | — |
| ฿2–฿5 | ปกติ | มาตรฐาน |
| ฿5–฿10 | สูง | ตรวจ audience |
| สูงกว่า ฿10 | สูงมาก | ปรับ bidding หรือ targeting |

## Budget Alert Thresholds

| เหลือ | Action |
|---|---|
| < 20% | แจ้ง user ว่าใกล้หมด |
| < 10% | 🚨 Alert ด่วน |
| 0% | 🚨 Alert + แนะนำเพิ่มงบ |

## Diagnosis Rules

```
ใช้ objective benchmark ก่อน generic rules
CTR ต่ำ + Impression สูง    → ปัญหา Creative
CPM สูง + Reach น้อย       → Audience แคบเกิน
CPC สูง + CTR ปกติ         → Bidding / competition
Budget หมดเร็ว + CPA สูง   → Audience ไม่ตรง
```
