# EPIC-025B — Phase 1: `modules/trading`; Trading and Dev Board become composition surfaces

- **Status:** 🔴 Backlog
- **Repository:** Elite
- **Blocked by:** A · **Blocks:** C
- **Read first:** HLD §3.4 (the contracts of `trading`), §4.2–§4.5 (the Trading and Dev Board
  surfaces, `dev_probe`); ADR D4, D12. **The highest-risk phase of the epic**: `TradingSessionState`
  is mutable state shared by three Presenters, three handlers and the websocket thread.

## 1. What to do

1. `modules/trading/`: today's `domain/trading`, `use_cases/trading` (except arm/disarm, which go
   to `strategy` in Phase 2 and are kept on the allowlist until then), the trading side of
   `infrastructure/binance` (futures REST and the user-data stream), credentials handling,
   `PositionRefreshService` (`BUG-117`) — `trading` **owns** the positions read model.
2. `contracts/`: `IOrderSubmission`, `ITradingSession` (including `claim_symbol` /
   `release_symbol`), `IAccountSnapshot`; the DTOs `PositionSnapshot`, `OpenOrderSnapshot`,
   `TradingSessionSnapshot`, `AccountSnapshot`; the events `OrderFilled`, `PositionChanged`,
   `PositionClosed`, `EquitySampled`, `TradingSessionChanged`.
3. Contributed widgets: the positions table, the open orders table, the manual order card, the
   session controls (enable / disable / emergency stop), account and equity — **one** of each, with
   its Python wrapper under `modules/trading/ui/`.
4. `screens/trading` and `screens/dashboard` become `surfaces/trading/` and `surfaces/dev_board/`:
   layout plus widget registration by contribution only, **zero business logic**. Dev Board is
   gated by `dev.mode` and hosts `dev_probe`s; the first probe is trading's "Exchange API tester",
   which calls the real adapter.
5. The 9 items in `ui/common/` used only by these two screens move into `modules/trading` (the
   strategy-related ones move in Phase 2).

## 2. Done when

- The script counting duplicated member names between `trading` and `dashboard` reports **59 → 0**
  (the number is written into the pull request).
- The user runs Testnet: placing a manual order, cancelling, enabling and disabling trading, PnL
  updating — all behave as before (the regression tests for `BUG-112 / 116 / 117` stay green).
