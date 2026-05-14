# knowledge/interest-catalog.md
# LINE Ads Interest Catalog Router

ไฟล์นี้เป็น compatibility shim เท่านั้น เพื่อไม่ให้ agent โหลด catalog เต็มโดยไม่จำเป็น

## Load Order

1. อ่าน `knowledge/interest-catalog-INDEX.md` ก่อนเสมอ
2. ถ้า INDEX มี code เพียงพอ ให้ใช้ได้เลย
3. ถ้าต้องการรายละเอียดเพิ่ม ค่อยโหลด detail file เฉพาะหมวด:
   - `knowledge/interest-detail-interests.md`
   - `knowledge/interest-detail-business-commerce.md`
   - `knowledge/interest-detail-lifestyle-consumer.md`
   - `knowledge/interest-detail-line-signals.md`
4. เรียก `list_advanced_targeting_codes` เฉพาะเมื่อ detail files ไม่มี, objective/country/locale เปลี่ยน, API reject code, หรือต้องการ audience size ล่าสุด

## Why

ไม่ควรโหลด catalog เต็มก่อนถาม user เรื่อง audience เพราะสิ้นเปลือง token โดยไม่จำเป็น
INDEX ให้ภาพรวมพอสำหรับแนะนำ user ส่วน detail files ใช้เมื่อ user เลือกหมวดหรือต้องการ niche code
