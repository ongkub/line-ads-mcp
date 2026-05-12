# workflows/02-campaign.md
# Campaign + Ad Set + Ad Creation
# Version 2.0 | May 2026

---

## ARCHITECTURE: 2 PATHS

```
PATH A — AI Agent (Auto Targeting)   → เร็ว แต่ control น้อย
PATH B — Manual (Cowork ควบคุม Chrome) → ช้ากว่า แต่ control เต็ม
```

### Money Safety Rules — ห้ามเดาเรื่องเงิน

```
Hard stop:
- ห้าม assume / default ราคาต่อผลลัพธ์ เช่น CPF, CPC bid, CPA target, bid cap
- ห้าม assume / default งบรายวันหรืองบรวม
- ต้องถาม user ให้ระบุเป็นตัวเลขก่อนสร้าง draft หรือส่งข้อมูลให้ LINE AI
- ต้องทวนตัวเลขเงินในแผน และรอ user confirm ก่อนกรอก/สร้าง draft
- ต้องรอ user confirm อีกครั้งก่อน submit/publish/บันทึกโฆษณา
```

ถ้า user ยังไม่รู้ราคาต่อผลลัพธ์:
- อธิบายว่าเป็นเพดานราคาที่ระบบพยายามใช้ต่อ 1 result
- เสนอช่วงอ้างอิงได้ แต่ห้ามเลือกแทน user
- ถามให้ user เลือกตัวเลขเองก่อนเดินต่อ

ตัวอย่าง:
```
ราคาต่อการเพิ่มเพื่อน (CPF) อยากตั้งเพดานไว้กี่บาทครับ?
ผมเสนอช่วงให้คิดได้ แต่จะไม่เลือกแทน เพราะเป็นเรื่องค่าใช้จ่ายจริง
```

### ข้อจำกัดของ PATH A (AI Agent) ที่ต้องรู้ก่อน

```
✓ รองรับ 3 Objectives เท่านั้น:
  - Friend Added (เพิ่มเพื่อน LINE OA)
  - Website Click (การเข้าชมเว็บไซต์)
  - Reach (การเข้าถึง)

✗ ไม่รองรับ:
  - Conversion (cv ของ LINE Tag)
  - App Install / App Engagement
  - Video Views

✓ Targeting แบบ AUTO เท่านั้น:
  - LINE Auto-Targeting เรียนรู้กลุ่มเองใน 48 ชม.แรก
  - ใส่ Interest filter ได้ผ่านแชต **แต่ AI อาจไม่ apply เข้า form** (ฟอร์มจริงไม่มี Interest field ใน PATH A)
  - คุมได้แค่: ประเทศ, พื้นที่, เพศ, อายุ, OS

✗ ไม่รองรับ:
  - Custom Audience (Phone list, Email list)
  - Lookalike Audience
  - LINE Tag Retargeting
```

### Switch Logic (ตัดสินใจก่อนเริ่ม)

```
ใช้ PATH A ถ้า:
  ✓ user เพิ่งเริ่ม / ทดสอบตลาด
  ✓ มี URL เว็บ / landing page (AI ดึงรูป + copy ให้)
  ✓ Objective อยู่ใน 3 ตัวที่รองรับ
  ✓ ไม่มี data ลูกค้าเก่า / ไม่ต้องการ Custom Audience

ใช้ PATH B ถ้า:
  ✗ มี data ลูกค้าเก่า อยากใช้ Custom Audience / Lookalike
  ✗ ต้องการ Interest targeting ละเอียด
  ✗ Objective = Conversion, App Install, Video View
  ✗ user ไม่มี URL เว็บ
  ✗ PATH A ล้มเหลว (error / timeout)
```

---

## PHASE 0 — METHOD CHOICE

หลังรู้ว่า user ต้องการสร้างโฆษณา และก่อนเริ่มสร้าง campaign จริง ต้องให้ user เลือกวิธีสร้างเสมอ:

```
สร้างแคมเปญได้ 2 วิธีครับ:

1. AI Agent — เร็วกว่า ให้ LINE ช่วยสร้างรูป/copy/targeting อัตโนมัติ แต่คุม audience ละเอียดได้น้อย
2. Manual Audience — ช้ากว่าและมีหลายช่องกว่า แต่กำหนด audience/interest/custom audience ได้ละเอียดกว่า

อยากใช้วิธีไหนครับ?
```

