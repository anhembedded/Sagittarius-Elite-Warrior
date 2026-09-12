# §1 — Tiêu chí cắt module

Một "module" chỉ được tồn tại khi qua **cả 6** tiêu chí dưới đây. Tiêu chí là thứ để **tranh luận
bằng bằng chứng** khi ai đó muốn thêm module thứ 5 hoặc gộp 2 module — không phải cảm nhận.

## 1.1 Sáu tiêu chí

| # | Tiêu chí | Câu hỏi kiểm tra | Nguồn |
| :-: | :--- | :--- | :--- |
| **C1** | **Ngôn ngữ riêng (Ubiquitous Language)** | Có ≥1 từ mang nghĩa **khác** ở đây so với nơi khác, đến mức code phải giữ 2 type? | DDD: bounded context = ranh giới của ngôn ngữ |
| **C2** | **Sở hữu dữ liệu / state riêng** | Có entity, state hoặc bảng mà **chỉ** module này được ghi? | DDD: Aggregate = đơn vị nhất quán giao dịch |
| **C3** | **Vòng đời & luật đổi khác nhau** | Thứ này đổi vì lý do gì, do ai, bao lâu một lần — khác với mảnh bên cạnh? | SRP ở mức module (Martin: "one reason to change") |
| **C4** | **Đứng được một mình để test** | `domain/` + `application/` chạy test **không** cần Qt, không cần module khác (chỉ cần `contracts/` của họ, mock được)? | Clean Architecture: independent testability |
| **C5** | **Có consumer thật ở ngoài, hoặc là màn hình của user** | Có ít nhất 1 module khác dùng `contracts/` của nó, **hoặc** nó sở hữu 1 màn hình/CLI user thật sự dùng? | `architecture-rule.md` §6.3: promote when a second consumer **actually** appears |
| **C6** | **Không phải kỹ thuật thuần** | Nếu bỏ hết nghiệp vụ, mảnh này còn lý do tồn tại không? Còn → **support**, không phải bounded context | Distillation: Generic subdomain |

**Ngưỡng gộp/tách:** tách khi C1 **và** C2 cùng đúng. Chỉ C3 đúng (đổi khác nhịp) → tách **file/
package** bên trong module (`architecture-rule.md` §5), chưa tách module. Chỉ C6 sai → là support.

## 1.2 Áp dụng lên app này — bằng chứng đo 2026-09-10

| Ứng viên | C1 | C2 | C3 | C4 | C5 | C6 | Kết luận |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :--- |
| `market_data` | ✅ *Candle* = dữ liệu thị trường (OHLCV, shard, gap) | ✅ SQLite shard, catalog JSON | ✅ đổi theo sàn/định dạng dữ liệu | ✅ | ✅ 4 màn + 2 CLI dispatch `GetHistoricalKlinesQuery` | ✅ | **Bounded context** |
| `trading` | ✅ *Position* = `LivePosition` **sàn báo về**, read-only (`domain/trading/live_position.py`: *"this app never computes any of its fields"*) | ✅ `TradingSessionState`, credentials, lệnh thật | ✅ đổi theo luật an toàn/venue | ✅ | ✅ `strategy` cần `IOrderSubmission`; CLI 3 lệnh | ✅ | **Bounded context** |
| `strategy` | ✅ *Signal*, *Arm*, `LiveStrategyConfig` — không tồn tại ở nơi khác | ✅ config chiến lược đang arm | ✅ đổi theo ý tưởng giao dịch — **nhịp nhanh nhất app** | ✅ | ✅ `backtesting` chạy nó; `trading` nhận lệnh từ nó | ✅ | **Bounded context — Core** |
| `backtesting` | ✅ *Position* = `_OpenPosition` **mô phỏng**, app tự mutate từng tick (`paper_exchange.py`) | ✅ kết quả run, trade log | ✅ đổi theo mô hình mô phỏng (fee, matching) | ✅ | ✅ 1 màn hình 12.309 dòng user dùng | ✅ | **Bounded context** |
| Account/Equity | ❌ chỉ là dẫn xuất của `ACCOUNT_UPDATE` | ❌ không state riêng | — | — | ❌ 1 consumer | — | **Ở trong `trading`**, ứng viên tách sau |
| Dev Board | ❌ không từ nào riêng — 59 tên trùng với Trading | ❌ | ❌ | — | — | — | **Không phải module** — là *surface* (§4) |
| `charting` (chart_card 27 file) | ❌ | ❌ | ✅ | — | ✅ 3 màn | ❌ **kỹ thuật thuần** | **Support** |
| `indicators` (toán chỉ báo) | ❌ | ❌ | ✅ | ✅ | ✅ strategy, backtest, dev board | ❌ | **Support** |
| `ui_kit` | ❌ | ❌ | ✅ | — | ✅ mọi màn | ❌ | **Support** |
| `binance_gateway` (`exchange_session_factory`, `binance_endpoints`, credentials, error translator) | ❌ | ❌ | ✅ đổi theo SDK sàn | ✅ | ✅ `market_data` **và** `trading` cùng dựng client từ một factory (guard test *only the session factory constructs binance client*) | ❌ | **Support** — ACL chung cho SDK |

**Hai `Position` là bằng chứng mạnh nhất**: cùng một từ, hai nghĩa, hai vòng đời, hai chủ được sửa —
code **đã** giữ 2 type riêng trước khi có tên gọi. Đó là định nghĩa sách giáo khoa của 2 bounded
context. Tương tự *Order* (lệnh thật vs fill mô phỏng), *Candle* (dữ liệu thị trường vs model để vẽ).

## 1.3 Anti-criteria — thứ **không** được dùng để cắt

- **Không cắt theo màn hình.** Trading và Dev Board dựng lại cùng nghiệp vụ → 59 chỗ trùng. Màn hình là
  *nơi treo* widget của module (§4), không phải chủ sở hữu nghiệp vụ.
- **Không cắt theo tầng kỹ thuật ở mức đầu.** `domain/`, `application/` ở mức đầu là hiện trạng gây bệnh
  (không ai sở hữu context); tầng chỉ tồn tại **bên trong** module (§3.2).
- **Không cắt vì "cho đẹp".** Mỗi module phải chỉ ra được C5: ai dùng nó.
- **Không cắt trước khi có consumer.** Account/Equity ở lại `trading` cho tới khi có consumer thứ hai
  thật — `EPIC-024C` bị huỷ chính vì đã định cắt "Market Connector / Market Order" trước bằng chứng.
