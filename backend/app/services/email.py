import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeEmailMessage
from typing import Protocol

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str


class EmailProvider(Protocol):
    def send_email(self, message: EmailMessage) -> None: ...


class ConsoleEmailProvider:
    """Safe local development provider — logs metadata only (never raw tokens/body)."""

    def send_email(self, message: EmailMessage) -> None:
        logger.info(
            "ConsoleEmailProvider: queued email subject=%r recipient_domain=%s",
            message.subject,
            message.to.split("@")[-1] if "@" in message.to else "unknown",
        )


class InMemoryEmailProvider:
    """Test double capturing sent emails without network calls."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send_email(self, message: EmailMessage) -> None:
        self.sent.append(message)


class ResendEmailProvider:
    """Transactional email delivery via Resend HTTPS API."""

    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(self, *, api_key: str, email_from: str, timeout_seconds: float = 10.0) -> None:
        self._api_key = api_key
        self._email_from = email_from
        self._timeout = timeout_seconds

    def send_email(self, message: EmailMessage) -> None:
        response = httpx.post(
            self.RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": self._email_from,
                "to": [message.to],
                "subject": message.subject,
                "html": message.html,
                "text": message.text,
            },
            timeout=self._timeout,
        )
        if response.status_code >= 400:
            logger.error(
                "Resend delivery failed with status=%s", response.status_code
            )
            raise RuntimeError(f"Resend API error (status={response.status_code})")


class SmtpEmailProvider:
    """SMTP email delivery (works with local Mailpit, Mailtrap, Brevo SMTP, Gmail SMTP)."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        email_from: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._host = host
        self._port = port
        self._email_from = email_from
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._timeout = timeout_seconds

    def send_email(self, message: EmailMessage) -> None:
        mime = MimeEmailMessage()
        mime["From"] = self._email_from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        mime.add_alternative(message.html, subtype="html")

        with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as client:
            if self._use_tls:
                client.starttls()
            if self._username and self._password:
                client.login(self._username, self._password)
            client.send_message(mime)


def build_email_provider(settings: Settings) -> EmailProvider:
    if settings.email_provider == "resend":
        assert settings.resend_api_key and settings.email_from
        return ResendEmailProvider(
            api_key=settings.resend_api_key,
            email_from=settings.email_from,
        )
    if settings.email_provider == "smtp":
        assert settings.smtp_host and settings.email_from
        return SmtpEmailProvider(
            host=settings.smtp_host,
            port=settings.smtp_port,
            email_from=settings.email_from,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
        )
    return ConsoleEmailProvider()