บันทึกเป็น `campaign_creation_method`:
- `AI_AGENT` = PATH A
- `MANUAL_AUDIENCE` = PATH B

ถ้า user ไม่แน่ใจ ให้แนะนำตามเงื่อนไขได้ แต่ต้องให้ user ยืนยันวิธีก่อน:
```
เคสนี้ผมแนะนำ AI Agent เพราะมี URL และ objective รองรับ แต่ถ้าอยากคุม audience ละเอียดให้เลือก Manual Audience ครับ
จะใช้ AI Agent ไหมครับ?
```

---

## PHASE 1 — INTAKE (ใช้ทั้ง 2 paths)

ถามทีละข้อได้ แต่ถ้า user ให้ข้อมูลมาหลายอย่างแล้ว ให้เติมเองและถามเฉพาะช่องที่ขาด:

### Q1 — สินค้า/บริการ
"อยากลงโฆษณาสินค้าหรือบริการอะไรครับ?"
→ รับ: ชื่อสินค้า, ราคา, ช่องทางขาย

### Q2 — Objective
```
[ เพิ่มเพื่อน OA ]   → Friend Added       [Path A ✓ | Path B ✓]
[ ให้คนเข้าเว็บ ]    → Website Clicks     [Path A ✓ | Path B ✓]
[ ให้คนรู้จักแบรนด์ ] → Reach              [Path A ✓ | Path B ✓]
[ ให้คนซื้อสินค้า ]  → Conversion         [Path A ✗ | Path B ✓]
[ โปรโมทแอป ]       → App Install        [Path A ✗ | Path B ✓]
[ ดูวิดีโอ ]         → Video View         [Path A ✗ | Path B ✓]
```

⚠️ **ถ้า user เลือก Conversion / App Install / Video View** + เลือก PATH A
→ แจ้ง: "Objective นี้ต้องใช้ PATH B (Manual) นะครับ ขอ switch ให้?"

### Q3 — งบ
"งบประมาณต่อวันประมาณเท่าไหร่ครับ? (บาท)"

### Q4 — ราคาต่อผลลัพธ์ / Bid Cap
ถามตาม objective:
```
เพิ่มเพื่อน OA → "ราคาต่อการเพิ่มเพื่อน (CPF) อยากตั้งเพดานไว้กี่บาทครับ?"
เข้าเว็บ → "ถ้าจะตั้ง bid/cost cap ต่อคลิก อยากให้ไม่เกินกี่บาทครับ? ถ้าใช้ auto bid ให้ตอบ auto ได้"
Reach → "ต้องการใช้ auto bid หรือมีเพดาน CPM/ค่าใช้จ่ายที่อยากคุมไหมครับ?"
Conversion → "CPA target หรือ cost cap ต่อ conversion อยากตั้งไว้กี่บาทครับ?"
```

Rules:
- ถ้า objective มีช่อง CPF/CPA/bid cap ใน form หรือ AI Agent ถาม ต้องใช้ค่าจาก user เท่านั้น
- ถ้า user ตอบ `auto` ได้เฉพาะ objective/flow ที่ LINE Ads รองรับ auto bid โดยไม่ต้องใส่ตัวเลข
- ถ้า user ยังไม่ตอบ ห้ามเดินต่อไปสร้าง campaign/draft

### Q5 — URL Landing
"มีเว็บไซต์หรือหน้า Landing Page ของสินค้าไหมครับ?"
→ ถ้าไม่มี + เลือก PATH A → switch ไป PATH B (PATH A ต้องการ URL)

---

## PHASE 2 — RECOMMEND

```
📋 แผนที่ผมแนะนำครับ

🎯 Objective: [objective] — เพราะ [เหตุผล]
💰 Budget: ฿[X]/วัน | Bidding: [strategy]
💸 Cost cap/Bid: [CPF/CPA/CPC/Auto จาก user]
🛠️ PATH: [A/B] — [เหตุผลที่เลือก]
👥 Targeting: [auto/manual]
🎨 Ad Set Strategy: [จำนวน ad set]
🎨 Creative Plan: [จำนวน creative/ad ที่จะสร้าง]

ยืนยัน method + budget + bid/cost cap + targeting + creative plan นี้ไหมครับ?
```

