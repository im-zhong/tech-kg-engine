# tech-kg-engine
A Billion-Scale Technology Knowledge Graph Engine for Scientific Discovery and Industrial Intelligence

# graph-db
通用的图数据库操作 API，当前支持 Neo4j 后端，内置 FastAPI REST 服务与 Swagger 文档，支持可插拔后端扩展。

## 环境要求

- Docker & Docker Compose
- Python 3.10+（本地开发或运行测试时）

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，设置 Neo4j 密码
# NEO4J_PASSWORD=<your_password>
```

> **注意**：`NEO4J_AUTH` 仅在 Neo4j 首次初始化时生效。修改密码需删除数据卷重建：
> ```bash
> docker compose down
> docker volume rm tech-kg-engine_neo4j_data tech-kg-engine_neo4j_logs
> docker compose up -d
> ```

### 2. 构建并启动

```bash
docker compose up -d --build
```

### 3. 验证

```bash
curl http://localhost:8000/health
# {"status":"ok","connected":true}
```

### 4. 访问

| 服务 | 地址 |
|------|------|
| Swagger 文档 | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Neo4j Browser | http://localhost:7474 |
| 健康检查 | http://localhost:8000/health |

### 停止

```bash
docker compose down        # 停止服务
docker compose down -v     # 停止并清除数据卷
```

## Python SDK

### 连接数据库

```python
from graph_db import connect, GraphDBConfig

db = connect(GraphDBConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="your_password",
))
```

### 节点

```python
# 创建
alice = db.create_node(["Person"], {"name": "Alice", "age": 30})

# 幂等创建/更新（按 identity_props 匹配，存在则更新，不存在则创建）
bob = db.merge_node(["Person"], {"name": "Bob"}, {"age": 25})

# 按 ID 获取
node = db.get_node(alice.id)

# 按标签列表
result = db.get_nodes_by_label("Person", limit=10, offset=0)

# 按标签 + 属性查找
result = db.find_nodes(["Person"], {"name": "Alice"})

# 更新属性（合并更新）
db.update_node(alice.id, {"age": 31, "city": "北京"})

# 删除（detach=true 同时删除关联关系）
db.delete_node(alice.id, detach=True)
```

### 关系

```python
# 创建
edge = db.create_edge(alice.id, bob.id, "KNOWS", {"since": 2020})

# 幂等创建/更新
edge = db.merge_edge(
    alice.id, bob.id, "KNOWS",
    identity_props={"since": 2020},
    properties={"level": "close"},
)

# 按 ID 获取
edge = db.get_edge(edge.id)

# 按类型列表
result = db.get_edges_by_type("KNOWS", limit=10)

# 按类型 + 属性查找
result = db.find_edges("KNOWS", {"since": 2020})

# 更新属性
db.update_edge(edge.id, {"level": "best"})

# 删除
db.delete_edge(edge.id)
```

### 图遍历

```python
# 邻居节点（direction: "out" / "in" / "both"）
neighbours = db.get_neighbours(alice.id, direction="out", edge_type="KNOWS", limit=20)

# 节点的边
edges = db.get_node_edges(alice.id, direction="both", limit=20)

# 最短路径
path = db.shortest_path(alice.id, bob.id, edge_type="KNOWS", max_depth=10)
# path.nodes -> [Node, ...]
# path.edges -> [Edge, ...]
```

### Cypher 查询

```python
# 通用查询
result = db.execute_query(
    "MATCH (n:Person) WHERE n.age > $age RETURN n.name AS name",
    params={"age": 25},
)
# result.records -> [{"name": "Alice"}, ...]

# 只读查询（可路由到读副本）
result = db.execute_read("MATCH (n) RETURN count(n) AS total")

# 写入查询（自动重试瞬态错误）
result = db.execute_write("CREATE (n:Test {ts: timestamp()}) RETURN n")
```

### 批量操作

```python
# 批量创建节点
result = db.batch_create_nodes(
    [{"name": f"Person_{i}", "age": 20 + i} for i in range(100)],
    labels=["Person"],
)

