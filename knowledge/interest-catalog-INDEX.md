# knowledge/interest-catalog-INDEX.md
# LINE Ads Advanced Targeting Index
# โหลดเสมอเมื่อถึงขั้นเลือก audience/interest; ไฟล์นี้เล็กและใช้แนะนำ user ก่อนโหลด detail

---

## Context

- Verified for `campaignObjective=GAIN_FRIENDS`, `country=TH`, `locale=th`
- Source: LINE Ads API `/codes/advanced-targeting`
- Last verified: 2026-05-13
- Full selectable cache split into detail files: 54 interests, 201 behaviors, 12 purchase intents

## How To Load

1. อ่านไฟล์นี้ก่อนเสมอเพื่อแนะนำหมวด/strategy ให้ user
2. ถ้า code ใน common mapping หรือ top-level table พอ ให้ใช้ได้เลย
3. ถ้า user ขอ niche/sub-code ให้โหลด detail file เฉพาะหมวดที่เกี่ยวข้อง
4. เรียก `list_advanced_targeting_codes` เฉพาะเมื่อ cache ไม่มี, objective/country/locale เปลี่ยน, API reject code, หรือต้องการ audience size ล่าสุด

## Detail Files

| Detail file | ใช้เมื่อ | Content |
|---|---|---|
| `knowledge/interest-detail-interests.md` | ต้องการ sub-interest หรือ purchase intent | Interests 54 + purchase intents 12 |
| `knowledge/interest-detail-business-commerce.md` | B2B, finance, ecommerce, device/app, affluence | Business/commerce behaviors |
| `knowledge/interest-detail-lifestyle-consumer.md` | beauty, food, travel, home, sports, entertainment | Lifestyle/consumer behaviors |
| `knowledge/interest-detail-line-signals.md` | LINE OA follower, OpenChat, LINE TODAY, LINE services | LINE ecosystem behaviors |

## Customer Avatar → Interest Mapping (Need / Ability / Life Stage)

ก่อน map ต้องมี `customer_avatar` จาก `workflows/02-campaign.md` → Customer Avatar Gate ห้าม map ตรงจาก "Interest ที่ดูเกี่ยวข้อง"

หลักคิด: แบ่งเป็น 3 ชั้น แล้ว map แต่ละชั้นเป็น interest_group แยกกัน — **OR ภายในชั้น (แนะนำ 3–5 codes ผสม Interest + Behavior เพื่อให้ชั้นสะท้อนกลุ่มจริง), AND ข้ามชั้น** (`interest_groups=[[...], [...], [...]]`) ไม่ใช่โยนรวมเป็น OR กลุ่มเดียว และไม่ใช่ชั้นละ code เดียวโดดๆ

ตัวอย่าง: บ้านเดี่ยว 10–15 ล้านบาท (อิงเซ็ตตัวอย่างจริงจาก LINE for Business)

| ชั้น | Insight | Codes (OR กันในชั้น) |
|---|---|---|
| Need | กำลังหาบ้าน สนใจอสังหาฯ | `6` บ้านและสวน + `1639` ผู้ติดตาม OA อสังหาริมทรัพย์ + `1779` OpenChat ชุมชนผู้พักอาศัย |
| Ability | มีกำลังซื้อ สนใจการเงินการลงทุน | `10` การเงิน + `1612` การลงทุน + `1590` กำลังซื้อสูง + `1774` OpenChat การเงินและการลงทุน |
| Life Stage | มีครอบครัว แต่งงาน มีลูก | `1617` ครอบครัว + `1019` การเลี้ยงดูบุตร + `1618` งานแต่งงาน |

Payload ตัวอย่าง:

```python
interest_groups=[
    ["6", "1639", "1779"],            # Need
    ["10", "1612", "1590", "1774"],   # Ability
    ["1617", "1019", "1618"],         # Life Stage
]
```