→ user ไม่เห็นด้วย → ถามเพื่อเข้าใจก่อน วน loop สูงสุด 3 รอบ

---

## 🆕 AD SET STRATEGY (เพิ่มใหม่)

### กฎทั่วไป — สร้างกี่ Ad Set?

**สำหรับ PATH A (AI Agent — Auto Targeting):**
```
✓ 1 Ad Set + 3-5 Creatives
   → AI Auto-Targeting จัดการ audience เอง
   → A/B test ที่ Creative แทน
   → 3 Creative อย่างน้อย: 
      - Creative 1: Personal brand (รูปคน + credentials)
      - Creative 2: Product/Service (รูปงาน + benefit)
      - Creative 3: Social proof (รูป client logo / testimonial)
```

**สำหรับ PATH B (Manual — กำหนดเอง):**
```
✓ 3 Ad Sets (A/B/C) + Creative ตาม set
   Ad Set A — Broad Targeting    (อายุ + พื้นที่ ไม่จำกัด interest)
   Ad Set B — Interest Targeting (อายุ + พื้นที่ + interest เฉพาะ)
   Ad Set C — Custom/Lookalike   (Phone list, Email list, LINE Tag retarget)
   
   → แต่ละ set ใช้ creative ที่ตรงกับ targeting
   → หลัง 7-14 วัน ดู set ไหน CPF ต่ำสุด → scale set นั้น
```

### Decision Tree
```
มี data ลูกค้าเก่า (Phone/Email > 1,000 records)?
  YES → Ad Set C ทำได้ (Custom + Lookalike) → 3 sets
  NO  → 2 sets (Broad + Interest) ก็พอ
  
งบ < ฿500/วัน?
  YES → 1 set พอ (data ไม่พอจะเรียนรู้หลาย set)
  NO  → 3 sets เต็มสูตร
```

---

## PATH A — LINE AI Campaign Agent

### Step A1: Navigate
```
1. เปิด admanager.line.biz/adaccount/{ID}/campaign/
2. คลิกปุ่ม "+ สร้าง AI แคมเปญ (beta)"
3. ⚠️ ครั้งแรก: ขอ user ยอมรับ Terms ของ LINE Ads AI Agents
```

### Step A2: Feed info ให้ LINE AI
ส่งทีละข้อความ ตามลำดับที่ AI ถาม:
```
1. เลือก objective (จาก 3 ที่เลือกได้)
2. ส่ง: ชื่อแบรนด์ + บริการ + ราคา
3. ส่ง: URL landing
4. ส่ง: CPF max bid (ถ้า Friend Added) — ใช้ตัวเลขที่ user ระบุเท่านั้น ห้ามเดา
5. ส่ง: daily budget — ใช้ตัวเลขที่ user ระบุเท่านั้น ห้ามเดา
```

### Step A3: AI สรุป + ขอ refine
AI จะสรุป:
- อุตสาหกรรม
- รายละเอียดแบรนด์ (จาก URL)
- จุดขายสำคัญ
- กลุ่มเป้าหมายที่แนะนำ (อายุ + พื้นที่)

⚠️ **AI ใช้ Auto-Targeting** — ถ้า user ขอ "เพิ่ม Interest" ในแชต AI จะตอบว่ารับทราบ แต่ form จริงไม่มีฟิลด์ Interest → คุมได้แค่ อายุ พื้นที่ เพศ OS

```
ถาม user:
"AI สรุปแบบนี้ ปรับอะไรเพิ่มไหม?
- อายุ (ตอนนี้: [X-Y])
- พื้นที่ (ตอนนี้: [list])
- เพศ (ตอนนี้: [all/M/F])

ส่วน Interest ปรับไม่ได้ใน PATH A — ถ้าจำเป็นต้อง switch ไป PATH B"
```

