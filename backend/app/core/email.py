"""Email senders: one interface, three implementations (the Strategy pattern).

- ConsoleSender: prints the email. Default, needs no setup.
- SmtpSender:    speaks SMTP. Used locally with Mailpit, or with any SMTP provider.
- BrevoSender:   calls Brevo's HTTPS API. Used in production, because many hosts
                 (Render's free tier among them) block outgoing SMTP ports.

Business code only sees `EmailSender.send(...)`, so switching provider is a config change.
"""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to_address: str
    to_name: str
    subject: str
    text: str
    html: str


class EmailSender(Protocol):
    def send(self, email: Email) -> None: ...


class ConsoleSender:
    def send(self, email: Email) -> None:
        logger.warning("EMAIL to %s | %s\n%s", email.to_address, email.subject, email.text)


class SmtpSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, email: Email) -> None:
        s = self.settings
        message = EmailMessage()
        message["From"] = f"{s.email_from_name} <{s.email_from_address}>"
        message["To"] = f"{email.to_name} <{email.to_address}>"
        message["Subject"] = email.subject
        message.set_content(email.text)
        message.add_alternative(email.html, subtype="html")
        try:
            with smtplib.SMTP(s.smtp_host or "localhost", s.smtp_port, timeout=10) as smtp:
                if s.smtp_starttls:
                    smtp.starttls()
                if s.smtp_username and s.smtp_password:
                    smtp.login(s.smtp_username, s.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            logger.exception("SMTP send failed")
            raise ServiceUnavailableError("Could not send email right now.") from exc


class BrevoSender:
    URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, email: Email) -> None:
        s = self.settings
        body = {
            "sender": {"name": s.email_from_name, "email": s.email_from_address},
            "to": [{"email": email.to_address, "name": email.to_name}],
            "subject": email.subject,
            "textContent": email.text,
            "htmlContent": email.html,
        }
        try:
            response = httpx.post(
                self.URL,
                json=body,
                headers={"api-key": s.brevo_api_key or "", "accept": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Brevo send failed")
            raise ServiceUnavailableError("Could not send email right now.") from exc


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.email_provider == "smtp":
        return SmtpSender(settings)
    if settings.email_provider == "brevo":
        return BrevoSender(settings)
    return ConsoleSender()
