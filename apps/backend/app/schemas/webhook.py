from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class WebhookPayload(BaseModel):
    event_type: str  # delivery, bounce, complaint, open, click, unsubscribe
    event_id: str
    recipient_email: str
    provider: str
    provider_message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    raw_payload: Dict[str, Any] = {}


class WebhookResponse(BaseModel):
    status: str = "received"
    event_id: str
    processed: bool