### Step A4: AI สร้างฟอร์ม → Cowork ตรวจ
หลังกด "สร้าง" AI generate:
- Form Campaign settings (ชื่อ, budget, ระยะเวลา)
- Targeting fields (auto-fill ตามที่คุยในแชต)
- 6 รูป recommended + 3 ชุด text recommended

### Step A5: ประกอบ Creative + บันทึก
```
Default plan สำหรับ PATH A คือ 3 creative ขั้นต่ำ ยกเว้น user ยืนยันจำนวนอื่นก่อนเริ่ม

For each Creative (ตามจำนวนที่ user confirm):
  1. อ่าน interactive elements ก่อน
  2. คลิก "เลือก" บนรูป
  3. screenshot เฉพาะ crop/preview เพราะเป็น visual QA
  4. ตัดขอบ default 1080x1080 → "อัปโหลด"
  5. คลิก radio ชื่อ + คำอธิบาย ที่จะใช้
  6. คลิก "ใช้ชิ้นงานโฆษณานี้" → counter +1
  
→ แนะนำ: บันทึก 3 ชิ้นงาน (ชุด 1, 2, 3 + รูปต่างกัน) เพื่อ A/B test
```

ถ้าระหว่างทำสร้างได้ไม่ครบจำนวนที่ confirm:
```
หยุดก่อน submit แล้วแจ้ง user:
"ตอนแรกตกลงไว้ [N] creative แต่ตอนนี้สร้างได้ [M] creative เพราะ [เหตุผล]
จะให้ผมส่งด้วย [M] ชิ้นงานเลย หรือแก้/สร้างเพิ่มให้ครบ [N] ก่อนครับ?"
```

ห้ามลดจำนวน creative/ad set จากแผนเองโดยไม่ confirm

### Step A6: ตรวจ Targeting + Submit
```
1. คลิก "แก้ไข" พื้นที่ → เลือกจังหวัดตามแผน
2. ตรวจ อายุ / เพศ / OS
3. ดู audience size — ถ้า > 10M ลองแคบลง
4. สรุปจำนวน creative จริง + budget + CPF/bid/cost cap + targeting
5. รอ user พิมพ์ "ยืนยัน"
6. คลิก "บันทึกโฆษณา ([N])"
```

---

## PATH B — Cowork Manual

*โหลด knowledge/interest-catalog.md และ knowledge/bidding-strategy.md เพิ่ม*

### PATH B Entry Mode

ก่อนกรอก manual form ให้ user เลือกวิธีทำ:

```
Manual form มีหลายช่องครับ อยากทำแบบไหนดี?

1. กรอกเองบนหน้าเว็บ — ประหยัด token/เร็วกว่า ผมช่วยบอกช่องสำคัญและตรวจก่อน submit
2. ให้ผมถามในแชทแล้วกรอกให้ — ง่ายกว่า แต่ใช้ token/เวลามากกว่า

แนะนำ: ถ้าข้อมูลพร้อมและอยากประหยัด เลือก 1 ครับ
```

บันทึกเป็น `campaign_entry_mode`:
- `SELF_FILL` = user กรอก campaign/ad set/ad เอง, Cowork ช่วยนำทาง + checklist + ตรวจ preview/error
- `AI_ASSISTED` = Cowork ถามข้อมูลในแชท, สรุปให้ user ยืนยัน, แล้วกรอก form เป็น batch

ถ้า user ไม่แน่ใจ ให้ default เป็น `SELF_FILL` สำหรับ PATH B เพราะ form ยาวและกิน token ง่าย

ทั้งสอง mode ยังต้องรอ user confirm ชัดเจนก่อน submit/publish หรือ action ที่ใช้เงิน

### Step B1: Campaign
```
Navigate: admanager → "+ สร้างแคมเปญ" (ปุ่มเขียวซ้าย — ไม่ใช่ AI)
กรอก:
  - วัตถุประสงค์: [map จาก Q2 — รวม Conversion ที่ AI Agent ทำไม่ได้]
  - ชื่อ: [auto-generate]
  - งบ: [จาก Q3 — user ระบุเท่านั้น ห้ามเดา]
```

ถ้า `campaign_entry_mode = SELF_FILL`:
- แสดง checklist compact ของ field สำคัญ
- เปิดหน้าให้ user กรอกเอง
- หลัง user บอกว่าเสร็จ ให้ Cowork อ่าน interactive/DOM เพื่อตรวจ required field/error

