"""Tech KG Engine 压力测试

覆盖：并发写入、批量导入、并发查询、图遍历、混合读写
输出：各场景的 QPS / 平均延迟 / P95 / P99 / 错误率
运行方式：python stress_test.py
"""

import json
import os
import random
import string
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

CONFIG = {
    "并发写入节点": {"workers": 10, "total": 500},
    "并发写入边":   {"workers": 10, "total": 500},
    "批量导入节点": {"batches": 5, "batch_size": 200},
    "批量导入边":   {"batches": 5, "batch_size": 200},
    "并发查询":     {"workers": 20, "total": 500},
    "图遍历":       {"workers": 10, "total": 200},
    "混合读写":     {"workers": 20, "total": 500, "write_ratio": 0.3},
}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def api(method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
    """发送 HTTP 请求"""
    from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(path)
    encoded_path = quote(parsed.path, safe="/")
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        flat = {k: v[0] for k, v in params.items()}
        encoded_query = urlencode(flat)
    else:
        encoded_query = ""
    encoded_full = urlunparse(("", "", encoded_path, "", encoded_query, ""))
    url = f"{BASE}{encoded_full}"

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, e.read().decode()
    except Exception as e:
        return -1, str(e)


def percentile(sorted_data: list[float], p: float) -> float:
    """计算百分位数"""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def print_report(name: str, latencies: list[float], errors: int, total: int):
    """打印测试报告"""
    ok = [l for l in latencies if l >= 0]
    ok.sort()
    qps = len(ok) / sum(ok) if sum(ok) > 0 else 0
    avg = sum(ok) / len(ok) if ok else 0
    p50 = percentile(ok, 50)
    p95 = percentile(ok, 95)
    p99 = percentile(ok, 99)
    err_rate = errors / total * 100 if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  请求总数:  {total}")
    print(f"  成功数:    {len(ok)}")
    print(f"  错误数:    {errors} ({err_rate:.1f}%)")
    print(f"  QPS:       {qps:.1f}")
    print(f"  平均延迟:  {avg*1000:.1f} ms")
    print(f"  P50:       {p50*1000:.1f} ms")
    print(f"  P95:       {p95*1000:.1f} ms")
    print(f"  P99:       {p99*1000:.1f} ms")

    return {
        "name": name,
        "total": total,
        "success": len(ok),
        "errors": errors,
        "error_rate": round(err_rate, 2),
        "qps": round(qps, 1),
        "avg_ms": round(avg * 1000, 1),
        "p50_ms": round(p50 * 1000, 1),
        "p95_ms": round(p95 * 1000, 1),
        "p99_ms": round(p99 * 1000, 1),
    }


def random_name(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_chinese_name() -> str:
    """随机生成中文姓名"""
    surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张"
    given = "伟芳敏静丽强磊洋勇艳杰娟涛明超秀霞平刚桂英华"
    return random.choice(surnames) + random.choice(given) + random.choice(given)


def random_tech_name() -> str:
    prefixes = ["深度", "大规模", "分布式", "高效", "自适应", "多模态"]
    cores = ["知识图谱", "图神经网络", "自然语言处理", "推荐系统", "搜索引擎", "对话系统", "图像识别"]
    return random.choice(prefixes) + random.choice(cores)


# ---------------------------------------------------------------------------
# 准备数据
# ---------------------------------------------------------------------------

def prepare_test_data():
    """创建用于查询和遍历的基础数据"""
    print("准备基础测试数据...")

    # 清空
    api("POST", "/query/write", {"query": "MATCH (n) DETACH DELETE n"})

    # 创建节点池
    node_ids = []
    tech_ids = []
    org_ids = []

    # 50个人物
    for i in range(50):
        status, resp = api("POST", "/nodes", {
            "labels": ["压测人物"],
            "properties": {
                "name": f"人物_{i:04d}",
                "年龄": random.randint(22, 55),
                "职称": random.choice(["工程师", "高级工程师", "研究员", "教授", "学生"]),
                "研究方向": random.choice(["知识图谱", "自然语言处理", "图神经网络", "推荐系统"]),
                "h指数": random.randint(1, 50),
                "在职": True,
            }
        })
        if status == 200 and isinstance(resp, dict) and resp.get("success"):
            node_ids.append(resp["data"]["id"])

    # 20个技术
    for i in range(20):
        status, resp = api("POST", "/nodes", {
            "labels": ["压测技术"],
            "properties": {
                "name": f"技术_{i:04d}",
                "领域": random.choice(["人工智能", "深度学习", "数据挖掘"]),
                "成熟度": random.choice(["萌芽期", "成长期", "成熟期"]),
                "相关论文数": random.randint(100, 100000),
            }
        })
        if status == 200 and isinstance(resp, dict) and resp.get("success"):
            tech_ids.append(resp["data"]["id"])

    # 10个机构
    for i in range(10):
        status, resp = api("POST", "/nodes", {
            "labels": ["压测机构"],
            "properties": {
                "name": f"机构_{i:04d}",
                "类型": "高校",
                "所在地": random.choice(["北京", "上海", "杭州", "深圳", "南京"]),
            }
        })
        if status == 200 and isinstance(resp, dict) and resp.get("success"):
            org_ids.append(resp["data"]["id"])

    # 创建关系：人物↔人物、人物→技术、人物→机构、技术→技术
    edge_types_person = ["合作", "指导", "共事"]
    edge_types_tech = ["依赖", "应用于", "结合"]

    for _ in range(100):
        if len(node_ids) >= 2:
            a, b = random.sample(node_ids, 2)
            api("POST", "/edges", {
                "source_id": a, "target_id": b,
                "edge_type": random.choice(edge_types_person),
                "properties": {"合作项目": random_tech_name(), "开始年份": random.randint(2018, 2025)}
            })

    for nid in node_ids:
        if tech_ids:
            tid = random.choice(tech_ids)
            api("POST", "/edges", {
                "source_id": nid, "target_id": tid,
                "edge_type": "研究",
                "properties": {"角色": random.choice(["研究者", "核心贡献者"]), "年限": random.randint(1, 15)}
            })
        if org_ids:
            oid = random.choice(org_ids)
            api("POST", "/edges", {
                "source_id": nid, "target_id": oid,
                "edge_type": "隶属于",
                "properties": {"部门": random.choice(["计算机系", "智能学院", "数据科学中心"])}
            })

    for _ in range(20):
        if len(tech_ids) >= 2:
            a, b = random.sample(tech_ids, 2)
            api("POST", "/edges", {
                "source_id": a, "target_id": b,
                "edge_type": random.choice(edge_types_tech),
                "properties": {"描述": random_tech_name()}
            })

    print(f"  已创建: {len(node_ids)}个人物, {len(tech_ids)}个技术, {len(org_ids)}个机构")
    print(f"  基础数据准备完成\n")
    return node_ids, tech_ids, org_ids


# ---------------------------------------------------------------------------
# 压测场景
# ---------------------------------------------------------------------------

def bench_concurrent_write_nodes(workers: int, total: int):
    """场景1: 并发写入节点"""
    print(f"\n>>> 场景1: 并发写入节点 (workers={workers}, total={total})")

    def write_one(idx):
        start = time.monotonic()
        status, resp = api("POST", "/nodes", {
            "labels": ["压测写入节点"],
            "properties": {
                "name": f"stress_node_{idx:06d}",
                "年龄": random.randint(20, 60),
                "职称": random.choice(["工程师", "研究员", "教授"]),
                "在职": True,
                "分数": round(random.uniform(0, 100), 1),
            }
        })
        elapsed = time.monotonic() - start
        ok = status == 200 and isinstance(resp, dict) and resp.get("success")
        return elapsed if ok else -1

    latencies = []
    errors = 0
    start_t = time.monotonic()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(write_one, i) for i in range(total)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report("并发写入节点", latencies, errors, total)


def bench_concurrent_write_edges(node_ids: list, workers: int, total: int):
    """场景2: 并发写入边"""
    print(f"\n>>> 场景2: 并发写入边 (workers={workers}, total={total})")

    def write_one(idx):
        a, b = random.sample(node_ids, 2)
        start = time.monotonic()
        status, resp = api("POST", "/edges", {
            "source_id": a, "target_id": b,
            "edge_type": random.choice(["合作", "指导", "关联"]),
            "properties": {"权重": random.randint(1, 10)}
        })
        elapsed = time.monotonic() - start
        ok = status == 200 and isinstance(resp, dict) and resp.get("success")
        return elapsed if ok else -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(write_one, i) for i in range(total)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report("并发写入边", latencies, errors, total)


def bench_batch_import_nodes(batches: int, batch_size: int):
    """场景3: 批量导入节点"""
    print(f"\n>>> 场景3: 批量导入节点 (batches={batches}, batch_size={batch_size})")
    total = batches * batch_size

    def batch_one(bidx):
        items = [{"name": f"batch_node_{bidx}_{i:04d}", "年龄": random.randint(20, 60)} for i in range(batch_size)]
        start = time.monotonic()
        status, resp = api("POST", "/batch/nodes", {
            "labels": ["压测批量节点"],
            "items": items
        })
        elapsed = time.monotonic() - start
        ok = status == 200 and isinstance(resp, dict) and resp.get("success")
        return elapsed if ok else -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(batch_one, i) for i in range(batches)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report(f"批量导入节点 (每批{batch_size}个)", latencies, errors, total)


def bench_batch_import_edges(node_ids: list, batches: int, batch_size: int):
    """场景4: 批量导入边"""
    print(f"\n>>> 场景4: 批量导入边 (batches={batches}, batch_size={batch_size})")
    total = batches * batch_size

    def batch_one(bidx):
        items = []
        for i in range(batch_size):
            a, b = random.sample(node_ids, 2)
            items.append({"source_id": a, "target_id": b, "权重": random.randint(1, 10)})
        start = time.monotonic()
        status, resp = api("POST", "/batch/edges", {
            "edge_type": "压测批量关联",
            "items": items
        })
        elapsed = time.monotonic() - start
        ok = status == 200 and isinstance(resp, dict) and resp.get("success")
        return elapsed if ok else -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(batch_one, i) for i in range(batches)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report(f"批量导入边 (每批{batch_size}条)", latencies, errors, total)


def bench_concurrent_query(workers: int, total: int):
    """场景5: 并发查询"""
    print(f"\n>>> 场景5: 并发查询 (workers={workers}, total={total})")

    query_templates = [
        # 按标签列表
        lambda: ("GET", "/nodes?label=压测人物&limit=10", None),
        # 按属性查找
        lambda: ("POST", "/nodes/find", {"labels": ["压测人物"], "properties": {"在职": True}}),
        # Cypher 只读
        lambda: ("POST", "/query/read", {"query": "MATCH (n:压测人物) RETURN count(n) AS 总数"}),
        # Cypher 带参数
        lambda: ("POST", "/query", {"query": "MATCH (n:压测人物) WHERE n.年龄 > $age RETURN n.name AS 姓名, n.年龄 AS 年龄 LIMIT 5", "params": {"age": random.randint(25, 45)}}),
        # 聚合查询
        lambda: ("POST", "/query", {"query": "MATCH (n:压测人物) RETURN n.研究方向 AS 方向, count(n) AS 人数, avg(n.h指数) AS 平均h指数"}),
        # 按类型列表边
        lambda: ("GET", "/edges?edge_type=合作&limit=10", None),
        # 数据库信息
        lambda: ("GET", "/info/nodes/count?label=压测人物", None),
    ]

    def query_one(idx):
        method, path, body = random.choice(query_templates)()
        start = time.monotonic()
        try:
            status, resp = api(method, path, body)
            elapsed = time.monotonic() - start
            ok = status == 200 and isinstance(resp, dict) and resp.get("success")
            return elapsed if ok else -1
        except Exception:
            return -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(query_one, i) for i in range(total)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report("并发查询", latencies, errors, total)


def bench_traversal(node_ids: list, workers: int, total: int):
    """场景6: 图遍历"""
    print(f"\n>>> 场景6: 图遍历 (workers={workers}, total={total})")

    def traverse_one(idx):
        nid = random.choice(node_ids)
        op = random.choice(["neighbours", "edges", "shortest-path"])

        start = time.monotonic()
        try:
            if op == "neighbours":
                status, resp = api("POST", "/traverse/neighbours", {
                    "node_id": nid, "direction": random.choice(["out", "in", "both"]),
                    "limit": 20
                })
            elif op == "edges":
                status, resp = api("POST", "/traverse/edges", {
                    "node_id": nid, "direction": random.choice(["out", "in", "both"]),
                    "limit": 20
                })
            else:
                target = random.choice(node_ids)
                status, resp = api("POST", "/traverse/shortest-path", {
                    "source_id": nid, "target_id": target
                })
                # 404 是正常的（可能无路径），算成功
                if status == 404:
                    return time.monotonic() - start

            elapsed = time.monotonic() - start
            ok = status == 200 and isinstance(resp, dict) and resp.get("success")
            return elapsed if ok else -1
        except Exception:
            return -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(traverse_one, i) for i in range(total)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report("图遍历", latencies, errors, total)


def bench_mixed_rw(node_ids: list, workers: int, total: int, write_ratio: float):
    """场景7: 混合读写"""
    print(f"\n>>> 场景7: 混合读写 (workers={workers}, total={total}, 写比例={write_ratio:.0%})")

    def mixed_one(idx):
        is_write = random.random() < write_ratio
        start = time.monotonic()
        try:
            if is_write:
                # 写操作：创建节点或边
                if random.random() < 0.5:
                    status, resp = api("POST", "/nodes", {
                        "labels": ["压测混合节点"],
                        "properties": {"name": f"mixed_{idx:06d}", "值": random.randint(1, 100)}
                    })
                else:
                    a, b = random.sample(node_ids, 2)
                    status, resp = api("POST", "/edges", {
                        "source_id": a, "target_id": b,
                        "edge_type": "混合关联",
                        "properties": {"权重": random.randint(1, 10)}
                    })
            else:
                # 读操作
                r = random.random()
                if r < 0.4:
                    status, resp = api("GET", "/nodes?label=压测人物&limit=10", None)
                elif r < 0.7:
                    status, resp = api("POST", "/query/read", {
                        "query": "MATCH (n:压测人物) RETURN count(n) AS 总数"
                    })
                else:
                    nid = random.choice(node_ids)
                    status, resp = api("POST", "/traverse/neighbours", {
                        "node_id": nid, "direction": "both", "limit": 10
                    })

            elapsed = time.monotonic() - start
            ok = status == 200 and isinstance(resp, dict) and resp.get("success")
            return elapsed if ok else -1
        except Exception:
            return -1

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(mixed_one, i) for i in range(total)]
        for f in as_completed(futures):
            lat = f.result()
            if lat < 0:
                errors += 1
            else:
                latencies.append(lat)

    return print_report("混合读写", latencies, errors, total)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Tech KG Engine 压力测试")
    print("=" * 60)

    # 1. 准备数据
    node_ids, tech_ids, org_ids = prepare_test_data()

    # 2. 依次执行各场景
    reports = []

    cfg = CONFIG["并发写入节点"]
    reports.append(bench_concurrent_write_nodes(cfg["workers"], cfg["total"]))

    # 刷新 node_ids（包含新写入的节点）
    status, resp = api("POST", "/query/read", {"query": "MATCH (n:压测写入节点) RETURN n.name AS name LIMIT 1"})
    # 获取所有节点 ID 用于后续边写入
    all_node_status, all_node_resp = api("POST", "/query", {
        "query": "MATCH (n) WHERE n.name IS NOT NULL RETURN elementId(n) AS id LIMIT 2000"
    })
    if all_node_status == 200 and isinstance(all_node_resp, dict) and all_node_resp.get("success"):
        node_ids = [r["id"] for r in all_node_resp["data"]["records"] if r.get("id")]

    cfg = CONFIG["并发写入边"]
    reports.append(bench_concurrent_write_edges(node_ids, cfg["workers"], cfg["total"]))

    cfg = CONFIG["批量导入节点"]
    reports.append(bench_batch_import_nodes(cfg["batches"], cfg["batch_size"]))

    # 再次刷新 node_ids
    all_node_status, all_node_resp = api("POST", "/query", {
        "query": "MATCH (n) WHERE n.name IS NOT NULL RETURN elementId(n) AS id LIMIT 5000"
    })
    if all_node_status == 200 and isinstance(all_node_resp, dict) and all_node_resp.get("success"):
        node_ids = [r["id"] for r in all_node_resp["data"]["records"] if r.get("id")]

    cfg = CONFIG["批量导入边"]
    reports.append(bench_batch_import_edges(node_ids, cfg["batches"], cfg["batch_size"]))

    cfg = CONFIG["并发查询"]
    reports.append(bench_concurrent_query(cfg["workers"], cfg["total"]))

    cfg = CONFIG["图遍历"]
    reports.append(bench_traversal(node_ids, cfg["workers"], cfg["total"]))

    cfg = CONFIG["混合读写"]
    reports.append(bench_mixed_rw(node_ids, cfg["workers"], cfg["total"], cfg["write_ratio"]))

    # 3. 汇总
    print("\n" + "=" * 60)
    print("  压力测试汇总")
    print("=" * 60)
    print(f"{'场景':<20} {'QPS':>8} {'平均ms':>8} {'P50ms':>8} {'P95ms':>8} {'P99ms':>8} {'错误率':>8}")
    print("-" * 80)
    for r in reports:
        print(f"{r['name']:<20} {r['qps']:>8} {r['avg_ms']:>8} {r['p50_ms']:>8} {r['p95_ms']:>8} {r['p99_ms']:>8} {r['error_rate']:>7.1f}%")

    # 4. 保存结果
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stress_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到: {output_path}")
