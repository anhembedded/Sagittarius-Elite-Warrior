from __future__ import annotations

from unittest.mock import Mock

from Sagittarius_Elite_Warrior.src.application.ports.i_exchange_credentials_provider import (
    CredentialsSource,
    ResolvedCredentials,
)
from Sagittarius_Elite_Warrior.src.application.use_cases.queries.get_open_positions import (
    GetOpenPositionsQuery,
    GetOpenPositionsQueryHandler,
)
from Sagittarius_Elite_Warrior.src.domain.value_objects.exchange_credentials import (
    ExchangeCredentials,
)

_CREDENTIALS = ResolvedCredentials(
    ExchangeCredentials(api_key="key", api_secret="secret"), CredentialsSource.FILE
)

_POSITION_PAYLOAD = {
    "symbol": "BTCUSDT",
    "positionAmt": "0.01",
    "entryPrice": "64000",
    "markPrice": "64100",
    "unRealizedProfit": "1",
    "leverage": "10",
    "marginType": "cross",
}


def _handler(raw_client: Mock) -> GetOpenPositionsQueryHandler:
    session_factory = Mock()
    session_factory.create_trading_client.return_value = raw_client
    credentials_provider = Mock()
    credentials_provider.resolve.return_value = _CREDENTIALS
    metadata_provider = Mock()
    return GetOpenPositionsQueryHandler(
        session_factory, credentials_provider, metadata_provider
    )


def test_execute_reads_positions_through_a_freshly_built_trading_client() -> None:
    """Builds its own `FuturesTradingClient` from the always-registered
    session-factory/credentials/metadata collaborators rather than taking
    `ITradingClient` directly — see the handler's own docstring for why
    (`ITradingClient` is only registered when trading is enabled, and
    every use case must stay constructible regardless)."""
    raw_client = Mock()
    raw_client.futures_position_information.return_value = [_POSITION_PAYLOAD]
    handler = _handler(raw_client)

    result = handler.execute(GetOpenPositionsQuery())

    assert len(result) == 1
    assert result[0].symbol == "BTCUSDT"
    raw_client.futures_position_information.assert_called_once_with()


def test_execute_returns_empty_tuple_when_flat() -> None:
    raw_client = Mock()
    raw_client.futures_position_information.return_value = []
    handler = _handler(raw_client)

    assert handler.execute(GetOpenPositionsQuery()) == ()
