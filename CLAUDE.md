# LINE Ads Cowork — Project Instructions

> **Single source of truth: `AGENTS.md`** — โหลดและใช้ rules ทั้งหมดจากไฟล์นั้น
> ไฟล์นี้เก็บแค่ greeting + routing เพื่อความเร็วในการเริ่ม session

---

## Greeting

> สวัสดีครับ! วันนี้อยากให้ช่วยเรื่องอะไรครับ?
> [ เปิดบัญชีใหม่ ] [ สร้างโฆษณา ] [ ดูผล/ตั้งรายงาน ] [ ปรับโฆษณา ]

---

## Routing

| MODE | Trigger | Workflow |
|---|---|---|
| 1 | เปิดบัญชี, สมัคร LINE Ads | `workflows/01-account-setup.md` |
| 2 | สร้างโฆษณา, ยิงแอด | `workflows/02-campaign.md` |
| 3 | ดูผล, ตั้งรายงาน, เช็คผล | `workflows/03-report-schedule.md` |
| 4 | ปรับโฆษณา, optimize, ผลไม่ดี | `workflows/04-optimize.md` |

โหลด workflow file เฉพาะ MODE ที่ active เท่านั้น

---

## File Map

```
AGENTS.md              → rules ทั้งหมด (browser, money, confirmation, traps, self-audit)
workflows/01-04.md     → flow แต่ละ MODE (โหลดเฉพาะที่ active)
knowledge/*.md         → reference (โหลดตอน step ที่ใช้)
```

ดูรายละเอียดใน `AGENTS.md`
