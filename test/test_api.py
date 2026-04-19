"""Tech KG Engine Graph DB API 全量接口测试

测试范围：37 个 API 端点，覆盖正常流程和边界条件
运行方式：python test_api.py
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Callable

BASE = "http://localhost:8000"


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

results: list[dict] = []
pass_count = 0
fail_count = 0


def api(method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
    """发送 HTTP 请求，返回 (status_code, response_body)"""
    from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
    # 对 URL 中的非 ASCII 字符做 percent-encoding
    parsed = urlparse(path)
    encoded_path = quote(parsed.path, safe="/")
    # 重新编码 query 参数以支持中文
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        # parse_qs 返回 list 值，转成单值
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


def get_total(r: dict) -> int:
    """从响应中提取 total，兼容 data.total 和 data.page.total 两种结构"""
    data = r.get("data", {})
    if isinstance(data, dict):
        if "page" in data and isinstance(data["page"], dict):
            return data["page"].get("total", -1)
        return data.get("total", -1)
    return -1


def test(name: str, method: str, path: str, body: dict | None = None,
         expect_status: int = 200, check: Callable | None = None):
    """执行单个测试用例"""
    global pass_count, fail_count
    status, resp = api(method, path, body)
    ok = status == expect_status
    detail = ""
    if check and ok:
        try:
            ok = check(resp)
            if not ok:
                detail = "check() returned False"
        except Exception as e:
            ok = False
            detail = str(e)

    icon = "PASS" if ok else "FAIL"
    if not ok:
        fail_count += 1
    else:
        pass_count += 1

    result = {
        "name": name,
        "method": method,
        "path": path,
        "body": body,
        "expect_status": expect_status,
        "actual_status": status,
        "response": resp if isinstance(resp, dict) else str(resp)[:500],
        "result": icon,
        "detail": detail,
    }
    results.append(result)
    print(f"  [{icon}] {name}  (HTTP {status})")


# ---------------------------------------------------------------------------
# 清空 Neo4j 数据库
# ---------------------------------------------------------------------------

def clear_database():
    """通过 Cypher 写入接口清空数据库中的所有节点、关系、索引和约束"""
    print("清空数据库...")

    # 删除所有节点和关系
    status, resp = api("POST", "/query/write", {
        "query": "MATCH (n) DETACH DELETE n"
    })
    if status == 200 and isinstance(resp, dict) and resp.get("success"):
        print("  已删除所有节点和关系")
    else:
        print(f"  删除节点/关系失败: HTTP {status}, {resp}")

    # 删除所有索引
    status, resp = api("GET", "/schema/indexes")
    if status == 200 and isinstance(resp, dict) and resp.get("success"):
        for idx in resp.get("data", []):
            label = idx.get("label") or idx.get("labelsOrTypes", [None])[0]
            props = idx.get("properties") or idx.get("properties", [])
            if label and props:
                api("DELETE", "/schema/indexes", {"label": label, "properties": props})
        print("  已清理索引")

    # 删除所有约束
    status, resp = api("GET", "/schema/constraints")
    if status == 200 and isinstance(resp, dict) and resp.get("success"):
        for c in resp.get("data", []):
            name = c.get("name")
            if name:
                api("DELETE", f"/schema/constraints/{name}")
        print("  已清理约束")

    print("数据库已清空\n")


clear_database()

# ===========================================================================
# 0. 中文示例场景 —— 技术知识图谱
# ===========================================================================
print("--- 中文示例场景：技术知识图谱 ---")

# 创建人物节点（属性丰富，name 属性供 Neo4j Browser 显示节点标题）
_zhangsan = api("POST", "/nodes", {"labels": ["人物", "工程师"], "properties": {
    "name": "张三", "年龄": 32, "职称": "高级算法工程师",
    "所属机构": "清华大学", "研究方向": "知识图谱", "h指数": 18,
    "在职": True, "邮箱": "zhangsan@tsinghua.edu.cn"
}})[1]["data"]["id"]

_lisi = api("POST", "/nodes", {"labels": ["人物", "工程师"], "properties": {
    "name": "李四", "年龄": 28, "职称": "算法工程师",
    "所属机构": "北京大学", "研究方向": "自然语言处理", "h指数": 8,
    "在职": True, "邮箱": "lisi@pku.edu.cn"
}})[1]["data"]["id"]

_wangwu = api("POST", "/nodes", {"labels": ["人物", "教授"], "properties": {
    "name": "王五", "年龄": 45, "职称": "教授",
    "所属机构": "浙江大学", "研究方向": "图神经网络", "h指数": 35,
    "在职": True, "邮箱": "wangwu@zju.edu.cn"
}})[1]["data"]["id"]

_zhaoliu = api("POST", "/nodes", {"labels": ["人物", "学生"], "properties": {
    "name": "赵六", "年龄": 24, "职称": "博士研究生",
    "所属机构": "清华大学", "研究方向": "知识图谱", "h指数": 3,
    "在职": True, "邮箱": "zhaoliu@tsinghua.edu.cn"
}})[1]["data"]["id"]

# 创建技术节点
_kg_tech = api("POST", "/nodes", {"labels": ["技术"], "properties": {
    "name": "知识图谱", "领域": "人工智能", "成熟度": "成长期",
    "首次提出年份": 2012, "相关论文数": 50000, "简介": "以图结构组织和表达知识的技术"
}})[1]["data"]["id"]

_nlp_tech = api("POST", "/nodes", {"labels": ["技术"], "properties": {
    "name": "自然语言处理", "领域": "人工智能", "成熟度": "成熟期",
    "首次提出年份": 1950, "相关论文数": 200000, "简介": "让计算机理解和生成人类语言的技术"
}})[1]["data"]["id"]

_gnn_tech = api("POST", "/nodes", {"labels": ["技术"], "properties": {
    "name": "图神经网络", "领域": "深度学习", "成熟度": "成长期",
    "首次提出年份": 2009, "相关论文数": 30000, "简介": "在图结构数据上进行深度学习的方法"
}})[1]["data"]["id"]

# 创建论文节点
_paper1 = api("POST", "/nodes", {"labels": ["论文"], "properties": {
    "name": "基于图神经网络的知识图谱补全方法研究",
    "发表年份": 2023, "期刊": "中国科学", "被引次数": 45, "doi": "10.1234/kg-gnn-2023"
}})[1]["data"]["id"]

_paper2 = api("POST", "/nodes", {"labels": ["论文"], "properties": {
    "name": "面向大规模知识图谱的高效推理框架",
    "发表年份": 2024, "期刊": "软件学报", "被引次数": 12, "doi": "10.5678/kg-infer-2024"
}})[1]["data"]["id"]

# 创建机构节点
_tsinghua = api("POST", "/nodes", {"labels": ["机构"], "properties": {
    "name": "清华大学", "类型": "高校", "所在地": "北京",
    "成立年份": 1911, "双一流": True
}})[1]["data"]["id"]

_pku = api("POST", "/nodes", {"labels": ["机构"], "properties": {
    "name": "北京大学", "类型": "高校", "所在地": "北京",
    "成立年份": 1898, "双一流": True
}})[1]["data"]["id"]

_zju = api("POST", "/nodes", {"labels": ["机构"], "properties": {
    "name": "浙江大学", "类型": "高校", "所在地": "杭州",
    "成立年份": 1897, "双一流": True
}})[1]["data"]["id"]

# 创建人物之间的关系
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _lisi, "edge_type": "合作", "properties": {"合作项目": "知识图谱构建平台", "开始年份": 2022}})
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _wangwu, "edge_type": "合作", "properties": {"合作项目": "图神经网络与知识图谱融合", "开始年份": 2023}})
api("POST", "/edges", {"source_id": _lisi, "target_id": _wangwu, "edge_type": "合作", "properties": {"合作项目": "自然语言处理与图学习", "开始年份": 2021}})
api("POST", "/edges", {"source_id": _zhaoliu, "target_id": _zhangsan, "edge_type": "指导", "properties": {"关系": "博士生-导师", "入学年份": 2022}})
api("POST", "/edges", {"source_id": _zhaoliu, "target_id": _lisi, "edge_type": "合作", "properties": {"合作项目": "知识图谱推理", "开始年份": 2023}})

# 创建人物与技术的关系
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _kg_tech, "edge_type": "研究", "properties": {"角色": "核心贡献者", "年限": 8}})
api("POST", "/edges", {"source_id": _lisi, "target_id": _nlp_tech, "edge_type": "研究", "properties": {"角色": "研究者", "年限": 5}})
api("POST", "/edges", {"source_id": _wangwu, "target_id": _gnn_tech, "edge_type": "研究", "properties": {"角色": "先驱者", "年限": 10}})
api("POST", "/edges", {"source_id": _zhaoliu, "target_id": _kg_tech, "edge_type": "研究", "properties": {"角色": "研究生", "年限": 2}})

# 创建人物与论文的关系
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _paper1, "edge_type": "发表", "properties": {"作者排序": 1}})
api("POST", "/edges", {"source_id": _wangwu, "target_id": _paper1, "edge_type": "发表", "properties": {"作者排序": 2}})
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _paper2, "edge_type": "发表", "properties": {"作者排序": 1}})
api("POST", "/edges", {"source_id": _zhaoliu, "target_id": _paper2, "edge_type": "发表", "properties": {"作者排序": 2}})

# 创建论文与技术的关系
api("POST", "/edges", {"source_id": _paper1, "target_id": _kg_tech, "edge_type": "涉及", "properties": {"关联强度": "强"}})
api("POST", "/edges", {"source_id": _paper1, "target_id": _gnn_tech, "edge_type": "涉及", "properties": {"关联强度": "强"}})
api("POST", "/edges", {"source_id": _paper2, "target_id": _kg_tech, "edge_type": "涉及", "properties": {"关联强度": "强"}})

# 创建人物与机构的关系
api("POST", "/edges", {"source_id": _zhangsan, "target_id": _tsinghua, "edge_type": "隶属于", "properties": {"部门": "计算机系"}})
api("POST", "/edges", {"source_id": _lisi, "target_id": _pku, "edge_type": "隶属于", "properties": {"部门": "智能学院"}})
api("POST", "/edges", {"source_id": _wangwu, "target_id": _zju, "edge_type": "隶属于", "properties": {"部门": "计算机学院"}})
api("POST", "/edges", {"source_id": _zhaoliu, "target_id": _tsinghua, "edge_type": "隶属于", "properties": {"部门": "计算机系"}})

# 创建技术之间的关系
api("POST", "/edges", {"source_id": _kg_tech, "target_id": _nlp_tech, "edge_type": "依赖", "properties": {"描述": "知识图谱构建依赖自然语言处理技术"}})
api("POST", "/edges", {"source_id": _gnn_tech, "target_id": _kg_tech, "edge_type": "应用于", "properties": {"描述": "图神经网络可应用于知识图谱补全与推理"}})
api("POST", "/edges", {"source_id": _nlp_tech, "target_id": _gnn_tech, "edge_type": "结合", "properties": {"描述": "自然语言处理与图神经网络在语义理解上结合"}})

# 创建机构之间的合作关系
api("POST", "/edges", {"source_id": _tsinghua, "target_id": _pku, "edge_type": "合作", "properties": {"合作领域": "人工智能", "项目名称": "认知智能联合实验室"}})
api("POST", "/edges", {"source_id": _tsinghua, "target_id": _zju, "edge_type": "合作", "properties": {"合作领域": "图计算", "项目名称": "图智能联合研究中心"}})

print("  中文示例数据已创建：4个人物 + 3个技术 + 2篇论文 + 3个机构，共24条关系\n")


# ===========================================================================
# 开始测试
# ===========================================================================

print("=" * 60)
print("Tech KG Engine API 全量测试")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. 系统
# ---------------------------------------------------------------------------
print("\n--- 系统 ---")

test("健康检查", "GET", "/health",
     check=lambda r: r.get("connected") is True)

test("健康检查-数据库状态字段", "GET", "/health",
     check=lambda r: "status" in r and "connected" in r)

# ---------------------------------------------------------------------------
# 2. 节点 CRUD
# ---------------------------------------------------------------------------
print("\n--- 节点 CRUD ---")

# 创建 - 正常
test("创建节点-正常", "POST", "/nodes",
     {"labels": ["测试人物"], "properties": {"name": "sanm", "年龄": 28}},
     check=lambda r: r["success"] and r["data"]["labels"] == ["测试人物"])

# 创建 - 无属性
test("创建节点-无属性", "POST", "/nodes",
     {"labels": ["空节点"], "properties": {}},
     check=lambda r: r["success"] and r["data"]["properties"] == {})

# 创建 - 多标签
test("创建节点-多标签", "POST", "/nodes",
     {"labels": ["员工", "经理"], "properties": {"name": "李四"}},
     check=lambda r: r["success"] and set(r["data"]["labels"]) == {"员工", "经理"})

# 创建 - 特殊字符属性值
test("创建节点-特殊字符属性", "POST", "/nodes",
     {"labels": ["测试人物"], "properties": {"name": "O'Brien", "简介": "hello\nworld"}},
     check=lambda r: r["success"])

# 创建 - 中文字符属性
test("创建节点-中文属性", "POST", "/nodes",
     {"labels": ["测试人物"], "properties": {"name": "王五", "城市": "北京"}},
     check=lambda r: r["success"] and r["data"]["properties"]["城市"] == "北京")

# 创建 - 数字/布尔/列表属性
test("创建节点-多种类型属性", "POST", "/nodes",
     {"labels": ["测试人物"], "properties": {"分数": 99.5, "在职": True, "name": "测试"}},
     check=lambda r: r["success"] and r["data"]["properties"]["分数"] == 99.5)

# Merge - 首次创建
test("Merge节点-首次创建", "POST", "/nodes/merge",
     {"labels": ["测试人物"], "identity_props": {"name": "赵六"}, "properties": {"年龄": 30}},
     check=lambda r: r["success"] and r["data"]["properties"]["name"] == "赵六")

# Merge - 幂等更新
test("Merge节点-幂等更新", "POST", "/nodes/merge",
     {"labels": ["测试人物"], "identity_props": {"name": "赵六"}, "properties": {"年龄": 31, "城市": "上海"}},
     check=lambda r: r["success"] and r["data"]["properties"]["年龄"] == 31 and r["data"]["properties"]["城市"] == "上海")

# Merge - 多属性identity
test("Merge节点-多属性标识", "POST", "/nodes/merge",
     {"labels": ["测试人物"], "identity_props": {"name": "孙七", "城市": "深圳"}, "properties": {"年龄": 22}},
     check=lambda r: r["success"])

# 获取 - 按 ID
_node_id = api("POST", "/nodes", {"labels": ["获取测试"], "properties": {"值": 1}})[1]["data"]["id"]
test("获取节点-按ID存在", "GET", f"/nodes/{_node_id}",
     check=lambda r: r["success"] and r["data"]["properties"]["值"] == 1)

# 获取 - 不存在
test("获取节点-不存在404", "GET", "/nodes/nonexistent_id",
     expect_status=404)

# 列表 - 按标签
test("列表节点-按标签", "GET", "/nodes?label=测试人物",
     check=lambda r: r["success"] and get_total(r) > 0)

# 列表 - 分页
test("列表节点-分页limit=1", "GET", "/nodes?label=测试人物&limit=1",
     check=lambda r: r["success"] and len(r["data"]["items"]) <= 1)

# 列表 - 分页 offset
test("列表节点-分页offset", "GET", "/nodes?label=测试人物&limit=1&offset=0",
     check=lambda r: r["success"])

# 查找 - 按属性
test("查找节点-按属性", "POST", "/nodes/find",
     {"labels": ["测试人物"], "properties": {"name": "赵六"}},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 查找 - 空属性（等于按标签查）
test("查找节点-空属性", "POST", "/nodes/find",
     {"labels": ["测试人物"], "properties": {}},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 查找 - 无匹配
test("查找节点-无匹配", "POST", "/nodes/find",
     {"labels": ["测试人物"], "properties": {"name": "不存在的名字_xyz"}},
     check=lambda r: r["success"] and get_total(r) == 0)

# 更新 - 正常
test("更新节点-正常", "PATCH", f"/nodes/{_node_id}",
     {"properties": {"值": 999, "备注": "已更新"}},
     check=lambda r: r["success"] and r["data"]["properties"]["值"] == 999)

# 更新 - 不存在的节点
test("更新节点-不存在", "PATCH", "/nodes/nonexistent_id",
     {"properties": {"值": 1}},
     expect_status=500)  # Neo4j 会报错

# 删除 - 无关系的节点
_del_id = api("POST", "/nodes", {"labels": ["删除测试"], "properties": {}})[1]["data"]["id"]
test("删除节点-无关系detach=false", "DELETE", f"/nodes/{_del_id}?detach=false",
     check=lambda r: r["success"])

# 删除 - 有关系的节点 detach=false
_a = api("POST", "/nodes", {"labels": ["删除测试2"], "properties": {}})[1]["data"]["id"]
_b = api("POST", "/nodes", {"labels": ["删除测试2"], "properties": {}})[1]["data"]["id"]
api("POST", "/edges", {"source_id": _a, "target_id": _b, "edge_type": "关联"})
test("删除节点-有关系detach=false应409", "DELETE", f"/nodes/{_a}?detach=false",
     expect_status=409)

# 删除 - 有关系的节点 detach=true
test("删除节点-有关系detach=true", "DELETE", f"/nodes/{_a}?detach=true",
     check=lambda r: r["success"])

# 删除 - 不存在的节点
test("删除节点-不存在404", "DELETE", "/nodes/nonexistent_id",
     expect_status=404)

# ---------------------------------------------------------------------------
# 3. 关系 CRUD
# ---------------------------------------------------------------------------
print("\n--- 关系 CRUD ---")

# 创建测试节点
_s = api("POST", "/nodes", {"labels": ["关系测试"], "properties": {"name": "源节点"}})[1]["data"]["id"]
_t = api("POST", "/nodes", {"labels": ["关系测试"], "properties": {"name": "目标节点"}})[1]["data"]["id"]

# 创建 - 正常
test("创建关系-正常", "POST", "/edges",
     {"source_id": _s, "target_id": _t, "edge_type": "好友", "properties": {"等级": 5}},
     check=lambda r: r["success"] and r["data"]["type"] == "好友")

# 创建 - 无属性
test("创建关系-无属性", "POST", "/edges",
     {"source_id": _s, "target_id": _t, "edge_type": "关注"},
     check=lambda r: r["success"] and r["data"]["properties"] == {})

# 创建 - 中文关系类型
test("创建关系-中文类型名", "POST", "/edges",
     {"source_id": _s, "target_id": _t, "edge_type": "合作"},
     check=lambda r: r["success"])

# Merge - 首次
test("Merge关系-首次创建", "POST", "/edges/merge",
     {"source_id": _s, "target_id": _t, "edge_type": "共事",
      "identity_props": {"项目": "知识图谱"}, "properties": {"角色": "开发"}},
     check=lambda r: r["success"])

# Merge - 幂等
test("Merge关系-幂等更新", "POST", "/edges/merge",
     {"source_id": _s, "target_id": _t, "edge_type": "共事",
      "identity_props": {"项目": "知识图谱"}, "properties": {"角色": "负责人"}},
     check=lambda r: r["success"] and r["data"]["properties"]["角色"] == "负责人")

# 获取 - 按 ID
_eid = api("POST", "/edges", {"source_id": _s, "target_id": _t, "edge_type": "查询测试边"})[1]["data"]["id"]
test("获取关系-按ID存在", "GET", f"/edges/{_eid}",
     check=lambda r: r["success"])

# 获取 - 不存在
test("获取关系-不存在404", "GET", "/edges/nonexistent_edge",
     expect_status=404)

# 列表 - 按类型
test("列表关系-按类型", "GET", "/edges?edge_type=好友",
     check=lambda r: r["success"] and get_total(r) >= 1)

# 列表 - 分页
test("列表关系-分页", "GET", "/edges?edge_type=好友&limit=1",
     check=lambda r: r["success"] and len(r["data"]["items"]) <= 1)

# 查找 - 按属性
test("查找关系-按属性", "POST", "/edges/find",
     {"edge_type": "好友", "properties": {"等级": 5}},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 查找 - 空属性
test("查找关系-空属性", "POST", "/edges/find",
     {"edge_type": "好友", "properties": {}},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 查找 - 无匹配
test("查找关系-无匹配", "POST", "/edges/find",
     {"edge_type": "好友", "properties": {"等级": 99999}},
     check=lambda r: r["success"] and get_total(r) == 0)

# 更新
test("更新关系-正常", "PATCH", f"/edges/{_eid}",
     {"properties": {"备注": "已更新", "等级": 10}},
     check=lambda r: r["success"] and r["data"]["properties"]["备注"] == "已更新")

# 删除
_tmp_e = api("POST", "/edges", {"source_id": _s, "target_id": _t, "edge_type": "临时删除"})[1]["data"]["id"]
test("删除关系-正常", "DELETE", f"/edges/{_tmp_e}",
     check=lambda r: r["success"])

# 删除 - 不存在
test("删除关系-不存在404", "DELETE", "/edges/nonexistent_edge",
     expect_status=404)

# ---------------------------------------------------------------------------
# 4. 图遍历
# ---------------------------------------------------------------------------
print("\n--- 图遍历 ---")

# 准备遍历测试数据
_n1 = api("POST", "/nodes", {"labels": ["遍历测试"], "properties": {"name": "甲"}})[1]["data"]["id"]
_n2 = api("POST", "/nodes", {"labels": ["遍历测试"], "properties": {"name": "乙"}})[1]["data"]["id"]
_n3 = api("POST", "/nodes", {"labels": ["遍历测试"], "properties": {"name": "丙"}})[1]["data"]["id"]
api("POST", "/edges", {"source_id": _n1, "target_id": _n2, "edge_type": "认识", "properties": {"权重": 1}})
api("POST", "/edges", {"source_id": _n2, "target_id": _n3, "edge_type": "认识", "properties": {"权重": 2}})

# 邻居 - out
test("邻居查询-out方向", "POST", "/traverse/neighbours",
     {"node_id": _n1, "direction": "out"},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 邻居 - in
test("邻居查询-in方向", "POST", "/traverse/neighbours",
     {"node_id": _n3, "direction": "in"},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 邻居 - both
test("邻居查询-both方向", "POST", "/traverse/neighbours",
     {"node_id": _n2, "direction": "both"},
     check=lambda r: r["success"] and get_total(r) >= 2)

# 邻居 - 按关系类型过滤
test("邻居查询-按类型过滤", "POST", "/traverse/neighbours",
     {"node_id": _n1, "direction": "out", "edge_type": "认识"},
     check=lambda r: r["success"])

# 邻居 - limit
test("邻居查询-limit限制", "POST", "/traverse/neighbours",
     {"node_id": _n2, "direction": "both", "limit": 1},
     check=lambda r: r["success"] and len(r["data"]["items"]) <= 1)

# 邻居 - 不存在的节点
test("邻居查询-不存在节点返回空", "POST", "/traverse/neighbours",
     {"node_id": "nonexistent", "direction": "out"},
     check=lambda r: r["success"] and get_total(r) == 0)

# 节点的边 - out
test("节点边查询-out", "POST", "/traverse/edges",
     {"node_id": _n1, "direction": "out"},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 节点的边 - in
test("节点边查询-in", "POST", "/traverse/edges",
     {"node_id": _n3, "direction": "in"},
     check=lambda r: r["success"] and get_total(r) >= 1)

# 节点的边 - both
test("节点边查询-both", "POST", "/traverse/edges",
     {"node_id": _n2, "direction": "both"},
     check=lambda r: r["success"] and get_total(r) >= 2)

# 节点的边 - 按类型
test("节点边查询-按类型", "POST", "/traverse/edges",
     {"node_id": _n1, "direction": "out", "edge_type": "认识"},
     check=lambda r: r["success"])

# 最短路径 - 存在
test("最短路径-存在", "POST", "/traverse/shortest-path",
     {"source_id": _n1, "target_id": _n3},
     check=lambda r: r["success"] and len(r["data"]["nodes"]) >= 2)

# 最短路径 - 不存在
_iso = api("POST", "/nodes", {"labels": ["孤立节点"], "properties": {"name": "孤岛"}})[1]["data"]["id"]
test("最短路径-不存在返回404", "POST", "/traverse/shortest-path",
     {"source_id": _n1, "target_id": _iso},
     expect_status=404)

# 最短路径 - 按类型过滤
test("最短路径-按类型过滤", "POST", "/traverse/shortest-path",
     {"source_id": _n1, "target_id": _n3, "edge_type": "认识"},
     check=lambda r: r["success"])

# 最短路径 - 自身到自身
test("最短路径-自身到自身", "POST", "/traverse/shortest-path",
     {"source_id": _n1, "target_id": _n1},
     check=lambda r: r["success"] and len(r["data"]["nodes"]) >= 1)

# ---------------------------------------------------------------------------
# 5. Cypher 查询
# ---------------------------------------------------------------------------
print("\n--- Cypher 查询 ---")

# 查询 - 返回原始值
test("Cypher查询-返回原始值", "POST", "/query",
     {"query": "RETURN 1 AS x"},
     check=lambda r: r["success"] and r["data"]["records"][0]["x"] == 1)

# 查询 - 返回节点
test("Cypher查询-返回节点", "POST", "/query",
     {"query": "MATCH (n:测试人物) RETURN n LIMIT 1"},
     check=lambda r: r["success"] and "id" in r["data"]["records"][0]["n"])

# 查询 - 带参数
test("Cypher查询-带参数", "POST", "/query",
     {"query": "MATCH (n:测试人物) WHERE n.年龄 > $最小年龄 RETURN n.name AS 姓名", "params": {"最小年龄": 0}},
     check=lambda r: r["success"] and len(r["data"]["records"]) >= 1)

# 查询 - 聚合
test("Cypher查询-聚合函数", "POST", "/query",
     {"query": "MATCH (n:测试人物) RETURN count(n) AS 总数, avg(n.年龄) AS 平均年龄"},
     check=lambda r: r["success"] and "总数" in r["data"]["records"][0])

# 只读查询
test("只读Cypher查询", "POST", "/query/read",
     {"query": "MATCH (n) RETURN count(n) AS 总数"},
     check=lambda r: r["success"])

# 写入查询
test("写入Cypher查询", "POST", "/query/write",
     {"query": "CREATE (n:写入测试 {时间戳: timestamp()}) RETURN n.时间戳 AS 时间戳"},
     check=lambda r: r["success"])

# 错误语法
test("Cypher语法错误-应返回400", "POST", "/query",
     {"query": "INVALID CYPHER HERE"},
     expect_status=400)

# 空查询结果
test("Cypher查询-空结果", "POST", "/query",
     {"query": "MATCH (n:不存在的标签99) RETURN n"},
     check=lambda r: r["success"] and r["data"]["records"] == [])

# 大量参数
test("Cypher查询-多参数", "POST", "/query",
     {"query": "UNWIND range(1, $count) AS i RETURN i", "params": {"count": 5}},
     check=lambda r: r["success"] and len(r["data"]["records"]) == 5)

# ---------------------------------------------------------------------------
# 6. 批量操作
# ---------------------------------------------------------------------------
print("\n--- 批量操作 ---")

# 批量创建节点
test("批量创建节点-3个", "POST", "/batch/nodes",
     {"labels": ["批量人物"], "items": [{"name": "甲一", "年龄": 20}, {"name": "乙二", "年龄": 21}, {"name": "丙三", "年龄": 22}]},
     check=lambda r: r["success"] and get_total(r) == 3)

# 批量创建节点 - 空列表
test("批量创建节点-空列表", "POST", "/batch/nodes",
     {"labels": ["批量空"], "items": []},
     check=lambda r: r["success"] and get_total(r) == 0)

# 批量创建节点 - 1个
test("批量创建节点-1个", "POST", "/batch/nodes",
     {"labels": ["批量单项"], "items": [{"name": "唯一"}]},
     check=lambda r: r["success"] and get_total(r) == 1)

# 批量创建边
_ba = api("POST", "/nodes", {"labels": ["批量边测试"], "properties": {"name": "边甲"}})[1]["data"]["id"]
_bb = api("POST", "/nodes", {"labels": ["批量边测试"], "properties": {"name": "边乙"}})[1]["data"]["id"]
test("批量创建边-2个", "POST", "/batch/edges",
     {"edge_type": "批量关联", "items": [
         {"source_id": _ba, "target_id": _bb, "权重": 1},
         {"source_id": _ba, "target_id": _bb, "权重": 2},
     ]},
     check=lambda r: r["success"] and get_total(r) == 2)

# 批量创建边 - 空列表
test("批量创建边-空列表", "POST", "/batch/edges",
     {"edge_type": "空关联", "items": []},
     check=lambda r: r["success"] and get_total(r) == 0)

# ---------------------------------------------------------------------------
# 7. Schema 管理
# ---------------------------------------------------------------------------
print("\n--- Schema 管理 ---")

# 创建索引
test("创建索引-普通", "POST", "/schema/indexes",
     {"label": "批量人物", "properties": ["name"], "unique": False},
     check=lambda r: r["success"])

# 创建唯一索引（约束） - 使用独立标签避免冲突
test("创建索引-唯一约束", "POST", "/schema/indexes",
     {"label": "唯一索引测试标签", "properties": ["name"], "unique": True},
     check=lambda r: r["success"])

# 重复创建索引
test("创建索引-重复应400", "POST", "/schema/indexes",
     {"label": "批量人物", "properties": ["name"], "unique": False},
     expect_status=400)

# 列出索引
test("列出索引", "GET", "/schema/indexes",
     check=lambda r: r["success"] and len(r["data"]) > 0)

# 列出索引-按标签过滤
test("列出索引-按标签过滤", "GET", "/schema/indexes?label=批量人物",
     check=lambda r: r["success"])

# 删除索引
test("删除索引-正常", "DELETE", "/schema/indexes",
     {"label": "批量人物", "properties": ["name"]},
     check=lambda r: r["success"])

# 删除不存在的索引
test("删除索引-不存在应400", "DELETE", "/schema/indexes",
     {"label": "不存在", "properties": ["name"]},
     expect_status=400)

# 创建约束 - 使用独立标签，不和上面 unique index 冲突
test("创建约束-unique", "POST", "/schema/constraints",
     {"name": "constraint_test_unique", "label": "约束测试标签", "property": "name", "kind": "unique"},
     check=lambda r: r["success"])

# 创建约束-重复
test("创建约束-重复应400", "POST", "/schema/constraints",
     {"name": "constraint_test_unique", "label": "约束测试标签", "property": "name", "kind": "unique"},
     expect_status=400)

# 列出约束
test("列出约束", "GET", "/schema/constraints",
     check=lambda r: r["success"])

# 删除约束
test("删除约束-正常", "DELETE", "/schema/constraints/constraint_test_unique",
     check=lambda r: r["success"])

# 删除不存在的约束
test("删除约束-不存在应400", "DELETE", "/schema/constraints/nonexistent_constraint",
     expect_status=400)

# ---------------------------------------------------------------------------
# 8. 数据库信息
# ---------------------------------------------------------------------------
print("\n--- 数据库信息 ---")

test("节点总数", "GET", "/info/nodes/count",
     check=lambda r: r["success"] and r["data"] > 0)

test("节点数-按标签", "GET", "/info/nodes/count?label=测试人物",
     check=lambda r: r["success"] and r["data"] >= 1)

test("节点数-不存在标签返回0", "GET", "/info/nodes/count?label=不存在的标签99",
     check=lambda r: r["success"] and r["data"] == 0)

test("边总数", "GET", "/info/edges/count",
     check=lambda r: r["success"] and r["data"] > 0)

test("边数-按类型", "GET", "/info/edges/count?edge_type=好友",
     check=lambda r: r["success"] and r["data"] >= 1)

test("边数-不存在类型返回0", "GET", "/info/edges/count?edge_type=不存在的类型99",
     check=lambda r: r["success"] and r["data"] == 0)

test("列出标签", "GET", "/info/labels",
     check=lambda r: r["success"] and "测试人物" in r["data"])

test("列出关系类型", "GET", "/info/edge-types",
     check=lambda r: r["success"] and len(r["data"]) > 0)


# ===========================================================================
# 汇总
# ===========================================================================

print("\n" + "=" * 60)
print(f"测试完成: {pass_count} PASS / {fail_count} FAIL / {pass_count + fail_count} TOTAL")
print("=" * 60)

# 保存详细结果
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"详细结果已保存到: {output_path}")

if fail_count > 0:
    print("\n失败的测试:")
    for r in results:
        if r["result"] == "FAIL":
            print(f"  - {r['name']}: HTTP {r['actual_status']} (期望 {r['expect_status']}) {r.get('detail', '')}")

sys.exit(1 if fail_count > 0 else 0)
