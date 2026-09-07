"""`BOT-125` — Vietnamese labels for the two exchange-environment enums.

@details One table per enum, and a guard test that every member has a
label. Deriving the text from the enum value (`"futures_testnet"` ->
`"Futures Testnet"`) would look like it works and then quietly produce
"Disabled" for the one member whose meaning a user most needs stated
plainly — `TradingVenue.DISABLED` does not mean "off" in a vague sense, it
means no order can leave this app at all, which is worth a whole sentence
rather than one word.

Labels carry the value in parentheses on purpose: the same strings appear
in `app_config.json`, in `EPIC-021`'s docs and in log lines, and a user
following any of those needs to recognise what they picked here.
"""

from __future__ import annotations

from Sagittarius_Elite_Warrior.src.domain.value_objects.market_data_venue import (
    MarketDataVenue,
)
from Sagittarius_Elite_Warrior.src.domain.value_objects.trading_venue import (
    TradingVenue,
)

MARKET_DATA_VENUE_LABELS: dict[MarketDataVenue, str] = {
    MarketDataVenue.MAINNET_PUBLIC: "Mainnet — giá thật, công khai (mainnet_public)",
    MarketDataVenue.FUTURES_TESTNET: "Futures Testnet — giá testnet (futures_testnet)",
}

TRADING_VENUE_LABELS: dict[TradingVenue, str] = {
    TradingVenue.DISABLED: "TẮT — không gửi lệnh đi đâu cả (disabled)",
    TradingVenue.FUTURES_TESTNET: (
        "BẬT — Futures Testnet, tiền giả lập (futures_testnet)"
    ),
}


def market_data_venue_label(venue: MarketDataVenue) -> str:
    return MARKET_DATA_VENUE_LABELS[venue]


def trading_venue_label(venue: TradingVenue) -> str:
    return TRADING_VENUE_LABELS[venue]
