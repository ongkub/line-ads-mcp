# workflows/06-audience-advisor.md
# Audience Advisor Workflow
# Version 1.0 | October 2026 | MCP-first | บทที่ 5

---

## Overview

MODE 6 แนะนำกลุ่มเป้าหมายจากผลงานจริง โดยไม่สร้าง audience หรือ ad set
Trigger: “แนะนำกลุ่มเป้าหมายจากแคมเปญที่ผ่านมา”
ผู้ใช้เริ่มด้วยแชทได้เลย AI ดึง targeting และ report จากบัญชีเอง

```
PHASE 1 → INTAKE
PHASE 2 → FETCH TARGETING + PERFORMANCE
PHASE 3 → COMPARE TARGETING GROUPS
PHASE 4 → CORE + CUSTOM IDEAS
PHASE 5 → REACH CHECK
PHASE 6 → GROW BASE + HANDOFF
```

## Knowledge Loading Gate

อ่านก่อนเริ่ม:
- `knowledge/audience-strategy.md` — Core/Custom, AND/OR, friend exclusion, ARS และการขยายฐาน
- อ่านหัวข้อ **Customer Avatar Gate** ใน `workflows/02-campaign.md` ก่อนเสนอ targeting; ใช้ gate เดียวกัน ไม่ข้ามเพราะมี Custom audience
- `knowledge/interest-catalog-INDEX.md` — โหลดเพื่อ map code หลังผ่าน Avatar Gate; โหลด detail เฉพาะหมวดที่จำเป็น
- `knowledge/report-metrics.md` — หน่วย, ผลลัพธ์ตาม objective, weighted ratios และ UTC

ถ้าไฟล์ที่จำเป็นยังไม่มี ให้บอกข้อจำกัดก่อนแนะนำ ห้ามเดาเนื้อหาแทน

---

## PHASE 1 — Intake

### สิ่งที่ AI ต้องถาม

ถามทีละเรื่อง เฉพาะที่บัญชีตอบไม่ได้:
1. “อยากขยายกลุ่มให้สินค้าหรือบริการอะไรครับ?”
2. หลังดึงหลักฐานบัญชีใน PHASE 2–3 แล้ว ถามข้อเท็จจริงลูกค้า/กลุ่มใหม่เฉพาะ Need, Ability, Life Stage ที่ยังขาด เพื่อผ่าน Customer Avatar Gate ใน PHASE 4
3. ช่วงย้อนหลัง ถ้ายังไม่ระบุ เสนอ 4 สัปดาห์เต็มล่าสุดบนฐาน UTC พร้อมวันที่
4. ก่อนจำลอง reach ถ้ายังไม่มีงบที่ผู้ใช้ระบุ ให้ถามงบรายวันที่ตั้งใจใช้

ไม่ขอไฟล์ลูกค้า ไม่ถามให้ผู้ใช้คัด ID/ตัวเลข performance เอง
เงินจาก campaign เดิมเป็นข้อมูลอ้างอิง ไม่ถือว่าอนุมัติงบสำหรับแผนใหม่

---

## PHASE 2 — Fetch Targeting + Performance

```python
list_campaigns(status=None, fetch_all=True)
list_adsets(campaign_id=None, status=None, fetch_all=True)
get_report(level="ADGROUP", start_date=start_date, end_date=end_date,
           campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)
list_audiences()
```

ขั้นนี้อ่านหลักฐานบัญชีก่อน ยังไม่เสนอ Core interest; รอผ่าน Customer Avatar Gate ใน PHASE 4 แล้วจึงอ่าน INDEX และเรียก `list_advanced_targeting_codes(campaign_objective=objective, country="TH", locale="th")` เพื่อเช็ก `selectable`/ขนาดล่าสุดต่อ code
เรียกแยกตาม objective ที่จะเสนอ ไม่ใช้ cache GAIN_FRIENDS กับทุก objective โดยไม่ตรวจ

