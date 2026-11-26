import logging
from dataclasses import dataclass
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


def build_email_provider(settings: Settings) -> EmailProvider:
    if settings.email_provider == "resend":
        assert settings.resend_api_key and settings.email_from
        return ResendEmailProvider(
            api_key=settings.resend_api_key,
            email_from=settings.email_from,
        )
    return ConsoleEmailProvider()
