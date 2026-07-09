# workflows/02-campaign.md
# Campaign + Ad Set + Ad Creation
# Version 3.3 | July 2026 | MCP-first + Customer Avatar-first targeting

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
- ต้องได้คำว่า "ยืนยัน" หรือ "ทำได้เลย" ก่อน dry_run=False
- ถ้าเปลี่ยนจำนวน adset/ad/creative จากแผนเดิม ต้อง confirm ใหม่
```

---

## Phase 0 — Method Choice

หลังรู้ว่า user ต้องการสร้างโฆษณา ต้องให้ user เลือกวิธีสร้างก่อนเสมอ:

```
สร้างแคมเปญได้ 3 วิธีครับ:

1. MCP Manual/API-first — แนะนำ ใช้ API โดยตรง ประหยัด token และกำหนด audience/bid ได้ชัด
2. LINE AI Agent — เร็วกว่า ให้ LINE ช่วยสร้างรูป/copy/auto targeting แต่คุม audience ละเอียดน้อย
3. Browser Manual — ใช้หน้าเว็บเอง เหมาะกับงานที่ API ยังทำไม่ได้

อยากใช้วิธีไหนครับ?
```

บันทึกเป็น `campaign_creation_method`:
- `MCP_MANUAL` = PATH B default
- `AI_AGENT` = PATH A
- `BROWSER_MANUAL` = PATH C fallback

ถ้า user ไม่แน่ใจ ให้แนะนำ `MCP_MANUAL` ยกเว้น user ต้องการใช้ LINE AI Agent หรือขั้นตอนเป็น KYC/payment/UI-only

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

ถาม user 3 ชั้นตามลำดับ ก่อนไปหน้า Interest:

| ชั้น | คำถาม | ตัวอย่าง (บ้านเดี่ยว 10 ล้าน) |
|---|---|---|
| Need | ลูกค้ากำลังมองหาสินค้า/บริการประเภทนี้อยู่ไหม แสดงออกยังไง | มองหาบ้าน/สนใจอสังหาริมทรัพย์ |
| Ability | ลูกค้ามีกำลังซื้อระดับนี้ไหม มีสัญญาณอะไรบ่งบอก | สนใจการเงิน/การลงทุน |
| Life Stage | ลูกค้าอยู่ช่วงชีวิตที่ต้องการสินค้านี้ไหม | แต่งงาน/มีครอบครัว/มีลูก |

- ถ้า user ตอบไม่ได้ ให้ช่วย prompt ทีละชั้น อย่าข้ามไปเลือก Interest เอง
- บันทึกผลเป็น `customer_avatar`: `{ need, ability, life_stage }` ใช้ map ต่อใน Interest Targeting
- Audience ไม่มีขนาดที่ "ดีที่สุด" มีแต่ขนาดที่เหมาะกับงบ — ห้ามแคบจนเหลือหลักหมื่นด้วยความเชื่อว่ายิ่งแคบยิ่งแม่น (ดู Audience Size Check)

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

ยืนยันให้ผมทำ dry-run ตามนี้ไหมครับ?
```

เมื่อ user ยืนยันแผน ให้เรียก MCP ด้วย `dry_run=True` ก่อนทุก write tool

---

## Phase 3 — PATH B: MCP Manual/API-first

### Step B0 — Duplicate + Context Check

ใช้ read tools ก่อนสร้าง:

```
1. list_campaigns
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
create_campaign(..., dry_run=True)
แสดง payload
รอ user ยืนยัน
create_campaign(..., dry_run=False)
read back ด้วย list_campaigns
```

### Step B2 — Create Adset

Tool: `create_adset`

สำหรับ `GAIN_FRIENDS`:

```
1. list_audiences
2. หา `active_friends_audience_id`
3. ใส่ใน `excluded_audience_ids`
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
3. ถ้า INDEX ไม่มี niche/sub-code ที่ต้องการ ให้โหลด detail file เฉพาะหมวดที่เกี่ยวข้อง:
   - `knowledge/interest-detail-interests.md`
   - `knowledge/interest-detail-business-commerce.md`
   - `knowledge/interest-detail-lifestyle-consumer.md`
   - `knowledge/interest-detail-line-signals.md`
4. ถ้า detail file ยังไม่มี segment ที่ต้องการ ค่อยเรียก list_advanced_targeting_codes(campaign_objective="GAIN_FRIENDS", country="TH", locale="th")
5. เลือกเฉพาะ code ที่ selectable=true
6. ใช้ `interest_groups` แบบ intersection ตามชั้น avatar โดย**แต่ละชั้นต้องมีหลาย signal (แนะนำ 3–5 codes) OR กันภายในชั้น** ผสมทั้ง Interest + Behavior เพื่อให้ชั้นสะท้อนกลุ่มจริง ไม่ใช่ code เดียวโดดๆ:
   interest_groups=[
       ["6", "1639", ...],        # Need: interest บ้านและสวน OR ผู้ติดตาม OA อสังหาฯ OR ...
       ["10", "1684", "1590"],    # Ability: การเงิน OR OA การลงทุน OR กำลังซื้อสูง
       ["1617", "1019", "1618"],  # Life Stage: ครอบครัว OR เลี้ยงดูบุตร OR งานแต่งงาน
   ]
   กฎ 2 ข้อที่ผิดบ่อย:
   - ห้ามโยนทุก interest ที่ "ดูเกี่ยวข้อง" ลง group เดียว (OR รวมหมด เช่น บ้าน+รถยนต์+ครอบครัว+ท่องเที่ยว) — นั่นคือการกอง Interest ไม่ใช่การสร้าง Audience
   - ห้ามใส่ชั้นละ 1–2 code แล้ว intersect — แคบเกินจริงและชั้นไม่สะท้อนกลุ่ม (Ads Opt ดูก็รู้ว่า target ไม่ครบ) ให้หา signal เสริมจาก detail files จนแต่ละชั้นมีอย่างน้อย 3 codes เว้นแต่หมวดนั้นมี code ให้เลือกน้อยจริง
7. เมื่อมี `interest_codes` หรือ `interest_groups` tool ต้องใช้:
   targetingMode="MANUAL"
   includeAdvancedTargetings=[{"interests": ["..."]}]
```

