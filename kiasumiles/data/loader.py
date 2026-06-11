from __future__ import annotations
import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class MerchantRecord:
    merchant_name: str
    outlet: str | None
    channel: str
    mcc: str
    mcc_category: str
    confidence: str
    data_points: int
    last_verified: str


@dataclass
class CardRule:
    card_id: str
    card_name: str
    bank: str
    network: str
    eligible_mccs: list[str]
    earn_rate_mpd: float
    base_rate_mpd: float
    cap_sgd: float | None
    cap_period: str
    min_spend: float
    requires_amaze: bool
    amaze_fee_pct: float
    eligible_merchants: list[str] = field(default_factory=list)  # if set, bonus rate only applies at these merchants
    eligible_channels: list[str] = field(default_factory=list)  # if set, bonus rate only applies for these merchant channels
    caveat: str = ""
    last_verified: str = ""
    source_url: str = ""
    earn_block_sgd: float = 1.0  # spend rounds down to nearest block before earn rate applies (UOB/DBS = $5, others = $1)


_PACKAGE_DATA_DIR = Path(__file__).parent
_DEMO_DATA_DIR = _PACKAGE_DATA_DIR / "demo"
_REMOTE_TIMEOUT_SECONDS = 10.0
_SUPABASE_PAGE_SIZE = 1000


def _parse_bool(val: str) -> bool:
    return val.strip().lower() in ("true", "1", "yes")


def _parse_float_or_none(val: str) -> float | None:
    val = val.strip()
    return float(val) if val else None


def _parse_mccs(val: str) -> list[str]:
    if not val.strip():
        return []
    return [m.strip() for m in val.split(",") if m.strip()]


