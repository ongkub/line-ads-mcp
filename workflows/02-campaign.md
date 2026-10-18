# workflows/02-campaign.md
# Campaign + Ad Set + Ad Creation
# Version 4.0 | October 2026 | MCP-first + PAUSED creation + verified readback

---

## Architecture

Default path สำหรับ MODE 2 คือ MCP/API-first เพื่อลด token, ลดความเปราะจาก browser UI, และให้ผลลัพธ์ตรวจซ้ำได้จาก payload จริง

```
PATH A — LINE AI Agent via Browser
  เร็วสำหรับ campaign ง่าย ๆ แต่คุม audience ละเอียดไม่ได้

PATH B — MCP Manual/API-first (default)
  ใช้ MCP tools สร้าง campaign/adset/ad ผ่าน LINE Ads API
  เหมาะกับ interest targeting, bid/cost cap, repeatable workflow

PATH C — Browser Manual Fallback
  ใช้เฉพาะสิ่งที่ API ทำไม่ได้ หรือ MCP error แล้วต้องตรวจ UI
```

### MCP Capability Map

| งาน | Default |
|---|---|
| ดู campaign/adset/ad/report/status | MCP |
| สร้าง campaign/adset/ad | MCP dry-run ก่อนเสมอ |
| upload media | MCP |
| interest targeting | MCP + `list_advanced_targeting_codes` |
| KYC/account setup/card/payment | Browser + user self-fill |
| LINE AI Campaign Agent | Browser |
| Visual crop/preview QA | Browser/screenshot เฉพาะจุด |

---

## Knowledge Loading Gate

ก่อนเริ่ม MODE 2 ต้องอ่าน:
- `knowledge/bidding-strategy.md` — ใช้ประกอบการอธิบาย bid strategy แต่ห้ามเลือกเลขเงินแทน user
- `workflows/02-campaign.md` — ใช้ยืนยัน path, safety rules, dry-run flow

โหลดเพิ่มตามจังหวะ:
- ก่อนเลือก audience/interest/behavior: อ่าน `knowledge/interest-catalog-INDEX.md`
- ก่อน upload media หรือสร้าง ad creative: อ่าน `knowledge/ad-specs.md`
- ก่อนประเมิน performance ระหว่างสร้าง/แก้: อ่าน `knowledge/kpi-benchmarks.md`

Rule สำคัญ:
- ห้ามเรียก `list_advanced_targeting_codes` ก่อนอ่าน `knowledge/interest-catalog-INDEX.md` และ detail file ที่เกี่ยวข้อง เว้นแต่ cache ไม่มี segment, objective/country/locale เปลี่ยน, API reject code, หรือต้องการ audience size ล่าสุด
- ห้าม upload media ก่อนอ่าน `knowledge/ad-specs.md`
- ถ้าใช้ LINE AI Agent (PATH A) ต้องจำว่าเป็น browser/UI-only และไม่ใช่ default

---

## Money Safety Rules

```
Hard stop:
- ห้าม assume งบรายวัน งบรวม bid cap CPF CPC CPA หรือ CPM
- ต้องถาม user ให้ระบุเลขเงินก่อนสร้าง dry-run
- ทุก write action ต้อง dry_run=True ก่อน
- ต้องสรุป payload/ตัวเลขให้ user ตรวจ
- ต้องได้คำว่า "ยืนยัน" ก่อน dry_run=False
- ถ้าเปลี่ยนจำนวน adset/ad/creative จากแผนเดิม ต้อง confirm ใหม่
```

---

## Phase 0 — Method Choice

เริ่มจากแชทประโยคเดียว เช่น “ช่วยสร้างโฆษณาเพิ่มเพื่อนให้หน่อย” ใช้ PATH B (`MCP_MANUAL`) เป็น default และดึงข้อมูลบัญชีด้วย MCP เอง ไม่ถามสิ่งที่บัญชีตอบได้

ถามทีละเรื่องเฉพาะสิ่งที่ขาด: เป้าหมายธุรกิจ, งบ/bid (ห้ามเดา), วันเริ่ม, ข้อเท็จจริงสินค้า และ approval ผู้อ่านไม่ต้องเตรียม/แนบ/เขียนไฟล์ ยกเว้นรูป creative

ถ้าผู้ใช้ต้องการ LINE AI Agent ให้ใช้ PATH A; งาน UI-only หรือ MCP ใช้ไม่ได้ค่อยใช้ PATH C ไม่ต้องให้เลือกวิธีใหม่ทุกครั้ง

---

## Phase 1 — Intake

ถามตามลำดับ **Campaign → Ad Set → Ad** เท่านั้น อย่าถามข้อมูล Ad ก่อนที่ Campaign/Ad Set จะชัดเจน

### 1A — Campaign Level (ถามก่อน)

