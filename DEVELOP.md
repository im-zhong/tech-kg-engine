# Tech KG Engine 开发手册

## 目录

- [1. 环境准备](#1-环境准备)
- [2. 项目结构](#2-项目结构)
- [3. 基础设施](#3-基础设施)
- [4. 后端开发](#4-后端开发)
- [5. 前端开发](#5-前端开发)
- [6. 全流程启动](#6-全流程启动)
- [7. 外部组件连接](#7-外部组件连接)
- [8. 开发规范](#8-开发规范)

---

## 1. 环境准备

### 1.1 必装工具

| 工具 | 版本要求 | 安装链接 |
|------|---------|---------|
| JDK | 21 | https://adoptium.net/ |
| Maven | >= 3.8 | https://maven.apache.org/download.cgi |
| Node.js | >= 20 | https://nodejs.org/ |
| pnpm | >= 9 | `npm install -g pnpm` |
| Docker | >= 24 | https://docs.docker.com/get-docker/ |
| Docker Compose | >= 2.20 (随 Docker Desktop 自带) | https://docs.docker.com/compose/install/ |
| Git | >= 2.40 | https://git-scm.com/ |

### 1.2 推荐 IDE

| 工具 | 用途 | 安装链接 |
|------|------|---------|
| IntelliJ IDEA Ultimate | 后端 Java 开发 | https://www.jetbrains.com/idea/ |
| VS Code | 前端开发 | https://code.visualstudio.com/ |

#### IntelliJ IDEA 插件

- Lombok
- MyBatisX
- Alibaba Java Coding Guidelines (阿里编码规约)
- Spring Boot Helper

#### VS Code 插件

- Vue - Official
- ESLint
- Prettier
- TypeScript Vue Plugin

### 1.3 验证安装

```bash
java -version      # openjdk 21.x
mvn -version       # Apache Maven 3.8.x+
node -v            # v20.x+
pnpm -v            # 9.x+
docker -v          # 24.x+
docker compose version  # 2.20+
```

---

## 2. 项目结构

```
tech-kg-engine/
├── backend/                    # Java 后端 (Spring Boot 3.5 + SpringBlade)
│   ├── pom.xml
│   └── src/main/
│       ├── java/cn/techkg/
│       │   ├── Application.java
│       │   ├── auth/           # 认证模块
│       │   ├── business/       # 业务模块
│       │   ├── common/         # 公共模块 (config, constant, utils, controller)
│       │   ├── log/            # 日志模块
│       │   └── system/         # 系统模块 (user, role)
│       └── resources/
│           ├── application.yml           # 主配置
│           ├── application-dev.yml       # 开发环境
│           ├── application-prod.yml      # 生产环境
│           └── bootstrap.yml
├── frontend/                   # Vue 3 前端
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.vue
│       ├── main.ts
│       └── components/
├── docker-compose.yml          # 本地基础设施
├── package.json                # Monorepo 根配置
└── docs/                       # 项目文档
```

---

## 3. 基础设施

项目依赖以下外部服务，均通过 Docker Compose 在本地启动：

| 服务 | 端口 | 用途 | 管理界面 |
|------|------|------|---------|
| MySQL 8.0 | 3306 | 关系型数据库 | - |
| Redis 7 | 6379 | 缓存 / 会话存储 | - |
| Kafka 7.7 (KRaft) | 9092 | 消息队列 | - |
| Milvus 2.4 | 19530 | 向量数据库 | 9091 (metrics) |
| etcd 3.5 | (内部) | Milvus 元数据存储 | - |
| MinIO | 9000 / 9001 | Milvus 对象存储 | http://localhost:9001 |

### 启动基础设施

```bash
docker compose up -d
```

### 查看运行状态

```bash
docker compose ps
```

### 查看日志

```bash
docker compose logs -f <service>   # 如: docker compose logs -f milvus
```

### 停止

```bash
docker compose down                # 停止，保留数据
docker compose down -v             # 停止并删除数据卷
```

### 首次启动后需创建数据库

```bash
docker exec mysql mysql -uroot -p123456789 -e "CREATE DATABASE techkg CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### MinIO 管理界面

- 地址: http://localhost:9001
- 用户名: `minioadmin`
- 密码: `minioadmin`

---

## 4. 后端开发

### 4.1 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Java | 21 | LTS |
| Spring Boot | 3.5.13 | Web 框架 |
| Spring Cloud | 2025.0.2 | 微服务 |
| Spring Cloud Alibaba | 2025.0.0.0 | Nacos 等 |
| SpringBlade | 4.7.0 | 业务框架 |
| MyBatis Plus | 3.5.14 | ORM |
| MySQL Connector | (Spring Boot 管理) | 数据库驱动 |
| Milvus SDK Java | 2.4.8 | 向量数据库客户端 |
| Spring Data Redis | (Spring Boot 管理) | Redis 客户端 |
| Spring Kafka | (Spring Boot 管理) | Kafka 客户端 |
| Lombok | (Spring Boot 管理) | 代码简化 |
| OpenTelemetry | 1.30.0 | 链路追踪 |

### 4.2 安装依赖

```bash
cd backend
mvn dependency:resolve
```

Maven 仓库已配置阿里云镜像，国内下载速度有保障。如需修改，编辑 `pom.xml` 中的 `<repositories>` 部分。

### 4.3 启动

```bash
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

启动成功后输出: `---[TECH-KG-ENGINE]---启动完成，当前使用的端口:[8100]，环境变量:[dev]---`

### 4.4 构建 JAR

```bash
cd backend
mvn clean package -DskipTests
java -jar target/tech-kg-engine-1.0.0-SNAPSHOT.jar --spring.profiles.active=dev
```

### 4.5 配置文件说明

| 文件 | 用途 |
|------|------|
| `application.yml` | 主配置: 应用名、MyBatis mapper 路径 |
| `application-dev.yml` | 开发环境: 端口(8100)、数据库/Redis/Kafka/Milvus 连接，Nacos 已禁用 |
| `application-prod.yml` | 生产环境: 通过环境变量注入配置，Nacos 启用 |
| `application-prod.yml` | 生产环境: 通过环境变量注入配置，Nacos 启用 |

开发环境默认使用 `dev` profile，所有连接地址指向 `localhost`。

### 4.6 代码模块

| 模块 | 包路径 | 职责 |
|------|--------|------|
| auth | `cn.techkg.auth` | 登录、登出、Token 刷新 |
| business | `cn.techkg.business` | 核心业务逻辑 |
| system | `cn.techkg.system` | 用户、角色管理 |
| log | `cn.techkg.log` | 操作日志 |
| common | `cn.techkg.common` | 配置、工具类、常量、健康检查 |

### 4.7 可用接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | http://localhost:8100/health | 健康检查 (MySQL/Redis/Milvus/Kafka) |
| GET | http://localhost:8100/business/hello | Hello World 接口 |
| GET | http://localhost:8100/business/health | Business 模块健康检查 |
| POST | http://localhost:8100/auth/login | 登录 (待实现) |
| POST | http://localhost:8100/auth/logout | 登出 (待实现) |

---

## 5. 前端开发

### 5.1 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5 | 前端框架 |
| Vite | 7.3 | 构建工具 |
| TypeScript | 6.0 | 类型系统 |
| Ant Design Vue | 4.2 | UI 组件库 |
| Pinia | 2.1 | 状态管理 |
| Vue Router | 4.3 | 路由 |
| Axios | 1.7 | HTTP 客户端 |
| ECharts | 6.1 | 图表 |
| Vue Flow | 1.48 | 流程图 |
| Less | 4.6 | CSS 预处理器 |

### 5.2 安装 Node.js (nvm)

如果尚未安装 Node.js，推荐使用 nvm 管理：

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc   # 或 source ~/.zshrc

# 安装并使用 Node.js 20
nvm install 20
nvm use 20
```

### 5.3 安装依赖

```bash
cd frontend
pnpm install
```

如果遇到 build scripts 被忽略的提示:

```bash
pnpm approve-builds esbuild
```

### 5.4 启动开发服务器

```bash
cd frontend
pnpm dev
```

默认访问: http://localhost:5173 (如果 5173 被占用会自动递增)

### 5.5 构建生产包

```bash
cd frontend
pnpm build
```

产物输出到 `frontend/dist/`。

### 5.6 API 代理

开发环境下，Vite 会自动将 `/api` 开头的请求代理到后端:

```
/api/business/hello  →  http://localhost:8100/business/hello
```

配置在 `frontend/vite.config.ts` 的 `server.proxy` 中。如后端端口不是 8100，修改此处。

---

## 6. 全流程启动

从空白环境到完整运行:

```bash
# 1. 克隆代码
git clone <repo-url> && cd tech-kg-engine

# 2. 启动基础设施 (MySQL, Redis, Kafka, Milvus 等)
docker compose up -d

# 3. 创建数据库 (仅首次需要)
docker exec mysql mysql -uroot -p123456789 -e "CREATE DATABASE techkg CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 启动后端
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 5. 新终端 - 启动前端
nvm use 20
cd frontend
pnpm approve-builds # 首次安装可能需要approve，取决于pnpm的版本，这是 pnpm 10/11 新增的安全机制
pnpm install
pnpm dev

# 6. 访问
# 前端页面: http://localhost:5173
# 后端健康检查: http://localhost:8100/health
# 后端 Hello 接口: http://localhost:8100/business/hello
# MinIO 控制台: http://localhost:9001
```

---

## 7. 外部组件连接

所有开发环境连接配置集中在 `backend/src/main/resources/application-dev.yml`:

### MySQL

| 配置项 | 值 | 位置 |
|--------|-----|------|
| JDBC URL | `jdbc:mysql://localhost:3306/techkg?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai&characterEncoding=utf8` | `spring.datasource.url` |
| 用户名 | `root` | `spring.datasource.username` |
| 密码 | `123456789` | `spring.datasource.password` |
| 驱动 | `com.mysql.cj.jdbc.Driver` | `spring.datasource.driver-class-name` |

客户端连接:

```bash
docker exec -it mysql mysql -uroot -p123456789 techkg
```

### Redis

| 配置项 | 值 | 位置 |
|--------|-----|------|
| Host | `localhost` | `spring.data.redis.host` |
| Port | `6379` | `spring.data.redis.port` |
| 密码 | 无 | `spring.data.redis.password` (未设置) |
| Database | `0` | `spring.data.redis.database` |

客户端连接:

```bash
docker exec -it redis redis-cli
```

### Kafka

| 配置项 | 值 | 位置 |
|--------|-----|------|
| Brokers | `localhost:9092` | `spring.kafka.bootstrap-servers` |
| Consumer Group | `techkg` | `spring.kafka.consumer.group-id` |

运行模式: KRaft (无需 Zookeeper)

常用命令:

```bash
# 查看主题列表
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 创建主题
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic test --partitions 1 --replication-factor 1

# 消费消息
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning
```

### Milvus

| 配置项 | 值 | 位置 |
|--------|-----|------|
| Host | `localhost` | `milvus.host` |
| Port | `19530` | `milvus.port` |

Milvus 依赖 etcd (元数据) 和 MinIO (对象存储)，这三个服务由 Docker Compose 一并启动。

Python 客户端测试 (可选):

```bash
pip install pymilvus
python -c "from pymilvus import connections; connections.connect(host='localhost', port='19530'); print('OK')"
```

### TRSGraph

TRSGraph 当前部署在 211 服务器上，采用官方安装包解压方式部署，不通过 Docker Compose 启动。后端通过 TRSGraph Java Client 连接 Graph 服务端口 `9669`。

相关资料位于：

```text
docs/
```

连接信息如下：

| 配置项       | 值                            |
| --------- | ---------------------------- |                 
| 用户名       | `root`                       |
| 密码        | `trsadmin`                   |              

如果后端服务也部署在 211 服务器上，可以使用：

```text
host = 127.0.0.1
port = 9669
```

如果后端服务部署在其他服务器或本地开发环境，需要使用：

```text
host =  TRSGraph Graph 服务所在服务器 IP
port = 9669
```

TRSGraph 当前启动方式如下：

```bash
cd trsgraph安装目录
./scripts/trsgraph.service start all
./scripts/trsgraph.service status all
```

检查端口：

```bash
ss -lntp | egrep ':9559|:9669|:9779|:7001'
```

端口说明：

| 端口     | 服务         | 说明                    |
| ------ | ---------- | --------------------- |
| `9559` | Meta 服务    | 元数据、Schema、集群管理       |
| `9669` | Graph 服务   | Java Client / 后端连接该端口 |
| `9779` | Storage 服务 | 点、边、属性数据存储            |
| `7001` | Studio 服务  | TRSGraph 网页管理端        |


---

## 8. 开发规范

### 8.1 后端规范

遵循 **阿里巴巴 Java 开发手册**:

- 在线阅读: https://alibaba.github.io/p3c/
- IDEA 插件: 搜索安装 `Alibaba Java Coding Guidelines`
- 插件文档: https://github.com/alibaba/p3c

核心要点:

- 命名: 类名 UpperCamelCase，方法名 lowerCamelCase，常量全大写下划线分隔，包名全小写
- POJO 类使用 Lombok 的 `@Data` / `@Getter` / `@Setter`，不要手写 getter/setter
- Service 接口以 `I` 开头 (如 `IUserService`)，实现类以 `Impl` 结尾 (如 `UserServiceImpl`)
- Controller 方法返回统一包装结果 (SpringBlade 的 `R<T>`)
- 所有数据库字段必须有注释
- 禁止在循环中调用数据库/远程服务
- 异常不要用来做流程控制
- 优先使用 Java 8+ Stream API，避免嵌套 for 循环

### 8.2 前端规范

- 组件文件名使用 PascalCase (如 `HelloWorld.vue`)
- 组合式 API (Composition API) + `<script setup lang="ts">`
- 使用 Pinia 管理全局状态，不要用 `provide/inject` 传递跨层状态
- CSS 使用 Less 预处理器
- 提交前运行 `pnpm build` 确保编译通过

### 8.3 Git 规范

Commit message 格式:

```
<type>: <description>

type 可选值:
  feat     新功能
  fix      修复 bug
  docs     文档
  style    格式 (不影响逻辑)
  refactor 重构
  test     测试
  chore    构建/工具
```

分支命名:

- `main` - 主分支
- `feat/xxx` - 功能分支
- `fix/xxx` - 修复分支
- `scaffold` - 脚手架 (初始分支)

---

## 9. 端口配置

项目涉及以下端口：

| 端口 | 用途 | 配置位置 |
|------|------|---------|
| 8100 | Java 后端 | `application-dev.yml` → `server.port`，可通过 `SERVER_PORT` 环境变量覆盖 |
| 81-- | Vite 代理目标 | `frontend/.env` → `VITE_API_TARGET` |
| 5173 | 前端开发服务器 | Vite 自动递增，一般无需修改 |
| 3306 | MySQL | `docker-compose.yml` → `tdsql-mysql.ports` |
| 6379 | Redis | `docker-compose.yml` → `redis.ports` |
| 9092 | Kafka | `docker-compose.yml` → `kafka.ports`，同时改 `KAFKA_ADVERTISED_LISTENERS` |
| 9000 | MinIO API | `docker-compose.yml` → `minio.ports` (host 侧) |
| 9001 | MinIO 控制台 | `docker-compose.yml` → `minio.ports` (host 侧) |
| 19530 | Milvus | `docker-compose.yml` → `milvus.ports` |
| 9091 | Milvus Metrics | `docker-compose.yml` → `milvus.ports` |

### 修改后端端口

**方式：环境变量 (推荐，不改动任何文件)**

```bash
SERVER_PORT=8100 mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

### 修改前端调用后端的URL

**方式：前端 .env 文件**

```bash
# 复制模板
cp frontend/.env.example frontend/.env

# 修改 VITE_API_TARGET 指向新的后端地址
# frontend/.env 已被 gitignore，不会提交到仓库
```