- ผูก adgroup ID ใน report กับ ad set ID ในรายการ และ campaign เพื่อหา objective
- เก็บ targeting, exclusions, budget, bid, ช่วงเวลา และสถานะ; รวม PAUSED/REMOVED ที่มีประวัติ
- ตรวจ `paging.complete` ของ report และความครบของรายการเมื่อมี metadata; ไม่ครบให้ระบุว่าเป็นบางส่วน
- ตรวจวันรายงาน UTC, currency และ result ตาม objective; ไม่ใช้ CV แทน Friends
- ขนาดต่อ code ถ้าไม่คืนค่าให้ระบุ unknown ไม่เติม 0 และไม่บวกขนาดหลาย code เป็นขนาดรวม

---

## PHASE 3 — Compare Targeting Groups

จัดกลุ่ม ad set ที่ targeting เหมือนกัน โดยรวม objective, country/location, age/gender,
โหมด auto/manual, interest groups, included/excluded custom audiences ใน key เปรียบเทียบ
อย่ารวม targeting ต่างกันเพียงเพราะชื่อ ad set คล้ายกัน

1. แยก objective และชนิด result ก่อนเสมอ
2. รวม spend และ result ของแต่ละกลุ่ม แล้วคำนวณ cost per result จากยอดรวม
3. แสดง spend, จำนวน result, วันใช้งาน และจำนวน ad set เป็นหลักฐาน
4. เปรียบเทียบเมื่อปริมาณพอและช่วงเวลา/offer/creative/bid ใกล้กันตาม `knowledge/audience-strategy.md`
5. ถ้า result เป็น 0/unknown หรือ paging ไม่ครบ ให้ระบุข้อจำกัด ไม่จัดเป็นกลุ่มแพ้ทันที

ผลย้อนหลังบอกความสัมพันธ์ ไม่พิสูจน์ว่า targeting เป็นเหตุให้ต้นทุนต่ำ
Ad set report ไม่ได้บอกว่า code ใดใน AND/OR group ทำผลงานดีเป็นราย code
ข้อมูลน้อยให้เสนอเป็นสมมติฐานทดสอบ ไม่เรียกว่า audience ผู้ชนะ

---

## PHASE 4 — Core + Custom Ideas

### Customer Avatar Gate — ต้องผ่านก่อนเสนอ Core

อ่านและทำตามหัวข้อ **Customer Avatar Gate** ใน `workflows/02-campaign.md` ใช้หลักฐานบัญชีจาก PHASE 2–3 ร่วมกับคำตอบผู้ใช้ให้ครบ `customer_avatar` (Need / Ability / Life Stage) พร้อมที่มา
ถามทีละเรื่องเฉพาะข้อมูลที่บัญชีบอกไม่ได้; ถ้ายังขาดชั้นใด ให้ช่วยถามจนชัด ห้ามเสนอ Core interest ideas หรือเลือก code ก่อนผ่าน gate
Targeting/ผลย้อนหลังไม่พิสูจน์กำลังซื้อหรือช่วงชีวิต และ Custom audience ไม่แทน gate นี้

### Core Audience

เมื่อผ่าน gate แล้ว เสนอ 2–3 แนวคิดที่สัมพันธ์กับสินค้าและหลักฐาน:
- ระบุ code + ชื่อจริงที่ `selectable=true`, age/gender และเหตุผล
- อธิบาย OR ภายใน `interest_groups` แต่ละกลุ่ม และ AND ข้ามกลุ่ม
- ใช้ `interest_codes` เฉพาะเมื่อยอมรับการรวมแบบกว้าง; ห้ามอ้างว่าเป็น intersection
- ไม่เติม code เพื่อให้ครบจำนวนโดยไม่มีเหตุผล; ตรวจ App Behavior ตาม avatar และ detail ที่เกี่ยวข้อง
- อายุที่เสนอ: age_min = 20,25,…,65; age_max = 24,29,…,64 หรือไม่ระบุสำหรับไม่จำกัดบน
- ถ้าอายุที่ขอไม่ตรงชุด ให้เสนอช่วงที่ valid และแจ้งข้อจำกัดก่อนส่งต่อสร้าง; ห้าม age_max=65

### Custom Audience

