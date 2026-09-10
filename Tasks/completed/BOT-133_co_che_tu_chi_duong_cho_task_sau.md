# BOT-133 — Cơ chế tự chỉ đường: task sau không cần đọc tài liệu mới làm đúng

**Trạng thái:** ✅ Hoàn thành (2026-09-10)
**Nguồn:** user, ngay sau khi `BOT-132` merge và **chính user dính lỗi engine cũ**:
*"I want you make sure if any feature be develop later will aknowgale how to you corrent method.
I mean the mechanical must hint it self."*
**Rủi ro:** 🟢 — thêm guard + một validator lúc boot; không đổi hành vi UI nào.
**Độ phức tạp:** 🟡 `M`

---

## 1. Vấn đề

`BOT-132` sửa xong cơ chế nhúng QML, nhưng để lại **ba lỗ hổng cùng một dạng**: người viết task
sau chỉ làm đúng nếu họ *đọc tài liệu*. Tài liệu thì trôi — chính repo này ghi nhận `PLAYBOOK.md`,
`Handover.md`, `.agents/context/` đều từng sai. Và bằng chứng gần nhất không phải giả định:

- `qml-rule.md` đã tồn tại suốt thời gian 10 host copy-paste `setClearColor(transparent)`. Một
  dòng luật **không chặn được** bản chép thứ 10.
- Comment của `EPIC-006F` (*"no QML left in this app"*) còn **chỉ sai đường** cho người đọc kế
  tiếp về việc mồi theme, suốt từ khi `EPIC-015` đưa QML trở lại.
- Ngay trong lúc làm task này, guard mới tìm ra **bản chép thứ 7** của việc mồi theme
  (`components/chart_card/__main__.py`) — chưa ai biết nó tồn tại.

Cộng thêm lỗi user vừa gặp thật: app đúng, engine trong venv cũ → `TypeError:
create_quick_widget() got an unexpected keyword argument 'background'` **ở giữa constructor của
`PositionsPanel` lúc boot**. `install-rule.md` §1 đã ghi lớp lỗi này 3 lần (`BUG-044`, `BUG-054`,
`BUG-055`), **cả 3 lần đều bị chẩn đoán sai** thành "app gọi API không tồn tại". Đây là lần thứ 4.

Kết luận: chỗ nào còn phải *nhớ* thì chỗ đó sẽ hỏng. Việc của task này là chuyển từ **nhớ** sang
**không gõ sai được**.

## 2. Ba cơ chế đã thêm

| # | Cơ chế | Chặn cái gì | Hỏng thì báo gì |
| :-: | :--- | :--- | :--- |
| 1 | `infrastructure/engine_adapters/engine_capabilities.py` + `EngineCapabilityValidatorExtension` | engine trong venv **cũ hơn** source app | fail-fast lúc boot, nêu đúng API thiếu, task sinh ra nó, và **lệnh cài lại** |
| 2 | `test_quick_widget_only_in_embed.py` (viết lại bằng `ast`) | dựng/kế thừa `QQuickWidget`, `setClearColor(`, và **mồi theme** ngoài đúng một nơi | tên API phải dùng thay thế |
| 3 | docstring ở `qml/__init__.py`, `kit/style.py::background_token`, `theme_bootstrap.py` | người mới mở package không thấy cơ chế | chỉ thẳng `QuickSurface` / `seed_app_theme()` |

### 2.1 Preflight engine — khai báo, không phải đâm vào rồi mới biết

`REQUIRED_ENGINE_CAPABILITIES` khai báo **API engine mà source app hiện đang gọi và có khả năng
thiếu ở bản cài cũ**: module, symbol, *tham số* (đây mới là ca thật — hàm có, tham số không, nên
`pip show` vô dụng vì hai bản cùng version `2.3.0`), và task sinh ra phụ thuộc đó.

Thêm một phụ thuộc mới về sau = **thêm một dòng**. Đó chính là phần "tự chỉ đường": không phải
viết thêm tài liệu nào, lần stale-build kế tiếp tự giải thích.

Cố ý **không** liệt kê mọi thứ app import — một danh sách không ai giữ đúng được còn tệ hơn không
có (đúng thứ `ONBOARDING.md` §12.2 phàn nàn). Chỉ những API mới thêm/mới đổi chữ ký.

Thứ tự trong `main.py` có chủ đích: `DependencyValidatorExtension` (có cài chưa?) → **capability**
(cài rồi nhưng đủ mới chưa?) → `AssetValidatorExtension` (icon còn không?). Engine thiếu hẳn thì
báo "chưa cài", không phải một danh sách attribute khó hiểu.

