# workflows/08-customer-list-audience.md
# Customer List Audience Workflow
# Version 1.0 | October 2026 | MCP-first | MODE 8

---

## Overview

สร้างหรือปรับฐานลูกค้าจากเบอร์โทร อีเมล หรือ IFA ที่ธุรกิจมีสิทธิใช้
Trigger: “อัปโหลดเบอร์ลูกค้าไปทำกลุ่มเป้าหมาย”, “เอารายชื่อลูกค้าเก่าไปยิงโฆษณา/ยกเว้นลูกค้าเดิม”
**MODE 8 เป็นโหมดเดียวที่ผู้ใช้ต้องเตรียมไฟล์ข้อมูลลูกค้าที่ตนมีอยู่แล้ว** แล้วบอก absolute path ในเครื่องที่ MCP เข้าถึงได้ ไม่แนบไฟล์หรือวางข้อมูลลูกค้าในแชท

```text
PHASE 1 → PURPOSE + PDPA
PHASE 2 → FILE + COLUMN
PHASE 3 → DRY RUN + FIX
PHASE 4 → CONFIRM + UPLOAD
PHASE 5 → TRACK JOB + READY
PHASE 6 → USE + HANDOFF
```

## Knowledge Loading Gate

อ่าน `knowledge/customer-list-format.md` และกฎ write ใน `CLAUDE_PROJECT_PROMPT.md` ก่อนเริ่ม
ก่อนนำฐานไปสร้าง ad set หรือ LOOKALIKE อ่านหัวข้อ **Custom Audience** และ **Customer Avatar Gate** ใน `workflows/02-campaign.md`; ฐานลูกค้าไม่แทน Avatar Gate

---

## PHASE 1 — Intake & Purpose

ถามทีละเรื่อง เฉพาะข้อมูลที่ยังขาด:
1. “อยากยิงหาลูกค้าเดิม ยกเว้นลูกค้าเดิม หรือหาคนคล้ายลูกค้าเดิมครับ?”
2. “ลูกค้ายินยอม หรือธุรกิจมีฐานกฎหมายรองรับการใช้ข้อมูลติดต่อนี้เพื่อโฆษณาหรือยังครับ?”

ต้องได้รับคำตอบเรื่องสิทธิใช้ข้อมูลก่อนอ่านไฟล์ผ่าน tool ห้ามถือว่าการมีไฟล์หรือเคยซื้อสินค้าเท่ากับยินยอม
ถ้าไม่แน่ใจ ให้หยุดก่อน dry-run และแนะนำตรวจสอบกับ DPO/ฝ่ายกฎหมายของธุรกิจ; นี่ไม่ใช่คำปรึกษากฎหมาย
ใช้เฉพาะข้อมูลจำเป็นตามวัตถุประสงค์ ไม่ขอข้อมูลลูกค้าเพิ่มเพื่อให้ match มากขึ้น
บัญชีต้องมีสิทธิ์ Custom Audience; ถ้าไม่มีสิทธิ์ให้แจ้งข้อจำกัด ไม่ลองข้ามสิทธิ์

---

## PHASE 2 — File

- ขอ absolute path ของ CSV/TXT ในเครื่องที่รัน MCP เช่น `/Users/owner/Documents/customers.csv` ไม่ขอแนบไฟล์ในแชท
- ถ้าเป็น `.xlsx` ให้ผู้ใช้ export เป็น CSV UTF-8 ก่อน ไม่เปิดอ่านแถวข้อมูลลูกค้าด้วยเครื่องมืออื่น
- เลือก `id_type`: `PHONE`, `EMAIL` หรือ `IFA`; หนึ่งครั้งใช้หนึ่งชนิด ถ้ามีหลายชนิดให้แยกไฟล์/รอบ
- tool ตรวจชื่อคอลัมน์อัตโนมัติ: phone/tel/mobile/เบอร์/โทร, email/อีเมล, ifa/adid
- ถ้าชื่อคอลัมน์กำกวม ให้ถามชื่อคอลัมน์แล้วส่ง `column` ตามที่ผู้ใช้ระบุ ห้ามขอแถวตัวอย่างดิบ
- ประเทศเริ่มต้น `default_country_code="66"` (ไทย); ถ้าเป็นประเทศอื่นหรือหลายประเทศ ให้ผู้ใช้ยืนยันรหัส/แยกไฟล์ก่อน ไม่เติม 66 ให้ทุกประเทศ
- ถามชื่อฐานใหม่ (`audience_name`) หรือเลือกฐานเดิมด้วย `list_audiences()` แล้วใช้ `audience_id`; ใช้อย่างใดอย่างหนึ่ง ไม่เดา ID
- สำหรับฐานเดิม เสนอ `action="ADD"` เป็น default; `REPLACE` ต้องเป็นความต้องการชัดเจนของผู้ใช้

---

## PHASE 3 — Dry Run & Fix

ใช้ `upload_customer_list` อ่าน/ปรับรูปแบบในเครื่องเท่านั้น ไม่ใช้ shell, file reader หรือแชทแสดงเนื้อหาไฟล์ลูกค้า

