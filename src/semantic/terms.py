"""Convert RDF values to the existing Python/UI contract."""

from datetime import datetime, timezone

from pyoxigraph import Literal


def value(term):
    if term is None:
        return None
    if isinstance(term, Literal):
        kind = term.datatype.value.rsplit("#", 1)[-1]
        if kind in ("integer", "int"):
            return int(term.value)
        if kind in ("double", "decimal", "float"):
            return float(term.value)
        if kind == "boolean":
            return term.value in ("true", "1")
        if kind == "dateTime":
            # Oxigraph canonicalizes redundant fractional zeroes. Restore M4's
            # six-digit UTC display/context-token representation from the value.
            instant = datetime.fromisoformat(term.value.replace("Z", "+00:00"))
            if instant.utcoffset() is None:
                raise ValueError("Source timestamps require a known timezone")
            return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return term.value