อ่านฐานเดิมด้วย `list_audiences()` และเสนอแนวคิดตาม `function_type` ที่รองรับ:
- `LOOKALIKE` — คนคล้าย source audience พร้อม size ratio ที่ต้องเลือก
- `APP_EVENT` — ผู้ทำ event ในแอปที่มีข้อมูลจริง
- `WEBTRAFFIC` — ผู้เข้าเว็บจาก LINE Tag; retentionDays 1–180 วัน
- `ACCOUNT_FRIENDS` — เพื่อน LINE OA
- `VIDEO_VIEW` — ผู้ดูวิดีโอโฆษณาที่ผ่านมา
- `IMAGE_CLICK` — ผู้คลิกรูปโฆษณาที่ผ่านมา

ฐานเดิมแสดง ID/function_type/`status`/`estimated_audience_size`/`usable_in_adset` ตามที่คืนจริง; ใช้ในแผนสร้างหรือ reach check ได้เฉพาะ `status="READY"` และ `usable_in_adset=true`
ขนาด `"-"` หมายถึงเล็กเกินรายงาน; `"100 or fewer"` คือไม่เกิน 100 คน ไม่แปลงเป็นจำนวนแน่นอน; ข้อมูลหายให้บอกไม่ทราบ ไม่เติม 0
ฐานใหม่ที่เสนอ **ยังไม่ทราบขนาดจน LINE สร้างเสร็จ** และจะเริ่ม IN_PROGRESS ต้องส่งต่อ MODE 2 เพื่อสร้างและตรวจ READY ก่อนใช้
Customer-list upload (hashed phone/email) ไม่รองรับผ่าน MCP ให้ผู้ใช้ทำเองใน LINE Ads Manager ไม่อ่าน/ขอแนบไฟล์ลูกค้า; บัญชีต้องมีสิทธิ์ Custom Audience
สำหรับ `GAIN_FRIENDS` หา `active_friends_audience_id` ที่ READY/ใช้ได้ และเสนอใส่ใน `excluded_audience_ids`
ถ้าหา ID ไม่พบหรือยังไม่พร้อม ห้ามสร้างหรือเดา ID ให้ส่งต่อข้อจำกัดเพื่อพักขั้นสร้าง ad set ใน MODE 2
ไม่เรียก `create_audience` หรือ `create_adset` ในบทนี้ แม้เครื่องมือจะมีอยู่

---

## PHASE 5 — Reach Check (Read-only)

`estimate_adset_reach` คือ LINE Adgroup Result Simulator (`simulation/ars`) ไม่สร้างอะไร
ต้องมี campaign_id ที่มีอยู่จริงและ objective ตรงกัน รวมถึงงบรายวันจากผู้ใช้
หา bid_type/auto_bid_type ที่รองรับจากบริบท campaign/`knowledge/bidding-strategy.md`
ถ้าจะใช้ bid_amount ต้องถามผู้ใช้ ห้ามใช้ต้นทุนย้อนหลังแทน bid อัตโนมัติ

```python
estimate_adset_reach(
    campaign_id=campaign_id, campaign_objective=objective,
    daily_budget=user_daily_budget, bid_type=bid_type,
    auto_bid_type=auto_bid_type, targeting=proposed_targeting)
```

ส่ง `custom_audience_ids` / `excluded_audience_ids` ที่ READY และใช้ได้ตามแผนไปด้วย; ถ้าฐานใหม่ยังไม่มี ให้บอกว่ายังจำลองชุดนั้นไม่ได้ ไม่แทนด้วย ID สมมติ
ถ้า strategy ต้องใช้ cap ให้ส่ง `bid_amount=user_bid_amount, bid_strategy=bid_strategy` เพิ่ม
ถ้าจำลอง ad set เดิมใช้ `adset_id=existing_adset_id` ได้; ต้องบอกว่าใช้ targeting ใด

