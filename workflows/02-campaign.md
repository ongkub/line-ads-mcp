# workflows/02-campaign.md
# Campaign + Ad Set + Ad Creation
# Version 3.0 | May 2026 | MCP-first

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

ถามเฉพาะข้อมูลที่ยังขาด:

| ข้อมูล | คำถาม | Required |
|---|---|---|
| สินค้า/บริการ | อยากลงโฆษณาสินค้าหรือบริการอะไรครับ? | ใช่ |
| Objective | เพิ่มเพื่อน / เข้าเว็บ / Reach / Conversion / App install / Video | ใช่ |
| Budget | งบประมาณต่อวันกี่บาทครับ? | ใช่ |
| Bid/cost cap | CPF/CPC/CPA/bid cap อยากตั้งไว้กี่บาทครับ? | ถ้าใช้ cost cap |
| Start date | วันเวลาเริ่มโฆษณาเมื่อไหร่? เช่น `2026-05-14T09:00:00+07:00` | ใช่ |
| Targeting | อายุ เพศ พื้นที่ interest/custom audience | ใช่ |
| Creative | มีรูป/วิดีโอและข้อความไหม? | ก่อนสร้าง ad |
| Landing/OA | URL หรือ LINE OA objective | ตาม objective |

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
4. ถ้ามี interest ให้ list_advanced_targeting_codes ก่อน map code
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

```
1. list_advanced_targeting_codes(campaign_objective="GAIN_FRIENDS", country="TH", locale="th")
2. เลือกเฉพาะ code ที่ selectable=true
3. ส่งผ่าน `interest_codes`
4. เมื่อมี `interest_codes` tool ต้องใช้:
   targetingMode="MANUAL"
   includeAdvancedTargetings=[{"interests": ["..."]}]
```

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

LINE Ads ใช้ bracket เฉพาะ:

| ageMin | ageMax |
|---|---|
| 20 | 24 |
| 25 | 29 |
| 30 | 34 |
| 35 | 39 |
| 40 | 44 |
| 45 | 54 |
| 55 | 65 |

ถ้า user บอก "28-45" ให้เสนอปรับเป็น `25-44` หรือ `25-54` แล้วรอ confirm

### Step B3 — Upload Media

Tool: `upload_media`

Rules:
- รองรับ JPG/PNG/MP4/MOV
- รูปแนะนำ `1080x1080` หรือ `1200x628`
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

สำหรับงบน้อยกว่า ฿500/วัน:
- ใช้ 1 adset ก่อน เพื่อให้ data ไม่กระจาย

สำหรับงบมากกว่า/เท่ากับ ฿500/วัน:
- Broad adset
- Interest adset
- Custom/lookalike adset ถ้ามีข้อมูลลูกค้าเพียงพอและ feature เปิดแล้ว

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

---

*Version 3.0 | May 2026*
*Updated: MCP-first architecture, interest code lookup, media upload/create_ad flow, API write safety, browser fallback scope*