**คำเตือน 2 ทาง:**
- อย่าติ๊กทุก interest ที่ "ดูเกี่ยวข้องกับบ้าน" ไว้กลุ่มเดียว (เช่น บ้านและสวน + อสังหา + รถยนต์ + ครอบครัว + ท่องเที่ยว รวมกัน) — นั่นคือการกอง Interest ไม่ใช่การสร้าง Audience
- อย่าใส่ชั้นละ 1–2 code แล้ว intersect — ชั้นจะบางเกินจนไม่สะท้อนกลุ่มจริง และ audience แคบเกินโดยไม่จำเป็น ให้ไล่หา signal เสริมจาก detail files (Interest + OA follower + OpenChat + LINE TODAY + purchase power) จนครบชั้นละอย่างน้อย 3 codes

**คำเตือนเรื่องขนาด:** อย่าแคบจนเหลือ audience หลักหมื่นด้วยความเชื่อว่ายิ่งแคบยิ่งแม่น — เช็คกับสูตร `Audience Size ≈ Budget ÷ CPM × 5,000` และ `get_adset_audience_size` ก่อนสรุปแผน (ดู Audience Size Check ใน `workflows/02-campaign.md`)

## Common Business Mapping

| User segment | Recommended payload | Notes |
|---|---|---|
| SME / เจ้าของกิจการทั่วไป | `interest_groups=[["4"]]` | อาชีพและธุรกิจ |
| เจ้าของโชว์รูม / ยานยนต์ | `interest_groups=[["4"], ["12"]]` | ธุรกิจ + รถยนต์ |
| พ่อค้าแม่ค้าออนไลน์ | `interest_groups=[["4"], ["31"]]` | ธุรกิจ + ช้อปปิ้ง |
| คลินิกเสริมความงาม | `interest_groups=[["4"], ["1604"]]` | ธุรกิจ + ความงาม |
| ร้านเสื้อผ้าออนไลน์ | `interest_groups=[["4"], ["31"], ["1605"]]` | ธุรกิจ + ช้อปปิ้ง + แฟชั่น |
| ร้านอาหาร / F&B owner | `interest_groups=[["4"], ["1607"]]` | ธุรกิจ + อาหาร |
| กำลังซื้อสูง | `behavior_codes=["1590"]` | ใช้เป็น behavior เสริม ไม่ใช่ interest |

## Top-Level Interests

| Code | Interest | Use case |
|---|---|---|
| `1` | เกม | Games / entertainment apps |
| `2` | แกดเจ็ตและเครื่องใช้ไฟฟ้า | Gadgets, electronics, tech products |
| `3` | กีฬา | Sports, fitness-adjacent offers |
| `4` | อาชีพและธุรกิจ | B2B, SME, owner, marketing, career |
| `5` | แฟชั่น | Fashion, apparel |
| `6` | บ้านและสวน | Home, garden, property, construction-adjacent |
| `7` | ทีวีและภาพยนตร์ | TV/movie entertainment |
| `8` | ดนตรี | Music, events |
| `9` | การศึกษา การเรียนรู้ | Education, courses, training |
| `10` | การเงิน | Finance, insurance, investment |
| `11` | สุขภาพและการออกกำลัง | Health, fitness, wellness |
| `12` | รถยนต์ | Automotive, showroom, car owners |
| `15` | หนังสือและการ์ตูน | Books, comics, reading |
| `16` | อาหารเครื่องดื่ม | Food, drink, restaurant |
| `17` | บิวตี้ | Beauty, clinic, skincare |
| `18` | ท่องเที่ยว | Travel, hotel, accommodation |
| `30` | บันเทิง | Broad entertainment |
| `31` | ช้อปปิ้ง | Shopping, ecommerce, online sellers |

## Behavior Taxonomy — 6 กลุ่มหลัก (201 behaviors รวม)

ใช้เป็น guide ก่อนโหลด detail file เพื่อแนะนำ user ได้ถูกกลุ่ม

