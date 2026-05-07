#!/usr/bin/env python3
"""
Формує email-дайджест з validated artifact і надсилає через Gmail SMTP.

Використання:
    python3 scripts/send-digest.py --agent validator-state [--artifact path/to/file.json]
    python3 scripts/send-digest.py --agent validator-edo   [--artifact path/to/file.json]

Якщо --artifact не вказано, скрипт знаходить останній файл у runs/{agent}/.

Змінні середовища:
    GMAIL_APP_PASSWORD  — обов'язково, Gmail App Password (16 символів без пробілів)
    GMAIL_SENDER        — необов'язково, адреса відправника (default: legal.monitor.ai@gmail.com)
    GMAIL_TO            — необов'язково, адреса отримувача   (default: legal.monitor.ai@gmail.com)

Exit codes:
    0 — успішно надіслано
    1 — помилка відправки
    2 — артефакт не знайдено або помилка JSON
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

DEFAULT_ADDR = "legal.monitor.ai@gmail.com"

AGENT_RUNS_DIR = {
    "validator-state": "runs/validator-state",
    "validator-edo":   "runs/validator-edo",
}


# ── helpers ──────────────────────────────────────────────────────────────────

def find_latest_artifact(agent: str) -> Path:
    runs_dir = REPO_ROOT / AGENT_RUNS_DIR[agent]
    candidates = sorted(
        runs_dir.glob("????-??-??T??-??-??Z.json"),
        reverse=True,
    )
    if not candidates:
        print(f"ERROR: no artifacts in {runs_dir}", file=sys.stderr)
        sys.exit(2)
    return candidates[0]


def load_artifact(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: artifact not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def fmt_period(period: dict) -> tuple[str, str]:
    def fmt(ts: str) -> str:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M UTC")
        except ValueError:
            return ts
    return fmt(period.get("from", "")), fmt(period.get("to", ""))


# ── digest formatters ─────────────────────────────────────────────────────────

def _item_block(item: dict, idx: int) -> str:
    number = item.get("number") or "—"
    date   = item.get("date_published") or "—"
    note   = item.get("validation_note", "")
    lines  = [
        f"{idx}. {item.get('title', '—')}",
        f"   Реквізити: {number}, {date}",
        f"   Посилання: {item.get('url', '—')}",
    ]
    if note:
        lines.append(f"   Примітка: {note}")
    return "\n".join(lines)


def format_state(data: dict) -> tuple[str, str]:
    period  = data.get("period", {})
    p_from, p_to = fmt_period(period)
    stats   = data.get("stats", {})
    n_valid = stats.get("items_valid", 0)
    n_unc   = stats.get("items_uncertain", 0)

    subject = f"[НПА] Дайджест моніторингу за {p_from} — {p_to}"

    valid_items = [i for i in data.get("items", []) if i.get("validation_status") == "valid"]
    unc_items   = [i for i in data.get("items", []) if i.get("validation_status") == "uncertain"]

    by_source: dict[str, list] = {
        "monitor-rada-bills": [],
        "monitor-kmu":        [],
        "monitor-nbu":        [],
    }
    for item in valid_items:
        src = item.get("source_agent_id", "")
        if src in by_source:
            by_source[src].append(item)

    lines = [
        "Моніторинг НПА держорганів — автоматичний дайджест",
        "Джерела: Верховна Рада, КМУ, НБУ",
        f"Період: з {p_from} до {p_to}",
        "",
    ]

    if n_valid == 0 and n_unc == 0:
        lines.append("За вказаний період нових змін не виявлено.")
    else:
        lines.append(
            f"ЗНАЙДЕНО {n_valid} нових документів"
            + (f" ({n_unc} потребують перевірки)" if n_unc else "")
            + ":"
        )
        lines.append("")

        # Sections per source
        source_labels = {
            "monitor-rada-bills": "ЗАКОНОПРОЕКТИ ВРУ",
            "monitor-kmu":        "ПОСТАНОВИ КМУ",
            "monitor-nbu":        "АКТИ НБУ",
        }
        global_idx = 1
        for src_id, label in source_labels.items():
            items = by_source[src_id]
            lines.append(f"── {label} ({len(items)}) ──")
            if not items:
                lines.append("   Нових документів не виявлено.")
            else:
                for item in items:
                    lines.append(_item_block(item, global_idx))
                    global_idx += 1
            lines.append("")

        if unc_items:
            lines.append(f"── ПОТРЕБУЮТЬ ПЕРЕВІРКИ ({len(unc_items)}) ──")
            for item in unc_items:
                lines.append(_item_block(item, global_idx))
                global_idx += 1
            lines.append("")

    lines += [
        "---",
        "[Автоматичний дайджест] | ai-monitoring-legal | trotsenko-ms",
        "Інформаційний характер. Не замінює правову експертизу.",
    ]
    return subject, "\n".join(lines)


def format_edo(data: dict) -> tuple[str, str]:
    period  = data.get("period", {})
    p_from, p_to = fmt_period(period)
    stats   = data.get("stats", {})
    n_valid = stats.get("items_valid", 0)
    n_unc   = stats.get("items_uncertain", 0)

    subject = f"[ЕДО] Дайджест моніторингу за {p_from} — {p_to}"

    valid_items = [i for i in data.get("items", []) if i.get("validation_status") == "valid"]
    unc_items   = [i for i in data.get("items", []) if i.get("validation_status") == "uncertain"]

    lines = [
        "Моніторинг НПА у сфері ЕДО — автоматичний дайджест",
        f"Період: з {p_from} до {p_to}",
        "",
    ]

    if n_valid == 0 and n_unc == 0:
        lines.append("За вказаний період нових змін не виявлено.")
    else:
        lines.append(
            f"ЗНАЙДЕНО {n_valid} нових документів"
            + (f" ({n_unc} потребують перевірки)" if n_unc else "")
            + ":"
        )
        lines.append("")
        idx = 1
        for item in valid_items + unc_items:
            lines.append(_item_block(item, idx))
            idx += 1
            lines.append("")

    lines += [
        "---",
        "[Автоматичний дайджест] | ai-monitoring-legal | trotsenko-ms",
        "Інформаційний характер. Не замінює правову експертизу.",
    ]
    return subject, "\n".join(lines)


FORMATTERS = {
    "validator-state": format_state,
    "validator-edo":   format_edo,
}


# ── send ──────────────────────────────────────────────────────────────────────

def send_email(sender: str, recipient: str, subject: str, body: str, app_password: str) -> None:
    msg = EmailMessage()
    msg["From"]    = sender
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.set_content(body, charset="utf-8")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(sender, app_password)
        smtp.send_message(msg)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Send monitoring digest via Gmail SMTP")
    parser.add_argument(
        "--agent",
        required=True,
        choices=list(AGENT_RUNS_DIR.keys()),
        help="Which validator artifact to use",
    )
    parser.add_argument(
        "--artifact",
        help="Explicit path to validated artifact JSON (default: latest in runs/{agent}/)",
    )
    args = parser.parse_args()

    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not app_password:
        print("ERROR: GMAIL_APP_PASSWORD env var is not set", file=sys.stderr)
        sys.exit(1)

    sender    = os.environ.get("GMAIL_SENDER", DEFAULT_ADDR).strip()
    recipient = os.environ.get("GMAIL_TO",     DEFAULT_ADDR).strip()

    artifact_path = (
        Path(args.artifact) if args.artifact else find_latest_artifact(args.agent)
    )
    if not artifact_path.is_absolute():
        artifact_path = REPO_ROOT / artifact_path

    data = load_artifact(artifact_path)

    formatter = FORMATTERS[args.agent]
    subject, body = formatter(data)

    print(f"▶ Sending digest: agent={args.agent} artifact={artifact_path.name}")
    print(f"  From: {sender} → To: {recipient}")
    print(f"  Subject: {subject}")

    try:
        send_email(sender, recipient, subject, body, app_password)
        print("✓ Email sent successfully")
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: SMTP authentication failed — {e}", file=sys.stderr)
        print("  Verify GMAIL_APP_PASSWORD is a valid Gmail App Password.", file=sys.stderr)
        sys.exit(1)
    except smtplib.SMTPException as e:
        print(f"ERROR: SMTP error — {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Network error — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
