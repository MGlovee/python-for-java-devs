# P4 · 一个 HTTP 服务（选做冲刺）

> 本项目的完整可运行参考实现见 example/app.py，卡住 20 分钟以上再看。

| 项 | 值 |
|---|---|
| 交付物 | 一个 `app.py`：标准库 `http.server` 起的**只读 JSON 接口**（`/health`、`/api/items`、`/api/items/<id>`），进阶再换 FastAPI + uvicorn |
| 预计工时 | 4–6 小时（标准库版 3h + 进阶 2h） |
| 用到的课 | 全部——路由是 L01 分支、handler 类是 L05、错误分支是 L06、JSON 是 L10、HTTP 是 L11、后台线程是 L12、模块入口是 L09 |
| 依赖 | 标准库版**零第三方依赖**，离线可验收；FastAPI 版仅进阶（`pip install fastapi uvicorn`，未装不影响判分） |
| 验收 | `py verify.py`（9 条探测全 `[通过]`，退出码 0；服务用 OS 随机端口，测完必须关闭） |

---

## 1. 需求

- 数据：进程内列表（3–5 条 dict，含唯一 `id`）即可，不接数据库。分层：**数据层函数**与**HTTP 层 handler** 分开——Spring 的 Controller/Service 心智直接平移。
- 路由（全部 GET）：

| 路径 | 命中 | 未命中 |
|---|---|---|
| `/health` | 200 `{"status": "ok"}` | — |
| `/api/items` | 200 JSON 数组 | — |
| `/api/items/<id>` | 200 单个对象 | 400/404 见下 |
| 其他任意路径 | — | 404 |

- 硬性要求：
  - 每个响应都要 `Content-Type: application/json; charset=utf-8`，**404 也返回 JSON**（带 `error` 字段），
    不许把 `BaseHTTPRequestHandler` 的默认 HTML 错误页或 Python 堆栈吐给客户端；
  - **必须用 `argparse`**：`--host`（默认 127.0.0.1）、`--port`（默认 8000，`0` = OS 随机分配）；
  - 启动后立刻打印一行 `LISTENING http://<host>:<端口>`（**要 `flush=True`**，端口要打印实际值），
    便于脚本冒烟；`--help` 不得起服务；
  - Ctrl+C：捕获 `KeyboardInterrupt`，`shutdown()` + `server_close()` 后干净退出；
  - 端口被占用：友好报错、非 0 退出码、无 Traceback；
  - **import 本模块不得有任何副作用**（不 bind 端口、不 serve_forever、不读 stdin）。

## 2. 函数契约表（verify.py 按这个探测）

| 函数 | 签名 | 返回 | 异常 |
|---|---|---|---|
| `list_items` | `() -> list[dict]` | 全部条目（拷贝，调用方改不动全局） | 不抛 |
| `get_item` | `(item_id: int) -> dict \| None` | 命中返回该条，不存在返回 `None` | 不抛 |
| `create_server` | `(host="127.0.0.1", port=0) -> ThreadingHTTPServer` | **已在后台守护线程开始服务**的 server；`server.server_address[1]` 是真实端口 | 不抛 |
| `main` | `(argv=None) -> int` | 阻塞服务直到 Ctrl+C，退出码 | 捕获 KeyboardInterrupt |

`create_server` 是**为可测试性而存在的设计**：验收脚本用它以端口 0 起服务、发真 HTTP 请求、
再 `shutdown()`。Java 里你写 `@SpringBootTest` 注入随机端口，本质是同一件事。

## 3. 里程碑

| 阶段 | 目标 | 检查点 |
|---|---|---|
| M1 数据层 | `list_items`/`get_item` 写好，`py -c "import app; print(app.get_item(1))"` 能看到结果 | 探测 1、5（后半）绿 |
| M2 路由 | handler 的 `do_GET` 三条路由 + JSON 工具方法 | `py example版手动 curl 对比` 或直接跑探测 3–7 |
| M3 可测试性 | `create_server` 起在守护线程，port=0 | 探测 2、9 绿 |
| M4 CLI | argparse + `LISTENING` 行 + Ctrl+C 收尾 | 探测 8 绿；自己开两个终端起停一次 |

## 4. 验收标准（= verify.py 探测清单）

1. 模块可导入、三个契约函数就位、import 时未占端口。
2. `create_server(host, 0)` 返回已服务中的对象，真实端口可从 `server_address` 拿到。
3. `GET /health` → 200 + JSON Content-Type。
4. `GET /api/items` → JSON 数组、id 唯一。
5. `GET /api/items/<id>` → 对象与数据层一致；`get_item(不存在)` → `None`。
6. 不存在 id → 404 + 带 `error` 的 JSON。
7. 未知路径 → 404，无堆栈泄漏。
8. `--help` 列出 `--port/--host` 且不起服务（subprocess 实跑）。
9. `shutdown()+server_close()` 后端口拒绝连接。

**额外自拟一条**：实现 `POST /api/items`（请求体 JSON，name 必填否则 400），
并自己用 `urllib.request` 写一个 20 行的冒烟脚本验证。

## 5. 参考实现提示（代码在 example/app.py）