class DataLoader:
    def __init__(self, backend: str | None = None) -> None:
        self._merchants: list[MerchantRecord] | None = None
        self._cards: list[CardRule] | None = None
        self._backend = backend or os.environ.get("KIASUMILES_DATA_BACKEND", "auto").strip().lower()

    def merchants(self) -> list[MerchantRecord]:
        if self._merchants is None:
            self._merchants = self._load_merchants()
        return self._merchants

    def cards(self) -> list[CardRule]:
        if self._cards is None:
            self._cards = self._load_cards()
        return self._cards

    def backend_name(self) -> str:
        if self._should_use_supabase():
            return "supabase"
        if self._private_data_dir():
            return "private_csv"
        return "demo_csv"

    def _should_use_supabase(self) -> bool:
        if self._backend == "supabase":
            return True
        if self._backend == "csv":
            return False
        return bool(self._supabase_url() and self._supabase_service_role_key())

    def _supabase_url(self) -> str:
        return os.environ.get("KIASUMILES_SUPABASE_URL", "").strip()

    def _supabase_service_role_key(self) -> str:
        return os.environ.get("KIASUMILES_SUPABASE_SERVICE_ROLE_KEY", "").strip()

    def _supabase_table(self, default: str, env_var: str) -> str:
        return os.environ.get(env_var, default).strip() or default

    def _private_data_dir(self) -> Path | None:
        raw = os.environ.get("KIASUMILES_DATA_DIR", "").strip()
        if not raw:
            return None
        return Path(raw).expanduser()

    def _csv_path(self, filename: str) -> Path:
        private_dir = self._private_data_dir()
        if private_dir is not None:
            candidate = private_dir / filename
            if candidate.exists():
                return candidate
        return _DEMO_DATA_DIR / filename

    def _fetch_supabase_rows(self, table_name: str) -> list[dict]:
        supabase_url = self._supabase_url().rstrip("/")
        service_role_key = self._supabase_service_role_key()
        if not supabase_url or not service_role_key:
            raise RuntimeError("Supabase credentials are not configured.")

        headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Accept": "application/json",
        }
        rows: list[dict] = []
        start = 0

        while True:
            query = urlencode({"select": "*", "offset": start, "limit": _SUPABASE_PAGE_SIZE})
            endpoint = f"{supabase_url}/rest/v1/{table_name}?{query}"
            request = Request(
                endpoint,
                headers=headers,
            )
            with urlopen(request, timeout=_REMOTE_TIMEOUT_SECONDS) as response:
                payload = response.read().decode("utf-8")
            batch = json.loads(payload)
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected Supabase response for {table_name}.")
            rows.extend(batch)
            if len(batch) < _SUPABASE_PAGE_SIZE:
                break
            start += _SUPABASE_PAGE_SIZE

        return rows

    def _load_merchants(self) -> list[MerchantRecord]:
        if self._should_use_supabase():
            try:
                rows = self._fetch_supabase_rows(
                    self._supabase_table("merchant_mcc", "KIASUMILES_SUPABASE_MERCHANTS_TABLE")
                )
                return [
                    MerchantRecord(
                        merchant_name=str(row["merchant_name"]).strip(),
                        outlet=str(row.get("outlet") or "").strip() or None,
                        channel=str(row.get("channel") or "any").strip() or "any",
                        mcc=str(row["mcc"]).strip(),
                        mcc_category=str(row["mcc_category"]).strip(),
                        confidence=str(row["confidence"]).strip(),
                        data_points=int(row.get("data_points") or 0),
                        last_verified=str(row.get("last_verified") or "").strip(),
                    )
                    for row in rows
                ]
            except (KeyError, TypeError, ValueError, RuntimeError, URLError):
                if self._backend == "supabase":
                    raise
        path = self._csv_path("merchant_mcc.csv")
        records = []
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                records.append(MerchantRecord(
                    merchant_name=row["merchant_name"].strip(),
                    outlet=row["outlet"].strip() or None,
                    channel=row["channel"].strip() or "any",
                    mcc=row["mcc"].strip(),
                    mcc_category=row["mcc_category"].strip(),
                    confidence=row["confidence"].strip(),
                    data_points=int(row["data_points"] or 0),
                    last_verified=row["last_verified"].strip(),
                ))
        return records

    def _load_cards(self) -> list[CardRule]:
        if self._should_use_supabase():
            try:
                rows = self._fetch_supabase_rows(
                    self._supabase_table("card_rules", "KIASUMILES_SUPABASE_CARDS_TABLE")
                )
                rules = []
                seen: set[str] = set()
                for row in rows:
                    cid = str(row["card_id"]).strip()
                    if cid in seen:
                        continue
                    seen.add(cid)
                    rules.append(CardRule(
                        card_id=cid,
                        card_name=str(row["card_name"]).strip(),
                        bank=str(row["bank"]).strip(),
                        network=str(row["network"]).strip(),
                        eligible_mccs=_parse_mccs(str(row.get("eligible_mccs") or "")),
                        earn_rate_mpd=float(row["earn_rate_mpd"]),
                        base_rate_mpd=float(row["base_rate_mpd"]),
                        cap_sgd=_parse_float_or_none(str(row.get("cap_sgd") or "")),
                        cap_period=str(row["cap_period"]).strip(),
                        min_spend=float(row.get("min_spend") or 0),
                        requires_amaze=_parse_bool(str(row.get("requires_amaze") or "")),
                        amaze_fee_pct=float(row.get("amaze_fee_pct") or 0),
                        eligible_merchants=_parse_mccs(str(row.get("eligible_merchants") or "")),
                        eligible_channels=_parse_mccs(str(row.get("eligible_channels") or "")),
                        caveat=str(row.get("caveat") or "").strip(),
                        last_verified=str(row.get("last_verified") or "").strip(),
                        source_url=str(row.get("source_url") or "").strip(),
                        earn_block_sgd=float(row.get("earn_block_sgd") or 1),
                    ))
                return rules
            except (KeyError, TypeError, ValueError, RuntimeError, URLError):
                if self._backend == "supabase":
                    raise
        path = self._csv_path("card_rules.csv")
        rules = []
        seen: set[str] = set()
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["card_id"].strip()
                if cid in seen:
                    continue
                seen.add(cid)
                rules.append(CardRule(
                    card_id=cid,
                    card_name=row["card_name"].strip(),
                    bank=row["bank"].strip(),
                    network=row["network"].strip(),
                    eligible_mccs=_parse_mccs(row["eligible_mccs"]),
                    earn_rate_mpd=float(row["earn_rate_mpd"]),
                    base_rate_mpd=float(row["base_rate_mpd"]),
                    cap_sgd=_parse_float_or_none(row["cap_sgd"]),
                    cap_period=row["cap_period"].strip(),
                    min_spend=float(row["min_spend"] or 0),
                    requires_amaze=_parse_bool(row["requires_amaze"]),
                    amaze_fee_pct=float(row["amaze_fee_pct"] or 0),
                    eligible_merchants=_parse_mccs(row.get("eligible_merchants", "")),
                    eligible_channels=_parse_mccs(row.get("eligible_channels", "")),
                    caveat=row.get("caveat", "").strip(),
                    last_verified=row.get("last_verified", "").strip(),
                    source_url=row.get("source_url", "").strip(),
                    earn_block_sgd=float(row.get("earn_block_sgd") or 1),
                ))
        return rules