```python
upload_customer_list(
    file_path=absolute_path, id_type=id_type,
    audience_name=new_name,  # ฐานใหม่; ฐานเดิมใช้ audience_id แทน
    action="ADD", column=chosen_column,
    default_country_code="66", dry_run=True
)
```

สรุปผลตามค่าที่ tool คืน ไม่คำนวณสูตรที่สมมติว่าทุก count แยกจากกัน:
- `rows_read`, `valid`, `duplicates`, `blank`, `prehashed`
- `invalid_by_reason` เรียงสาเหตุที่พบมากก่อน พร้อม `invalid_samples` เฉพาะค่าปิดบังและเลขแถว
- `file_bytes`, `within_size_limit` — จำกัด 60 MB ต่อ upload

อธิบายว่าจำนวน valid คือรายการผ่านรูปแบบ ไม่ใช่จำนวนคนที่ LINE จับคู่ได้; **match rate ยังไม่ทราบจน LINE ประมวลผล** และห้ามรับปากเปอร์เซ็นต์
PHONE/EMAIL ถูก normalize แล้ว hash SHA-256 ในหน่วยความจำ; tool ไม่คืนหรือเก็บค่าดิบ แสดงเฉพาะ masked samples
`prehashed` คือรายการที่ tool ตรวจพบว่า hash มาแล้ว ไม่ใช่การยืนยันว่าต้นทาง normalize ถูก

### แก้ในชีตต้นทาง แล้วตรวจซ้ำ

| ปัญหา | ให้ผู้ใช้แก้อะไร |
|---|---|
| เบอร์ขาด 0 นำหน้า / เหลือ 9 หลัก | ตรวจเบอร์กับต้นทาง ตั้งคอลัมน์เป็นข้อความก่อน export; ห้าม AI เดาเติมตัวเลข |
| phone/email ปนคอลัมน์ | แยกชนิดและเลือก `column` ให้ถูก |
| อีเมลผิดรูปแบบ/ยาวเกิน 120 ตัวอักษร | ตรวจต้นทาง แก้หรือนำรายการที่ยืนยันไม่ได้ออก |
| IFA ไม่ใช่ UUID | ตรวจ advertising ID ต้นทาง ไม่ใช้หมายเลขลูกค้าแทน |
| ไฟล์เกินขนาด / `within_size_limit=false` | แบ่งไฟล์ แล้ว dry-run แต่ละไฟล์; รอบต่อฐานเดิมใช้ ADD ไม่ REPLACE ซ้ำ |

ให้ผู้ใช้แก้ไฟล์ต้นทางแล้วเรียก dry-run ซ้ำจนไม่มี invalid, มี valid และผ่าน size limit; blank/duplicates ถูกตัดออก ให้แจ้งจำนวนตามจริง
ถ้าไฟล์ path/column/options เปลี่ยน ต้อง dry-run ใหม่ก่อนสรุปยืนยัน

### ตัวอย่างคำตอบ (ตัวอย่างสมมติ)

> อ่าน 1,000 แถว ผ่าน 950 รายการ ซ้ำ 20 ว่าง 10 ไม่ผ่าน 20 รายการ
> สาเหตุหลัก: เบอร์ไม่ครบหลัก เช่น แถว 18 `08******78` — ตรวจต้นทางและ export ใหม่ครับ
> ยังไม่ทราบจำนวนที่ LINE จะจับคู่ได้ และยังไม่ได้อัปโหลด

---

## PHASE 4 — Confirm & Upload

สรุปชื่อฐาน/ID, ชนิดข้อมูล, วัตถุประสงค์, คอลัมน์/ประเทศ, จำนวนรายการที่จะส่งหลังปรับรูปแบบ/ตัดซ้ำ และขนาดไฟล์
สำหรับ PHONE/EMAIL ระบุจำนวนรายการ hash ที่จะส่ง; สำหรับ IFA ระบุจำนวน UUID ไม่เรียกว่า hash

| Action | ผลกระทบที่ต้องแจ้ง |
|---|---|
| ฐานใหม่ (`audience_name`) + ADD | สร้างฐานใหม่ |
| ฐานเดิม (`audience_id`) + ADD | เพิ่มรายการเข้าไปในฐานเดิม |
| ฐานเดิม (`audience_id`) + REPLACE | **แทนที่สมาชิกเดิมทั้งหมด** ด้วยรายการในไฟล์นี้ |

ถาม “ยืนยันอัปโหลดตามสรุปนี้ไหมครับ?” แล้ว **รอผู้ใช้พิมพ์ “ยืนยัน”** ก่อนส่งจริง
REPLACE ต้องระบุชื่อ/ID และผลว่าลบสมาชิกเดิมทั้งหมดในสรุป และได้รับอนุมัติ REPLACE ชัดเจน ไม่ใช้คำยืนยันของ ADD แทน
ถ้าผู้ใช้แก้ไฟล์หรือเปลี่ยน action/ฐาน/จำนวนหลังยืนยัน ให้ dry-run และขอยืนยันใหม่