| ข้อมูล | คำถาม | Required |
|---|---|---|
| เป้าหมายธุรกิจ | อยากให้แคมเปญนี้ทำอะไรครับ? เช่น เพิ่มเพื่อน OA / เข้าเว็บ / Conversion | ใช่ |
| Budget | งบประมาณต่อวันกี่บาทครับ? (หรืองบรวมทั้งหมด?) | ใช่ |
| Start date | เริ่มยิงวันไหนครับ? | ใช่ |

### 1B — Ad Set Level (ถามหลัง Campaign ชัดแล้ว)

| ข้อมูล | คำถาม | Required |
|---|---|---|
| กลุ่มเป้าหมาย | เน้นคนกลุ่มไหนครับ? (ดู Customer Avatar Gate ก่อนถามข้อนี้) | ใช่ |
| จำนวน Ad Set | อยากแบ่งกลุ่มเป้าหมายเป็นกี่กลุ่มเพื่อ compare ครับ? | ใช่ |
| Bid/cost cap | CPF/CPC/CPA สูงสุดกี่บาทครับ? | ถ้าใช้ cost cap |

### Customer Avatar Gate (ก่อนถามหรือเลือก Interest)

**กฎเหล็ก: ห้ามเปิดหน้า Interest แล้วเริ่มติ๊กทันที** — ต้องตอบคำถาม "ลูกค้าคนนี้คือใคร?" ให้ได้ก่อน ไม่งั้นเป็นการ**กอง Interest ที่ดูเกี่ยวข้อง** ไม่ใช่การสร้าง Audience จริง (พบบ่อยในสินค้าราคาสูง เช่น บ้าน 10 ล้าน ที่ใช้งบ 7 หลัก/เดือนแต่หาลูกค้าจริงไม่ได้ เพราะเริ่มคิดจาก Interest ก่อน Customer Avatar)

ใช้หลักฐานจากบัญชีร่วมกับคำตอบ user เติม `customer_avatar` 3 ชั้นตามลำดับ ก่อนไปหน้า Interest; ถามทีละเรื่องเฉพาะข้อเท็จจริงที่บัญชีตอบไม่ได้ และไม่ถือว่า targeting เดิมพิสูจน์กำลังซื้อหรือช่วงชีวิต:

| ชั้น | คำถาม | บ้านเดี่ยว 10 ล้าน (ตัวอย่างสมมติ) | สัญญาณจากแอปในมือถือ (App Behavior) |
|---|---|---|---|
| Need | ลูกค้ากำลังมองหาสินค้า/บริการประเภทนี้อยู่ไหม แสดงออกยังไง | มองหาบ้าน/สนใจอสังหาริมทรัพย์ | ใช้แอปหมวดไหนที่ตรงกับปัญหา เช่น แอปท่องเที่ยว / การศึกษา / แอปทำงาน |
| Ability | ลูกค้ามีกำลังซื้อระดับนี้ไหม มีสัญญาณอะไรบ่งบอก | สนใจการเงิน/การลงทุน | ระดับความมั่งคั่ง + ราคามือถือที่ใช้ |
| Life Stage | ลูกค้าอยู่ช่วงชีวิตที่ต้องการสินค้านี้ไหม | แต่งงาน/มีครอบครัว/มีลูก | persona จากแอป: แม่และเด็ก / วัยเกษียณ / ซื้อรถคันแรก |

ทุกชั้นต้องถามต่อ 1 ข้อ: **"ลูกค้ากลุ่มนี้น่าจะใช้แอปแบบไหนในมือถือ?"** แล้ว map เป็น app code จาก `knowledge/interest-detail-app-behavior.md` ใส่ในชั้นนั้น (OR ร่วมกับ interest เดิม)

- ถ้า user ตอบไม่ได้ ให้ช่วย prompt ทีละชั้น อย่าข้ามไปเลือก Interest เอง
- บันทึกผลเป็น `customer_avatar`: `{ need, ability, life_stage }` พร้อมหลักฐาน/คำตอบที่รองรับ ใช้ map ต่อใน Interest Targeting
- Custom audience ไม่แทน Customer Avatar Gate; ต้องตอบครบก่อนเลือก targeting แม้มีฐานเดิมอยู่แล้ว
- Audience ไม่มีขนาดที่ "ดีที่สุด" มีแต่ขนาดที่เหมาะกับงบ — ห้ามแคบจนเหลือหลักหมื่นด้วยความเชื่อว่ายิ่งแคบยิ่งแม่น (ดู Reach Estimate ก่อนสร้าง Ad Set)

### 1C — Ad Level (ถามสุดท้าย หลัง Ad Set ชัดแล้ว)

