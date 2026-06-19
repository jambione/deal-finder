"""Email the top 5 greatest discounts across all categories to subscribers.

Runs after the deal pipeline. Reads output/*.json (the scored category files),
ranks every deal by discount_pct, takes the top 5, and emails them.

Skips silently if SMTP credentials are not configured, so local runs and
unconfigured CI runs don't fail.

Required env vars (set as GitHub Actions secrets):
  SMTP_HOST      e.g. smtp.gmail.com
  SMTP_PORT      e.g. 587
  SMTP_USER      sending account username
  SMTP_PASS      sending account password / app password
  SMTP_FROM      From address (defaults to SMTP_USER)
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SITE_URL = "https://deals.jbrasfield.com"

CATEGORY_FILES = ["electronics", "apparel", "travel", "games", "software"]
NAVY = "#1B2438"
GOLD = "#C9A44A"
TOP_N = 5
MAX_PER_CATEGORY = 2


def load_subscribers():
    path = os.path.join(CONFIG_DIR, "subscribers.json")
    try:
        with open(path) as f:
            subs = json.load(f).get("subscribers", [])
        return [s for s in subs if s.get("active") and s.get("email")]
    except Exception as e:
        print(f"[notify] could not read subscribers: {e}")
        return []


def load_top_deals():
    deals = []
    for cat in CATEGORY_FILES:
        path = os.path.join(OUTPUT_DIR, f"{cat}.json")
        try:
            with open(path) as f:
                data = json.load(f)
            for d in data.get("deals", []):
                d["category"] = d.get("category", cat)
                deals.append(d)
        except Exception:
            continue
    # Only deals with a real discount, ranked highest first
    discounted = [d for d in deals if (d.get("discount_pct") or 0) > 0]
    discounted.sort(key=lambda d: d.get("discount_pct", 0), reverse=True)

    # Diversify: at most MAX_PER_CATEGORY so one franchise/category can't fill
    # the whole list. Backfill from the remainder if we come up short.
    picked, per_cat = [], {}
    for d in discounted:
        cat = d.get("category", "other")
        if per_cat.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        picked.append(d)
        per_cat[cat] = per_cat.get(cat, 0) + 1
        if len(picked) >= TOP_N:
            break
    if len(picked) < TOP_N:
        chosen = {id(d) for d in picked}
        for d in discounted:
            if id(d) not in chosen:
                picked.append(d)
                if len(picked) >= TOP_N:
                    break
    return picked[:TOP_N]


def _price(d):
    p = d.get("price")
    if p is None:
        return ""
    return f"${p:,.2f}"


def build_html(top_deals):
    rows = []
    for i, d in enumerate(top_deals, 1):
        disc = d.get("discount_pct", 0)
        cat = (d.get("category") or "").title()
        price = _price(d)
        orig = d.get("original_price")
        orig_html = (
            f'<span style="text-decoration:line-through;color:#999;margin-left:6px;">${orig:,.2f}</span>'
            if orig else ""
        )
        rows.append(f"""
        <tr>
          <td style="padding:14px 0;border-bottom:1px solid #eee;">
            <div style="font-size:13px;color:{GOLD};font-weight:700;">#{i} · {disc}% OFF · {cat}</div>
            <a href="{d.get('url', '#')}" style="font-size:16px;color:{NAVY};font-weight:600;text-decoration:none;">{d.get('title','')}</a>
            <div style="margin-top:4px;font-size:14px;color:#333;">{price}{orig_html}
              <span style="color:#888;margin-left:8px;">via {d.get('source','')}</span>
            </div>
          </td>
        </tr>""")

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;background:#f4f5f7;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:24px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;">
        <tr><td style="background:{NAVY};padding:20px 28px;">
          <span style="color:#fff;font-size:20px;font-weight:700;">Brasfield Deals</span>
          <span style="color:{GOLD};font-size:13px;float:right;padding-top:6px;">Top 5 · {today}</span>
        </td></tr>
        <tr><td style="padding:8px 28px 0;">
          <h2 style="color:{NAVY};font-size:18px;margin:18px 0 4px;">Today's biggest discounts</h2>
          <table width="100%" cellpadding="0" cellspacing="0">{''.join(rows)}</table>
        </td></tr>
        <tr><td style="padding:24px 28px;">
          <a href="{SITE_URL}" style="display:inline-block;background:{GOLD};color:{NAVY};font-weight:700;
             text-decoration:none;padding:12px 22px;border-radius:8px;">See all deals →</a>
        </td></tr>
        <tr><td style="padding:0 28px 24px;color:#aaa;font-size:12px;">
          You're receiving this because you subscribed to Brasfield Deals.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_email(host, port, user, password, from_addr, to_addr, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText("Open in an HTML-capable client to view today's top deals.", "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(host, int(port), timeout=20) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())


def main():
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT", "587")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM", user)

    if not (host and user and password):
        print("[notify] skipping — SMTP_HOST / SMTP_USER / SMTP_PASS not set")
        return

    subscribers = load_subscribers()
    if not subscribers:
        print("[notify] no active subscribers, nothing to send")
        return

    top_deals = load_top_deals()
    if not top_deals:
        print("[notify] no discounted deals found, nothing to send")
        return

    html = build_html(top_deals)
    top_disc = top_deals[0].get("discount_pct", 0)
    subject = f"Brasfield Deals: today's top 5 (up to {top_disc}% off)"

    sent = 0
    for sub in subscribers:
        try:
            send_email(host, port, user, password, from_addr, sub["email"], subject, html)
            sent += 1
        except Exception as e:
            print(f"[notify] failed to send to {sub['email']}: {e}")

    print(f"[notify] sent to {sent}/{len(subscribers)} subscribers")


if __name__ == "__main__":
    main()
