from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path


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


_BUNDLED = Path(__file__).parent


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
    def __init__(self) -> None:
        self._merchants: list[MerchantRecord] | None = None
        self._cards: list[CardRule] | None = None

    def merchants(self) -> list[MerchantRecord]:
        if self._merchants is None:
            self._merchants = self._load_merchants()
        return self._merchants

    def cards(self) -> list[CardRule]:
        if self._cards is None:
            self._cards = self._load_cards()
        return self._cards

    def _load_merchants(self) -> list[MerchantRecord]:
        path = _BUNDLED / "merchant_mcc.csv"
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
        path = _BUNDLED / "card_rules.csv"
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
                ))
        return rules
