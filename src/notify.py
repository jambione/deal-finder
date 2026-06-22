"""
Email flight price alert to subscribers.
Sends daily with best fares and buy/wait recommendation.
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
NAVY = "#1B2438"
GOLD = "#C9A44A"


def load_subscribers():
    path = os.path.join(CONFIG_DIR, "subscribers.json")
    try:
        with open(path) as f:
            subs = json.load(f).get("subscribers", [])
        return [s for s in subs if s.get("active") and s.get("email")]
    except Exception as e:
        print(f"[notify] could not read subscribers: {e}")
        return []


def load_data():
    def read(name):
        try:
            with open(os.path.join(OUTPUT_DIR, name)) as f:
                return json.load(f)
        except Exception:
            return {}

    flights = read("flights.json").get("flights", [])
    analysis = read("analysis.json")
    oil = read("oil.json")
    return flights, analysis, oil


def build_email(flights, analysis, oil):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    rec = analysis.get("recommendation", "neutral")
    reason = analysis.get("reason", "")
    signal_color = "#27c56f" if rec == "buy_now" else "#f0b429" if rec == "wait" else "#aaa"
    signal_label = "BUY NOW" if rec == "buy_now" else "WAIT" if rec == "wait" else "MONITOR"

    biz = sorted([f for f in flights if f.get("cabin") == "business" and f.get("price")], key=lambda x: x["price"])
    pe  = sorted([f for f in flights if f.get("cabin") == "premium_economy" and f.get("price")], key=lambda x: x["price"])
    best_biz = biz[0] if biz else None
    best_pe  = pe[0]  if pe  else None

    def row(f, label):
        if not f:
            return f"<tr><td style='padding:12px 0;border-bottom:1px solid #eee;color:#999'>{label}: no data</td></tr>"
        return f"""
        <tr>
          <td style="padding:14px 0;border-bottom:1px solid #eee;">
            <div style="font-size:12px;color:{GOLD};font-weight:700;margin-bottom:4px">{label} · {f.get('route_label','')} · {f.get('month','').title()}</div>
            <div style="font-size:24px;font-weight:800;color:{NAVY}">${f['price']:,.0f} <span style="font-size:14px;font-weight:400;color:#888">per person</span></div>
            <div style="font-size:13px;color:#555;margin-top:4px">{f.get('airline','')} · Depart {f.get('outbound_date','')} · Return {f.get('return_date','')}</div>
          </td>
        </tr>"""

    oil_price = oil.get("current_price")
    oil_chg = oil.get("month_change_pct")
    oil_line = ""
    if oil_price:
        chg_str = f" ({'+' if oil_chg and oil_chg > 0 else ''}{oil_chg:.1f}% this month)" if oil_chg else ""
        oil_line = f"<p style='font-size:12px;color:#888;margin:4px 0'>WTI Crude: ${oil_price:.2f}/bbl{chg_str}</p>"

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;background:#f4f5f7;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:24px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;">
        <tr><td style="background:{NAVY};padding:20px 28px;">
          <span style="color:#fff;font-size:20px;font-weight:700;">Brasfield Deals</span>
          <span style="color:{GOLD};font-size:13px;float:right;padding-top:6px;">NYC→Milan · {today}</span>
        </td></tr>
        <tr><td style="padding:20px 28px 0;">
          <div style="background:{signal_color}22;border:1px solid {signal_color}55;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
            <span style="color:{signal_color};font-weight:700;font-size:13px">{signal_label}</span>
            <span style="color:#444;font-size:13px;margin-left:8px">{reason}</span>
          </div>
          <h2 style="color:{NAVY};font-size:16px;margin:0 0 4px">Today's Best Fares</h2>
          <p style="font-size:12px;color:#888;margin:0 0 12px">JFK / EWR → Milan (MXP / LIN) · June &amp; July 2027</p>
          <table width="100%" cellpadding="0" cellspacing="0">
            {row(best_biz, 'Business Class')}
            {row(best_pe,  'Premium Economy')}
          </table>
          {oil_line}
        </td></tr>
        <tr><td style="padding:24px 28px;">
          <a href="{SITE_URL}" style="display:inline-block;background:{GOLD};color:{NAVY};font-weight:700;
             text-decoration:none;padding:12px 22px;border-radius:8px;">View full tracker →</a>
        </td></tr>
        <tr><td style="padding:0 28px 24px;color:#aaa;font-size:12px;">
          You're subscribed to Brasfield Deals flight alerts.
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
    msg.attach(MIMEText("Open in an HTML-capable client to view today's flight prices.", "plain"))
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
        print("[notify] skipping — SMTP not configured")
        return

    subscribers = load_subscribers()
    if not subscribers:
        print("[notify] no active subscribers")
        return

    flights, analysis, oil = load_data()
    if not flights:
        print("[notify] no flight data, skipping")
        return

    html = build_email(flights, analysis, oil)
    rec = analysis.get("recommendation", "monitor")
    biz = sorted([f for f in flights if f.get("cabin") == "business" and f.get("price")], key=lambda x: x["price"])
    best_price = biz[0]["price"] if biz else None
    subject = (f"NYC→Milan: {'BUY NOW — ' if rec == 'buy_now' else ''}Business from ${best_price:,.0f}"
               if best_price else "Brasfield Deals — NYC→Milan flight update")

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