### 1. ผู้ติดตามบัญชีทางการ LINE (LINE Official Account Follower)
ติดตาม OA ในหมวด: ผลิตภัณฑ์เด็ก, **ความงาม** (คลินิก / ร้านเสริมสวย / เครื่องสำอาง / สกินแคร์ / น้ำหอม / ความงามหรูหรา), **บริการธุรกิจ** (เกษตร / อาชีพ / โลจิสติกส์ / โทรคมนาคม), **รถยนต์** (รถใหม่ / รถมือสอง / อะไหล่ / เช่ารถ / มอเตอร์ไซค์), สินค้าอุปโภคบริโภค (เครื่องดื่ม / กาแฟ / นม), บันเทิง (ดารา / คอนเสิร์ต / ภาพยนตร์), การศึกษา, **แฟชั่น** (เสื้อผ้า / เครื่องประดับ / รองเท้า), **การเงิน** (ธนาคาร / บัตรเครดิต / สินเชื่อ / ลงทุน), **อาหาร** (จีน / ญี่ปุ่น / เกาหลี / ฟาสต์ฟู้ด / delivery), งานอดิเรก (หนังสือ / เกม / ดูดวง / สัตว์เลี้ยง), บ้านและสวน, ประกัน, **ช้อปปิ้ง** (ห้าง / ออนไลน์ / ซูเปอร์มาร์เก็ต), **กีฬา**, **ท่องเที่ยว** (ที่พัก / เที่ยวบิน), อสังหาริมทรัพย์
→ โหลด `interest-detail-lifestyle-consumer.md` หรือ `interest-detail-business-commerce.md` ตามหมวด

### 2. หัวข้อ LINE OpenChat (LINE OpenChat Topic)
ยานยนต์, บันเทิง, การเงินและการลงทุน, อาหารและเครื่องดื่ม, ความงามและสุขภาพ, การเลี้ยงดูบุตร, สัตว์เลี้ยง, ชุมชนผู้พักอาศัย, ช้อปปิ้ง, กีฬา, เทคโนโลยี, ท่องเที่ยว
→ โหลด `interest-detail-line-signals.md`

### 3. ผู้ใช้งานบริการของ LINE (LINE Service Users)
LINE เกม, LINE ดูดวง, LINE เมโลดี้, LINE ธีม, LINE วอลเล็ต, LINE เว็บตูน
→ โหลด `interest-detail-line-signals.md`

### 4. ประเภทข่าว LINE TODAY (LINE TODAY Category)
บันเทิงเอเชียน, ธุรกิจ-เศรษฐกิจ, บันเทิง, อาหาร, ทั่วไป, สุขภาพ, ดูดวง, ข่าวต่างประเทศ, การลงทุน, ไลฟ์สไตล์, ข่าวท้องถิ่น, ลอตเตอรี่, สังคม, กีฬา, ไอที-ธุรกิจ, ท่องเที่ยว
→ โหลด `interest-detail-line-signals.md`

### 5. พฤติกรรมการซื้อสินค้า (Purchase Behaviors)
กำลังซื้อสูง (`1590`), online shopper, brand loyal, deal seeker ฯลฯ
→ โหลด `interest-detail-business-commerce.md`

### 6. พฤติกรรมการใช้งานแอปบนมือถือ (Mobile App Behavior)
ผู้ใช้ iOS / Android, กลุ่มเกม, กลุ่มการเงิน ฯลฯ
→ โหลด `interest-detail-business-commerce.md`

---

## Narrow Targeting Pattern

ถ้าต้องการ narrow/intersection ให้ใช้ `interest_groups` แทนการรวมหลาย code ใน `interest_codes`

```python
interest_groups=[["4"], ["12"]]
```

จะสร้าง:

```json
"includeAdvancedTargetings": [
  { "interests": ["4"] },
  { "interests": ["12"] }
]
```

หลีกเลี่ยง `interest_codes=["4", "12"]` เมื่อ user ต้องการ audience แคบ เพราะ LINE มีแนวโน้มตีความเป็น audience pool แบบรวม
