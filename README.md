# LINE Ads MCP Server

> Built by **Praphat Srisuma (Ong)** · [Spark Factor Co., Ltd.](https://sparkth.io) · LINE Certified Coach
> Co-developed with **OpenAI Codex (o3)** and **Anthropic Claude**
> Licensed under [Apache 2.0](LICENSE) — attribution required, see [NOTICE](NOTICE)

MCP server สำหรับให้ Claude เรียก LINE Ads API v3 โดยตรง แทนการควบคุม browser ในงานที่ API ทำได้ เช่น report, campaign/adset/ad management และ audience management

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
