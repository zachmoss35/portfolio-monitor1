"""Send daily report via email."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from portfolio_agent.config import Config

logger = logging.getLogger(__name__)


def send_report_email(
    config: Config,
    subject: str,
    markdown_body: str,
) -> bool:
    """Send the daily report as an HTML email derived from Markdown."""
    if not config.smtp_user or not config.email_to:
        logger.warning("Email not configured — skipping send")
        return False

    html_body = _markdown_to_html(markdown_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.email_from or config.smtp_user
    msg["To"] = config.email_to
    msg.attach(MIMEText(markdown_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
        logger.info("Report emailed to %s", config.email_to)
        return True
    except Exception:
        logger.exception("Failed to send email")
        return False


def _markdown_to_html(md: str) -> str:
    """Simple Markdown-to-HTML conversion for email rendering."""
    lines = md.split("\n")
    html_lines: list[str] = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("|") and not in_table:
            in_table = True
            html_lines.append("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>")
            html_lines.append(_table_row(stripped, is_header=True))
        elif stripped.startswith("|") and in_table:
            if set(stripped.replace("|", "").replace("-", "").strip()) == set():
                continue
            html_lines.append(_table_row(stripped))
        elif in_table and not stripped.startswith("|"):
            in_table = False
            html_lines.append("</table>")
            html_lines.append(_inline_line(stripped))
        elif stripped.startswith("- "):
            html_lines.append(f"<li>{_format_inline(stripped[2:])}</li>")
        elif stripped == "---":
            html_lines.append("<hr>")
        elif stripped == "":
            html_lines.append("<br>")
        else:
            html_lines.append(_inline_line(stripped))

    if in_table:
        html_lines.append("</table>")

    return (
        "<html><body style='font-family:Arial,sans-serif;max-width:800px;margin:auto;'>"
        + "\n".join(html_lines)
        + "</body></html>"
    )


def _table_row(line: str, is_header: bool = False) -> str:
    cells = [c.strip() for c in line.strip("|").split("|")]
    tag = "th" if is_header else "td"
    return "<tr>" + "".join(f"<{tag}>{_format_inline(c)}</{tag}>" for c in cells) + "</tr>"


def _inline_line(text: str) -> str:
    if text.startswith("**") and text.endswith("**"):
        return f"<p><strong>{text[2:-2]}</strong></p>"
    return f"<p>{_format_inline(text)}</p>"


def _format_inline(text: str) -> str:
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<a href='\2'>\1</a>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    return text