ถ้า `campaign_entry_mode = AI_ASSISTED`:
- สรุป field ที่จะกรอก และรอ user confirm
- กรอกหลายช่องเป็น batch ด้วย ref/form input
- อ่าน interactive/DOM หลัง major step แทน screenshot

### Step B2: Ad Sets — สร้าง 3 set ตามกลยุทธ์

**Ad Set A — Broad:**
```
Audience: ประเทศ + อายุ + เพศ (ไม่จำกัด interest)
Bidding: Auto / Lowest CPF
```

**Ad Set B — Interest:**
```
Audience: + Interest categories (3-5 หมวด)
Bidding: Manual CPF based on user-confirmed bid/cost cap
```

**Ad Set C — Custom/Lookalike:**
```
ถาม: "มีเบอร์โทร/อีเมลลูกค้าเก่าไหม? ถ้ามีกี่ราย?"
→ < 1,000 records: ข้าม set นี้ (ไม่พอสร้าง audience)
→ ≥ 1,000: upload + สร้าง Lookalike 1-3%
```

Sensitive upload rule:
- Custom Audience ที่มีเบอร์โทร/อีเมลลูกค้า ให้ default เป็น `SELF_FILL`
- Cowork ห้ามอ่าน/คัดลอก/สรุปข้อมูลในไฟล์ลูกค้า
- Cowork ช่วยได้เฉพาะนำทาง, บอก format, ตรวจว่า upload สำเร็จหรือมี error
- ถ้า user ขอให้ AI-assisted ในขั้นนี้ ให้ยืนยันว่าไม่มีข้อมูล sensitive ที่ต้องให้ AI อ่าน

### Step B3-4: Creative + Copy

ก่อน upload/crop creative ให้เลือก mode เฉพาะถ้าต้องทำหลายชิ้นหรือ user อยากประหยัด token:

- `SELF_FILL`: user เลือกรูป/ครอปเอง, Cowork ตรวจ preview ก่อน submit
- `AI_ASSISTED`: Cowork ช่วยเลือกรูป/ข้อความ, ใช้ screenshot เฉพาะ crop/preview เพราะเป็น visual QA

Default:
- ถ้า user มีไฟล์/ข้อความพร้อม -> `SELF_FILL`
- ถ้า user อยากให้ช่วยเลือก creative/copy -> `AI_ASSISTED`

---

## PHASE 3 — FINAL REVIEW

```
═══════════════════════════════
📋 สรุปก่อน Submit
═══════════════════════════════
📁 Campaign: [ชื่อ] | ฿[X]/วัน | [Objective]
💸 Bid/Cost cap: [ตัวเลขจาก user หรือ Auto ถ้ารองรับ]
👥 Ad Set(s): [จำนวน] | [targeting summary]
🎨 Ad(s): [จำนวนที่ตกลง] | [จำนวนที่สร้างจริง] | [format] | [URL]
═══════════════════════════════
[ ✅ ยืนยัน สร้างเลย ] [ ✏️ แก้ไข ]
```

ถ้า `จำนวนที่สร้างจริง` ไม่เท่ากับ `จำนวนที่ตกลง`:
- ห้าม submit
- ถาม user ว่าจะส่งเท่าที่มี หรือให้สร้างเพิ่ม/แก้ก่อน

---

## PHASE 4 — POST-SUBMIT

```
✅ Campaign: [ชื่อ] — สร้างแล้ว
✅ Ad Set(s): [จำนวน] sets — สร้างแล้ว
⏳ Ad(s): [จำนวน] ชิ้นงาน — รอ LINE ตรวจสอบ (~24 ชั่วโมง)
```

เสนอ Schedule Report (MODE 3) ทันที

---

## ERROR HANDLING

**LINE AI Agent error:**
```
แจ้ง user → switch PATH B โดยใช้ข้อมูลที่เก็บไว้จาก INTAKE
```

**Ad Reject:**
```
อ่าน rejection reason → แปลภาษาไทย → แนะนำวิธีแก้
แก้ได้ → resubmit | แก้ไม่ได้ → alternative
```

