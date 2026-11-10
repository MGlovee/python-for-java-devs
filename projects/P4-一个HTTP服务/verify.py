#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4 验收脚本 —— 只用标准库（urllib 探测 HTTP 行为，端口 0 随机分配，测完必关）。

用法：
    py projects/P4-一个HTTP服务/verify.py               # 验收项目根下的 app.py
    py projects/P4-一个HTTP服务/verify.py example/app.py # 先验参考实现

退出码：0 = 没有红色项；1 = 有未过项或还没写 app.py。
"""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
TIMEOUT = 5
stats = {"通过": 0, "未过": 0, "缺依赖": 0}
sys.dont_write_bytecode = True  # 判分不在仓库留 __pycache__


class MissingDep(Exception):
    pass


def _call_with_timeout(func):
    box: dict = {}

    def target():
        try:
            func()
        except BaseException as exc:  # noqa: BLE001
            box["exc"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(TIMEOUT)
    if t.is_alive():
        raise TimeoutError(f"单条探测超过 {TIMEOUT}s，多半是服务没在后台线程 serve_forever")
    if "exc" in box:
        raise box["exc"]


def _probe(title: str, guide: str, func):
    try:
        _call_with_timeout(func)
        stats["通过"] += 1
        print(f"[通过] {title}")
    except MissingDep as exc:
        stats["缺依赖"] += 1
        print(f"[缺依赖] {title} — {exc}（不计失败，装上后重跑）")
    except AssertionError as exc:
        stats["未过"] += 1
        print(f"[未过] {title} — {exc or '断言失败'}。{guide}")
    except Exception as exc:  # noqa: BLE001
        stats["未过"] += 1
        print(f"[未过] {title} — 抛了 {type(exc).__name__}: {exc}。{guide}")


def _load(app_path: Path):
    name = "p4_target_app"
    sys.path.insert(0, str(app_path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, app_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载 {app_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    except ModuleNotFoundError as exc:
        raise MissingDep(f"pip install {exc.name}") from exc


def _get(base: str, path: str):
    """返回 (status, content_type, body_bytes)；404 也正常拿到响应。"""
    try:
        with urllib.request.urlopen(base + path, timeout=2) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.headers.get("Content-Type", "") if err.headers else "", err.read()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) > 1:
        raw = Path(sys.argv[1])
        candidates = [raw]
        if not raw.is_absolute():
            candidates += [PROJECT / raw, Path.cwd() / raw]
        target = next((c for c in candidates if c.is_file()), None)
    else:
        target = PROJECT / "app.py" if (PROJECT / "app.py").is_file() else None
        if target is None and (Path.cwd() / "app.py").is_file():
            target = Path.cwd() / "app.py"

    if target is None:
        print("还没有 app.py。先从 example/ 参考实现看起：")
        print(f"    py {Path(__file__)} example/app.py   # 确认验收脚本本身是绿的")
        return 1
    target = target.resolve()
    print(f"验收对象：{target}")
    print("=" * 60)

    holder: dict = {}

    def load():
        holder["mod"] = _load(target)
        mod = holder["mod"]
        missing = [f for f in ("create_server", "list_items", "get_item")
                   if not callable(getattr(mod, f, None))]
        assert not missing, f"缺少契约函数：{missing}，见 README 函数契约表"

    _probe("1. 模块可导入：create_server/list_items/get_item 就位，import 时未占用端口",
           "回到 L09：起服务的代码必须收在 __main__ 守卫里。", load)
    if "mod" not in holder:
        print("-" * 60)
        print("模块加载失败，其余探测无法进行。")
        return 1
    mod = holder["mod"]

    try:  # finally 保证任何情况下都关服、不留监听线程
        # ---- 2. create_server 起得来 ----
        def p2():
            srv = mod.create_server("127.0.0.1", 0)
            holder["srv"] = srv
            assert callable(getattr(srv, "shutdown", None)), \
                "返回值要有 shutdown()（ThreadingHTTPServer 即可）"
            assert callable(getattr(srv, "server_close", None)), "还要有 server_close()"
            port = srv.server_address[1]
            assert isinstance(port, int) and port != 0, f"server_address 里拿不到真实端口：{srv.server_address}"
            base = f"http://127.0.0.1:{port}"
            holder["base"] = base
            status, _, _ = _get(base, "/health")
            assert status == 200, f"创建后 /health 应可达，得到 {status}（忘了在后台线程 serve_forever？）"
        _probe("2. create_server(host, port=0) 返回【已在后台服务中】的对象，端口由 OS 分配",
               "回到 L12：serve_forever 要放到守护线程里，主线程不能阻塞。", p2)

        if "base" in holder:
            base = holder["base"]

            # ---- 3. /health ----
            def p3():
                status, ctype, body = _get(base, "/health")
                assert status == 200, f"应为 200，得到 {status}"
                assert "application/json" in ctype, f"Content-Type 应为 JSON：{ctype!r}"
                assert json.loads(body).get("status") == "ok", f"体不对：{body[:80]!r}"
            _probe("3. GET /health 返回 200 + Content-Type: application/json",
                   "回到 L11：HTTP 响应三件套（状态行/头/体），send_header 别漏。", p3)

            # ---- 4. 列表 ----
            def p4():
                status, _, body = _get(base, "/api/items")
                assert status == 200, f"应为 200，得到 {status}"
                data = json.loads(body)
                assert isinstance(data, list) and len(data) >= 1, f"应为非空 JSON 数组：{data!r}"
                ids = [x["id"] for x in data]
                assert len(ids) == len(set(ids)), f"id 应唯一：{ids}"
            _probe("4. GET /api/items 返回 JSON 数组且 id 唯一",
                   "回到 L10：json.dumps 整个 list；L05：数据层返回 dict 拷贝。", p4)

            # ---- 5. 详情（进程内 + HTTP 双验） ----
            def p5():
                data = json.loads(_get(base, "/api/items")[2])
                first_id = data[0]["id"]
                status, _, body = _get(base, f"/api/items/{first_id}")
                assert status == 200, f"已存在 id 应 200，得到 {status}"
                assert json.loads(body)["id"] == first_id, "详情与列表对不上"
                got = mod.get_item(first_id)
                assert isinstance(got, dict) and got["id"] == first_id, f"get_item 契约不符：{got!r}"
                assert mod.get_item(987654321) is None, "不存在的 id 应返回 None"
            _probe("5. GET /api/items/<id> 命中返回该对象；get_item 数据层行为一致",
                   "回到 L03：正则从路径提 id；L05：路由/数据分两层。", p5)

            # ---- 6. 不存在 → 404 ----
            def p6():
                status, _, body = _get(base, "/api/items/987654321")
                assert status == 404, f"应 404，得到 {status}"
                payload = json.loads(body)
                assert "error" in payload, f"404 也要返回 JSON 且带 error 字段：{payload!r}"
            _probe("6. 不存在的 id：404 且响应体是带 error 的 JSON",
                   "回到 L06：404 是业务分支不是异常；别让 BaseHTTPRequestHandler 吐默认 HTML 错误页。", p6)

            # ---- 7. 未知路由 ----
            def p7():
                status, _, body = _get(base, "/api/nope")
                assert status == 404, f"未知路径应 404，得到 {status}"
            _probe("7. 未知路径统一 404，不泄漏堆栈",
                   "回到 L06：handler 里任何异常都会变 500/断连，路由兜底 else 返 404。", p7)

        # ---- 8. CLI --help ----
        def p8():
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            proc = subprocess.run([sys.executable, str(target), "--help"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=TIMEOUT, env=env)
            assert proc.returncode == 0, f"--help 应 0 退出，得到 {proc.returncode}"
            assert "--port" in proc.stdout, f"帮助里看不到 --port：{proc.stdout[:150]!r}"
        _probe("8. CLI：--help 列出 --port/--host（argparse），且 --help 不起服务",
               "回到 L09：argparse 解析发生在 main()，import 阶段不碰网络。", p8)

        # ---- 9. 优雅关闭 ----
        def p9():
            srv = holder.get("srv")
            assert srv is not None, "第 2 条没起成服务，本条无从谈起"
            port = srv.server_address[1]
            srv.shutdown()
            srv.server_close()
            holder["closed"] = True
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=2):
                    raise AssertionError("shutdown + server_close 后端口竟仍可连接")
            except OSError:
                pass  # 拒绝连接 = 关干净了
        _probe("9. shutdown()+server_close() 后端口关闭，无残留监听",
               "回到 L12：serve_forever 与 shutdown 配对；finally 里收尾。", p9)
    finally:
        srv, closed = holder.get("srv"), holder.get("closed", False)
        if srv is not None and not closed:
            try:
                srv.shutdown()
                srv.server_close()
            except OSError:
                pass

    print("=" * 60)
    print(f"结果：通过 {stats['通过']}，未过 {stats['未过']}，缺依赖 {stats['缺依赖']}")
    return 0 if stats["未过"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(130)
