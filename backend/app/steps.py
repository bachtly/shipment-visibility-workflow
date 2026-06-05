"""
External side-effect steps — decorated with @DBOS.step so DBOS checkpoints them.
In real life these would call vendor APIs, send emails, etc.
"""
import logging

from dbos import DBOS

logger = logging.getLogger(__name__)


@DBOS.step()
def notify_status_change(shipment_id: str, status: str, note: str = "") -> None:
    logger.info("NOTIFY shipment=%s status=%s note=%s", shipment_id, status, note)


@DBOS.step()
def notify_customs_outcome(shipment_id: str, leg: str, outcome: str, attempts: int) -> None:
    logger.info(
        "CUSTOMS shipment=%s leg=%s outcome=%s attempts=%d",
        shipment_id, leg, outcome, attempts,
    )


@DBOS.step()
def notify_escalation(shipment_id: str, leg: str) -> None:
    logger.warning("ESCALATION shipment=%s leg=%s — customs exceeded max attempts", shipment_id, leg)