| ข้อมูล | คำถาม | Required |
|---|---|---|
| Creative | มีรูป 1080×1080 และรูปเล็ก 600×400 ไหมครับ? | ใช่ |
| Title / Description | ข้อความหัวโฆษณาและคำอธิบาย (สูงสุด 20 ตัวอักษร) | ใช่ |
| Long Title | ชื่อยาวสำหรับ Smart Channel (บังคับเมื่อมีรูปเล็ก) | ถ้ามีรูปเล็ก |
| Landing/OA | URL หรือ LINE OA | ตาม objective |

### Objective Mapping

| User พูดว่า | MCP/API objective |
|---|---|
| เพิ่มเพื่อน OA | `GAIN_FRIENDS` |
| เข้าเว็บ | `WEBSITE_TRAFFIC` |
| Conversion | `CONVERSIONS` |
| Reach | `REACH` |
| ติดตั้งแอป | `APP_INSTALL` |
| ดูวิดีโอ | `VIDEO_VIEW` |

### Bid Rules

```
เพิ่มเพื่อน OA → CPF/bid cap ต้องมาจาก user
เข้าเว็บ → CPC/cost cap หรือ auto ต้องมาจาก user
Conversion → CPA/cost cap ต้องมาจาก user
Reach → CPM/auto ต้องมาจาก user
```

ถ้า user ยังไม่รู้ราคา ให้เสนอช่วงอ้างอิงได้ แต่ห้ามเลือกแทน

---

## Phase 2 — Recommend Plan

ก่อนสร้างอะไรจริง ต้องสรุปแผน:

```
สรุปแผน:
- Method: MCP Manual/API-first
- Objective: [objective]
- Campaign: [name]
- Budget: ฿[X]/วัน
- Bid/cost cap: ฿[Y] [CPF/CPC/CPA/CPM]
- Start date: [YYYY-MM-DDTHH:mm:ss+07:00]
- Adset plan: [จำนวน + targeting]
- Creative plan: [จำนวน ads + format]

ผมจะตรวจ dry-run แล้วสรุปก่อนขอคำว่า "ยืนยัน" สำหรับ write แต่ละครั้งครับ
```

เรียก MCP ด้วย `dry_run=True` ก่อนทุก write tool; การเห็นชอบแผนยังไม่อนุญาตให้ส่งจริง

---

## Phase 3 — PATH B: MCP Manual/API-first

### Step B0 — Duplicate + Context Check

ใช้ read tools ก่อนสร้าง:

```
1. list_campaigns(fetch_all=True)
2. ถ้ามี campaign คล้ายกัน ให้แจ้ง user ก่อนสร้างซ้ำ
3. ถ้า objective = GAIN_FRIENDS ให้ list_audiences เพื่อหา active_friends_audience_id
4. ถ้ามี interest ให้ map จาก `knowledge/interest-catalog-INDEX.md` ก่อน แล้วค่อยโหลด detail file หรือเรียก `list_advanced_targeting_codes` เฉพาะเมื่อ cache ไม่พอ
```

### Step B1 — Create Campaign

Tool: `create_campaign`

Rules:
- ใช้ objective enum จาก API เท่านั้น เช่น `GAIN_FRIENDS`
- เงินใช้ THB ใน tool แล้ว tool แปลงเป็น micro
- `start_date` เป็น required จาก LINE Ads API ต้องถาม user ตั้งแต่ intake
- dry-run ก่อนเสมอ

Flow:

```
create_campaign(..., status="PAUSED", dry_run=True)
สรุปชื่อ objective งบ วันเริ่ม และสถานะ PAUSED เป็นตัวเลขชัดเจน
รอ user พิมพ์ "ยืนยัน"
create_campaign(..., status="PAUSED", dry_run=False)
แสดง readback และ readback_ok จาก response
get_entity(entity_type="campaign", entity_id=[ID ที่สร้าง]) เพื่อตรวจ configured_status/delivery_status
```

### Step B2 — Create Adset

Tool: `create_adset`

สำหรับ `GAIN_FRIENDS`:

```
1. list_audiences
2. หา `active_friends_audience_id`
3. ตรวจว่า audience เพื่อนปัจจุบัน status=READY และ usable_in_adset=true แล้วใส่ใน `excluded_audience_ids`; ถ้าไม่พบหรือยังไม่พร้อม ให้พักขั้นสร้าง ad set ห้ามเดา ID หรือข้ามการยกเว้นเพื่อน
4. ใช้ bid_type="CPF"
5. ใช้ auto_bid_type="FRIEND"
6. ถ้า bid_strategy="COST_CAP" ต้องมี bid_amount จาก user
```

### Interest Targeting

ห้ามส่งชื่อ interest ตรง ๆ เช่น `Marketing`, `Branding`, `Business`

**Precondition:** ต้องมี `customer_avatar` (Need/Ability/Life Stage) จาก Customer Avatar Gate ก่อนเริ่ม map — ถ้ายังไม่มีให้ย้อนกลับไปถามก่อน อย่า map จาก "Interest ที่ดูเกี่ยวข้อง" ตรงๆ

