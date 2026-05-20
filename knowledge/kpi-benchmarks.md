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

## Real CPC Benchmark — Industry × Objective (THB, ข้อมูลจริง)

> ตารางนี้มาจากข้อมูลจริงของ LINE Ads TH ใช้เป็น reference เพื่อประเมิน cost ตาม industry + objective

| Industry | APP_ENGAGEMENT | APP_INSTALL | GAIN_FRIENDS | REACH | VIDEO_VIEW | VISIT_MY_WEBSITE | WEBSITE_CONVERSION |
|---|---:|---:|---:|---:|---:|---:|---:|
| automotive | 2.83 | 1.66 | 15.34 | 3.79 | 11.61 | 1.81 | 2.27 |
| beauty | — | — | 20.06 | 5.95 | 10.04 | 2.24 | 1.91 |
| careerAndBusiness | 2.91 | 3.11 | 19.56 | 3.28 | 20.51 | 1.94 | 2.31 |
| cosme | — | — | 17.02 | 3.82 | 10.96 | 1.89 | 1.94 |
| cpg | — | — | 14.44 | 3.49 | 9.14 | 3.47 | 2.58 |
| education | — | 0.90 | 17.77 | 3.10 | 19.02 | 1.79 | 3.35 |
| entertainmentAndMedia | — | 1.44 | 17.54 | 3.09 | 7.79 | 2.09 | 1.86 |
| familyAndSociety | — | 1.25 | 16.79 | 3.46 | 10.06 | 1.89 | 2.10 |
| fashion | 2.91 | 1.62 | 13.92 | 3.74 | 12.25 | 1.73 | 2.92 |
| financialServices | 3.10 | 2.17 | 12.22 | 3.92 | 15.74 | 2.08 | 2.82 |
| fitnessAndMedicalService | — | 1.99 | 22.58 | 3.90 | 12.46 | 2.09 | 2.15 |
| foodAndDrink | 4.16 | 2.37 | 15.01 | 3.48 | 13.23 | 2.05 | 1.88 |
| game | 1.83 | 2.23 | 24.56 | 5.79 | 17.48 | 2.35 | 2.22 |
| healthFood | — | — | 16.65 | 3.89 | 10.98 | 1.69 | 1.93 |
| lawAndGovernment | — | 1.60 | 10.34 | 4.90 | 10.95 | 2.05 | 2.58 |
| leisureAndSportsAndLifestyle | — | 1.32 | 13.45 | 3.94 | 11.31 | 1.90 | 2.69 |
| realEstate | — | — | 19.18 | 3.83 | 11.07 | 1.84 | 2.82 |
| shopping | 3.54 | 2.97 | 14.49 | 3.44 | 12.53 | 1.86 | 3.10 |
| technology | 0.91 | 2.07 | 18.40 | 3.77 | 12.51 | 2.30 | 2.56 |
| travel | — | — | 13.42 | 3.47 | 9.74 | 2.07 | 2.78 |

> หมายเหตุ: GAIN_FRIENDS CPC ≈ CPF จริง (cost per friend) ไม่ใช่ cost per click

## Real CPM Benchmark — Industry × REACH (THB)

| Industry | CPM (REACH) |
|---|---:|
| automotive | 6.69 |
| beauty | 7.60 |
| careerAndBusiness | 6.69 |
| cosme | 6.99 |
| cpg | 6.55 |
| education | 5.94 |
| entertainmentAndMedia | 7.47 |
| familyAndSociety | 6.59 |
| fashion | 7.50 |
| financialServices | 7.54 |
| fitnessAndMedicalService | 6.56 |
| foodAndDrink | 6.73 |
| game | 7.79 |
| healthFood | 6.71 |
| lawAndGovernment | 6.81 |
| leisureAndSportsAndLifestyle | 7.36 |
| realEstate | 6.66 |
| shopping | 7.65 |
| technology | 7.53 |
| travel | 6.25 |

## Real CPC Benchmark — Ad Format × Objective (THB)

| Ad Format | APP_ENGAGEMENT | APP_INSTALL | GAIN_FRIENDS | REACH | VIDEO_VIEW | VISIT_MY_WEBSITE | WEBSITE_CONVERSION |
|---|---:|---:|---:|---:|---:|---:|---:|
| ANIMATED IMAGE | 3.86 | 2.12 | 16.97 | 4.04 | — | 1.81 | 2.65 |
| CAROUSEL | 4.36 | 1.72 | — | 3.28 | — | 1.98 | 2.80 |
| IMAGE | 3.18 | 2.18 | 15.26 | 3.44 | — | 1.96 | 2.72 |
| SMALL IMAGE | 3.06 | 1.59 | 17.13 | 3.86 | — | 1.54 | 2.08 |
| SMALL VIDEO | — | 1.78 | 16.70 | 4.38 | 4.31 | 3.68 | 2.40 |
| VIDEO | 3.41 | 3.66 | 18.68 | 11.27 | 13.95 | 8.22 | 5.53 |

## Real CTR Benchmark — Industry × Objective (อัตราส่วน เช่น 0.0012 = 0.12%)