| 里程碑 | 关键思路 | 该用的标准库 |
|---|---|---|
| M2 | 一个 `_send_json(code, payload)` 私有方法统一写响应头/体；路由用 `re.match(r"^/api/items/(\d+)$")` | `http.server.BaseHTTPRequestHandler`、`json`、`re` |
| M3 | `ThreadingHTTPServer((host, port), Handler)` 后**必须** `threading.Thread(target=server.serve_forever, daemon=True).start()`，否则调用方拿不到控制权 | `http.server`、`threading`（L12） |
| M3 | 静音访问日志：子类覆写 `log_message(self, fmt, *args): pass` | L05 继承 |
| M4 | 主线程 `serve_forever()` 包 `try/except KeyboardInterrupt`，`finally` 里 `shutdown()+server_close()` | L06 |
| M4 | `port=0` 时实际端口看 `server.server_address[1]`；`LISTENING` 行要 `flush=True`（管道场景块缓冲） | — |

## 6. 常见错（Java 老手三连）

1. **把路由写成一串 if 却不兜底**。`/favicon.ico`、`//`、带 query 的路径都会打进来。
   先 `self.path.split("?", 1)[0]` 再匹配，最后必须有 `else: 404`。
2. **`send_header` 忘发 `Content-Length`，或响应体编码没转 bytes**。
   `wfile.write` 要的是 `bytes`：`json.dumps(...).encode("utf-8")`；漏 Content-Length 会让某些客户端一直等。
3. **handler 里异常裸奔**。数据层一个 `KeyError` 会让连接直接重置而不是 500 JSON。
   Java 有全局 `@ControllerAdvice`，这里你得自己在 `do_GET` 外层 `try/except` 兜住——
   更好的办法是让数据层根本不抛（返回 None），如契约所定。

## 7. 进阶：换成 FastAPI + uvicorn（对照代码）

先装依赖（需要联网）：

```powershell
pip install fastapi uvicorn
py projects/P4-一个HTTP服务/app.py     # 标准库版行为不变，verify 仍全绿
```

FastAPI 版完整对照（另存为 `app_fastapi.py` 体验即可，verify 不考它）：

```python
# app_fastapi.py —— py -m uvicorn app_fastapi:app --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="P4 进阶")
ITEMS = [
    {"id": 1, "name": "机械键盘", "done": True, "price": 399.0},
    {"id": 2, "name": "显示器支架", "done": False, "price": 159.5},
    {"id": 3, "name": "降噪耳机", "done": False, "price": 899.0},
]

class ItemIn(BaseModel):          # 相当于 Java 的 DTO + 校验注解
    name: str
    done: bool = False
    price: float = 0.0

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/items")
def list_items():
    return ITEMS

@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    for x in ITEMS:
        if x["id"] == item_id:
            return x
    raise HTTPException(status_code=404, detail="item not found")

@app.post("/api/items", status_code=201)
def create_item(payload: ItemIn):
    item = {"id": max(x["id"] for x in ITEMS) + 1, **payload.model_dump()}
    ITEMS.append(item)
    return item
```

对照着看你能发现：标准库版里你手写的 `_send_json`、路径正则、404 兜底，
FastAPI 全部替你做了——**先写过一遍裸的，才知道框架在赚什么**。
浏览器打开 `http://127.0.0.1:8000/docs` 就是自动生成的 Swagger。

继续推进的方向：CRUD 四动词补齐 → 数据层换 SQLite（接 P2）→ `pip install pytest httpx`
后用 `TestClient` 把本项目 9 条探测改写成 9 个 pytest 用例（L14）。

## 8. 回原文

| 想要 | 原文 |
|---|---|
| 前后端分离与 HTTP 接口概念 | [Day46-60/53.前后端分离开发入门.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day46-60/53.%E5%89%8D%E5%90%8E%E7%AB%AF%E5%88%86%E7%A6%BB%E5%BC%80%E5%8F%91%E5%85%A5%E9%97%A8.md) |
| RESTful 风格 API 设计 | [Day46-60/54.RESTful架构和DRF入门.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day46-60/54.RESTful%E6%9E%B6%E6%9E%84%E5%92%8CDRF%E5%85%A5%E9%97%A8.md) |
| 接口设计规范（错误码/版本） | [Day91-100/94.网络API接口设计.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day91-100/94.%E7%BD%91%E7%BB%9CAPI%E6%8E%A5%E5%8F%A3%E8%AE%BE%E8%AE%A1.md) |
| Django 全景（和 Spring 同心智，读一遍就够） | [Day46-60/46.Django快速上手.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day46-60/46.Django%E5%BF%AB%E9%80%9F%E4%B8%8A%E6%89%8B.md) |
| 线程与并发（serve_forever 放哪跑） | [Day61-65/63.Python中的并发编程-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-1.md) |
| 接口文档示例 | [番外篇/接口文档参考示例.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3%E5%8F%82%E8%80%83%E7%A4%BA%E4%BE%8B.md) |

主索引与判分机制见 [../../README.md](../../README.md)。四个项目全部完成后，
把 P1–P4 各写一行放进简历——这就是"会用 Python 干活"的证据。