```
1. อ่าน `knowledge/interest-catalog-INDEX.md` ก่อนเสมอ เพื่อเห็นหมวดหลัก + common mapping โดยไม่โหลด catalog เต็ม
2. Map ทีละชั้นของ customer_avatar → interest/behavior code แยกกลุ่มตามชั้น (Need / Ability / Life Stage)
   ดูตัวอย่างเต็มใน `knowledge/interest-catalog-INDEX.md` → "Customer Avatar → Interest Mapping"
   **ทุกชั้นต้องเช็ค App Behavior ก่อนสรุป** (หมวดหมู่แอป / persona จากแอป / ความมั่งคั่ง / ราคามือถือ) — ถ้าชั้นไหนไม่ใส่ app code ต้องบอก user ว่าเพราะอะไร เช่น ไม่มีหมวดที่ตรง หรือหมวดที่ตรงกว้างเกิน (โซเชียล / การติดต่อสื่อสาร / ตัดต่อภาพ)
3. ถ้า INDEX ไม่มี niche/sub-code ที่ต้องการ ให้โหลด detail file เฉพาะหมวดที่เกี่ยวข้อง:
   - `knowledge/interest-detail-interests.md`
   - `knowledge/interest-detail-business-commerce.md`
   - `knowledge/interest-detail-lifestyle-consumer.md`
   - `knowledge/interest-detail-line-signals.md`
   - `knowledge/interest-detail-app-behavior.md` — หมวดหมู่แอป / persona จากแอป / ระดับความมั่งคั่ง / ราคามือถือ (ใช้เติมทุกชั้น Need/Ability/Life Stage)
4. ถ้า detail file ยังไม่มี segment ที่ต้องการ ค่อยเรียก list_advanced_targeting_codes(campaign_objective="GAIN_FRIENDS", country="TH", locale="th")
5. เลือกเฉพาะ code ที่ selectable=true
6. ใช้ `interest_groups` แบบ intersection ตามชั้น avatar โดย**แต่ละชั้นต้องมีหลาย signal (แนะนำ 3–5 codes) OR กันภายในชั้น** ผสมทั้ง Interest + Behavior เพื่อให้ชั้นสะท้อนกลุ่มจริง ไม่ใช่ code เดียวโดดๆ:
   interest_groups=[
       ["6", "1639", ...],        # Need: interest บ้านและสวน OR ผู้ติดตาม OA อสังหาฯ OR ...
       ["10", "1590", "2444", "2445"],  # Ability: การเงิน OR กำลังซื้อสูง OR ความมั่งคั่งสูง/สูงมาก (app)
       ["1617", "1019", "1618"],  # Life Stage: ครอบครัว OR เลี้ยงดูบุตร OR งานแต่งงาน
   ]
   กฎ 2 ข้อที่ผิดบ่อย:
   - ห้ามโยนทุก interest ที่ "ดูเกี่ยวข้อง" ลง group เดียว (OR รวมหมด เช่น บ้าน+รถยนต์+ครอบครัว+ท่องเที่ยว) — นั่นคือการกอง Interest ไม่ใช่การสร้าง Audience
   - ห้ามใส่ชั้นละ 1–2 code แล้ว intersect — แคบเกินจริงและชั้นไม่สะท้อนกลุ่ม (Ads Opt ดูก็รู้ว่า target ไม่ครบ) ให้หา signal เสริมจาก detail files จนแต่ละชั้นมีอย่างน้อย 3 codes เว้นแต่หมวดนั้นมี code ให้เลือกน้อยจริง
7. เมื่อมี `interest_codes` หรือ `interest_groups` tool ต้องใช้:
   targetingMode="MANUAL"
   includeAdvancedTargetings=[{"interests": [...], "behaviors": [...], "purchaseIntents": [...]}, ...]
   ใส่ interest/behavior/purchase intent code ปนกันใน `interest_groups` ชั้นเดียวกันได้ — tool แยก key ตามประเภท code ให้เอง (behavior รวมถึงหมวดหมู่แอปทั้งหมด ห้ามอยู่ใต้ `interests`)
```

### Custom Audience — เลือกหรือสร้างก่อน Create Ad Set

ทำหลัง **Customer Avatar Gate** และวาง targeting แล้ว แม้รับแผนมาจาก MODE 6 ก็ต้องผ่าน gate เดียวกัน

