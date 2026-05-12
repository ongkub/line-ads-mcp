# knowledge/ad-specs.md
# LINE Ads Format Specifications
# โหลดเฉพาะตอน ad creation / creative upload check

---

## Image Ad
- Format: JPG, PNG, GIF (static)
- Aspect ratio: 1.91:1 (1200×628px) หรือ 1:1 (1080×1080px)
- ขนาดไฟล์: ≤ 30MB
- ข้อความในรูป: ≤ 20% ของพื้นที่ภาพ

## Video Ad
- Format: MP4, MOV
- ขนาดไฟล์: ≤ 500MB
- ความยาว: 5–60 วินาที (แนะนำ 15–30 วิ)
- Aspect ratio: 16:9, 1:1, หรือ 9:16
- Resolution: ≥ 720p

## Carousel Ad
- จำนวนภาพ: 2–10 ภาพ
- แต่ละภาพ: 1:1 (1080×1080px)
- Format: JPG, PNG
- ขนาดต่อภาพ: ≤ 30MB

## Small Image Ad (CPF)
- Aspect ratio: 1:1 (300×300px ขึ้นไป)
- Format: JPG, PNG

---

## Error Messages และวิธีแก้

| Error | สาเหตุ | แก้ไข |
|---|---|---|
| File too large | ไฟล์เกิน 30MB | Compress ภาพหรือลด resolution |
| Wrong aspect ratio | สัดส่วนไม่ตรง | Crop ให้ได้ 1.91:1 หรือ 1:1 |
| Too much text | ข้อความเกิน 20% | ลดข้อความในรูป |
| Unsupported format | ไฟล์ไม่ใช่ JPG/PNG/MP4 | Convert ไฟล์ก่อน |
