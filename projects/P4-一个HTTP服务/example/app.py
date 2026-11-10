#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4 参考实现 —— 标准库 http.server 的只读 JSON 接口（零第三方依赖）。

用法：
    py example/app.py                # 默认 127.0.0.1:8000
    py example/app.py --port 9000    # 指定端口；端口填 0 让操作系统随机分配

接口：
    GET /health            -> {"status": "ok"}
    GET /api/items         -> [{id,name,done,price}, ...]
    GET /api/items/<id>    -> 单个对象；不存在 -> 404 {"error": ...}
    其他路径               -> 404

create_server() 返回一个**已在后台线程开始服务**的 ThreadingHTTPServer，
供验收脚本以端口 0 起停探测；Ctrl+C 优雅退出。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

ITEMS: list[dict] = [
    {"id": 1, "name": "机械键盘", "done": True, "price": 399.0},
    {"id": 2, "name": "显示器支架", "done": False, "price": 159.5},
    {"id": 3, "name": "降噪耳机", "done": False, "price": 899.0},
]

_ITEM_PATH = re.compile(r"^/api/items/(\d+)$")


def list_items() -> list[dict]:
    """数据访问层：返回全部条目（拷贝，防止调用方改到全局）。"""
    return [dict(x) for x in ITEMS]


def get_item(item_id: int) -> Optional[dict]:
    """按 id 查一条；不存在返回 None。"""
    for x in ITEMS:
        if x["id"] == item_id:
            return dict(x)
    return None


class ApiHandler(BaseHTTPRequestHandler):
    """路由只有三条 GET；POST/PUT/DELETE 留给 FastAPI 进阶版。"""

    server_version = "P4-Learner/1.0"

    def _send_json(self, code: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - 方法名是 http.server 规定的
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send_json(200, {"status": "ok"})
        elif path == "/api/items":
            self._send_json(200, list_items())
        else:
            m = _ITEM_PATH.match(path)
            if m:
                item = get_item(int(m.group(1)))
                if item is None:
                    self._send_json(404, {"error": f"item {m.group(1)} not found"})
                else:
                    self._send_json(200, item)
            else:
                self._send_json(404, {"error": f"no route for {path}"})

    def log_message(self, fmt: str, *args) -> None:  # 静音访问日志
        pass


def create_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    """创建并【启动】服务：port=0 由 OS 分配端口；返回带后台线程的 server 对象。

    调用方负责 server.shutdown() + server.server_close()。
    """
    server = ThreadingHTTPServer((host, port), ApiHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="P4：标准库实现的只读 JSON 接口")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000,
                   help="监听端口，0 = 随机分配（默认 8000）")
    args = p.parse_args(argv)

    try:
        server = ThreadingHTTPServer((args.host, args.port), ApiHandler)
    except OSError as exc:
        print(f"错误：无法监听 {args.host}:{args.port} —— {exc}", file=sys.stderr)
        return 2

    host, port = server.server_address[0], server.server_address[1]
    # flush=True：stdout 被重定向到管道时是块缓冲，不刷行验收/冒烟脚本会读不到这行
    print(f"LISTENING http://{host}:{port}", flush=True)
    print("GET /health | /api/items | /api/items/<id>；Ctrl+C 退出")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C，关闭中……")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