1. เรียก `list_audiences()` แสดงชื่อ/ID และ `estimated_audience_size` ของรายการที่ `status="READY"` และ `usable_in_adset=true` ให้เลือกตามแผน; รายการที่ยังไม่พร้อมแจ้ง status แยกไว้ ไม่ใช้กับ ad set
2. ขนาด `"-"` หมายถึงเล็กเกินรายงาน; `"100 or fewer"` หมายถึงไม่เกิน 100 คน ไม่ใช่จำนวนที่แน่นอน; ถ้าไม่คืนขนาดให้บอกไม่ทราบ ไม่เติม 0
3. ถ้าต้องใช้ฐานที่ยังไม่มี เสนอ `create_audience(name, function_type, config, dry_run=True, workspace_dir=None)` ตามชนิดด้านล่าง ใช้ source IDs/config ที่ตรวจได้จริง ไม่เดา ID หรือ config; บัญชีต้องมีสิทธิ์ Custom Audience

| function_type | ฐานที่จะสร้าง | ต้องตรวจ |
|---|---|---|
| `LOOKALIKE` | คนคล้ายฐานต้นทาง | source audience + size ratio ที่ผู้ใช้เลือก |
| `APP_EVENT` | ผู้ทำ event ในแอป | แอป/event ต้นทางที่มีจริง |
| `WEBTRAFFIC` | ผู้เข้าเว็บจาก LINE Tag | LINE Tag และ retentionDays 1–180 วัน |
| `ACCOUNT_FRIENDS` | เพื่อน LINE OA | OA ต้นทางที่มีจริง |
| `VIDEO_VIEW` | ผู้ดูวิดีโอโฆษณาที่ผ่านมา | โฆษณาวิดีโอต้นทาง |
| `IMAGE_CLICK` | ผู้คลิกรูปโฆษณาที่ผ่านมา | โฆษณารูปต้นทาง |

Customer-list upload (hashed phone/email) **ไม่รองรับผ่าน MCP** ให้ผู้ใช้ทำเองใน LINE Ads Manager ไม่ขออ่าน/แนบไฟล์ลูกค้า

```text
create_audience(name=..., function_type=..., config=..., dry_run=True)
สรุปชื่อ ชนิด แหล่งข้อมูล และค่าที่ตั้ง เช่น retentionDays/size ratio; ขนาดฐานใหม่ยังไม่ทราบจน LINE สร้างเสร็จ
รอ user พิมพ์ "ยืนยัน"
create_audience(name=..., function_type=..., config=..., dry_run=False)
ตรวจ id/status ใน response (ปกติ IN_PROGRESS) แล้วเรียก list_audiences() ตรวจ ID/status/ขนาด
```

ฐานใหม่เริ่ม `IN_PROGRESS` แจ้งว่ายังใช้ใน ad set ไม่ได้ แล้ว re-check `list_audiences()` ก่อนใช้จริง
ถ้ายังไม่ READY ให้ถามทีละเรื่องว่า “จะรอฐานพร้อม หรือสร้าง ad set โดยไม่ใช้ฐานใหม่นี้ครับ?” ไม่ตัดฐานออกเอง
ถ้าเลือกไม่ใช้ ให้ทบทวน targeting/reach และ dry-run แผนใหม่ก่อนขอ “ยืนยัน”; สำหรับ GAIN_FRIENDS ยังต้องยกเว้น active friends audience ที่พร้อมใช้เสมอ ถ้าฐานยกเว้นนี้ไม่พร้อมต้องรอ

เมื่อ READY และ `usable_in_adset=true` แล้ว ส่ง ID ที่เลือกใน `custom_audience_ids` / `excluded_audience_ids` ให้ทั้ง `estimate_adset_reach` และ `create_adset` ด้วยชุดเดียวกัน ห้ามใช้ ID ที่ยัง IN_PROGRESS หรือเดา ID

### Reach Estimate ก่อนสร้าง Ad Set (optional)

ใช้ `estimate_adset_reach(campaign_id=..., campaign_objective=..., daily_budget=..., bid_type=..., auto_bid_type=..., targeting=...)` กับแผน targeting ก่อนสร้าง ad set ได้ รองรับ targeting params แบบ `create_adset` และ optional `adset_id`, `bid_amount`, `bid_strategy`

- เป็น LINE Adgroup Result Simulator (`simulation/ars`): คืน reach min–max และ click min–max เป็นค่าประมาณ ไม่ใช่จำนวน audience จริงหรือผลรับประกัน และไม่สร้างอะไร
- ส่ง `custom_audience_ids` / `excluded_audience_ids` ชุดที่จะใช้สร้างจริงด้วย โดยตรวจ READY/usable_in_adset ก่อนจำลอง
- ใช้งบ/bid ที่ user ระบุเท่านั้น เปรียบเทียบแผนภายใต้เงื่อนไขเดียวกัน; ถ้ามี absent/invalid fields ให้แจ้งข้อมูลที่ขาด ห้ามเติมตัวเลขเอง
- ไม่ใช้สูตรคำนวณ audience หรือ `targetReachRatio`/`balance_warning` ที่ tool นี้ไม่ได้รับรอง

