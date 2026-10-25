# workflows/03-report-schedule.md
# LINE Ads Report + Scheduled Tasks Workflow
# Version 4.0 | October 2026 | MCP-first + spend cap

## Entry Point — บทที่ 5

เริ่มจากประโยคเดียว เช่น “ช่วยสรุปผลโฆษณาเมื่อวาน และรายงานทุกเช้า” AI ดึงบัญชี/ชื่อ/IDs/objective ผ่าน MCP เอง ไม่ให้ผู้อ่านเตรียม แนบ หรือเขียนไฟล์

ถามทีละเรื่องเฉพาะสิ่งที่บัญชีตอบไม่ได้: ขอบเขตที่กำกวม, เวลา/ความถี่, cap และช่วงเวลาที่ cap ครอบคลุม ห้ามเดาเงินจาก daily budget หรือถือว่า budget เท่ากับ owner cap

ใช้ MCP เป็น default; browser เฉพาะ account/login issue หรือข้อมูลที่ API ไม่มี ห้ามเปลี่ยน budget/bid/status จาก workflow รายงาน

## Knowledge Loading Gate

- อ่าน workflow นี้และ `knowledge/report-metrics.md` ก่อนดึง/สรุปผล
- อ่าน `knowledge/kpi-benchmarks.md` เมื่อต้องวิเคราะห์ตามคำขอทันที (on-demand) เท่านั้น ไม่ใส่ benchmark alerts ใน scheduled task
- ถ้าจะปรับโฆษณา ให้ส่งต่อ `workflows/04-optimize.md` และขอ approval ใหม่

## Phase 1 — รายงานทันที

1. ใช้ `list_campaigns(status=None, fetch_all=True)`, `list_adsets(campaign_id=None, status=None, fetch_all=True)` และ `list_ads(adset_id=None, campaign_id=None, status=None, fetch_all=True)` เพื่อ resolve IDs ที่ต้องใช้ แต่ละ list อ่านทุกหน้าและกรอง ACTIVE/PAUSED/REMOVED ได้
2. เมื่อวานใช้ `get_daily_report` (ระดับ AD เป็น default); ช่วงอื่นใช้ `get_report(level="CAMPAIGN"|"ADGROUP"|"AD", start_date=..., end_date=..., campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)` หรือ `get_weekly_report(by_day=False)`
3. ต้องการรายวันใช้ `by_day=True` = หนึ่งแถวต่อวัน×entity สูงสุด 93 วันต่อคำขอ แบ่งช่วงเมื่อเกิน ตรวจ `paging.complete` ก่อนสรุป
4. บอกช่วงวันที่และ `date_basis: "UTC"` เสมอ วันรายงานไม่ใช่ Asia/Bangkok; เวลาแจ้งเตือนอาจเป็น Asia/Bangkok (+07:00) แต่ห้ามเปลี่ยนป้ายวันของ API
5. สรุปตาม objective เท่านั้น: GAIN_FRIENDS ดู CPF/Friends, VISIT_MY_WEBSITE ดู CTR/CPC, VIDEO_VIEW ดู VTR/CPV, REACH ดู CPM/Reach/Frequency, APP_INSTALL ดู CPI และ WEBSITE_CONVERSION ดู CV/CPA/ROAS เมื่อมีข้อมูล ห้ามใช้ CV/CPA/ROAS ตัดสิน objective อื่น

Summary keys ของ `get_report`: `total_spend`, `total_clicks`, `total_impressions`, `total_cv`, `avg_ctr` (%), `avg_cpc`, `avg_cpm` ค่า `None` เมื่อไม่มีตัวหารให้แสดง “คำนวณไม่ได้” ไม่แทนด้วยศูนย์ ไม่เดา metrics ที่ response ไม่มี

```text
รายงาน LINE Ads — [start_date ถึง end_date, UTC]
- Campaign: [ชื่อ/ID] | Objective: [objective]
- ใช้จ่าย: [ค่าจริง + สกุลเงิน] | Impressions: [ค่าจริง]
- ผลลัพธ์และต้นทุนตาม objective: [ค่าที่มีจริง]
- ความครบถ้วน: [paging.complete / ข้อจำกัดข้อมูล]
```

Read-only เรียกได้เลย หาก user ขอวิเคราะห์เพิ่ม ค่อยใช้ benchmark และ `get_entity`/`get_ad_status(ad_id)` ด้วย exact ID; `NOT_APPROVED` คือ review rejected ข้อมูลน้อยให้บอกข้อจำกัด ไม่ปรับเอง