**Auto-Targeting ไม่ delivery (Friend Added 0):**
```
หลัง 24-48 ชม.:
- Impression > 0 + Friend = 0 → CPF max ต่ำเกิน → ขยับขึ้น
- Impression = 0 → audience แคบเกิน หรือ ad ยังไม่ approve
```

---

## 🆕 TOKEN OPTIMIZATION (สำหรับ Cowork Agent)

ลด token ใช้ตอน execute workflow:

### 1) Browser Interaction
```
✅ อ่านหน้าแบบ interactive/DOM ก่อน screenshot
   → ได้ ref_X/label ของปุ่มโดยไม่ต้องอ่านภาพทั้งหน้า
   
✅ Batch action ที่ปลอดภัย เช่น click + wait + read_page
   → 1 round trip vs 3 round trips
   
✅ find() แทน screenshot เมื่อรู้ว่าหา element ชื่ออะไร
   → return ref_X อย่างเดียว ไม่มีภาพ
   
❌ หลีกเลี่ยง: screenshot หลัง action ทุกครั้งโดยไม่จำเป็น
   → ใช้ screenshot เฉพาะ visual QA, preview ก่อน submit, error
```

### 2) Text Output
```
✅ Compact tables แทน bullet lists ยาวๆ
✅ ใช้ "1 หรือ 2?" แทน [A] [B] [C] [D] เมื่อตัวเลือกมีแค่ 2
✅ ตัด re-quote AI response ที่ user เพิ่งเห็นในหน้าจอ
✅ ตัด preamble "ได้เลยครับ" / "เริ่มเลย" ที่ไม่จำเป็น

❌ หลีกเลี่ยง: long markdown tables ที่มี 5-6 columns
❌ หลีกเลี่ยง: emoji ทุกบรรทัด — ใช้เฉพาะตอน highlight สำคัญ
```

### 3) Decision Points
```
✅ Default + opt-out: "จะใช้ A นะครับ พิมพ์ 'B' ถ้าไม่ต้องการ"
   → ถ้า user เห็นด้วยก็ตอบสั้นๆ ได้
   
✅ Bundle confirmations: "ยืนยัน targeting + creative + budget?"
   → 1 confirm vs 3 confirms
   
❌ หลีกเลี่ยง: ถามทุก step เล็กๆ ที่ user ไม่จำเป็นต้องตัดสินใจ
```

### 4) Read File เฉพาะที่ต้องการ
```
✅ Read 02-campaign.md เท่านั้นเมื่อ MODE 2
✅ ไม่ load knowledge files ทั้งหมดล่วงหน้า
   → load interest-catalog.md เฉพาะตอนถึง PATH B Step B2
   → load bidding-strategy.md เฉพาะตอนตั้ง bid manual
```

---

## NOTES สำหรับ Cowork Agent

1. **Method choice required** — ต้องให้ user เลือก AI Agent หรือ Manual Audience ก่อนสร้าง campaign จริง
2. **PATH A = 3 obj + auto target** — ห้ามสัญญา feature ที่ไม่มี
3. **Money inputs required** — งบและ CPF/CPA/bid cap ห้าม assume ต้องมาจาก user เท่านั้น
4. **Creative count integrity** — ถ้าทำไม่ครบจำนวนที่ตกลง ห้ามลดเอง ต้องถาม user
5. **3 Ad Set rule** — แจ้งให้ user รู้แต่ไม่บังคับ ขึ้นกับ data + งบ
6. **Token discipline** — batch + minimal screenshot
7. **เช็ค duplicate ก่อนสร้าง** — บัญชีอาจมี campaign เดียวกันอยู่แล้ว

---

*Version 2.0 | May 2026*
*Updated:*
*- เพิ่ม PATH A constraints (3 obj, auto-targeting only)*
*- เพิ่ม PHASE 0 Method Choice*
*- เพิ่ม Ad Set Strategy section (1 vs 3 sets)*
*- เพิ่ม Token Optimization guide*
*- เพิ่ม Money Safety Rules: ห้าม assume งบ/CPF/CPA/bid cap*
*- เพิ่ม Creative count integrity rule*