> CTR ของ LINE Ads ต่ำกว่า Facebook/Google เป็นปกติ เพราะ format ใน feed ต่างกัน

| Industry | APP_ENGAGEMENT | APP_INSTALL | GAIN_FRIENDS | REACH | VIDEO_VIEW | VISIT_MY_WEBSITE | WEBSITE_CONVERSION |
|---|---:|---:|---:|---:|---:|---:|---:|
| automotive | 0.28% | 4.91% | 0.12% | 0.18% | 0.10% | 0.87% | 0.45% |
| beauty | — | — | 0.08% | 0.19% | 0.06% | 0.44% | 0.41% |
| careerAndBusiness | 0.32% | 0.18% | 0.11% | 0.22% | 0.07% | 0.51% | 0.44% |
| cosme | — | — | 0.11% | 0.19% | 0.10% | 0.49% | 0.55% |
| cpg | — | — | 0.14% | 0.17% | 0.09% | 0.34% | 0.65% |
| education | — | 0.23% | 0.10% | 1.52% | 0.06% | 0.31% | 0.39% |
| entertainmentAndMedia | — | 1.02% | 0.10% | 0.26% | 0.09% | 1.01% | 0.34% |
| familyAndSociety | — | 0.15% | 0.14% | 0.20% | 0.07% | 0.82% | 0.49% |
| fashion | 0.09% | 0.28% | 0.11% | 0.22% | 0.16% | 0.53% | 0.73% |
| financialServices | 1.66% | 0.66% | 0.16% | 0.19% | 0.06% | 0.45% | 0.54% |
| fitnessAndMedicalService | — | 0.48% | 0.08% | 0.18% | 0.09% | 0.46% | 2.03% |
| foodAndDrink | 0.29% | 0.29% | 0.13% | 0.20% | 0.14% | 0.45% | 0.53% |
| game | 0.27% | 0.35% | 0.10% | 0.19% | 0.04% | 0.40% | 0.47% |
| healthFood | — | — | 0.14% | 0.26% | 0.08% | 5.42% | 0.83% |
| lawAndGovernment | — | 0.98% | 0.19% | 0.16% | 0.06% | 0.69% | 0.41% |
| leisureAndSportsAndLifestyle | — | 0.32% | 0.14% | 0.30% | 0.09% | 0.46% | 0.64% |
| realEstate | — | — | 0.10% | 0.77% | 0.08% | 0.48% | 0.48% |
| shopping | 0.33% | 0.38% | 0.13% | 0.23% | 0.20% | 0.44% | 0.72% |
| technology | 0.36% | 0.28% | 0.14% | 0.36% | 0.09% | 0.40% | 1.02% |
| travel | — | — | 0.14% | 0.18% | 0.11% | 0.41% | 0.69% |

> GAIN_FRIENDS CTR ต่ำกว่า objective อื่นมากเป็นปกติ (0.08-0.19%) เพราะวัด friend add ไม่ใช่ click

## Real CTR Benchmark — Ad Format × Objective

| Ad Format | APP_ENGAGEMENT | APP_INSTALL | GAIN_FRIENDS | REACH | VIDEO_VIEW | VISIT_MY_WEBSITE | WEBSITE_CONVERSION |
|---|---:|---:|---:|---:|---:|---:|---:|
| ANIMATED IMAGE | 0.38% | 1.07% | 0.12% | 0.26% | — | 0.76% | 0.77% |
| CAROUSEL | 0.44% | 0.42% | — | 0.24% | — | 0.61% | 0.63% |
| IMAGE | 0.37% | 0.39% | 0.11% | 0.20% | — | 0.47% | 0.56% |
| SMALL IMAGE | 0.30% | 0.27% | 0.09% | 0.19% | — | 0.67% | 0.73% |
| SMALL VIDEO | — | 0.53% | 0.11% | 0.20% | 0.15% | 0.26% | 0.61% |
| VIDEO | 0.58% | 1.18% | 0.12% | 0.08% | 0.07% | 0.13% | 0.66% |

> ANIMATED IMAGE มี CTR สูงสุดสำหรับ APP_INSTALL และ WEBSITE_CONVERSION — ใช้เป็น A/B test option

## Real CPV Benchmark — VIDEO_VIEW (THB)

| Industry | CPV |
|---|---:|
| automotive | 0.02 |
| beauty | 0.03 |
| careerAndBusiness | 0.08 |
| cosme | 0.03 |
| cpg | 0.05 |
| education | 0.09 |
| entertainmentAndMedia | 0.04 |
| familyAndSociety | 0.03 |
| fashion | 0.04 |
| financialServices | 0.04 |
| fitnessAndMedicalService | 0.03 |
| foodAndDrink | 0.04 |
| game | 0.03 |
| healthFood | 0.03 |
| lawAndGovernment | 0.03 |
| leisureAndSportsAndLifestyle | 0.02 |
| realEstate | 0.02 |
| shopping | 0.03 |
| technology | 0.05 |
| travel | 0.03 |

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
