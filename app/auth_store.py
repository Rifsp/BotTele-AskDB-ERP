import secrets
import logging

logger = logging.getLogger(__name__)

pending_tokens: set[str] = set()
authorized_users: set[int] = set()


def generate_token() -> str:
    token = secrets.token_hex(8)
    pending_tokens.add(token)
    logger.info("Token generated: %s (pending_tokens=%d)", token, len(pending_tokens))
    return token


def consume_token(token: str, user_id: int) -> bool:
    if token in pending_tokens:
        pending_tokens.discard(token)
        authorized_users.add(user_id)
        logger.info("Token consumed by user_id=%d, token=%s", user_id, token)
        return True
    return False
