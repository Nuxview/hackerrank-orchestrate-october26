"""Immutable scoped observations and time-eligible exact identity links."""

from dataclasses import dataclass
from datetime import datetime
import json
import re

from inputs import InputError, timestamp


@dataclass(frozen=True)
class Fact:
    fact_id: str
    evidence_id: str
    path: str
    location: str
    claim_kind: str
    system_id: str
    resource_id: str
    category: str
    subject_keys: tuple[tuple[str, str], ...]
    payload_json: str
    observed_at: datetime
    captured_at: datetime
    snapshot_at: datetime
    scope: str

    def __post_init__(self):
        if self.claim_kind not in {"observation", "activity_claim", "identity_link", "scope"}:
            raise InputError("Unknown fact kind")
        if not all([self.fact_id, self.evidence_id, self.path, self.location, self.scope]):
            raise InputError("Missing fact provenance or scope")
        for value in [self.observed_at, self.captured_at, self.snapshot_at]:
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise InputError("Fact timestamps must be timezone-aware")
        if not isinstance(json.loads(self.payload_json), dict):
            raise InputError("Fact payload must be an object")

    def eligible(self, cutoff):
        return all(t <= cutoff for t in [self.observed_at, self.captured_at, self.snapshot_at])


def normalize(field, value):
    if field in {"email", "email_hash"}:
        return value.strip().casefold()
    if field == "phone":
        return re.sub(r"[\s().-]", "", value)
    return value.strip()


@dataclass(frozen=True, order=True)
class Alias:
    field: str
    normalized: str
    raw: str
    source_id: str
    observed_at: datetime


def resolve_identity(email, cutoff, identities, history):
    """An old/new alias is available only through an eligible snapshot/history row."""
    aliases = {}
    for row in identities:
        if timestamp(row["updated_at"]) <= cutoff:
            user = aliases.setdefault(row["user_id"], set())
            observed = timestamp(row["updated_at"])
            user.add(Alias("user_id", row["user_id"], row["user_id"], row["user_id"], observed))
            for field in ["name", "email", "phone", "email_hash"]:
                if row[field]:
                    user.add(Alias(field, normalize(field, row[field]), row[field], row["user_id"], observed))
    for row in history:
        if timestamp(row["event_time"]) <= cutoff:
            user = aliases.setdefault(row["user_id"], set())
            observed = timestamp(row["event_time"])
            user.add(Alias("user_id", row["user_id"], row["user_id"], row["audit_id"], observed))
            for key in ["old_value", "new_value"]:
                if row[key]:
                    field = row["field_name"]
                    user.add(Alias(field, normalize(field, row[key]), row[key], row["audit_id"], observed))
    key = normalize("email", email)
    candidates = [u for u, values in aliases.items()
                  if any(a.field == "email" and a.normalized == key for a in values)]
    if len(candidates) != 1:
        raise InputError("Unresolved or ambiguous request identity")
    user_id = candidates[0]
    return user_id, tuple(sorted(aliases[user_id]))