# 批量创建边
result = db.batch_create_edges(
    [{"source_id": alice.id, "target_id": bob.id, "weight": i} for i in range(10)],
    edge_type="LINKS",
)
```

### Schema 管理

```python
from graph_db import IndexSpec, ConstraintSpec

# 创建索引
db.create_index(IndexSpec(label="Person", properties=["name"], unique=False))

# 创建唯一约束
db.create_index(IndexSpec(label="Person", properties=["name"], unique=True))

# 列出索引
indexes = db.list_indexes()

# 删除索引
db.drop_index(IndexSpec(label="Person", properties=["name"]))

# 创建约束
db.create_constraint(ConstraintSpec(
    name="person_name_unique", label="Person", property="name", kind="unique",
))

# 列出约束
constraints = db.list_constraints()

# 删除约束
db.drop_constraint("person_name_unique")
```

### 数据库信息

```python
db.count_nodes()                          # 节点总数
db.count_nodes(label="Person")            # 按标签计数
db.count_edges()                          # 边总数
db.count_edges(edge_type="KNOWS")         # 按类型计数
db.list_labels()                          # 所有标签
db.list_edge_types()                      # 所有关系类型
db.health_check()                         # 健康检查
```

### 关闭连接

```python
db.close()
```

## REST API 参考

完整接口文档见 http://localhost:8000/docs

### 节点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/nodes` | 创建节点 |
| POST | `/nodes/merge` | 幂等 upsert 节点 |
| GET | `/nodes/{id}` | 按 ID 获取 |
| GET | `/nodes?label=` | 按标签列表查询 |
| POST | `/nodes/find` | 按标签 + 属性查找 |
| PATCH | `/nodes/{id}` | 更新属性 |
| DELETE | `/nodes/{id}?detach=` | 删除（detach=true 同时删关系） |

### 关系

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/edges` | 创建关系 |
| POST | `/edges/merge` | 幂等 upsert 关系 |
| GET | `/edges/{id}` | 按 ID 获取 |
| GET | `/edges?edge_type=` | 按类型列表查询 |
| POST | `/edges/find` | 按类型 + 属性查找 |
| PATCH | `/edges/{id}` | 更新属性 |
| DELETE | `/edges/{id}` | 删除 |

### 遍历 / 查询 / 批量 / Schema / 信息

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/traverse/neighbours` | 邻居查询 |
| POST | `/traverse/edges` | 节点的边 |
| POST | `/traverse/shortest-path` | 最短路径 |
| POST | `/query` | Cypher 查询 |
| POST | `/query/read` | 只读 Cypher |
| POST | `/query/write` | 写入 Cypher |
| POST | `/batch/nodes` | 批量创建节点 |
| POST | `/batch/edges` | 批量创建边 |
| POST | `/schema/indexes` | 创建索引 |
| GET | `/schema/indexes` | 列出索引 |
| DELETE | `/schema/indexes` | 删除索引 |
| POST | `/schema/constraints` | 创建约束 |
| GET | `/schema/constraints` | 列出约束 |
| DELETE | `/schema/constraints/{name}` | 删除约束 |
| GET | `/info/nodes/count` | 节点计数 |
| GET | `/info/edges/count` | 边计数 |
| GET | `/info/labels` | 标签列表 |
| GET | `/info/edge-types` | 关系类型列表 |
| GET | `/health` | 健康检查 |

## 测试

```bash
cd test
python3 test_api.py      # 88 个接口测试用例
python3 stress_test.py   # 7 个压力测试场景
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `GRAPH_DB_BACKEND` | `neo4j` | 图数据库后端类型 |
| `GRAPH_DB_URI` | `bolt://localhost:7687` | 数据库连接 URI |
| `GRAPH_DB_USERNAME` | `neo4j` | 数据库用户名 |
| `GRAPH_DB_PASSWORD` | — | 数据库密码（必填） |
| `GRAPH_DB_DATABASE` | `neo4j` | 目标数据库名 |
| `GRAPH_DB_MAX_CONNECTION_POOL_SIZE` | `50` | 连接池大小 |
| `GRAPH_DB_CONNECTION_TIMEOUT` | `30` | 连接超时（秒） |
| `NEO4J_PASSWORD` | — | Docker Compose 中 Neo4j 的密码 |
