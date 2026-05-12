# LINE Ads MCP Server

> Built by **Praphat Srisuma (Ong)** · [Spark Factor Co., Ltd.](https://sparkth.io) · LINE Certified Coach
> Co-developed with **OpenAI Codex (o3)** and **Anthropic Claude**
> Licensed under [Apache 2.0](LICENSE) — attribution required, see [NOTICE](NOTICE)

MCP server สำหรับให้ Claude เรียก LINE Ads API v3 โดยตรง แทนการควบคุม browser ในงานที่ API ทำได้ เช่น report, campaign/adset/ad management และ audience management

---

## สำหรับนักการตลาด — ใช้งานผ่าน Claude หรือ ChatGPT

ไม่ต้องเขียนโค้ด ไม่ต้องเปิด LINE Ads Manager ทุกครั้ง — คุยกับ AI แล้วให้มันดึงข้อมูลและจัดการ campaign แทน

### วิธีใช้กับ Claude Desktop (แนะนำ)

Claude Desktop รองรับ MCP โดยตรง ใช้งานได้เลยหลัง setup ครั้งเดียว

**ขั้นตอน:**

1. **ติดตั้ง Python และ repo นี้**
   ```bash
   git clone https://github.com/ongkub/line-ads-mcp.git
   cd line-ads-mcp
   python -m venv .venv && source .venv/bin/activate
   pip install -e .
   ```

2. **ตั้งค่า credentials ใน `.env`**
   ```bash
   cp .env.example .env
   # แก้ไขไฟล์ .env ใส่ Access Key / Secret Key จาก LINE Ads Manager
   # (Settings → API Management)
   LINE_ADS_ACCESS_KEY=your_access_key
   LINE_ADS_SECRET_KEY=your_secret_key
   LINE_ADS_AD_ACCOUNT_ID=A_xxxxxxxxxxxx
   ```

3. **เพิ่ม MCP server ใน Claude Desktop**

   เปิดไฟล์ config ของ Claude Desktop:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   เพิ่ม block นี้:
   ```json
   {
     "mcpServers": {
       "line-ads": {
         "command": "/absolute/path/to/.venv/bin/python",
         "args": ["-m", "line_ads_mcp.server"],
         "cwd": "/absolute/path/to/line-ads-mcp",
         "env": {
           "LINE_ADS_ACCESS_KEY": "your_key",
           "LINE_ADS_SECRET_KEY": "your_secret",
           "LINE_ADS_AD_ACCOUNT_ID": "A_xxxxxxxxxxxx"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop แล้วคุยได้เลย**

5. **ใส่ System Prompt (สำคัญ)** — เพื่อให้ Claude รู้บทบาทและกฎความปลอดภัยโดยอัตโนมัติ

   ไปที่ Claude Desktop → สร้าง **Project** ใหม่ → **Project Instructions** → ก้อปวางจาก [`CLAUDE_PROJECT_PROMPT.md`](CLAUDE_PROJECT_PROMPT.md)

**ตัวอย่างที่พิมพ์ใน Claude หลัง setup:**
```
ดู campaign ที่รันอยู่ทั้งหมดให้หน่อย
```
```
สรุปผล 7 วันที่ผ่านมาให้หน่อย campaign ไหน CPF ถูกที่สุด
```
```
หยุด campaign "เพิ่มเพื่อน: ..." ชั่วคราวก่อน
```

---

### วิธีใช้กับ ChatGPT (ผ่าน Custom GPT + Actions)

ChatGPT ยังไม่รองรับ MCP โดยตรง แต่สามารถเชื่อมผ่าน **OpenAPI wrapper** ได้

**ขั้นตอน:**

1. Deploy MCP server นี้เป็น REST API (เช่นผ่าน FastAPI wrapper หรือ Cloudflare Worker)
2. สร้าง Custom GPT → เพิ่ม Action → import OpenAPI schema ที่ wrap tools เหล่านี้
3. ChatGPT จะเรียก LINE Ads API ผ่าน Action ได้เหมือน Claude

> หมายเหตุ: วิธีนี้ต้องมีคนช่วย deploy server ขึ้น cloud ก่อน ไม่ได้รันบน local เหมือน Claude Desktop
> สำหรับ setup แบบ production พร้อมใช้ สามารถติดต่อ [Spark Factor](https://sparkth.io) ได้เลย

---

### ความปลอดภัยสำหรับนักการตลาด

- **ทุก action ที่เกี่ยวกับเงิน** (สร้าง campaign, ตั้ง budget, สร้าง ad) จะ **แสดง preview ก่อนเสมอ** — AI ต้องขอ confirm ก่อนส่งจริง
- **ไม่มีปุ่มลบ** — ไม่มี tool สำหรับลบ campaign/ad/adset ในชุดนี้
- Credentials เก็บใน `.env` บนเครื่องคุณเอง ไม่ผ่านเซิร์ฟเวอร์ภายนอก

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

ตั้งค่า `.env`:

```bash
LINE_ADS_ACCESS_KEY=your_access_key
LINE_ADS_SECRET_KEY=your_secret_key
LINE_ADS_BASE_URL=https://ads.line.me/api/v3
LINE_ADS_AD_ACCOUNT_ID=A_xxxxxxxxxxxx
```

## Run

```bash
python -m line_ads_mcp.server
```

หรือใช้ console script:

```bash
line-ads-mcp
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "line-ads": {
      "command": "python",
      "args": ["-m", "line_ads_mcp.server"],
      "cwd": "/Users/ongkub/Desktop/lineads-ai/LINE Ads V0.1.3 - MCP Layer",
      "env": {
        "LINE_ADS_ACCESS_KEY": "your_key",
        "LINE_ADS_SECRET_KEY": "your_secret",
        "LINE_ADS_AD_ACCOUNT_ID": "A_xxxxxxxxxxxx"
      }
    }
  }
}
```

## Safety

- ไม่มี delete tools
- write tools ตั้ง `dry_run=true` เป็นค่าเริ่มต้น
- budget/bid changes ต้องให้ assistant ขอ user confirm ก่อนเรียก `dry_run=false`
- credentials อ่านจาก env เท่านั้น ไม่ hardcode ในโค้ด
- error message ส่งกลับเป็นภาษาไทยเพื่อให้ assistant ส่งต่อ user ได้ทันที

## Tool Status

### ✅ Read-ready (smoke test ผ่านกับ API จริง)

| Tool | หมายเหตุ |
|---|---|
| `list_campaigns` | ✅ |
| `list_adsets` | ✅ |
| `list_ads` | ✅ |
| `get_ad_status` | ✅ |
| `get_report` / `get_daily_report` / `get_weekly_report` | ✅ |
| `list_audiences` | ✅ |

### ✅ Write-ready (payload ตรง spec + tests ผ่าน — ยังคง dry_run=true โดย default)

| Tool | Budget/Bid | Objective/Status | หมายเหตุ |
|---|---|---|---|
| `create_campaign` | `dailyBudgetMicro` / `totalBudgetMicro` (THB × 1M) | `campaignObjective: GAIN_FRIENDS` | payload verified จาก real API data |
| `update_campaign` | `dailyBudgetMicro` | `configuredStatus` | |
| `pause_campaign` / `resume_campaign` | — | `configuredStatus: PAUSED/ACTIVE` | |
| `create_adset` | `dailyBudgetMicro` / `bidAmountMicro` (THB × 1M) | `bidType`, `bidStrategy` required | ต้องระบุ bid_type + bid_strategy |
| `update_adset` | `dailyBudgetMicro` / `bidAmountMicro` | `configuredStatus` | |
| `pause_adset` / `resume_adset` | — | `configuredStatus: PAUSED/ACTIVE` | |

### ✅ Write-ready — payload verified จาก real API response + error probing

| Tool | หมายเหตุ |
|---|---|
| `create_ad` | creative เป็น nested object; ใช้ `imageHash` (จาก upload_media), `title`, `callToAction.type` |
| `upload_media` | endpoint `/media/upload`; ต้องส่ง `mediaType: IMAGE\|VIDEO`; signing ใช้ `"multipart/form-data"` |

### ⚠️ Dry-run only (403 permissions — โค้ดถูก แต่ account ยังไม่ได้เปิด feature)

| Tool | สถานะ |
|---|---|
| `create_audience` | API ตอบ 403 ทุก type — ต้องเปิด Custom Audience feature ใน LINE Ads Manager ก่อน |

## Budget & Bid Units

LINE Ads API v3 ใช้หน่วย **micro** สำหรับเงินทุกตัว:

```
1 THB = 1,000,000 micro

ตัวอย่างจาก real adset:
  dailyBudgetMicro: 300_000_000  →  300 THB/วัน
  bidAmountMicro:    10_000_000  →  10 THB/friend
```

Tool รับค่า THB ปกติ (float) แล้วแปลง micro ให้อัตโนมัติผ่าน `to_micro()` ใน `common.py`

## Valid Campaign Objectives

```
GAIN_FRIENDS     ← เพิ่มเพื่อน LINE OA (ยืนยันจาก real API)
WEBSITE_TRAFFIC  ← เข้าเว็บไซต์
CONVERSIONS
REACH
APP_INSTALL
VIDEO_VIEW
```

> ⚠️ `FRIEND_ADDED`, `VISIT_MY_WEBSITE`, `APP_INSTALLS`, `VIDEO_VIEWS` เป็น enum เก่าที่ผิด — tool จะ reject ทันที