### 2.2 Guard đọc AST, không đọc text

Bản nháp đầu dùng regex và **đỏ ngay trên chính tài liệu của các API đó**: docstring `style.py`
giải thích khi nào app phải tự gọi `get_theme_bridge(palette)`, comment `app_bootstrapper.py` kể
lịch sử `configure_app_qml()`. Một guard phạt đúng những comment làm cơ chế dễ tìm là guard sai.
Viết lại bằng `ast`: chỉ tính **lời gọi thật** và **base class thật**.

Chi tiết đáng giữ: guard chỉ chặn `get_theme_bridge(<có tham số>)`. Gọi trần
`get_theme_bridge()` là *đọc* singleton đã mồi — hợp lệ ở mọi nơi. Phân biệt được hai ca đó là lý
do phải dùng AST chứ không phải grep.

### 2.3 Mutation-verify (`testing-rule.md` §2)

Không tin guard chỉ vì nó xanh. Cấy vi phạm thật vào `qml/host.py` (dựng `QQuickWidget()`, gọi
`setClearColor(...)`, gọi `configure_app_qml(...)`) → **cả 3 test đỏ đúng cái cần đỏ**; gỡ ra →
xanh lại. Có làm thì mới biết guard thật sự bắt.

## 3. Kiểm thử

- `tests/unit/infrastructure/engine_adapters/test_engine_capabilities.py` — 8 test: bản engine
  **đang cài** thoả mọi khai báo (nửa "sống" của guard); thiếu attribute / thiếu tham số / module
  không import được đều báo riêng; report có lệnh cài lại và câu *"not a bug in the app"*;
  extension im lặng khi engine đủ mới, `SystemExit(1)` khi không.
- `test_quick_widget_only_in_embed.py` — 4 test (3 guard + 1 chống-mục-rữa), mutation-verified.
- Gate đầy đủ: xem §5.

## 4. Cái không làm, và vì sao

- **Không** thêm shim để app chạy được với engine cũ. Shim đó sẽ âm thầm trả lại nền trắng/đen —
  đúng bug vừa sửa. Hỏng to, hỏng sớm, hỏng kèm cách sửa là đúng hướng.
- **Không** pin engine bằng version trong `requirements.txt`: hai bản engine khác nhau cùng report
  `2.3.0` (`install-rule.md` ghi rõ), nên pin theo version không phát hiện được gì. Kiểm tra
  **capability** là thứ đo được thật.
- **Không** đưa `StyleRole` sang engine để engine tự biết token. `ui-architecture.md` §4 của engine
  cấm runtime biết app; ranh giới đó giữ `TASK-042` tái dùng được cho consumer khác.


## 5. Bằng chứng — đo trên chính ca đã xảy ra

Tái hiện đúng tình huống user gặp: giữ nguyên source app, đưa working tree của engine về `main`
(bản chưa có `TASK-042`), rồi boot app thật (`--self-check`).

| | Trước `BOT-133` | Sau `BOT-133` |
| :--- | :--- | :--- |
| Nơi lỗi nổ | giữa `PositionsPanel.__init__`, sau khi đã boot xong engine + dựng MainWindow | **bước pre-flight**, trước khi dựng widget nào |
| Thông báo | `TypeError: create_quick_widget() got an unexpected keyword argument 'background'` | nêu API thiếu + task sinh ra nó + **lệnh cài lại** + câu *"This is not a bug in the app"* |
| Traceback | 9 khung, kết thúc trong code UI | không có traceback — không phải crash |
| Đếm `PositionsPanel`/`TypeError` trong log | nhiều | **0** |

Nguyên văn dòng đầu sau khi sửa:

```
CRITICAL FAULT: the installed `sagittarius_engine` build is older than this app's source.
The following engine APIs this app depends on are missing:
    - sagittarius_engine.extensions.pyside_mvc.create_quick_widget(..., background=...)
      [TASK-042 (engine) / BOT-132 (app)] — parameter 'background' missing from () -> 'QQuickWidget'
...
    pip install --upgrade --force-reinstall git+https://github.com/anhembedded/Sagittarius_Engine.git
```

Với engine đúng bản: boot đi qua `Pre-flight engine check passed`, tới `UI Layer Ready`, thoát
`App stopped.`, exit code 0 — đúng thứ tự `DependencyValidator` → **`EngineCapabilityValidator`**
→ `AssetValidator` đã thiết kế ở §2.1.
