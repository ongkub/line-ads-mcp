# knowledge/ad-specs.md
# LINE Ads Format Specifications
# โหลดเฉพาะตอน ad creation / creative upload check

---

## Recommended Format per Objective

| Objective | แนะนำ | หมายเหตุ |
|---|---|---|
| GAIN_FRIENDS | Image 1:1 | Square เด่นใน feed และเหมาะกับ CTA เพิ่มเพื่อน |
| WEBSITE_TRAFFIC | Image 1.91:1 หรือ Carousel | Carousel ใช้เมื่อมีหลาย pain point/offer |
| CONVERSIONS | Image 1:1 หรือ Carousel | ใช้ format ที่เห็น offer และ proof ชัด |
| REACH | Image 1.91:1 | เหมาะกับ reach/CPM และ message กว้าง |
| APP_INSTALL | Image 1:1 หรือ Video 1:1 | แสดง app screen หรือ use case สั้น ๆ |
| VIDEO_VIEW | Video 1:1 หรือ 16:9 | แนะนำ 15-30 วินาทีสำหรับ performance |

## Image Ad
- Format: JPG, PNG
- Aspect ratio: 1.91:1 (1200×628px) หรือ 1:1 (1080×1080px)
- ขนาดไฟล์: ≤ 10MB ต่อภาพ
- ข้อความในรูป: ≤ 20% ของพื้นที่ภาพ

## Small Image Ad
- Format: JPG, PNG
- ขนาดไฟล์: ≤ 10MB ต่อภาพ
- Recommended image size: 600×400px

## Video Ad
- Format: MP4, MOV
- ขนาดไฟล์: ≤ 1GB ต่อวิดีโอ
- ความยาว: ≤ 600 วินาที (แนะนำ 15–30 วินาทีสำหรับ performance)
- Aspect ratio / resolution:
  - 1:1 — 600–1280 × 600–1280px
  - 16:9 — 240–1920 × 135–1080px
  - 9:16 — 135–1080 × 240–1920px

## Small Video Ad
- Format: MP4, MOV
- ขนาดไฟล์: ≤ 1GB ต่อวิดีโอ
- ความยาว: ≤ 600 วินาที
- Aspect ratio / resolution:
  - 1:1 — 600–1280 × 600–1280px
  - 16:9 — 240–1920 × 135–1080px

## Carousel Ad
- จำนวนภาพ: 2–10 ภาพ
- แต่ละภาพ: 1:1 (1080×1080px)
- Format: JPG, PNG
- ขนาดต่อภาพ: ≤ 10MB
- Maximum: 10 cards

## Animation Ad
- Format: PNG (APNG)
- ขนาดไฟล์: ≤ 300KB ต่อ animated image
- Image size: 600×400px
- ความยาว: 1–4 วินาที
- Frames: 5–20
- Loops: 1–4

---

## Error Messages และวิธีแก้

| Error | สาเหตุ | แก้ไข |
|---|---|---|
| File too large | รูปเกิน 10MB หรือวิดีโอเกิน 1GB | Compress ไฟล์หรือลด resolution |
| Wrong aspect ratio | สัดส่วนไม่ตรง | Crop ให้ได้ 1.91:1 หรือ 1:1 |
| Too much text | ข้อความเกิน 20% | ลดข้อความในรูป |
| Unsupported format | ไฟล์ไม่ใช่ JPG/PNG/MP4/MOV | Convert ไฟล์ก่อน |
