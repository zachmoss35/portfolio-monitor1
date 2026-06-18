"""Data models for portfolio monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class Flag(str, Enum):
    BUY = "buy"
    WATCH = "watch"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Holding:
    ticker: str
    shares: float
    cost_basis: float
    notes: str = ""


@dataclass
class Valuation:
    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    ev_to_ebitda: float | None = None


@dataclass
class MarketSnapshot:
    ticker: str
    company_name: str
    price: float
    previous_close: float
    daily_change: float
    daily_change_pct: float
    market_cap: float | None
    volume: int | None
    avg_volume: int | None
    volume_ratio: float | None
    change_30d_pct: float | None
    valuation: Valuation = field(default_factory=Valuation)
    sector: str = ""
    industry: str = ""


@dataclass
class EarningsEvent:
    ticker: str
    earnings_date: date | None
    days_to_earnings: int | None
    eps_estimate: float | None = None
    revenue_estimate: float | None = None


@dataclass
class NewsItem:
    ticker: str
    title: str
    publisher: str
    link: str
    published: datetime | None
    summary: str = ""
    is_material: bool = False


@dataclass
class SECFiling:
    ticker: str
    form_type: str
    filed_date: date
    description: str
    link: str
    is_new: bool = False


@dataclass
class ScreenerHit:
    ticker: str
    rule_name: str
    description: str
    severity: Flag
    field: str
    actual_value: float | str | None


@dataclass
class TickerAnalysis:
    holding: Holding
    market: MarketSnapshot
    earnings: EarningsEvent
    news: list[NewsItem] = field(default_factory=list)
    filings: list[SECFiling] = field(default_factory=list)
    screener_hits: list[ScreenerHit] = field(default_factory=list)
    flag: Flag = Flag.HOLD


@dataclass
class DailyReport:
    report_date: date
    analyses: list[TickerAnalysis]
    portfolio_value: float
    portfolio_cost: float
    portfolio_pnl: float
    portfolio_pnl_pct: float