### Audience Size Check

สูตรอ้างอิงเร็ว: **Audience Size ≈ Budget ÷ CPM × 5,000**

- ก่อนสรุปแผน (Phase 2) ให้ประเมินคร่าวๆ ว่า audience ที่ map จาก avatar ใหญ่พอสำหรับงบที่ user จะใช้ไหม ถ้าดูแคบเกินไปเทียบกับงบ ให้เตือน user ก่อนสร้างจริง — Audience ไม่มีขนาดที่ดีที่สุด มีแต่ขนาดที่เหมาะกับงบ
- หลังสร้าง adset จริง (หรือหลาย adset สำหรับ compare) ให้เรียก `get_adset_audience_size(campaign_id)` เพื่อตรวจ `targetReachRatio` ของแต่ละ adset
- ถ้า tool แจ้ง `balance_warning` (ต่างกันเกิน 3x) ให้แจ้ง user และเสนอปรับ targeting ให้ใกล้กันก่อน compare ผล

Live-tested mapping:

| User พูดว่า | LINE Ads code |
|---|---|
| Marketing / Branding / Advertising / Business | `4` = อาชีพและธุรกิจ |

ตัวอย่าง payload ที่ถูก:

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

LINE Ads รองรับเฉพาะค่าเหล่านี้เท่านั้น — ค่าอื่นนอกจากนี้ API reject ทันที:

| valid ageMin | valid ageMax |
|---|---|
| 20 | 24 |
| 25 | 29 |
| 30 | 34 |
| 35 | 39 |
| 40 | 44 |
| 45 | 54 |
| 55 | 65 |

**กฎเหล็ก:** ห้ามแนะนำค่าที่ไม่อยู่ในตารางนี้ เช่น 28, 22, 42 — จะทำให้ API error เสมอ

ถ้า user บอกช่วงอายุที่ไม่ตรง bracket:
- Map ไปหา bracket ที่ใกล้ที่สุดและ**ครอบคลุม**ช่วงนั้น
- แสดงตัวเลือก bracket ที่ valid ให้ user เลือก อย่าตัดสินใจแทน
- ตัวอย่าง: user บอก "28-45" → เสนอ `25-44` (แคบกว่า) หรือ `25-54` (กว้างกว่า) แล้วรอ confirm

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
รอ user ยืนยันให้อัปโหลด
upload_media(file_path, dry_run=False)
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
create_ad(..., dry_run=True)
แสดง payload
รอ user ยืนยันสร้าง Ad
create_ad(..., dry_run=False)
read back ด้วย list_ads / get_ad_status
```

Live-tested result:
- create ad สำเร็จผ่าน MCP
- image review อาจ `APPROVED`
- creative review อาจ `IN_REVIEW`
- delivery อาจ `NOT_DELIVERING` ถ้า campaign/adset paused

---

## PATH A — LINE AI Campaign Agent via Browser

ใช้เมื่อ user ต้องการให้ LINE AI ช่วยคิดรูป/copy/auto targeting และ objective อยู่ในกลุ่มที่รองรับ

ข้อจำกัด:
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

Multiple Ad Sets หมายถึงการแบ่ง **Customer Avatar ที่ต่างกัน** (ไม่ใช่สลับ Interest แบบสุ่ม) เพื่อ compare ว่า avatar ไหน perform ดีกว่า เช่น กรณีบ้าน 10 ล้าน:
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
- สถานะหลังสร้าง: active/paused ตามแผน

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

เสนอ MODE 3 report schedule ต่อทันที

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
9. Audience ไม่มีขนาดที่ดีที่สุด มีแต่ขนาดที่เหมาะกับงบ ใช้ `get_adset_audience_size` เช็คก่อน compare

---

*Version 3.3 | July 2026*
*Updated: Customer Avatar Gate (Need/Ability/Life Stage) ก่อนเลือก Interest, Audience Size Check, multiple adsets = multiple avatars*
*v3.2: Intake order Campaign→AdSet→Ad, ห้าม Broad targeting, multiple adsets = multiple Interest groups for compare*
*v3.1: Goal-first intake, LINE Tag pre-check, min budget table, image spec warning, small image recommendation, debug discipline*