```python
upload_customer_list(
    file_path=absolute_path, id_type=id_type,
    audience_id=existing_id,  # ฐานใหม่ใช้ audience_name แทน
    action=confirmed_action, column=chosen_column,
    default_country_code=confirmed_country_code,
    dry_run=False, workspace_dir=workspace_dir
)
```

ส่ง `workspace_dir` ที่ใช้งานอยู่เพื่อบันทึก `line-ads-data/change_log.jsonl` (fallback `LINE_ADS_WORKSPACE_DIR` ตามกฎหลัก); ไม่บันทึกค่าดิบใน log
tool ส่ง multipart ไป `POST custom-audiences/upload`; ตรวจ response/ID จริงและ readback ที่คืนมา ไม่อ้างว่า READY เพียงเพราะรับ upload แล้ว
ฐานใหม่เริ่ม `IN_PROGRESS`; ถ้า timeout/ผลไม่ชัด ให้ตรวจสถานะก่อน retry ไม่ส่งซ้ำอัตโนมัติ โดยเฉพาะ REPLACE

---

## PHASE 5 — Track

```python
get_customer_list_upload_status(audience_id=uploaded_audience_id)
```

- ตรวจ `jobs` และ `job_status`: `QUEUED` / `WORKING` ยังรอ, `FINISHED` ประมวลผลงานเสร็จ, `FAILED` ล้มเหลว
- เรียกติดตามเป็นระยะจน `done=true` ไม่วนถี่; ถ้ายังไม่จบในรอบสนทนานี้ แจ้งว่ารอและติดตามต่อ ไม่รายงานว่าสำเร็จ
- แสดง `audience_count` ตามที่คืนจริง ไม่ถือว่าเท่าจำนวน valid หรือคำนวณ match rate จากคนละฐานนับ
- ถ้า FAILED แสดง `failed_type` ตามจริง พร้อมแนวแก้ตาม error; ไม่เดาสาเหตุหรือ upload ซ้ำโดยไม่ยืนยัน
- หลังงานเสร็จ เรียก `list_audiences()` ตรวจ ID เดิมซ้ำเป็นระยะจน `status="READY"` และ `usable_in_adset=true`; งาน FINISHED ไม่แทนสถานะ READY
- แสดง `estimated_audience_size`: `"-"` = เล็กเกินรายงาน, `"100 or fewer"` = ไม่เกิน 100 คน ไม่เติมเป็น 0 หรือ 100 แน่นอน
- ถ้าฐานล้มเหลว/ใช้ไม่ได้ ให้แจ้ง status และพักขั้นใช้ฐาน ไม่วนรอ READY โดยไม่ดู error

---

## PHASE 6 — Use & Handoff

ส่ง ID จริง, ชื่อ, status, `estimated_audience_size`, `usable_in_adset` และวัตถุประสงค์ต่อในแชทเดิม:
- ยิงหาลูกค้าเดิม → MODE 2 ใช้ `custom_audience_ids`
- ยกเว้นลูกค้าเดิม → MODE 2 ใช้ `excluded_audience_ids`
- หาคนคล้าย → เมื่อฐานต้นทาง READY/ใช้ได้แล้ว เสนอ `create_audience(name, function_type="LOOKALIKE", config=..., dry_run=True, workspace_dir=...)` โดยตรวจ source ID/config จริงและถาม size ratio; สรุป → รอ “ยืนยัน” → `dry_run=False` → ตรวจ readback แล้วรอ LOOKALIKE READY ผ่าน `list_audiences()` เช่นกัน

ก่อนสร้าง LOOKALIKE/เลือก targeting ให้ผ่าน Customer Avatar Gate ตาม workflow 02; การยืนยัน upload ไม่อนุมัติการสร้าง LOOKALIKE หรือ ad set
MODE 2 ส่ง IDs ชุดเดียวกันให้ `estimate_adset_reach` และ `create_adset` และทำ dry-run/ยืนยันใหม่ตาม workflow 02
GAIN_FRIENDS ยังต้องยกเว้น active friends audience ที่ READY/ใช้ได้ ไม่ใช้รายชื่อลูกค้าแทนโดยอัตโนมัติ

## ห้าม

1. ห้ามวางหรือขอให้ paste ข้อมูลลูกค้าในแชท
2. ห้ามขอแนบไฟล์ข้อมูลลูกค้าดิบในแชท; ใช้ path ในเครื่องผ่าน tool เท่านั้น
3. ห้ามแสดงค่าดิบในคำตอบ/log/ตัวอย่าง; ใช้ masked samples จาก tool
4. ห้าม upload จริงโดยไม่มีคำว่า “ยืนยัน” หลัง dry-run
5. ห้ามเดาความยินยอมหรือฐานกฎหมาย
6. ห้าม REPLACE โดยไม่มีอนุมัติแทนที่สมาชิกเดิมทั้งหมดอย่างชัดเจน
7. ห้ามใช้ฐาน IN_PROGRESS หรือเดา ID/ขนาด/match rate
