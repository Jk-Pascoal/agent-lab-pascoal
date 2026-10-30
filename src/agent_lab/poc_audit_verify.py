"""Fail-closed consumer of the PoC v0 report/manifest pair (#204).

This validates the report's *published bytes*, canonical JSON, v0 contract,
and corresponding digest. It does not verify original CSV custody, a human
decision, crash-atomic publication, or the semantics of duplicate candidates.
"""
import argparse
import hashlib
import hmac
import json
import re
from pathlib import Path

from .poc_audit_report import canonical_report_bytes, validate_poc_audit_report


class InvalidPocAuditPairError(ValueError):
    """A report/manifest pair must not be consumed as verified."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidPocAuditPairError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise InvalidPocAuditPairError("non-finite JSON constant")


def _parse_canonical_json(data: bytes, label: str) -> dict:
    try:
        parsed = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        canonical = (
            json.dumps(parsed, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n"
        ).encode("utf-8")
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InvalidPocAuditPairError(f"{label}: invalid JSON") from exc
    if type(parsed) is not dict or data != canonical:
        raise InvalidPocAuditPairError(f"{label}: noncanonical JSON envelope")
    return parsed


def verify_poc_audit_report_pair(path: str | Path) -> dict:
    """Return the validated snapshot, or reject partial/corrupt/mixed pairs.

    Only the sibling '<report>.manifest.json' is accepted. A hard crash can
    leave one published file; it is never accepted without the valid partner.
    Files are read into independent byte snapshots, without writes or repairs.
    """
    report_path = Path(path)
    manifest_path = report_path.with_name(report_path.name + ".manifest.json")
    try:
        report_bytes = report_path.read_bytes()
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise InvalidPocAuditPairError("report/manifest pair missing or unreadable") from exc

    manifest = _parse_canonical_json(manifest_bytes, "manifest")
    if set(manifest) != {"schema_version", "report_sha256"} or (
        manifest["schema_version"] != "poc_audit_manifest.v0"
    ) or type(manifest["report_sha256"]) is not str or not re.fullmatch(
        r"[0-9a-f]{64}", manifest["report_sha256"]
    ):
        raise InvalidPocAuditPairError("invalid manifest contract")

    digest = hashlib.sha256(report_bytes).hexdigest()
    if not hmac.compare_digest(digest, manifest["report_sha256"]):
        raise InvalidPocAuditPairError("report digest does not match manifest")

    payload = _parse_canonical_json(report_bytes, "report")
    try:
        validate_poc_audit_report(payload)
        if canonical_report_bytes(payload) != report_bytes:
            raise InvalidPocAuditPairError("report serialization mismatch")
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise InvalidPocAuditPairError("report violates v0 contract") from exc
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_json", help="v0 report; manifest is the sibling file")
    args = parser.parse_args(argv)
    try:
        payload = verify_poc_audit_report_pair(args.report_json)
    except InvalidPocAuditPairError as exc:
        parser.exit(1, f"REFUSED: {exc}\n")
    print(json.dumps({
        "status": "REPORT_AND_MANIFEST_VALIDATED",
        "scope": "report bytes, digest and structural schema only",
        "source_custody": payload["catalog"]["provenance_status"],
        "human_review": "NOT_VERIFIED",
        "report_sha256": hashlib.sha256(canonical_report_bytes(payload)).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
