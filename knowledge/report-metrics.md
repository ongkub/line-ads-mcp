# นิยามและวิธีรวมผลรายงาน

ใช้ใน MODE 3–7; อ่าน KPI ตาม objective จาก [kpi-benchmarks.md](kpi-benchmarks.md#objective-benchmarks) แทนการคัดลอก benchmark มาไว้ที่นี่

## แหล่งอ้างอิงและขอบเขต

- [API] [LINE Ads API v3.12.3](https://ads.line.me/public-docs/v3/3.12.3/certificated-ad-tech-general-partner) — อ้างอิงชื่อสถิติและ reporting; ตรวจ field ที่ response คืนจริงก่อนใช้
- [KPI] [KPI ของ repo](kpi-benchmarks.md#objective-benchmarks) และ [GAIN_FRIENDS](kpi-benchmarks.md) — หลักเลือกผลลัพธ์
- [สัญญา MCP] [กฎหลักและ Tools](../CLAUDE_PROJECT_PROMPT.md#tools-ที่มีและใช้เมื่อไหร่) — contract อัปเกรดที่เจ้าของอนุมัติ 2026-10-18; ไม่ใช่ชื่อ field ของ LINE API โดยตรง
- สูตรรวมและเกณฑ์ขั้นต่ำด้านล่างเป็นกติกาวิเคราะห์ของเอกสารนี้; เกณฑ์ขั้นต่ำเป็น **heuristic** ไม่ใช่ข้อกำหนด LINE

## Data dictionary

นิยามสถิติอ้างอิง [API]; วิธีรวมเป็นสูตรวิเคราะห์ของ repo ตาม [KPI] เมื่อ field มีข้อมูลครบในช่วงเดียวกัน
`Σ` หมายถึงผลรวมแถวที่ไม่ซ้ำ ในระดับรายงานเดียว สกุลเงินเดียว และช่วงวันที่ไม่ซ้อนกัน

| Field | ความหมาย | การรวม/คำนวณใหม่ |
|---|---|---|
| `imp` | จำนวนการแสดงผล ไม่ใช่คนไม่ซ้ำ [API] | บวกจำนวนครั้ง |
| `viewableImp` | จำนวนการแสดงผลที่เข้าเกณฑ์มองเห็นของแพลตฟอร์ม [API] | บวกเมื่อ API คืน field; ไม่แทนด้วย `imp` |
| `click` | จำนวนคลิก; การตีความผลขึ้นกับ objective [API][KPI] | บวกจำนวนคลิก |
| `cost` | ค่าใช้จ่ายของช่วงรายงาน [API] | บวกหลังตรวจหน่วยและ currency |
| `cv` | จำนวน conversion ที่รายงาน [API] | บวกเฉพาะนิยาม conversion เดียวกัน; ไม่ใช่ผลของทุก objective |
| `ctr` | อัตราคลิก [API] | `Σclick / Σimp × 100` เป็น % |
| `cvr` | อัตรา conversion ต่อคลิก [API] | `Σcv / Σclick × 100` เป็น % |
| `cpc` | ต้นทุนต่อคลิก [API] | `Σcost / Σclick` |
| `cpm` | ต้นทุนต่อการแสดงผลหนึ่งพันครั้ง [API] | `Σcost / Σimp × 1,000` |
| `cpa` | ต้นทุนต่อ conversion [API] | `Σcost / Σcv` สำหรับ WEBSITE_CONVERSION |

**ห้ามเฉลี่ย ratios รายแถว** รวมตัวตั้ง/ตัวหารก่อนคำนวณใหม่ทุกครั้ง; ไม่เฉลี่ย CTR/CVR/CPC/CPM/CPA/CPF ของวันหรือแคมเปญเข้าด้วยกัน [KPI; กติกาคำนวณข้างต้น]
ตัวหาร 0 หรือไม่ทราบ → `None`/“คำนวณไม่ได้” ไม่ใช่ 0; คำนวณจากแถวที่ขาดได้เพียง “ค่าของข้อมูลที่มี” ห้ามเรียกว่าอัตรารวมทั้งช่วง [กติกาวิเคราะห์]

## หน่วยเงินและ summary

- ก่อนเทียบเงิน ให้ **ยืนยันหน่วยกับบัญชีจริง** โดยเทียบ report ช่วงเดียวกับ Ads Manager และ currency; ห้ามเดาว่า `cost` เป็นบาทหรือ micro และห้ามหารหนึ่งล้านโดยอัตโนมัติ [API; กติกาตรวจหน่วย]
- หน่วยเงินใน payload การตั้ง bid/budget ไม่ใช่หลักฐานว่าหน่วย report เหมือนกัน; ถ้ายังตรวจไม่ได้ให้ติดป้าย “หน่วยเงินยังไม่ยืนยัน” และงดข้อสรุปต้นทุน [กติกาตรวจหน่วย]
- MCP summary ใช้ `total_spend`, `total_clicks`, `total_impressions`, `total_cv`, `avg_ctr`, `avg_cpc`, `avg_cpm`; `avg_ctr` เป็น % แล้ว ห้ามคูณ 100 ซ้ำ; ratios ไม่มีตัวหารเป็น `None` [สัญญา MCP]
- ชื่อ `avg_*` ไม่ใช่คำสั่งให้เฉลี่ย ratios; ตรวจ raw rows และ field ที่ขาดก่อนเชื่อ summary เพราะผลรวมของส่วนที่มีไม่รับรองว่าครบ [สัญญา MCP; กติกาวิเคราะห์]

## วัน UTC และความครบ

- `get_report(level="CAMPAIGN"|"ADGROUP"|"AD", start_date=..., end_date=..., campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)` ดึงทุกหน้า; ส่งวันที่ `YYYY-MM-DD` และตรวจ `date_basis: "UTC"` [สัญญา MCP]
- `by_day=True` คืนหนึ่งแถวต่อวัน×entity สูงสุด 93 วันต่อคำขอ; ช่วงยาวกว่านี้แบ่งช่วงไม่ซ้อน แล้วตรวจแต่ละ response [สัญญา MCP]
- `get_daily_report` คือเมื่อวาน UTC ระดับ AD โดย default; `get_weekly_report(by_day=False)` ใช้ดูสัปดาห์ตามช่วงที่ tool คืน [สัญญา MCP]
- `paging.complete=true` หมายถึงดึงหน้าครบตามขอบเขตคำขอ ไม่ได้รับรอง tracking ครบ, metric ไม่ขาด หรือผล attribution สิ้นสุดแล้ว; false/ไม่มี metadata → “ยังยืนยันความครบไม่ได้” [สัญญา MCP; กติกาตรวจข้อมูล]
- แสดงช่วง “วันที่ … ถึง … (UTC)” เสมอ; เวลาเรียกข้อมูลอาจแสดง Asia/Bangkok ได้แต่ห้ามเปลี่ยนชื่อวัน UTC เป็นวันไทยโดยไม่จัดกลุ่มข้อมูลใหม่ [สัญญา MCP; กติกาวิเคราะห์]
- รวมวันปัจจุบันให้ติด “วันยังไม่เต็ม”; อย่าเทียบกับวันเต็มโดยไม่ระบุข้อจำกัด [กติกาวิเคราะห์]
- อย่าบวก campaign totals กับ ad totals หรือรวมรายงานแบบทั้งช่วงกับรายวันซ้ำ; ตรวจ duplicate ด้วยระดับ+ID และวันที่เมื่อเป็นรายวัน [กติกาวิเคราะห์]

## ผลลัพธ์ตาม objective

| Objective | ผลลัพธ์และต้นทุนที่ใช้ | ข้อจำกัด |
|---|---|---|
| GAIN_FRIENDS | เพื่อนใหม่โดยประมาณจาก `click`; CPF = `Σcost/Σclick` [KPI] | `cv=0` เป็นปกติตาม convention repo ไม่ใช่หลักฐาน tracking เสีย; ไม่รับรองเพื่อนสุทธิหรือยอดขาย |
| VISIT_MY_WEBSITE | คลิก, CTR, CPC [KPI] | ไม่ใช้ CV/CPA/ROAS ตัดสิน |
| WEBSITE_CONVERSION | `cv`, CPA, CVR; ROAS เมื่อมีรายได้ที่ตรวจสอบได้ [KPI] | ไม่มีรายได้ → ไม่คำนวณ ROAS |
| REACH | Reach, CPM, Frequency เมื่อมี field [KPI] | `imp` ไม่ใช่ Reach; ห้ามบวก unique reach ข้ามวัน/กลุ่มเป็นคนไม่ซ้ำรวม |
| APP_INSTALL | Installs, CPI เมื่อมี install metric [KPI] | ห้ามถือว่า click หรือ `cv` เป็น install โดยไม่มี mapping ยืนยัน |
| VIDEO_VIEW | Views, CPV, completion ตาม field ที่มี [KPI] | `viewableImp` ไม่ใช่ยอดดูวิดีโอจนจบ |

ชื่อ objective ที่ API คืนจริง (ตรวจ 25 ต.ค. 2026): GAIN_FRIENDS, VISIT_MY_WEBSITE, WEBSITE_CONVERSION, REACH · WEBSITE_CONVERSION: ผลอาจอยู่ในคอลัมน์คอนเวอร์ชันแบบกำหนดเอง (เช่น "กดปุ่มแชทสอบถาม") ขณะที่ CV (All) = 0 → ใช้คอนเวอร์ชันที่กลุ่มโฆษณา "เพิ่มประสิทธิภาพแก่"

ถ้า `summary.total_cv = 0` แต่ `conversion_events` มีค่า ให้ดูอีเวนต์ที่แคมเปญตั้งไว้ เช่น `cvViewItemDetail` แทนการสรุปว่าไม่มีคอนเวอร์ชัน
`conversion_events` รวมเฉพาะจำนวนที่ขึ้นต้นด้วย `cv` และไม่เป็นศูนย์ ไม่รวม `cv`, `cvr*`, ค่าที่มี `Value` หรือคอลัมน์ซ้ำที่ลงท้าย `WithEv`
เลือกอีเวนต์ตาม objective และสิ่งที่กลุ่มโฆษณาเพิ่มประสิทธิภาพ ห้ามบวกหลายอีเวนต์เป็นยอดลูกค้าไม่ซ้ำ

GAIN_FRIENDS ใช้ “เพื่อน ≈ click” ในสรุป (ผู้เขียนยืนยัน 25 ต.ค. 2026: รายงานไม่มีคอลัมน์เพื่อนใหม่ และคิดเงินต่อการเพิ่มเพื่อน) และตรวจผลกับบัญชีจริงเมื่อจำเป็น; ไม่เปลี่ยน conversion ศูนย์ให้เป็นปัญหาหรือเรียกเพื่อนว่าลูกค้าที่ซื้อ [KPI; กติกาการสื่อสาร]

## Missing ต่างจาก zero

| ข้อมูลที่พบ | แสดง | การตัดสินใจ |
|---|---|---|
| Field คืนเลข `0` จริง | `0` พร้อมหน่วย | เป็นศูนย์ที่รายงานมา ไม่ได้พิสูจน์สาเหตุ [กติกาวิเคราะห์] |
| ไม่มี field / `null` / ไม่มีแถวของวัน | “ไม่มีข้อมูล” | ห้ามเติม 0 หรือแต่ง result [กติกาวิเคราะห์] |
| หน้าหรือวันขาด | “ข้อมูลบางส่วน” | แสดงยอดที่ดึงได้ งดจัดผู้ชนะและเทียบทั้งบัญชี [กติกาวิเคราะห์] |
| ตัวหาร 0 | “คำนวณไม่ได้” | ไม่แสดงต้นทุนต่อผลลัพธ์เป็น 0 [สูตรด้านบน] |

## ปริมาณขั้นต่ำก่อนเปรียบเทียบ

**Heuristic เริ่มต้นที่เจ้าของปรับได้:** ใช้อย่างน้อย 7 วันเต็ม UTC และ 30 ผลลัพธ์ต่อกลุ่มก่อนจัดอันดับต้นทุน; ถ้าใช้ CTR/CPM ให้มีอย่างน้อย 1,000 impressions ต่อกลุ่มด้วย ไม่ใช่หลักฐานนัยสำคัญทางสถิติ [กติกาวิเคราะห์; บริบท learning ดู bidding-strategy.md]
สำหรับ Friends/Traffic ใช้ click เป็นผลลัพธ์ตาม objective; Conversion/Install/Video ต้องมี metric ผลจริง; REACH ไม่บังคับเกณฑ์ 30 results แบบคลิก [KPI; heuristic ข้างต้น]
ข้อมูลต่ำกว่าเกณฑ์ยังแสดงได้ แต่ติด “ข้อมูลน้อย — ยังไม่จัดผู้ชนะ”; เกณฑ์เจ้าของแทน default ได้และต้องแสดงเกณฑ์ที่ใช้ [heuristic ข้างต้น]
เกณฑ์ confidence และการเทียบอย่างเป็นธรรมดู [planning-from-history.md](planning-from-history.md); คำแนะนำ bid/learning ดู [bidding-strategy.md](bidding-strategy.md) ไม่ยกเกณฑ์นี้เป็นคำสั่งเพิ่มงบ

[API]: https://ads.line.me/public-docs/v3/3.12.3/certificated-ad-tech-general-partner
[KPI]: kpi-benchmarks.md
[สัญญา MCP]: ../CLAUDE_PROJECT_PROMPT.md
