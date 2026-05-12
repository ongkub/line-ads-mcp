# knowledge/kpi-benchmarks.md
# KPI Benchmarks สำหรับ LINE Ads ไทย
# โหลดเฉพาะ MODE 3 (Report) และ MODE 4 (Optimize)

---

## CTR Benchmark

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
CTR ต่ำ + Impression สูง    → ปัญหา Creative
CPM สูง + Reach น้อย       → Audience แคบเกิน
CPC สูง + CTR ปกติ         → Bidding / competition
Budget หมดเร็ว + CPA สูง   → Audience ไม่ตรง
```
