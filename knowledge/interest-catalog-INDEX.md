# knowledge/interest-catalog-INDEX.md
# LINE Ads Advanced Targeting Index
# โหลดเสมอเมื่อถึงขั้นเลือก audience/interest; ไฟล์นี้เล็กและใช้แนะนำ user ก่อนโหลด detail

---

## Context

- Verified for `campaignObjective=GAIN_FRIENDS`, `country=TH`, `locale=th`
- Source: LINE Ads API `/codes/advanced-targeting`
- Last verified: 2026-09-27 (codes เท่าเดิม, audience size อัปเดตแล้ว)
- Full selectable cache split into detail files: 54 interests, 201 behaviors (รวม 45 app behaviors), 12 purchase intents

## How To Load

1. อ่านไฟล์นี้ก่อนเสมอเพื่อแนะนำหมวด/strategy ให้ user
2. ถ้า code ใน common mapping หรือ top-level table พอ ให้ใช้ได้เลย
3. ถ้า user ขอ niche/sub-code ให้โหลด detail file เฉพาะหมวดที่เกี่ยวข้อง
4. ถ้าต้องการเช็คว่า code ที่เห็นใน Ads Manager มีไหม / ค้นด้วยชื่อ → grep `knowledge/targeting-codes-full.md` (ครบทุก code พร้อม path ตาม UI; ไฟล์ใหญ่ ~43KB อย่าโหลดทั้งไฟล์)
5. เรียก `list_advanced_targeting_codes` เฉพาะเมื่อ cache ไม่มี, objective/country/locale เปลี่ยน, API reject code, หรือต้องการ audience size ล่าสุด

## Detail Files

| Detail file | ใช้เมื่อ | Content |
|---|---|---|
| `knowledge/interest-detail-interests.md` | ต้องการ sub-interest หรือ purchase intent | Interests 54 + purchase intents 12 |
| `knowledge/interest-detail-business-commerce.md` | B2B, finance, ecommerce, กำลังซื้อ | Business/commerce behaviors |
| `knowledge/interest-detail-app-behavior.md` | หมวดหมู่แอป, เกม, persona จากแอป, ระดับความมั่งคั่ง, ราคา/อายุมือถือ | Mobile app behaviors (45) + วิธี map เข้า Avatar |
| `knowledge/targeting-codes-full.md` | เช็คความครบ / ค้นหา code ด้วยชื่อ (auto-generated) | ครบ 267 codes + path ตาม Ads Manager — refresh ด้วย `uv run python scripts/sync_targeting_codes.py` |
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

### เติมชั้นด้วยหมวดหมู่แอป (App Behavior)

App behavior = แอปที่คนใช้จริงบนมือถือ เป็น signal ที่แรงกว่า interest ทั่วไป ใช้เติมแต่ละชั้นให้หนาขึ้น (OR ในชั้นเดิม) ไม่ต้องเพิ่มเป็นชั้นใหม่:

| ชั้น | App codes ที่ใช้บ่อย |
|---|---|
| Need | `2479` แอปท่องเที่ยว, `2435` ชอบเดินทาง, `2469` แอปการศึกษา, `2474` แอปทำงาน, `2466` แอปกราฟิก, `2437` ผู้หญิงใส่ใจความงาม, `2438` ผู้ชายใส่ใจแฟชั่น, `2440` ใส่ใจสิ่งแวดล้อม |
| Ability | `2443`–`2445` ความมั่งคั่งกลาง/สูง/สูงมาก, `2449`–`2450` มือถือราคา 30k+ |
| Life Stage | `2436` แม่และเด็ก, `2439` วัยเกษียณ, `2441` สนใจซื้อรถคันแรก |

ห้ามใช้ `2468` การติดต่อสื่อสาร, `2470` ความบันเทิง, `2476` ตัดต่อภาพ/วิดีโอ, `2477` โซเชียล, `2478` เครื่องมือ เป็น code หลักของชั้น — กว้างเกิน (5–12M) ไม่ได้คัดใคร
ตัวอย่างเต็ม + ตาราง code ทั้งหมด → `knowledge/interest-detail-app-behavior.md`

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
| กำลังซื้อสูง | ใส่ `1590`, `2444`, `2445` ในชั้น Ability ของ `interest_groups` | behavior code ใส่ปนใน `interest_groups` ได้ tool แยก key ให้เอง |

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
Persona จากแอป (ชอบเดินทาง / แม่และเด็ก / ใส่ใจความงาม / ผู้ชายใส่ใจแฟชั่น / วัยเกษียณ / ใส่ใจสิ่งแวดล้อม / รถคันแรก), ระดับความมั่งคั่ง 4 ระดับ, **หมวดหมู่แอป 14 หมวด + เกม 11 ประเภท**, ผู้ใช้อุปกรณ์มือถือ (ระดับราคา / อายุเครื่อง)
→ โหลด `interest-detail-app-behavior.md`

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

ถ้าชั้นเดียวมีทั้ง interest + behavior (เช่น app category) tool จะแยก key ให้อัตโนมัติ — `[["18", "2479"]]` → `{ "interests": ["18"], "behaviors": ["2479"] }` (purchase intent → `purchaseIntents`)

หลีกเลี่ยง `interest_codes=["4", "12"]` เมื่อ user ต้องการ audience แคบ เพราะ LINE มีแนวโน้มตีความเป็น audience pool แบบรวม