- แสดง reach min–max และ click min–max ตามที่คืนจริง พร้อมงบและเงื่อนไขที่ใช้
- นี่คือ **ค่าประมาณ** ไม่ใช่ขนาดฐานทั้งหมด ไม่ใช่ยอดเพื่อน/ยอดขายที่รับประกัน
- ขนาดแต่ละ code ไม่เท่ากับ reach หลัง AND/OR, exclusion และงบ; ใช้ ARS เช็กข้อเสนอรวม
- missing/invalid fields ให้แจ้งว่าจำลองไม่ได้และเติมเฉพาะข้อมูลที่ทราบจริง
- ถ้าไม่มี campaign ที่ใช้จำลองได้ ให้ข้ามพร้อมเหตุผล ห้ามสร้าง campaign ชั่วคราว
- ขนาดฐาน Custom เดิมอ่าน `estimated_audience_size` จาก `list_audiences`; reach/click ของแผน ad set ใช้ `estimate_adset_reach` ห้ามสับสนสองค่านี้หรืออ้าง tool ที่ไม่มีใน MCP

---

## PHASE 6 — Grow Base + Handoff

เสนอวิธีขยายฐานตามสิ่งที่มีจริง เช่น เพิ่มผู้เข้าเว็บที่ยินยอมติดตาม,
เพิ่ม engagement ด้วยเนื้อหาที่เกี่ยวข้อง หรือสะสมลูกค้าที่ให้สิทธิใช้ข้อมูล
ถ้า tracking/consent/ฐานยังไม่พร้อม บอกสิ่งที่ต้องเตรียมโดยไม่รับปากว่าจะมี audience ทันที
เสนอขยาย signal ภายใน avatar ทีละชั้นและ creative test เพื่อเรียนรู้ แทนการรวมทุก interest
ยังต้องระบุลูกค้าที่ต้องการ ไม่เสนอ ad set แบบ Broad ที่ไร้ targeting ตามกฎ MODE 2

### ตัวอย่างผลลัพธ์ (ตัวอย่างสมมติ)

```
ช่วง 1–28 ก.ย. 2026 (UTC), objective GAIN_FRIENDS
กลุ่มเดิม A: ฿3,000 / 200 เพื่อน → CPF ฿15
กลุ่มเดิม B: ฿150 / 5 เพื่อน → CPF ฿30 แต่ข้อมูลยังน้อย เทียบชนะ/แพ้ไม่ได้
Core ที่น่าทดสอบ: code 4 อาชีพและธุรกิจ, อายุ 25–44, ทุกเพศ
Custom: เสนอ VIDEO_VIEW ที่ READY/usable_in_adset=true แล้ว ขนาดตาม list_audiences และยกเว้นเพื่อน OA ปัจจุบันที่พร้อมใช้
ที่งบผู้ใช้ ฿300/วัน: ARS ประเมิน reach 8,000–12,000 คน ไม่รับประกันผลจริง
ขั้นนี้ยังไม่ได้สร้าง audience หรือ ad set ครับ
```

ถ้าผู้ใช้อยากสร้าง ให้ต่อ `workflows/02-campaign.md` ในแชทเดิม
ส่งต่อ customer_avatar พร้อมหลักฐาน/คำตอบ, objective, targeting/codes, audience IDs/exclusions พร้อม status/ขนาด, ชนิด/config ที่เสนอสำหรับฐานใหม่, งบที่ผู้ใช้ระบุ และข้อจำกัด
MODE 2 เลือกหรือสร้างฐานตามแผนได้หลัง Avatar Gate; ฐานใหม่ต้องตรวจ READY ก่อนใช้ใน ad set
MODE 2 ตรวจข้อมูลที่ยังขาด → dry_run=True → สรุปตัวเลข → รอ “ยืนยัน” → execute → read back
คำขอให้สร้างไม่ใช่การอนุมัติ write จริงข้ามขั้นตอน

## ห้าม

- ห้ามเรียก create_audience/create_adset หรือ MCP write tools ใดใน MODE 6
- ห้ามสร้าง/ขอไฟล์รายชื่อเบอร์โทรหรืออีเมลลูกค้า
- ห้ามเดาเงิน, code, audience ID, size หรือ demographic performance ที่ไม่มี breakdown
- ห้ามอ้างว่าขนาดต่อ code รวมกันได้ หรือ reach estimate รับประกันยอดขาย
- ห้ามสรุป audience ชนะจาก result น้อยหรือเทียบข้าม objective
