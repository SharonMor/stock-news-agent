import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import EMAIL_SENDER, EMAIL_RECIPIENT, GMAIL_APP_PASSWORD


def send_digest(html_body: str) -> None:
    subject = f"Stock Digest — {date.today().strftime('%B %d, %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECIPIENT

    # Plain-text fallback
    plain = "Your daily stock digest is ready. Please view in an HTML-capable email client."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print(f"Digest sent to {EMAIL_RECIPIENT}")
