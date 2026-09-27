"""Regenerate knowledge/targeting-codes-full.md from LINE Ads /codes/advanced-targeting.

Usage:
    uv run python scripts/sync_targeting_codes.py                    # fetch live (needs .env keys)
    uv run python scripts/sync_targeting_codes.py --from-json x.json # use a saved API response

The file mirrors the Ads Manager tree (every group and every selectable code with its
full path) so nothing shown in the UI is missing from the local cache.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

OUTPUT = Path(__file__).resolve().parent.parent / "knowledge" / "targeting-codes-full.md"
SECTIONS = [
    ("interests", "Interests (ความสนใจ)", "INTEREST"),
    ("purchaseIntents", "Purchase Intents (ความตั้งใจซื้อ)", "PURCHASE_INTENT"),
    ("behaviors", "Behaviors (พฤติกรรม)", "BEHAVIOR"),
]


async def fetch_live(objective: str, country: str, locale: str) -> dict[str, Any]:
    from line_ads_mcp.client import LineAdsClient, LineAdsConfig

    async with LineAdsClient(LineAdsConfig.from_env()) as client:
        return await client.get(
            "/codes/advanced-targeting",
            params={"campaignObjective": objective, "country": country, "locale": locale},
        )


def load_json(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    # Accept both the raw API body and the MCP tool wrapper {"ok": true, "data": {...}}.
    return data.get("data", data) if isinstance(data, dict) else data


def fmt_size(size: Any) -> str:
    return "—" if size in (None, -1) else f"{size:,}"


def render(data: dict[str, Any], objective: str, country: str, locale: str) -> str:
    lines: list[str] = []
    counts: dict[str, int] = {}

    def walk(node: dict[str, Any], path: list[str], rows: list[str]) -> None:
        children = node.get("children") or []
        if node.get("selectable"):
            rows.append(
                f"| `{node['code']}` | {node['name']} | {' > '.join(path) or '—'} | {fmt_size(node.get('audienceSize'))} |"
            )
        for child in children:
            walk(child, path + [node["name"]], rows)

    body: list[str] = []
    for key, title, _type in SECTIONS:
        roots = data.get(key) or []
        section_rows = 0
        body.append(f"## {title}\n")
        # Selectable roots without children (e.g. top-level interests 1–31) go in one table.
        flat = [n for n in roots if n.get("selectable") and not n.get("children")]
        if flat:
            body.append("### หมวดหลัก\n")
            body.append("| Code | Name | Path | Audience size |")
            body.append("|---|---|---|---:|")
            for n in flat:
                body.append(f"| `{n['code']}` | {n['name']} | — | {fmt_size(n.get('audienceSize'))} |")
                section_rows += 1
            body.append("")
        for root in roots:
            if root in flat:
                continue
            rows: list[str] = []
            if root.get("selectable"):
                walk(root, [], rows)
            else:
                for child in root.get("children") or []:
                    walk(child, [root["name"]], rows)
            body.append(f"### {root['name']} (`{root['code']}`)\n")
            body.append("| Code | Name | Path | Audience size |")
            body.append("|---|---|---|---:|")
            body.extend(rows)
            body.append("")
            section_rows += len(rows)
        counts[key] = section_rows

    lines.append("# knowledge/targeting-codes-full.md")
    lines.append("# LINE Ads Advanced Targeting — Full Catalog (auto-generated)\n")
    lines.append("> ห้ามแก้มือ — สร้างใหม่ด้วย `uv run python scripts/sync_targeting_codes.py`\n")
    lines.append(f"- Source: `/codes/advanced-targeting` (`{objective}`, `{country}`, `{locale}`)")
    lines.append("- ผลเหมือนกันทุก objective (ตรวจ GAIN_FRIENDS / WEBSITE_CONVERSION / VISIT_MY_WEBSITE / VIDEO_VIEW / REACH / APP_INSTALL เมื่อ 2026-09-27)")
    lines.append(f"- Generated: {date.today().isoformat()}")
    lines.append(
        "- Selectable codes: "
        + ", ".join(f"{counts[k]} {k}" for k, _, _ in SECTIONS)
        + f" = {sum(counts.values())} รวม"
    )
    lines.append("- Path = ลำดับชั้นเหมือนหน้า Ads Manager; code แบบ `TH...` คือหัวข้อกลุ่ม เลือกไม่ได้")
    lines.append("- ใช้ไฟล์นี้เมื่อต้องการเช็คว่ามี code ครบ/ค้นหาด้วยชื่อ ส่วนการเลือกตาม Avatar ให้เริ่มที่ `interest-catalog-INDEX.md`\n")
    return "\n".join(lines + body).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-json")
    parser.add_argument("--objective", default="GAIN_FRIENDS")
    parser.add_argument("--country", default="TH")
    parser.add_argument("--locale", default="th")
    args = parser.parse_args()

    if args.from_json:
        data = load_json(args.from_json)
    else:
        data = asyncio.run(fetch_live(args.objective, args.country, args.locale))
    OUTPUT.write_text(render(data, args.objective, args.country, args.locale))
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