## Phase 2 — ตั้ง Schedule

ใช้ **Cowork Schedule tab** (บาง UI ใช้ชื่อ Scheduled) หรือ **`/schedule`** ไม่มี scheduler MCP tool และไม่ใช้ cron ให้ AI เตรียม prompt/เวลาในแชทแล้วสร้างผ่านความสามารถ Schedule ที่มีจริง หากไม่มีสิทธิ์/เข้า UI ไม่ได้ ให้แสดง prompt และบอกว่ายังไม่ได้ตั้ง ห้ามอ้างว่าตั้งสำเร็จ

งานที่ต้องใช้ local files/apps รวมถึงการเก็บ CSV บนเครื่อง **รันเฉพาะเครื่อง local** ต้องให้เครื่องและ local runtime พร้อมใช้งาน อย่าสัญญาว่าจะรันบน cloud เมื่อปิดเครื่อง อ้างอิง [Schedule recurring tasks in Claude Cowork](https://support.claude.com/en/articles/13854387)

ก่อนตั้ง ให้สรุปและขอ “ยืนยัน”:

- ชื่อ task, เวลา/ความถี่ + timezone ของ schedule เช่น 09:00 Asia/Bangkok (ตัวอย่างสมมติ), campaign scope
- owner cap ที่ผู้ใช้บอก พร้อมช่วงวันที่ UTC และ `period_end` ถ้าต้องการ projection; ถ้ายังไม่มีให้ถามก่อนตั้ง cap alert
- เก็บประวัติหรือไม่: เป็น optional เฉพาะ scheduled task บทนี้ ถ้าเลือก ให้ใช้ `workspace_dir` ที่ได้รับสิทธิ์ AI สร้าง/ดูแลไฟล์เอง ไม่ให้ผู้อ่านเตรียม CSV

CSV เป็น write: ก่อนเปิดใช้ ทำ `sync_ad_daily_csv(..., dry_run=True)` สรุป path/ช่วงวันที่/การ upsert แล้วรอ “ยืนยัน” ให้ชัดว่าครอบคลุมการ sync ทุก run ตามขอบเขตนี้ จึงตั้ง prompt ให้ `dry_run=False` ได้ หากเปลี่ยน path/scope ต้อง dry-run และขอยืนยันใหม่ ไม่มี approval นี้ให้ข้ามการ sync

## Phase 3 — Scheduled-task Prompt

AI เติมช่องว่างจากข้อมูลบัญชีและคำตอบที่ยืนยันแล้วในแชท ไม่ให้ผู้อ่านสร้างไฟล์ prompt ระบุสูตรช่วงวันที่ให้คำนวณใหม่ทุก run ไม่ตรึงวันที่ตัวอย่างไว้

```text
คุณคือ LINE Ads Report Agent ใช้ MCP ดึงข้อมูลเอง ห้ามเดาข้อมูลหรือเงิน

Context ที่ยืนยันแล้ว:
- บัญชี: [account ID] | Campaign scope: [ID หรือทั้งบัญชี]
- Objective: [จากบัญชี; refresh เมื่อจำเป็น]
- Schedule: [ความถี่/เวลา/timezone]
- Report window: [เมื่อวาน UTC หรือสูตรช่วงวันที่ UTC ที่ตกลง]
- Owner cap: [จำนวน + สกุลเงินจากผู้ใช้]
- Cap window: [สูตร start_date/end_date UTC ที่ cap ครอบคลุม]
- period_end: [วันที่ UTC ที่ตกลงสำหรับ projection หรือไม่ส่ง]
- CSV history: [ปิด หรือเปิดพร้อม workspace_dir ที่ได้รับสิทธิ์]
- CSV approval: [ขอบเขต/การอนุมัติ sync แบบเกิดซ้ำ หรือยังไม่ได้อนุมัติ]

ทุก run ทำตามลำดับ:
1. คำนวณวันที่ UTC ของ run นี้ ใช้ get_daily_report สำหรับเมื่อวาน (AD เป็น default)
   หรือ get_report(level="AD", start_date=..., end_date=..., fetch_all=True, by_day=True)
   ตามขอบเขตที่ตกลง; กรอง campaign_id เมื่อกำหนด แบ่งคำขอไม่เกิน 93 วัน
2. ตรวจ paging.complete และ date_basis="UTC" สรุปสั้นเป็นไทย:
   ช่วงวันที่ UTC, scope, spend, impressions, clicks และผลลัพธ์/ต้นทุนตาม objective
   None = คำนวณไม่ได้; ข้อมูลไม่ครบให้บอก ห้ามใช้ CV/CPA/ROAS กับ objective อื่น
3. เรียก check_spend_cap(cap_amount=[owner cap], start_date=[cap start],
   end_date=[cap end], campaign_id=[ถ้ากรอง], period_end=[ถ้าตกลง])
   - status="exceeded": แจ้งเตือนใช้จ่ายเกิน cap พร้อม spend/cap/ส่วนเกินจริง
   - status="within_cap": สรุปตามปกติ ไม่แจ้งเตือน; spend เท่ากับ cap ไม่ถือว่าเกิน
   - status="indeterminate": บอกว่าข้อมูลไม่ครบ ยังยืนยันการเกิน cap ไม่ได้
   แสดง per-campaign spend/optional projection ตาม response เท่านั้น
   projection ไม่ใช่ยอดจริงและไม่ใช้เป็นเหตุแจ้งเตือนเพิ่ม
4. ถ้า CSV history เปิดและมี recurring approval ครบแล้ว จึงเรียก
   sync_ad_daily_csv(start_date=[report start], end_date=[report end],
   workspace_dir=[approved path], campaign_id=[ถ้ากรอง], dry_run=False)
   รายงานผล sync พร้อม readback/readback_ok ที่คืนมา ตรวจผลบันทึกก่อนบอกว่าสำเร็จ
   ถ้าอ่านกลับไม่ได้หรือ sync ล้มเหลวให้บอกตรง ๆ ว่ายังยืนยันการเก็บไม่ได้

แจ้งเตือนเฉพาะ check_spend_cap status exceeded เท่านั้น ไม่มี alerts เรื่อง benchmark,
creative rejection, delivery, result=0 หรือ pace ใน task นี้
ห้าม pause/resume/update/create โฆษณาอัตโนมัติ แม้เกิน cap
ห้ามเขียนไฟล์อื่นหรือขอให้ผู้อ่านเตรียม/แนบไฟล์
```

`check_spend_cap` อ่านอย่างเดียว: spend > cap เท่านั้นคือ exceeded ไม่ pause เอง; ถ้าข้อมูลไม่ครบเป็น indeterminate ไม่อนุมานว่าอยู่ใน cap

`sync_ad_daily_csv` upsert `line-ads-data/ad_daily.csv` ด้วย key `date+ad_id` (16 columns: date, account_timezone, campaign_id, campaign_name, objective, adgroup_id, adgroup_name, ad_id, ad_name, impressions, clicks, spend, currency, results, result_type, pulled_at) และบันทึก `run_log.csv`; ผู้อ่านไม่ต้องสร้างไฟล์ก่อน

## Phase 4 — ตรวจ Schedule และจัดการต่อ

แจ้ง “ตั้งแล้ว” เฉพาะเมื่อ Schedule ยืนยันสำเร็จ พร้อมชื่อ task, เวลา/timezone, scope, owner cap/ช่วง cap, วันที่ข้อมูลเป็น UTC, CSV เปิด/ปิด และข้อจำกัด local หากมี ตรวจ run แรกจากผลจริง ไม่อ้างว่าได้รายงานก่อนรัน

จัดการ pause/resume/edit/delete/run now ที่ Schedule tab หรือ `/schedule` ตามสิ่งที่ UI รองรับ การหยุด task รายงานไม่ใช่การ pause โฆษณา ถ้าอยากปรับโฆษณาจากผล ให้ไป MODE 4

## Error Handling

- API error/permission/rate limit: แจ้งข้อผิดพลาดจริง ไม่อ้างยอดศูนย์หรือสรุปว่ายังอยู่ใน cap
- `paging.complete=false` หรือข้อมูลขาด: สรุปข้อจำกัด; cap indeterminate ต้องบอกว่ายังตรวจไม่ได้
- CSV write ไม่สำเร็จ: แยกผลรายงานกับผลบันทึก ไม่ให้ผู้อ่านเตรียมไฟล์แทน
- Schedule/local runtime ไม่พร้อม: บอกว่ายังรันไม่ได้ ตรวจสถานะผ่าน Schedule ไม่สัญญาว่าจะ catch up โดยไม่มีผลยืนยัน
