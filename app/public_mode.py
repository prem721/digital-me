"""When PUBLIC_MODE is on, only these paths exist. Everything else answers 404.
Exact matches only, so odd paths like /presentation/../ingest or //ingest are blocked too."""

PUBLIC_PATHS = {"/", "/health", "/presentation/chat"}


def is_allowed_in_public_mode(path: str) -> bool:
    return path in PUBLIC_PATHS