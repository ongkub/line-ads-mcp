# LINE Ads MCP Server

> Built by **Praphat Srisuma (Ong)** · [Spark Factor Co., Ltd.](https://sparkth.io) · LINE Certified Coach
> Licensed under [Apache 2.0](LICENSE) — attribution required, see [NOTICE](NOTICE)

MCP server สำหรับให้ Claude เรียก LINE Ads API v3 โดยตรง แทนการควบคุม browser ในงานที่ API ทำได้ เช่น report, campaign/adset/ad management และ audience management

---

## ⚡ ติดตั้งด้วย Claude Cowork (วิธีที่ง่ายที่สุด)

ไม่ต้องพิมพ์คำสั่งเอง — ก้อปวาง prompt ด้านล่างนี้ใน **Claude Desktop (Cowork mode)** แล้วให้ Claude ทำให้ทั้งหมด:

```
ช่วย setup LINE Ads MCP Server ให้หน่อยครับ

ก่อนเริ่ม: เช็คก่อนว่าเครื่องฉันเป็น macOS หรือ Windows แล้วใช้คำสั่งให้ถูกฝั่งตลอดทั้งงาน

ขั้นตอนที่ต้องทำ:
1. Clone repo: https://github.com/ongkub/line-ads-mcp.git
   - แนะนำ path เช่น ~/line-ads-mcp (macOS) หรือ C:\Users\<ชื่อ>\line-ads-mcp (Windows)
   - ถ้า folder มีอยู่แล้วให้ git pull แทน

2. ติดตั้ง dependencies (ไม่ต้อง activate venv — เรียก pip ใน venv ตรงๆ กัน PATH เพี้ยน):
   - macOS:   python3 -m venv .venv && .venv/bin/pip install -e .
   - Windows: py -3 -m venv .venv แล้วตามด้วย .venv\Scripts\pip.exe install -e .
     (ถ้า py ไม่มีให้ลอง python; ถ้าพิมพ์ python แล้วเด้ง Microsoft Store ให้แจ้งฉันว่าต้องติดตั้ง Python จาก python.org ก่อน)

3. สร้างไฟล์ .env:
   - copy จาก .env.example ถ้ามี (macOS: cp / Windows PowerShell: Copy-Item) ถ้าไม่มีให้สร้างใหม่เลย
   - ถามฉันทีละตัว: LINE_ADS_ACCESS_KEY, LINE_ADS_SECRET_KEY, LINE_ADS_AD_ACCOUNT_ID
     (หาได้ที่ LINE Ads Manager → Settings → API Management)
   - เขียนไฟล์เป็น UTF-8 ธรรมดา (ห้าม UTF-16/BOM — ระวัง PowerShell Out-File)

4. ตรวจว่า server import ได้จริงก่อนแตะ config:
   - macOS:   .venv/bin/python -c "import line_ads_mcp.server; print('OK')"
   - Windows: .venv\Scripts\python.exe -c "import line_ads_mcp.server; print('OK')"
   ถ้าไม่ OK ให้หยุดแก้ตรงนี้ก่อน อย่าเพิ่งไปข้อ 5

   ถ้า macOS ขึ้น error "No such file or directory" ตอนรันคำสั่งข้างบน:
   - venv บน macOS ใช้ symlink ชี้ไป python จริง ถ้าเครื่องเพิ่งอัปเดต/ลบ Python version เดิมออก symlink จะพัง
   - ตรวจ: file .venv/bin/python
   - ถ้าขึ้น "broken symbolic link to python3.XX" ให้หา version ที่มีจริงแล้วชี้ใหม่:
     ls .venv/bin/python3.*
     ln -sf python3.12 .venv/bin/python   (ใส่เลข version ที่เจอจริงจากคำสั่งก่อนหน้า)
   - รัน import test ซ้ำอีกครั้งให้ได้ OK ก่อนไปข้อ 5

   Windows ไม่มีปัญหานี้ (venv ใช้ python.exe ตรงๆ ไม่ใช่ symlink) แต่ถ้า import ไม่ผ่าน ให้ตรวจว่ารัน .venv\Scripts\pip.exe install -e . สำเร็จจริงในข้อ 2 ก่อน

5. อัปเดต claude_desktop_config.json — เพิ่ม block นี้ใต้ mcpServers:
   {
     "mcpServers": {
       "line-ads": {
         "command": "<absolute path ของ python ใน venv>",
         "args": ["-m", "line_ads_mcp.server"],
         "cwd": "<absolute path ของ repo>",
         "env": {
           "LINE_ADS_ACCESS_KEY": "<จาก .env>",
           "LINE_ADS_SECRET_KEY": "<จาก .env>",
           "LINE_ADS_AD_ACCOUNT_ID": "<จาก .env>"
         }
       }
     }
   }
   ตำแหน่งไฟล์ config:
   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
   - Windows: %APPDATA%\Claude\claude_desktop_config.json (ปกติคือ C:\Users\<ชื่อ>\AppData\Roaming\Claude\)
   กฎสำคัญ (พลาดแล้ว Claude Desktop จะไม่โหลด MCP เลยโดยไม่แจ้ง error):
   - "command" บน Windows ต้องชี้ .venv\Scripts\python.exe (ไม่ใช่ .venv/bin/python ซึ่งเป็นของ macOS)
   - path ใน JSON ให้ใช้ forward slash ทั้งหมดแม้บน Windows เช่น "C:/Users/ong/line-ads-mcp/.venv/Scripts/python.exe" — ห้ามใช้ backslash เดี่ยวเด็ดขาดเพราะทำให้ JSON พัง
   - ถ้าไฟล์มี mcpServers อยู่แล้ว ให้ merge เพิ่ม "line-ads" เข้าไป อย่า overwrite ของเดิม
   - บันทึกไฟล์เป็น UTF-8 ไม่มี BOM (บน Windows อย่าใช้ Out-File default ให้ใช้วิธีเขียนที่คุม encoding ได้)

6. ตรวจ config หลังเขียนเสร็จ — ต้อง parse ผ่าน:
   - macOS:   .venv/bin/python -m json.tool "<path config>"
   - Windows: .venv\Scripts\python.exe -m json.tool "<path config>"
   ถ้า parse ไม่ผ่าน = JSON พัง ต้องแก้ก่อนจบงาน (นี่คือสาเหตุอันดับหนึ่งที่ restart แล้วไม่เห็น connector)

7. แจ้งฉันว่าสำเร็จหรือไม่ พร้อมผลตรวจข้อ 4 และข้อ 6 แล้วบอกให้ Quit แล้วเปิด Claude Desktop ใหม่ (ไม่ใช่แค่ปิดหน้าต่าง) เพื่อโหลด MCP

ระหว่างทำ ถ้าขาดข้อมูลไหน ให้ถามฉันทีละอย่างครับ
```

> **หมายเหตุ:** หลัง Claude Cowork ทำสำเร็จ ต้อง **Quit แล้วเปิด Claude Desktop ใหม่** (ไม่ใช่แค่ปิดหน้าต่าง) เพื่อให้โหลด MCP server ใหม่

### Restart แล้วไม่เห็น connector `line-ads`? (พบบ่อยบน Windows)

อาการ "ไม่มี connector โผล่เลยสักตัว" เกือบทั้งหมดเกิดจาก **ไฟล์ config เป็น JSON ที่พัง** — Claude Desktop จะเงียบๆ ไม่โหลด MCP ทั้งไฟล์โดยไม่ขึ้น error เช็คตามลำดับ:

1. **JSON parse ผ่านไหม** — รัน `python -m json.tool "%APPDATA%\Claude\claude_desktop_config.json"` (Windows) ถ้า error แปลว่าไฟล์พัง สาเหตุยอดฮิตคือ path แบบ `C:\Users\...` ที่ backslash ไม่ได้ escape → แก้เป็น forward slash `C:/Users/...` ทั้งหมด
2. **Encoding ของไฟล์** — ถ้าไฟล์ถูกเขียนด้วย PowerShell `Out-File` อาจเป็น UTF-16/มี BOM ซึ่ง parse ไม่ผ่าน ให้เปิดด้วย Notepad แล้ว Save As เป็น UTF-8
3. **`command` ชี้ถูกไฟล์ไหม** — Windows ต้องเป็น `.venv/Scripts/python.exe` (macOS เท่านั้นที่เป็น `.venv/bin/python`) ลองรัน path นั้นตรงๆ ว่ามีจริง
4. **แก้ถูกไฟล์ไหม** — ต้องเป็น `claude_desktop_config.json` ใน `%APPDATA%\Claude\` (Roaming) ไม่ใช่ `Local` และไม่ใช่ไฟล์ config อื่น

### เห็น connector `line-ads` แต่ Claude ขึ้น "Could not attach to MCP server" (macOS)

Config JSON ถูกต้อง แต่ python ใน venv รันไม่ได้จริง — สาเหตุหลักคือ **symlink พัง** ครับ

อาการนี้เกิดเมื่อเครื่อง macOS มีการอัปเดต/ลบ Python เวอร์ชันที่ใช้ตอนสร้าง venv ออกไปทีหลัง (เช่น สร้าง venv ตอนมี Python 3.13 แล้วต่อมาเครื่องเหลือแต่ 3.12) เพราะ `.venv/bin/python` บน macOS เป็นแค่ symlink ชี้ไป python จริง ไม่ใช่ไฟล์จริง

ตรวจสอบ:
```bash
file ~/line-ads-mcp/.venv/bin/python
```
ถ้าขึ้น `broken symbolic link to python3.XX` ให้แก้:
```bash
ls ~/line-ads-mcp/.venv/bin/python3.*
# ดูว่ามี python3.12 หรือ python3.11 อะไรจริงบ้าง แล้วชี้ symlink ใหม่ไปตัวนั้น
ln -sf python3.12 ~/line-ads-mcp/.venv/bin/python
~/line-ads-mcp/.venv/bin/python -c "import line_ads_mcp.server; print('OK')"
```
ได้ `OK` แล้วค่อย Quit + เปิด Claude Desktop ใหม่

Windows ไม่เจอปัญหานี้เพราะ `.venv\Scripts\python.exe` เป็นไฟล์จริง ไม่ใช่ symlink — ถ้า Windows ขึ้น attach error ให้ตรวจว่า path ใน config ตรงกับที่มีไฟล์จริงแทน (`.venv\Scripts\python.exe` ไม่ใช่ `.venv\bin\python`)

### Server crash ทันทีหลัง start (เคยใช้ได้ แต่จู่ๆ attach ไม่ได้)

สาเหตุคือ `mcp` ใน venv ถูกอัปเกรดเป็น 2.x ซึ่งลบ `Server.list_tools` ออกไปแล้ว โปรเจกต์นี้ pin ไว้ที่ `mcp>=1.0.0,<2` ใน `pyproject.toml` ให้ติดตั้งใหม่เพื่อให้กลับมาเป็น 1.x:

```bash
cd ~/line-ads-mcp
source .venv/bin/activate
pip install -e .
pip show mcp | grep Version
```

ต้องได้เวอร์ชัน `1.x` แล้วค่อย Quit + เปิด Claude Desktop ใหม่ — ⚠️ อย่าใช้ `uv run` ตรงๆ ในโฟลเดอร์นี้ เพราะมันจะ sync venv และอาจอัปเกรด `mcp` เป็น 2.x อีก (ถ้าจำเป็นให้ใช้ `uv run --no-project`)

### ขั้นตอนสุดท้าย — ใส่ System Prompt

หลัง restart แล้ว สร้าง **Project** ใหม่ใน Claude Desktop → **Project Instructions** → ก้อปวางเนื้อหาจาก [`CLAUDE_PROJECT_PROMPT.md`](CLAUDE_PROJECT_PROMPT.md) ทั้งหมด

แค่นี้พร้อมใช้งานเลยครับ

---

### อัปเดตเวอร์ชันใหม่ด้วย Claude Cowork

เมื่อมีอัปเดตบน GitHub ให้วาง prompt นี้:

```
ช่วย update LINE Ads MCP Server ให้หน่อยครับ

repo อยู่ที่: https://github.com/ongkub/line-ads-mcp.git
folder ในเครื่องอยู่ที่: (บอก path)

ทำตามขั้นตอน:
1. cd เข้า folder นั้น
2. git pull --rebase origin main
3. source .venv/bin/activate && pip install -e .
4. python -m pytest (ถ้า test ไม่ผ่านให้แจ้งฉัน)
5. แจ้งว่าต้อง Quit และเปิด Claude Desktop ใหม่
```

---

## สำหรับนักการตลาด — ใช้งานผ่าน AI

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

### วิธีใช้กับ Gemini CLI

Gemini CLI รองรับ MCP server ผ่านไฟล์ `settings.json` หรือคำสั่ง `gemini mcp add`

**ขั้นตอนพื้นฐาน:**

1. **ติดตั้ง repo และ dependencies**
   ```bash
   git clone https://github.com/ongkub/line-ads-mcp.git
   cd line-ads-mcp
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env
   ```

2. **ใส่ค่า credentials ใน `.env`**
   ```bash
   LINE_ADS_ACCESS_KEY=your_access_key
   LINE_ADS_SECRET_KEY=your_secret_key
   LINE_ADS_BASE_URL=https://ads.line.me/api/v3
   LINE_ADS_AD_ACCOUNT_ID=A_xxxxxxxxxxxx
   ```

3. **เพิ่ม MCP server ให้ Gemini CLI**

   แบบใช้คำสั่ง:
   ```bash
   gemini mcp add line-ads \
     -e LINE_ADS_ACCESS_KEY=your_access_key \
     -e LINE_ADS_SECRET_KEY=your_secret_key \
     -e LINE_ADS_BASE_URL=https://ads.line.me/api/v3 \
     -e LINE_ADS_AD_ACCOUNT_ID=A_xxxxxxxxxxxx \
     /absolute/path/to/line-ads-mcp/.venv/bin/python \
     -m line_ads_mcp.server
   ```

   หลังใช้คำสั่งนี้ ให้ตรวจ `settings.json` ว่า `cwd` ชี้ไปที่ repo นี้ถูกต้อง ถ้าไม่มีให้เพิ่มเองตามตัวอย่าง JSON ด้านล่าง

   หรือแก้ไฟล์ `~/.gemini/settings.json` / `.gemini/settings.json` เอง:
   ```json
   {
     "mcpServers": {
       "line-ads": {
         "command": "/absolute/path/to/line-ads-mcp/.venv/bin/python",
         "args": ["-m", "line_ads_mcp.server"],
         "cwd": "/absolute/path/to/line-ads-mcp",
         "env": {
           "LINE_ADS_ACCESS_KEY": "your_access_key",
           "LINE_ADS_SECRET_KEY": "your_secret_key",
           "LINE_ADS_BASE_URL": "https://ads.line.me/api/v3",
           "LINE_ADS_AD_ACCOUNT_ID": "A_xxxxxxxxxxxx"
         },
         "timeout": 600000,
         "trust": false
       }
     }
   }
   ```

4. **ตรวจว่า Gemini เห็น MCP tools**
   ```bash
   gemini
   /mcp
   ```

   ควรเห็น server ชื่อ `line-ads` และ tools เช่น `list_campaigns`, `get_report`, `create_campaign`

5. **ใส่ instruction ให้ Gemini อ่านก่อนใช้งาน**

   ตอนเริ่ม session ให้ paste:
   ```text
   อ่าน CLAUDE_PROJECT_PROMPT.md, AGENTS.md, และ workflow/knowledge ที่เกี่ยวข้องก่อนเรียก LINE Ads MCP tools
   ทุก write action ต้อง dry_run=True ก่อนเสมอ และต้องรอคำว่า "ยืนยัน" ก่อน dry_run=False
   ห้าม assume ค่าเงิน เช่น budget, bid cap, CPF, CPC, CPA
   ```

**ตัวอย่าง prompt ใน Gemini CLI:**
```text
ใช้ LINE Ads MCP ดึง campaign active ทั้งหมด แล้วสรุป performance 7 วันล่าสุด
```

```text
ฉันต้องการสร้าง campaign เพิ่มเพื่อน LINE OA แบบ MCP Manual/API-first
อ่าน workflow/02-campaign.md ก่อน แล้วถามข้อมูลที่ขาดทีละข้อ
```

อ้างอิง: [Gemini CLI MCP server docs](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html)

---

### วิธีใช้กับ OpenAI Codex (สำหรับทีม technical / system operator)

[Codex](https://codex.com) เป็น AI coding agent ของ OpenAI ที่รันโค้ด Python ได้โดยตรง
ไม่ต้องผ่าน MCP protocol — Codex import tools แล้วเรียกใช้งานได้เลย

**ขั้นตอน:**

1. **เปิด Codex แล้ว clone repo นี้เข้า environment**
   ```bash
   git clone https://github.com/ongkub/line-ads-mcp.git
   cd line-ads-mcp
   pip install -e .
   ```

2. **ตั้งค่า `.env`** เหมือน Claude Desktop (ข้อ 2 ด้านบน)

3. **บอก Codex ว่าต้องการทำอะไร** ได้เลย เช่น:
   ```
   ดึง campaign ทั้งหมดแล้วสรุป performance 7 วันล่าสุด
   ```
   ```
   สร้าง campaign เพิ่มเพื่อน งบ 300 บาท/วัน แล้วแสดง payload ให้ confirm ก่อน
   ```

Codex จะ import tools จาก `src/line_ads_mcp/tools/` แล้วเรียกใช้โดยตรง
กฎความปลอดภัย `dry_run=True` ยังทำงานเหมือนเดิม

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

## Update From Git

ใช้เมื่อมีการอัปเดตเวอร์ชันใหม่บน GitHub แล้วต้องการดึงลงเครื่อง

### กรณีไม่มีแก้ไฟล์เองในเครื่อง

```bash
cd /path/to/line-ads-mcp
git status
git pull --rebase origin main
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

ถ้าใช้ path เครื่องนี้:

```bash
cd "/Users/ongkub/Desktop/lineads-ai/LINE Ads V0.1.3 - MCP Layer"
git pull --rebase origin main
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

### กรณีมีไฟล์แก้ค้างในเครื่อง

เช็กก่อน:

```bash
git status
```

ถ้ามีไฟล์ที่แก้เองและยังไม่อยาก commit:

```bash
git stash push -m "local work before update"
git pull --rebase origin main
git stash pop
python -m pytest
```

ถ้ามี conflict หลัง `git stash pop` ให้แก้ไฟล์ที่ conflict แล้วรัน:

```bash
git status
python -m pytest
```

### ไฟล์ที่ไม่ควรถูกทับ

- `.env` ไม่ควร commit และไม่ควรถูกทับจาก Git
- credentials เช่น Access Key / Secret Key ให้เก็บใน `.env` หรือ config ของ AI client เท่านั้น
- ถ้ามี `.env.example` เปลี่ยน ให้เทียบแล้วค่อยเพิ่ม key ใหม่ลง `.env` เอง

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
- ทุก write ต้อง dry-run → สรุปตัวเลข → ผู้ใช้พิมพ์ “ยืนยัน” → `dry_run=false` → ตรวจ readback
- credentials อ่านจาก env เท่านั้น ไม่ hardcode ในโค้ด
- error message ส่งกลับเป็นภาษาไทยเพื่อให้ assistant ส่งต่อ user ได้ทันที

## Tool Status

รายการต่อไปนี้อธิบาย contract หลังอัปเกรด ไม่ได้ยืนยันว่าทุก feature เปิดใช้ได้กับทุกบัญชี; permission/API response ต้องตรวจจากบัญชีจริง

### Read tools — อ่านทั้งบัญชีและทุกหน้า

| Tool / parameters | พฤติกรรม |
|---|---|
| `list_campaigns(status=None, fetch_all=True)` | ทุก campaign; กรอง ACTIVE/PAUSED/REMOVED |
| `list_adsets(campaign_id=None, status=None, fetch_all=True)` | ทั้งบัญชีหรือเฉพาะ campaign; status filter เดียวกัน |
| `list_ads(adset_id=None, campaign_id=None, status=None, fetch_all=True)` | ทั้งบัญชีหรือกรอง parent; status filter เดียวกัน |
| `get_entity(entity_type="campaign"\|"adset"\|"ad", entity_id=...)` | exact entity: configured_status, delivery_status, budget, bid, targeting, raw |
| `get_ad_status(ad_id)` | exact-ID safe; ตรวจ review/delivery; `NOT_APPROVED` = review rejected |
| `get_report(level="CAMPAIGN"\|"ADGROUP"\|"AD", start_date=..., end_date=..., campaign_id=None, adgroup_id=None, fetch_all=True, by_day=False)` | ทุกหน้า; `by_day=True` = หนึ่งแถวต่อวัน×entity สูงสุด 93 วัน/คำขอ |
| `get_daily_report` / `get_weekly_report(by_day=False)` | เมื่อวาน ระดับ AD เป็น default / รายงานสัปดาห์ |
| `list_audiences` / `list_advanced_targeting_codes` | audience เดิมพร้อม `status`, `estimated_audience_size`, `usable_in_adset` / official interest, behavior, status codes |
| `get_customer_list_upload_status(audience_id)` | MODE 8: jobs พร้อม job_status QUEUED/WORKING/FINISHED/FAILED, audience_count, failed_type, done; จบแล้วตรวจ list_audiences จน READY/usable_in_adset=true |
| `estimate_adset_reach(campaign_id, campaign_objective, daily_budget, bid_type, auto_bid_type, targeting=...)` | LINE Adgroup Result Simulator (`simulation/ars`): reach/click min–max เป็นค่าประมาณ ไม่สร้างอะไร ไม่ใช่ขนาด audience จริง/ผลรับประกัน |
| `check_spend_cap(cap_amount, start_date, end_date, campaign_id=None, period_end=None)` | อ่านอย่างเดียว; per-campaign spend และ optional projection; ไม่ pause เอง |

`estimate_adset_reach` รองรับ targeting params แบบ `create_adset` หรือ `targeting` และ optional `adset_id`, `bid_amount`, `bid_strategy`; แจ้ง absent/invalid fields โดยไม่เดาตัวเลขเงิน

รายงานคืน `paging.complete` (true/false) และ `date_basis: "UTC"` ต้องตรวจความครบถ้วนก่อนสรุป วันรายงานเป็น UTC; summary keys คือ `total_spend`, `total_clicks`, `total_impressions`, `total_cv`, `avg_ctr` (%), `avg_cpc`, `avg_cpm` ค่าเฉลี่ยเป็น `None` เมื่อไม่มีตัวหาร ไม่ใช้ CV/CPA/ROAS วิเคราะห์ objective ที่ไม่ใช่ WEBSITE_CONVERSION

Cap ใช้เลขและช่วงวันที่ที่เจ้าของระบุเท่านั้น: `exceeded` เมื่อ spend > cap อย่างเคร่งครัด, เท่ากับ cap ยังเป็น `within_cap`, `indeterminate` เมื่อข้อมูลไม่ครบต้องบอกว่ายังสรุปไม่ได้ ไม่ auto-pause

### Write tools — dry-run → สรุป → “ยืนยัน” → execute → readback

| Tool | Contract / ข้อควรตรวจ |
|---|---|
| `create_campaign` | `status="PAUSED"` default; objective enum, งบจาก user และต้องมี `start_date` |
| `create_adset` | `status="PAUSED"` default; งบ/bid เป็น THB; interest/behavior targeting ใช้ official codes |
| `upload_customer_list(file_path, id_type PHONE\|EMAIL\|IFA, audience_name=None, audience_id=None, action="ADD"\|"REPLACE", column=None, default_country_code="66", dry_run=True, workspace_dir=None)` | MODE 8: CSV/TXT absolute path ในเครื่อง; normalize/ตัดซ้ำ/hash PHONE/EMAIL แสดงเฉพาะ masked samples; ตรวจสิทธิใช้ → dry-run → “ยืนยัน” → upload; REPLACE แทนที่สมาชิกเดิมทั้งหมด ต้องอนุมัติชัดเจน |
| `upload_media` | อัปโหลดรูป/วิดีโอเพื่อรับ imageHash; เป็น write ต้อง dry-run + “ยืนยัน” |
| `create_ad` | `status="PAUSED"` default; nested creative, imageHash จาก upload, title/description ไม่เกิน 20 ตัวอักษร |
| `update_campaign` / `update_adset` | แก้ budget/bid/targeting/status ตาม fields ที่ tool รองรับ; ห้ามเดาเงิน |
| `pause_campaign` / `resume_campaign` | PAUSED / ACTIVE หลัง approval ใหม่ |
| `pause_adset` / `resume_adset` | PAUSED / ACTIVE หลัง approval ใหม่ |
| `pause_ad(ad_id, dry_run=True)` / `resume_ad(ad_id, dry_run=True)` | หยุด/เปิด ad ด้วย exact ID หลัง approval ใหม่ |
| `create_audience(name, function_type, config, dry_run=True, workspace_dir=None)` | `LOOKALIKE` (source audience + size ratio), `APP_EVENT`, `WEBTRAFFIC` (LINE Tag, retentionDays 1–180), `ACCOUNT_FRIENDS` (OA), `VIDEO_VIEW`, `IMAGE_CLICK` (ผู้มีส่วนร่วมกับโฆษณาที่ผ่านมา); ต้องมีสิทธิ์ Custom Audience |
| `sync_ad_daily_csv(start_date, end_date, workspace_dir, campaign_id=None, dry_run=True)` | optional history เฉพาะ scheduled task บทที่ 5; upsert ด้วย key date+ad_id และบันทึก run log |

Audience: MODE 2 เลือกหรือสร้างฐานหลัง Customer Avatar Gate ก่อนสร้าง ad set ได้; MODE 6 ให้คำแนะนำเท่านั้น ส่งต่อ MODE 2 ในแชทเดิมเมื่อจะสร้าง ไม่เรียก create_audience/create_adset เอง ทุก write ต้อง dry-run → สรุป → “ยืนยัน” → execute → readback ฐานใหม่เริ่ม `IN_PROGRESS` ต้อง re-check `list_audiences` และใช้ใน ad set เฉพาะ `status="READY"` / `usable_in_adset=true` ส่ง `custom_audience_ids` / `excluded_audience_ids` ชุดเดียวกันให้ create_adset และ estimate_adset_reach; GAIN_FRIENDS ยังต้องยกเว้น active friends audience ที่พร้อมใช้

ขนาดฐานเดิมใช้ `estimated_audience_size`: `"-"` = เล็กเกินรายงาน, `"100 or fewer"` = ไม่เกิน 100 คน; ฐานใหม่ยังไม่ทราบขนาดจน LINE สร้างเสร็จ ถ้ายังไม่ READY ถามว่าจะรอหรือสร้าง ad set โดยไม่ใช้ฐานใหม่นี้ ไม่ข้าม friend exclusion ที่จำเป็น Customer-list upload (hashed phone/email) ไม่รองรับผ่าน MCP ให้ผู้ใช้ทำเองใน LINE Ads Manager ไม่ขอไฟล์ลูกค้า

ทุก real write (`dry_run=False`) คืน `readback`, `readback_ok`; update/pause/resume คืน `before` snapshot ด้วย ต้องตรวจแล้วแสดงผลหลังทำ หาก readback ไม่ตรง/ไม่ครบ ห้ามอ้างว่าสำเร็จ ตรวจ `get_entity` / `get_ad_status` ก่อน retry การสร้างจบที่ PAUSED; `resume_*` เป็น approval แยก ไม่ถือว่าอนุมัติพร้อมการสร้าง

Write tools รับ optional `workspace_dir` (fallback env `LINE_ADS_WORKSPACE_DIR`) เพื่อ append before/after/time ใน `line-ads-data/change_log.jsonl` ต้องให้สิทธิ์ path ที่ใช้จริง ไม่ตั้ง path อย่าอ้างว่ามี log

`sync_ad_daily_csv` ต้องระบุ `workspace_dir` ตาม signature; AI จัดการ `line-ads-data/ad_daily.csv` (16 columns: date, account_timezone, campaign_id, campaign_name, objective, adgroup_id, adgroup_name, ad_id, ad_name, impressions, clicks, spend, currency, results, result_type, pulled_at) และ `run_log.csv` เอง ผู้อ่านไม่ต้องเตรียม/แนบ/เขียนไฟล์ ยกเว้นรูป creative ก่อน sync จริงต้อง dry-run และ “ยืนยัน”; การตั้ง sync ทุก run ต้องยืนยันขอบเขต recurring write ไว้ใน task

### Workflows 01–07

เริ่มด้วยแชทประโยคเดียว AI ดึงข้อมูลบัญชีผ่าน MCP แล้วถามทีละเรื่องเฉพาะสิ่งที่บัญชีตอบไม่ได้ เช่น เป้าหมายธุรกิจ งบ/cap วันเริ่ม ข้อเท็จจริงสินค้า และ approval ตัวเลขตัวอย่างต้องระบุ “(ตัวอย่างสมมติ)” ไม่ใช้แทนเงินจริง

| Workflow | งาน |
|---|---|
| [01-account-setup](workflows/01-account-setup.md) | เปิดบัญชี/KYC; sensitive fields ให้ user กรอกเอง |
| [02-campaign](workflows/02-campaign.md) | บทที่ 3: campaign → ad set → upload → ad เป็น PAUSED พร้อมตรวจ readback |
| [03-report-schedule](workflows/03-report-schedule.md) | บทที่ 5: report → summary → cap exceeded alert → optional CSV history |
| [04-optimize](workflows/04-optimize.md) | บทที่ 6: ดึง ACTIVE/report → diagnose → เสนอ → before/dry-run/ยืนยัน/execute → after/log/follow-up |
| [05-dashboard](workflows/05-dashboard.md) | บทที่ 4: Claude สร้าง Artifact จาก MCP; ไม่มี dashboard tool |
| [06-audience-advisor](workflows/06-audience-advisor.md) | บทที่ 1: แนะนำ Core audience จากประวัติ อ่านอย่างเดียว ไม่สร้าง audience |
| [07-campaign-planner](workflows/07-campaign-planner.md) | โหมดเสริม (ไม่อยู่ในเล่ม): วางแผนจากประวัติ ส่งต่อบทที่ 1 ถ้าจะสร้างจริง |
| [08-customer-list-audience](workflows/08-customer-list-audience.md) | บทที่ 2 / MODE 8: ไฟล์ลูกค้าที่มีอยู่แล้วผ่าน path ในเครื่อง; ตรวจ PDPA/รูปแบบ → dry-run → ยืนยัน ADD/REPLACE → รอ READY → ใช้/ยกเว้น/LOOKALIKE |

ไม่มี scheduler MCP tool: ใช้ Cowork Schedule tab หรือ `/schedule` ไม่ใช้ cron งานที่ต้องใช้ local files/apps รันเฉพาะเครื่อง local ตาม [คู่มือ Cowork Schedule](https://support.claude.com/en/articles/13854387) Scheduled task แจ้งเตือนเฉพาะ `check_spend_cap.status="exceeded"`; benchmark/creative/delivery analysis ใช้เมื่อต้องการวิเคราะห์ทันที ไม่ใส่เป็น alerts อื่นใน task

## Budget & Bid Units

LINE Ads API v3 ใช้หน่วย **micro** สำหรับเงินทุกตัว:

```
1 THB = 1,000,000 micro

ตัวอย่างจาก real adset:
  dailyBudgetMicro: 300_000_000  →  300 THB/วัน
  bidAmountMicro:    10_000_000  →  10 THB/friend
```

Tool รับค่า THB ปกติ (float) แล้วแปลง micro ให้อัตโนมัติผ่าน `to_micro()` ใน `common.py`

## Interest Targeting

LINE Ads API ไม่รับชื่อ interest ตรง ๆ เช่น `Marketing`, `Branding`, `Advertising`, `Business` ต้องใช้ official code เท่านั้น

ให้ใช้ [knowledge/interest-catalog-INDEX.md](knowledge/interest-catalog-INDEX.md) เป็น local cache ชั้นแรกก่อน เพื่อประหยัด tokens/API calls แล้วค่อยโหลด `knowledge/interest-detail-*.md` เฉพาะหมวดที่ต้องใช้ หรือเรียก `list_advanced_targeting_codes` เฉพาะเมื่อไม่มี segment ใน cache, objective/country/locale เปลี่ยน, API reject code, หรือต้องการ audience size ล่าสุด

สำหรับ `TH + GAIN_FRIENDS` ที่ทดสอบจริง:

```
อาชีพและธุรกิจ = code "4"
```

การใส่ interest แบบกว้างใช้ `interest_codes`:

```json
{
  "targeting": {
    "targetingMode": "MANUAL",
    "ageMin": 25,
    "ageMax": 44,
    "country": "TH",
    "excludedCustomAudienceIds": ["5343822743474"],
    "includeAdvancedTargetings": [
      { "interests": ["4"] }
    ]
  }
}
```

ถ้าต้องการ narrow audience ให้ใช้ `interest_groups` เช่น `[[ "4" ], [ "12" ]]` เพื่อสร้างหลาย object ใน `includeAdvancedTargetings`:

```json
"includeAdvancedTargetings": [
  { "interests": ["4"] },
  { "interests": ["12"] }
]
```

### App Behavior (หมวดหมู่แอป / ระดับความมั่งคั่ง / persona จากแอป)

code จาก [knowledge/interest-detail-app-behavior.md](knowledge/interest-detail-app-behavior.md) (เช่น `2466` การออกแบบกราฟิก, `2444` ความมั่งคั่งระดับสูง) เป็น **behavior** ไม่ใช่ interest — ใส่ปนกับ interest code ใน `interest_groups` ชั้นเดียวกันได้เลย tool จะแยก key ให้เองตามประเภท code (`interests` / `behaviors` / `purchaseIntents`):

`interest_groups: [["4"], ["12", "2441"]]` จะได้:

```json
"includeAdvancedTargetings": [
  { "interests": ["4"] },
  { "interests": ["12"], "behaviors": ["2441"] }
]
```

หรือส่ง behavior แบบกว้างผ่าน `behavior_codes` ก็ได้ — parent code (`TH1...`) เลือกไม่ได้ ใช้เฉพาะ code ตัวเลข

ถ้า `targetingMode=AUTO` interest/custom advanced targeting จะไม่ถูกใช้

## Valid Campaign Objectives

```
GAIN_FRIENDS     ← เพิ่มเพื่อน LINE OA (ยืนยันจาก real API)
VISIT_MY_WEBSITE  ← เข้าเว็บไซต์
WEBSITE_CONVERSION
REACH
APP_INSTALL
VIDEO_VIEW
```

> ⚠️ `FRIEND_ADDED`, `VISIT_MY_WEBSITE`, `APP_INSTALLS`, `VIDEO_VIEWS` เป็น enum เก่าที่ผิด — tool จะ reject ทันที

## Acknowledgements

โปรเจกต์นี้พัฒนาโดยใช้ AI coding agents เป็นส่วนหนึ่งของกระบวนการพัฒนา:

- **OpenAI Codex (o3)** — scaffold หลัก, auth layer, tool architecture
- **Anthropic Claude** — payload verification, API probing, test suite
