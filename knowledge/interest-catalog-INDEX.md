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
