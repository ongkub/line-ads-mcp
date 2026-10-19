# หลักคิดแนะนำ Audience จากบัญชีจริง

ใช้ MODE 6 / บทที่ 1 (Core Audience); Custom Audience อยู่ MODE 8 / บทที่ 2: **ให้คำแนะนำอย่างเดียว ไม่สร้าง audience หรือ ad set** ตาม [กฎหลัก](../CLAUDE_PROJECT_PROMPT.md#mode-routing) [C]
เริ่มจากแชทหนึ่งประโยค AI ดึงบัญชีเอง ถามทีละเรื่องเฉพาะสินค้า/ลูกค้าที่ต้องการ/งบที่บัญชีตอบไม่ได้ ไม่ขอไฟล์ลูกค้า [C]

## แหล่งอ้างอิง

- [I] [interest-catalog-INDEX.md](interest-catalog-INDEX.md#customer-avatar--interest-mapping-need--ability--life-stage) — avatar, code และการจัด AND/OR; โหลด detail เฉพาะหมวด
- [API] [LINE Ads API v3.12.3](https://ads.line.me/public-docs/v3/3.12.3/certificated-ad-tech-general-partner) — advanced targeting, custom audiences และ Adgroup Result Simulator
- [M] [report-metrics.md](report-metrics.md) — objective/results, UTC, หน่วยและความครบ
- [P] [planning-from-history.md](planning-from-history.md) — ความพอของข้อมูลและ confidence
- การส่ง targeting ตรวจเทียบกับ [`_build_advanced_targeting_groups` และ `_build_targeting`](../src/line_ads_mcp/tools/adsets.py); ชื่อ tool/ข้อห้ามใช้ตาม [C] contract อัปเกรด 2026-10-18

## Customer Avatar Gate มาก่อน

อ่านหัวข้อ **Customer Avatar Gate** ใน [workflows/02-campaign.md](../workflows/02-campaign.md) และใช้ gate เดียวกันทั้ง MODE 2/6: เติม `customer_avatar` (Need / Ability / Life Stage) จากหลักฐานบัญชีและคำตอบผู้ใช้ พร้อมที่มา ถามทีละเรื่องเฉพาะที่ยังขาด [C]
ห้ามเสนอ Core interest ideas หรือเลือก codes ก่อนตอบครบ; targeting เดิมไม่พิสูจน์กำลังซื้อ/ช่วงชีวิต และ Custom audience ไม่แทน Avatar Gate

## Core กับ Custom

| ประเภท | ใช้หลักฐานอะไร | สิ่งที่ต้องตรวจ |
|---|---|---|
| Core | demographic + interest/behavior/purchase intent codes ตาม avatar [I][API] | code/ชื่อ/selectable และ country/objective ที่เสนอ |
| Custom: `LOOKALIKE` | คนคล้ายฐานต้นทาง | source audience + size ratio |
| Custom: `APP_EVENT` | ผู้ทำ event ในแอป | แอป/event ที่มีจริง |
| Custom: `WEBTRAFFIC` | ผู้เข้าเว็บจาก LINE Tag | Tag ต้นทาง + retentionDays 1–180 วัน |
| Custom: `ACCOUNT_FRIENDS` | เพื่อน LINE OA | OA ต้นทาง |
| Custom: `VIDEO_VIEW` | ผู้ดูวิดีโอโฆษณาที่ผ่านมา | โฆษณาวิดีโอต้นทาง |
| Custom: `IMAGE_CLICK` | ผู้คลิกรูปโฆษณาที่ผ่านมา | โฆษณารูปต้นทาง |

AI อ่าน `list_campaigns(status=None, fetch_all=True)`, `list_adsets(campaign_id=None, status=None, fetch_all=True)`, report ADGROUP และ `list_audiences()` เพื่อเชื่อม targeting กับผลตาม ID; ไม่กรองเหลือเฉพาะ ACTIVE จนทิ้งประวัติ [C][M]
ฐานเดิมแสดง ID/function_type/`status`/`estimated_audience_size`/`usable_in_adset` ตามที่คืนจริง; ใช้กับ ad set ได้เฉพาะ `status="READY"` และ `usable_in_adset=true` ไม่คืนข้อมูลให้ “ไม่ทราบ” ไม่เติม 0 หรือเดา ID [C]
`estimated_audience_size="-"` = เล็กเกินรายงาน; `"100 or fewer"` = ไม่เกิน 100 คน ห้ามแปลงเป็นจำนวนแน่นอน; ฐานใหม่ที่เสนอ **ยังไม่ทราบขนาดจน LINE สร้างเสร็จ** ไม่ใช้ ARS แทนขนาดฐาน [C]
Customer-list upload ส่งต่อ [MODE 8](../workflows/08-customer-list-audience.md) ใช้ `upload_customer_list` ผ่าน path ในเครื่อง หลังตรวจ consent/ฐานกฎหมายและ dry-run/“ยืนยัน”; MODE 6 ไม่อ่านไฟล์หรือ upload และห้ามขอแนบข้อมูลดิบในแชท; บัญชีต้องมีสิทธิ์ Custom Audience [C]

### เลือกหรือสร้างใน MODE 2 เท่านั้น

หลัง Avatar Gate/targeting ใน workflow 02 ให้ `list_audiences()` เลือกฐาน READY พร้อมขนาดก่อนสร้าง ad set ถ้าฐานที่ต้องการยังไม่มี เสนอ `create_audience(name, function_type, config, dry_run=True, workspace_dir=None)` ตามหกชนิดด้านบน ใช้ source/config ที่ตรวจได้จริง [C]
ทุก write ต้อง dry-run → สรุปชื่อ/ชนิด/source/ค่าตั้ง → ผู้ใช้พิมพ์ “ยืนยัน” → execute → ตรวจ readback และ re-check `list_audiences()` ฐานใหม่เริ่ม IN_PROGRESS ห้ามใช้จน READY/usable_in_adset=true [C]
ถ้ายังไม่พร้อม ถามว่าจะรอหรือสร้าง ad set โดยไม่ใช้ฐานใหม่นี้; ห้ามตัดฐานออกเอง ต้องทบทวนแผนและ dry-run/ยืนยันใหม่ ส่วน active friends exclusion ของ GAIN_FRIENDS ต้องพร้อมก่อนสร้างเสมอ [C]
ส่ง `custom_audience_ids` / `excluded_audience_ids` ชุด READY เดียวกันให้ `estimate_adset_reach` และ `create_adset` ส่วน MODE 6 เสนอแผนและส่งต่อ MODE 2 ในแชทเดิมเท่านั้น ไม่เรียกสอง create tools นี้ [C]
ขนาดต่อ code ใช้ `list_advanced_targeting_codes(campaign_objective=..., country="TH", locale="th")` และใช้เฉพาะ `selectable=true`; cache ใน [I] มีบริบท/วันที่ ไม่ใช่ขนาดล่าสุดทุก objective [I][C]
**ขนาดต่อ code ไม่ใช่ขนาดรวม:** ห้ามบวก sizes ของ codes เพราะคนอาจซ้ำและ AND/OR เปลี่ยนชุดคน; ประเมินชุดจริงด้วย ARS ด้านล่าง [I][API; กติกาวิเคราะห์]

## AND ข้ามกลุ่ม / OR ในกลุ่ม

ตาม [I] และโครงสร้าง create_adset ในโค้ดอ้างอิง:

- `interest_groups` แต่ละ inner list เป็น OR ของ codes ในชั้นนั้น; แต่ละกลุ่มเป็นเงื่อนไข AND ข้ามชั้น
- tool แยก code ใน `interest_groups` เป็น `interests`, `behaviors`, `purchaseIntents` ให้อัตโนมัติใน object ของกลุ่มเดิม ไม่ได้แยกเป็น AND เพิ่ม
- `interest_codes` และ `behavior_codes` แบบ flat ถูกสร้างเป็นกลุ่มกว้างร่วมกัน; ถ้าส่งพร้อม `interest_groups` จะเพิ่มอีกกลุ่ม จึงอย่าส่ง code ซ้ำทั้งสองรูปแบบโดยไม่ตั้งใจ
- demographic และ included/excluded custom audience เป็นส่วนอื่นของ targeting; อย่านำสูตร OR ของ advanced group ไปอ้างว่ารายการ custom IDs มีตรรกะเดียวกันโดยไม่ตรวจ [API; กติกาวิเคราะห์]

**(ตัวอย่างสมมติ)** `interest_groups=[["4"], ["12", "2441"]]` = อาชีพและธุรกิจ AND (รถยนต์ OR สนใจซื้อรถคันแรก); code ชื่ออ้างอิง [I] แต่ต้องเช็ก selectable/ขนาดในบัญชีอีกครั้ง
payload ที่ builder สร้างคือ `[{"interests":["4"]}, {"interests":["12"],"behaviors":["2441"]}]`; นี่เป็นตัวอย่างอธิบายโครงสร้าง ไม่ใช่คำสั่งสร้าง [โค้ดอ้างอิง]
เลือกชั้นตาม Need/Ability/Life Stage ใน [I] และเสริม signals ที่มีเหตุผล; ไม่เติม code เพียงเพื่อให้ครบจำนวน และไม่กองทุก interest ที่เกี่ยวข้องไว้กลุ่มเดียว [I; กติกาแนะนำ]

### ยกเว้นเพื่อน OA

สำหรับ GAIN_FRIENDS อ่าน `list_audiences()` หา `active_friends_audience_id` ที่ READY/usable_in_adset=true เพื่อเสนอ `excluded_audience_ids` ในแผนที่จะส่งต่อ MODE 2; ไม่ใช้ interest “ผู้ติดตาม OA หมวด…” แทน audience เพื่อนปัจจุบันของบัญชี [C][I]
ถ้า ID ไม่มีหรือยังไม่พร้อม ให้แจ้งข้อจำกัดและพักขั้นที่ต้องใช้ ID ห้ามเดา/สร้าง audience เพื่อให้ผ่าน; บทนี้ไม่เรียก write แม้ `create_audience` มีอยู่ [C]

## อ่าน estimate_adset_reach

ชื่อ tool ที่ใช้คือ `estimate_adset_reach` แทนชื่อเก่าที่ไม่มีจริงใน INDEX; เป็น LINE Adgroup Result Simulator (`simulation/ars`) **ประเมินอย่างเดียว ไม่สร้างอะไร** [C][API]

ค่าที่ต้องเตรียมตาม contract [C]:

```text
campaign_id, campaign_objective, daily_budget, bid_type, auto_bid_type
+ targeting params แบบ create_adset หรือ targeting object
+ adset_id, bid_amount, bid_strategy เมื่อจำเป็น
```

- ใช้ campaign ID ที่มีจริงและ objective ตรงกัน; ถ้ายังไม่มี ID ที่เหมาะสมให้บอกว่ายังจำลองไม่ได้ ห้ามสร้าง campaign ชั่วคราว [C; กติกาแนะนำ]
- ใช้งบ/เพดานที่ผู้ใช้ระบุ ไม่เดาเงินเพื่อเรียก simulator; ถ้าค่า bid/budget ยังขาด ให้ถามทีละเรื่องหรือเสนอแนวคิดก่อนโดยไม่จำลอง [C]
- แสดง reach **min–max** และ click **min–max** พร้อม inputs และข้อจำกัดตาม response; ไม่เรียกเป็นขนาดฐานลูกค้าทั้งหมดหรือผลรับประกัน [API; กติกาตีความ]
- แสดง absent/invalid fields ที่ tool แจ้ง; ค่าไม่ครบ/invalid ไม่เท่ากับ reach 0 และไม่ใช่เหตุผลให้เดาตัวเลขเติม [C; กติกาตีความ]
- เปรียบเทียบแนวคิดด้วยงบ/bid/objective และ inputs อื่นเท่ากัน เปลี่ยน targeting ทีละส่วนเพื่ออ่านผลจำลองได้ชัด [กติกาวิเคราะห์]

**Heuristic ที่เจ้าของปรับได้:** ไม่ตั้งเลข cutoff “คนเท่านี้แคบ/กว้างแน่นอน” จาก per-code size; ดูบริบทสินค้า/พื้นที่และผล ARS ภายใต้เงินเดียวกัน [I; กติกาแนะนำ]

| สัญญาณ | คำตีความแบบ heuristic | แนวทางทดสอบ ไม่ใช่ write |
|---|---|---|
| เพิ่ม AND แล้วช่วง reach หดมาก หรือผลจริงมี frequency สูง/underspend | อาจแคบเกิน แต่ bid/creative ก็เป็นเหตุร่วมได้ | ลดชั้นที่เหตุผลอ่อน แล้วจำลองใหม่ |
| OR กว้างมากแต่ signals ไม่สัมพันธ์สินค้า | อาจกว้างเกิน ไม่ใช่เพราะตัวเลข reach สูงอย่างเดียว | ทบทวน avatar และกลุ่ม code ที่อธิบายลูกค้าได้ |
| ช่วง min–max กว้างหรือทับซ้อนระหว่างแผน | ยังแยกความได้เปรียบไม่ได้ | ไม่เลือกผู้ชนะจาก midpoint; ทดสอบจริงภายหลัง |

สูตรขนาด audience ใน [I] เป็นแนวประมาณเดิม ไม่ใช่ output ARS; ห้ามนำไปยืนยัน delivery หรือยอดขาย [I; กติกาตีความ]

## ใช้ประวัติและขยายฐาน

- รวมผลของ targeting เดียวกันเฉพาะ objective/result/currency/ช่วงเดียวกัน; ตรวจ demographic, groups, custom IDs และ exclusions ไม่ใช้ชื่อ ad set เป็นตัวตัดสิน [M][P]
- ใช้เกณฑ์วัน/ผลลัพธ์และ confidence ใน [P]; sample น้อยเป็นสมมติฐาน ไม่ใช่ audience ชนะ และผล ADGROUP ไม่ได้แจกผลงานเป็นราย code [M][P]
- **ข้อเสนอเชิง heuristic:** เพิ่มฐาน WEBTRAFFIC ด้วย LINE Tag และผู้เข้าเว็บที่เกี่ยวข้อง, เพิ่มฐาน OA ด้วยเพื่อนที่สนใจจริง, เพิ่ม engagement ด้วยเนื้อหาที่ตอบโจทย์; ตรวจความพร้อม/สิทธิใช้งานก่อน ไม่รับปากว่ากลายเป็น audience ทันที [API; กติกาแนะนำ]
- เสนอรายชื่อลูกค้าเฉพาะที่มีสิทธิใช้ แล้วส่งต่อ MODE 8 เพื่อตรวจไฟล์/ยืนยัน upload ผ่าน MCP; บทนี้ไม่อ่านไฟล์ลูกค้า ไม่ upload ไม่ติดตั้ง tracking และไม่เปลี่ยนระบบ consent [C; กติกาขอบเขต]
- ตรวจข้อจำกัดสินค้าจาก [line-ads-guidelines.md](line-ads-guidelines.md) ก่อนเสนอแนวทาง; รายละเอียด creative ให้ไป [ad-specs.md](ad-specs.md) ไม่คัดลอกเกณฑ์ซ้ำ

## ส่งต่อและข้อห้าม

ส่งแผนในแชท: customer_avatar พร้อมหลักฐาน/คำตอบ, objective, เหตุผล/ช่วง UTC, codes+ตรรกะ, Custom IDs/exclusions พร้อม status/ขนาด และ function_type/config ที่เสนอสำหรับฐานใหม่, งบที่ผู้ใช้ให้, ARS inputs/output, confidence และข้อมูลขาด ไป [workflows/02-campaign.md](../workflows/02-campaign.md) เมื่อผู้ใช้ขอสร้าง [C]
MODE 2 ต้อง dry-run → สรุปตัวเลข → ผู้ใช้พิมพ์ “ยืนยัน” → execute → ตรวจ readback; คำขอคำแนะนำหรือสร้างตามแผนไม่ข้าม gate [C]
ห้าม `create_audience`, `create_adset` หรือ write tools ทุกชนิดในบทนี้; ห้ามแต่ง codes/IDs/size, อ้างเหตุเป็นผลจาก snapshot, หรือสรุป demographic performance ที่ไม่มี breakdown [C][P]

[I]: interest-catalog-INDEX.md
[API]: https://ads.line.me/public-docs/v3/3.12.3/certificated-ad-tech-general-partner
[M]: report-metrics.md
[P]: planning-from-history.md
[C]: ../CLAUDE_PROJECT_PROMPT.md