### Create Ad Set หลังทบทวน targeting

```text
create_adset(..., custom_audience_ids=ready_include_ids, excluded_audience_ids=ready_exclude_ids, status="PAUSED", dry_run=True)
สรุปงบ bid targeting อายุ audience IDs/ขนาด/status และ exclusions ให้ชัด
รอ user พิมพ์ "ยืนยัน"
create_adset(..., custom_audience_ids=ready_include_ids, excluded_audience_ids=ready_exclude_ids, status="PAUSED", dry_run=False)
แสดง readback และ readback_ok
get_entity(entity_type="adset", entity_id=[ID ที่สร้าง])
```

Live-tested mapping:

| User พูดว่า | LINE Ads code |
|---|---|
| Marketing / Branding / Advertising / Business | `4` = อาชีพและธุรกิจ |

ตัวอย่าง payload ที่ถูก (ตัวอย่างสมมติ):

```json
{
  "targeting": {
    "targetingMode": "MANUAL",
    "ageMin": 25,
    "ageMax": 44,
    "country": "TH",
    "excludedCustomAudienceIds": ["5343822743474"],
    "includeAdvancedTargetings": [
      { "interests": ["4"] }
    ]
  }
}
```

### Age Brackets

ตรงกับ dropdown ใน Ads Manager (อายุเริ่ม กับ อายุสิ้นสุด ใช้ชุดค่าคนละชุด) — ค่าอื่น API reject ทันที:

| age_min (อายุเริ่ม) | age_max (อายุสิ้นสุด) |
|---|---|
| 20, 25, 30, 35, 40, 45, 50, 55, 60, 65 | 24, 29, 34, 39, 44, 49, 54, 59, 64 หรือ **ไม่ระบุ** (= ไม่ตั้งค่า ไม่จำกัดอายุสูงสุด) |

- เลือกคู่ไหนก็ได้ที่ age_min < age_max เช่น 25–34, 30–49, 20–64
- "X ปีขึ้นไป" → ใส่แค่ `age_min=X` ไม่ใส่ `age_max`
- ห้ามส่ง `age_max=65` (ไม่มีใน dropdown และ API reject — tool จะแปลงเป็น "ไม่ตั้งค่า" ให้เพื่อกันพัง)

**กฎเหล็ก:** ห้ามแนะนำค่าที่ไม่อยู่ในตารางนี้ เช่น 28, 22, 42, age_max=65 — จะทำให้ API error เสมอ

ถ้า user บอกช่วงอายุที่ไม่ตรง bracket:
- Map ไปหาค่าที่ใกล้ที่สุดและ**ครอบคลุม**ช่วงนั้น เช่น 18–60 → 20–64, 22–28 → 20–29
- แสดงตัวเลือกที่ valid ให้ user เลือก อย่าตัดสินใจแทน
- (ตัวอย่างสมมติ): user บอก "28-45" → เสนอ `25-44` (แคบกว่า) หรือ `25-54` (กว้างกว่า) แล้วรอ confirm

### Step B3 — Upload Media

Tool: `upload_media`

Rules:
- รองรับ JPG/PNG/MP4/MOV
- รูปแนะนำ `1080x1080` หรือ `1200x628`
- Small image แนะนำ `600x400`
- ขนาดไฟล์: รูป ≤ 10MB, วิดีโอ ≤ 1GB
- Video: MP4/MOV, ความยาว ≤ 600 วินาที (แนะนำ 15–30 วินาที)
- ถ้า API ตอบ `INVALID_IMAGE_SIZE` ให้ user แก้ไฟล์ก่อน
- upload media เป็น write action ต้อง confirm ก่อน `dry_run=False`

Flow:

```
upload_media(file_path, dry_run=True)
สรุปไฟล์ที่จะอัปโหลด แล้วรอ user พิมพ์ "ยืนยัน"
upload_media(file_path, dry_run=False)
แสดง readback และ readback_ok; ถ้าไม่มี/ตรวจไม่ผ่าน ให้แจ้งว่ายังไม่ยืนยันผล
เก็บ imageHash จาก response.object.obsHash
```

### Step B4 — Create Ad

Tool: `create_ad`

Text limits:
- `title` ไม่เกิน 20 ตัวอักษร
- `description` ไม่เกิน 20 ตัวอักษร
- ต้อง validate ก่อน dry-run/create จริง เพื่อไม่ให้ API reject กลางทาง

สำหรับ `GAIN_FRIENDS`:

```
call_to_action="ADD_FRIEND"
destination_url ไม่จำเป็น
creative เป็น nested object
imageHash จาก upload_media
```

Flow:

```
create_ad(..., status="PAUSED", dry_run=True)
สรุป creative ข้อความ parent IDs และสถานะ PAUSED
รอ user พิมพ์ "ยืนยัน"
create_ad(..., status="PAUSED", dry_run=False)
แสดง readback และ readback_ok
get_entity(entity_type="ad", entity_id=[ad_id])
get_ad_status(ad_id=[ad_id]) เพื่อดู review/delivery ด้วย exact ID
```

Live-tested result:
- create ad สำเร็จผ่าน MCP
- image review อาจ `APPROVED`
- creative review อาจ `IN_REVIEW`
- delivery อาจ `NOT_DELIVERING` เพราะ campaign/adset/ad เป็น PAUSED
- `NOT_APPROVED` = review rejected ต้องแก้เหตุผลที่ถูกปฏิเสธ ไม่ใช่เพียงรอต่อ

---

## PATH A — LINE AI Campaign Agent via Browser

ใช้เมื่อ user ต้องการให้ LINE AI ช่วยคิดรูป/copy/auto targeting และ objective อยู่ในกลุ่มที่รองรับ

ข้อจำกัด:
- รองรับ Friend Added / Website Click / Reach เท่านั้น
- Targeting เป็น Auto เป็นหลัก
- Interest/custom audience คุมละเอียดไม่ได้
- ต้องใช้ browser/Cowork เพราะเป็น UI-only

ต้องทำตาม safety เดิม:
- งบและ bid ต้องมาจาก user
- สร้าง 3 creative ตามแผนเดิม ยกเว้น user confirm จำนวนอื่น
- ถ้าสร้างได้น้อยกว่าที่ตกลง ต้องหยุดถามก่อน submit
- screenshot เฉพาะ crop/preview/error

---

## PATH C — Browser Manual Fallback

ใช้เมื่อ:
- MCP tool ยังไม่รองรับ endpoint นั้น
- API permission ไม่พอ
- ต้องทำ KYC/payment/UI-only
- ต้องตรวจ visual preview ที่ API อ่านไม่ได้

Entry mode:
- `SELF_FILL`: user กรอกเองบนหน้าเว็บ, agent ช่วย checklist + ตรวจ error
- `AI_ASSISTED`: agent กรอกให้หลัง user confirm, ใช้ DOM/interactive ก่อน screenshot

Sensitive upload เช่น phone/email customer list ให้ default เป็น `SELF_FILL`

---

## Ad Set Strategy

### หลักการ: หลาย Ad Set = หลาย Interest Group เพื่อ Compare

**ห้ามแนะนำ Broad targeting** ไม่ว่ากรณีใด — ไม่มี "Broad adset" ในแผนเลย

Multiple Ad Sets หมายถึงการแบ่ง **Customer Avatar ที่ต่างกัน** (ไม่ใช่สลับ Interest แบบสุ่ม) เพื่อ compare ว่า avatar ไหน perform ดีกว่า เช่น กรณีบ้าน 10 ล้าน (ตัวอย่างสมมติ):
- Adset A: avatar "ครอบครัวมีลูก มองหาบ้านหลังแรก" → Need=บ้านและสวน + Ability=การเงิน + Life Stage=ครอบครัว/เลี้ยงดูบุตร
- Adset B: avatar "นักลงทุนอสังหาฯ" → Need=อสังหาริมทรัพย์ + Ability=การลงทุน/กำลังซื้อสูง + Life Stage=วัยทำงานมั่นคง
- Adset C: avatar "คู่แต่งงานใหม่กำลังหาบ้าน" → Need=บ้านและสวน + Ability=การเงิน + Life Stage=งานแต่งงาน

แต่ละ adset ต้องตอบคำถาม "ลูกค้ากลุ่มนี้คือใคร" ได้ก่อนสร้าง ไม่ใช่แค่สลับ Interest code ไปมา

สำหรับงบน้อยกว่า ฿500/วัน:
- ใช้ **1 adset** — เลือก Interest/Behavior กลุ่มที่ match ที่สุด
- เหตุผล: งบน้อยถ้าแตกหลาย adset แต่ละกลุ่มจะได้ข้อมูลไม่พอสรุป

สำหรับงบมากกว่า/เท่ากับ ฿500/วัน:
- ถามว่าอยากแบ่งกี่ Interest Group เพื่อ compare
- แต่ละ adset = Interest กลุ่มต่างกัน เช่น กลุ่ม 1, กลุ่ม 2, กลุ่ม 3
- Custom/lookalike adset ถ้ามีข้อมูลลูกค้าเพียงพอ

อย่าลดจำนวน adset/ad จากแผนที่ user confirm เอง

---

## Final Review

ก่อน write จริงรอบสุดท้าย:

```
สรุปก่อนสร้างจริง:
- Campaign: [ชื่อ/ID] | Objective | ฿[X]/วัน
- Adset: [ชื่อ/ID] | Bid ฿[Y] | Targeting summary
- Ads: [จำนวน] | creative format | review status ถ้ามี
- สถานะหลังสร้าง: campaign/adset/ad เป็น PAUSED ทั้งหมด

พิมพ์ "ยืนยัน" เพื่อดำเนินการจริง
```

---

## Post-submit

หลังสร้าง:

```
✅ Campaign: [ID]
✅ Adset: [ID]
✅ Ad: [ID]
⏳ Creative review: [status]
📌 Delivery status: [status + reasons]
```

สรุปว่าโครงสร้างพร้อมเมื่อ IDs ครบ, `readback_ok=true` และค่าตรงแผนทุกขั้น พร้อมผล `get_entity`/`get_ad_status` ล่าสุด แยก “สร้างครบ” จาก “ผ่าน review/พร้อม delivery”; `IN_REVIEW` ยังรอ, `NOT_APPROVED` คือถูกปฏิเสธ หาก readback ไม่ตรง/อ่านไม่ได้ ห้ามรายงานว่าสำเร็จหรือทำ write ซ้ำทันที ให้ตรวจ exact ID ก่อน

Campaign → Ad Set → upload media → Ad จบที่ PAUSED; media ไม่มีสถานะเปิด/พัก ห้ามเปิดให้อัตโนมัติ หาก review ผ่านและไม่มี delivery blocker จึงบอกว่าพร้อมขอเปิดใช้งาน การใช้ `resume_campaign` / `resume_adset` / `resume_ad` เป็นอีกชุด approval ผ่าน MODE 4: dry-run → สรุปงบ/ผลกระทบ → “ยืนยัน” → execute → readback แยกจาก approval สร้าง

ถ้ามี `workspace_dir` ให้ส่งกับ write tools เพื่อบันทึก `line-ads-data/change_log.jsonl` (fallback `LINE_ADS_WORKSPACE_DIR`); AI จัดการไฟล์เอง ไม่ให้ผู้อ่านเตรียมไฟล์ เสนอ MODE 3 report schedule ต่อ

---

## Error Handling

| Error | วิธีจัดการ |
|---|---|
| `INVALID_IMAGE_SIZE` | ให้ user แก้รูปเป็น 1080x1080 หรือ 1200x628 |
| `401` | ตรวจ Access Key/Secret/signature |
| `403` | แจ้งว่า feature/permission อาจยังไม่เปิด |
| `404` ตอน update | เช็ค method ก่อน: LINE update ใช้ POST ไม่ใช่ PUT |
| creative `IN_REVIEW` | แจ้งว่ารอ LINE review |
| `CAMPAIGN_PAUSED` / `ADGROUP_PAUSED` | แจ้งว่าสร้างแล้วแต่ยังไม่ deliver |

---

## Token Discipline

สำหรับ MCP path:
- ใช้ tool call แทน browser/screenshot
- แสดง payload แบบ compact เฉพาะ field สำคัญ
- read back ด้วย list/get tools หลัง write

สำหรับ browser fallback:
- อ่าน DOM/interactive ก่อน screenshot
- screenshot เฉพาะ visual QA, preview, crop, error
- batch action ที่ปลอดภัย

---

## Notes

1. MCP-first เป็น default สำหรับ campaign creation
2. Browser ใช้เฉพาะ UI-only หรือ fallback
3. Money inputs ต้องมาจาก user เท่านั้น
4. dry-run ก่อน write จริงทุกครั้ง
5. เช็ค duplicate ก่อนสร้าง
6. ใช้ official codes สำหรับ interest เท่านั้น
7. ไม่มี delete tools ใช้ pause แทน
8. ห้ามเลือก Interest ก่อนตอบคำถาม "ลูกค้าคนนี้คือใคร" (Customer Avatar Gate) — กองไม่ใช่ Audience
9. ใช้ `estimate_adset_reach` เป็น optional reach/click min–max estimate ก่อนสร้าง ad set ไม่ใช่ขนาด audience จริง

---

*Version 4.0 | October 2026*
*Updated: หมวดหมู่แอป/App Behavior (`interest-detail-app-behavior.md`) ใช้เติมชั้น Need/Ability/Life Stage; `interest_groups` แยก interests/behaviors/purchaseIntents อัตโนมัติ; อายุตรงกับ dropdown UI (min 20–65, max 24–64 หรือไม่ตั้งค่า)*
*v3.3: Customer Avatar Gate (Need/Ability/Life Stage) ก่อนเลือก Interest, Audience Size Check, multiple adsets = multiple avatars*
*v3.2: Intake order Campaign→AdSet→Ad, ห้าม Broad targeting, multiple adsets = multiple Interest groups for compare*
*v3.1: Goal-first intake, LINE Tag pre-check, min budget table, image spec warning, small image recommendation, debug discipline*
