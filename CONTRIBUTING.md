# Contributing to Tech-KG-Engine

Welcome to **Tech-KG-Engine** — a Billion-Scale Technology Knowledge Graph Engine for Scientific Discovery and Industrial Intelligence.

This document describes how to set up, develop, and contribute to the project.

---

## Table of Contents

- [Contributing to Tech-KG-Engine](#contributing-to-tech-kg-engine)
  - [Table of Contents](#table-of-contents)
  - [Project Architecture](#project-architecture)
  - [Prerequisites](#prerequisites)
    - [必装](#必装)
    - [基础设施 (本地开发可选，Docker 可替代)](#基础设施-本地开发可选docker-可替代)
  - [Quick Start](#quick-start)
  - [Project Structure](#project-structure)
    - [Frontend (`frontend/`)](#frontend-frontend)
    - [Backend (`backend/`)](#backend-backend)
  - [Development Guide](#development-guide)
    - [Frontend (Vue 3)](#frontend-vue-3)
    - [Backend (Spring Cloud)](#backend-spring-cloud)
  - [Coding Standards](#coding-standards)
    - [通用](#通用)
    - [Frontend](#frontend)
    - [Java](#java)
  - [Git Workflow](#git-workflow)
    - [分支策略 (GitHub Flow)](#分支策略-github-flow)
    - [Commit 规范](#commit-规范)
    - [工作流程](#工作流程)
  - [Build \& Deploy](#build--deploy)
    - [Docker 部署 (推荐)](#docker-部署-推荐)
    - [手动部署](#手动部署)
  - [Infrastructure](#infrastructure)
    - [可观测性 (OpenTelemetry)](#可观测性-opentelemetry)
    - [公共组件](#公共组件)
    - [项目组共建能力](#项目组共建能力)

---

## Project Architecture

```
tech-kg-engine/
├── frontend/              # Vue 3 + Vite 前端应用
├── backend/               # Spring Cloud 微服务 (Maven)
├── packages/              # 共享包 (未来扩展)
├── docs/                  # 项目文档
├── package.json           # 根 workspace 配置
├── pnpm-workspace.yaml    # pnpm workspace 定义
└── CONTRIBUTING.md
```

| 层级 | 技术栈 | 包管理 | 构建工具 |
|------|--------|--------|----------|
| Frontend | Vue 3 + Vite 7 + TypeScript | pnpm 9 | Vite |
| Backend | Spring Boot 3.5 + Spring Cloud 2025 | Maven | Maven |

---

## Prerequisites

### 必装

| 工具 | 版本 | 说明 |
|------|------|------|
| **Node.js** | >= 20.0.0 | 前端运行时 |
| **pnpm** | >= 9.0.0 | 前端包管理器 (`corepack enable && corepack prepare pnpm@latest --activate`) |
| **Java JDK** | 21 | 后端运行时 |
| **Maven** | >= 3.9 | 后端构建工具 |
| **Git** | >= 2.40 | 版本控制 |

### 基础设施 (本地开发可选，Docker 可替代)

| 服务 | 用途 | 默认端口 |
|------|------|----------|
| MySQL / TDSQL | 关系型数据库 | 3306 |
| Redis 7 | 缓存 | 6379 |
| Nacos 3 | 服务注册与配置中心 | 8848 |
| Neo4j | 图数据库 | 7474/7687 |
| Milvus | 向量数据库 | 19530 |
| Kafka | 消息队列 | 9092 |

---

## Quick Start

```bash
# 1. 克隆仓库
git clone <repo-url> tech-kg-engine
cd tech-kg-engine

# 2. 安装前端依赖
pnpm install

# 3. 启动前端开发服务器
pnpm dev

# 4. (可选) 启动后端
cd backend
mvn clean install -DskipTests
# 按需启动具体微服务模块
```

---

## Project Structure

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── api/                # API 接口层
│   │   ├── modules/        # 按业务模块拆分
│   │   └── http.ts         # Axios 实例 + 拦截器
│   ├── assets/             # 静态资源
│   │   ├── styles/         # 全局样式 (Less)
│   │   └── svg/            # SVG 图标
│   ├── components/         # 通用组件
│   ├── hooks/              # 组合式函数 (Composables)
│   ├── layouts/            # 布局组件
│   ├── locales/            # 国际化 (中/英)
│   ├── router/             # 路由配置
│   ├── stores/             # Pinia 状态管理
│   ├── utils/              # 工具函数
│   ├── views/              # 页面视图
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .eslintrc.js
```

**核心技术栈**: Vue 3.5 + Vite 7 + TypeScript 5.9 + Vue Router 4 + Pinia 2 + Ant Design Vue 4

### Backend (`backend/`)

```
backend/
├── pom.xml                     # Maven 父工程 POM
├── common/                     # 公共基础模块
├── auth/                       # 统一认证中心
├── gateway/                    # API 网关
├── service/                    # 业务微服务
│   ├── business/               # 业务管理服务
│   ├── system/                 # 系统管理服务
│   └── log/                    # 日志服务
└── service-api/                # Feign 接口 + DTO + VO + Entity
    ├── business-api/
    └── system-api/
```

**核心技术栈**: Java 21 + Spring Boot 3.5 + Spring Cloud 2025 + Spring Cloud Alibaba + MyBatis Plus 3.5

---

## Development Guide

### Frontend (Vue 3)

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 代码检查
pnpm lint

# 自动修复
pnpm lint:fix

# 类型检查
pnpm type-check

# 单元测试
pnpm test

# E2E 测试
pnpm test:e2e

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

**环境切换**: 通过 Vite mode 切换 `dev` / `pre` / `prod` / `mock`，对应 `.env.[mode]` 配置文件。

**代码规范工具**: ESLint 9 (Flat Config) + Prettier 3 + Husky + lint-staged + commitlint

### Backend (Spring Cloud)

```bash
# 构建全部模块
cd backend
mvn clean install -DskipTests

# 启动指定微服务 (示例: 业务服务)
cd service/business
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 运行测试
mvn test

# Docker 构建
mvn package -DskipTests
docker build -t business-service:latest ./service/business
```

**配置文件**: `bootstrap.yml` (通用) + `application-dev.yml` (开发) + `application-prod.yml` (生产)

**代码分层**: Controller → Service → Mapper (MyBatis Plus)，Feign 用于服务间调用

---

## Coding Standards

### 通用

- 遵循 `.editorconfig` 配置：UTF-8, LF, 尾行换行, 去除尾空格
- 所有文件头部不得添加作者/日期注释
- 注释使用中文或英文，保持同一文件内一致

### Frontend

- Vue SFC 使用 `<script setup lang="ts">` + `<style scoped>`
- 组件命名使用 PascalCase，文件命名使用 PascalCase
- 组合式函数 (hooks) 使用 camelCase，以 `use` 开头
- API 按业务模块拆分，统一经过 `http.ts` 拦截器
- 优先使用 `@vueuse/core` 提供的工具函数
- 状态管理使用 Pinia，按模块拆分 store

### Java

- 遵循阿里巴巴 Java 开发手册
- Controller 只做参数校验和结果封装，业务逻辑在 Service 层
- Service 间调用通过 Feign Client，禁止直接注入其他服务的 Mapper
- Entity / DTO / VO 严格分离，定义在 `service-api` 模块
- 异常处理：业务异常用 `BusinessErrorCode`，未知异常走全局拦截
- 配置类统一放在 `config/` 包下

---

## Git Workflow

### 分支策略 (GitHub Flow)

采用 [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)，只有一个长期分支 `main`：

1. `main` 始终可部署
2. 所有变更从 `main` 创建分支，完成后通过 PR 合并回 `main`
3. 合并后立即部署

| 分支 | 命名规则 | 示例 |
|------|----------|------|
| `main` | — | — |
| 功能分支 | `<type>/<short-desc>` | `feat/kg-query` |
| 修复分支 | `<type>/<short-desc>` | `fix/login-error` |

### Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 列表**:

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 缺陷修复 |
| `docs` | 文档变更 |
| `style` | 代码格式 (不影响逻辑) |
| `refactor` | 重构 (非新功能/非修复) |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖变更 |
| `ci` | CI/CD 配置变更 |

**示例**:

```
feat(kg-query): 添加知识图谱多跳查询接口

支持 1-5 跳的实体关系查询，返回路径和中间节点

Closes #42
```

### 工作流程

1. 从 `main` 创建分支（`feat/xxx` 或 `fix/xxx`）
2. 开发过程中频繁提交，遵循 commit 规范
3. 开发完成后确保 lint 和测试通过
4. 创建 Pull Request 到 `main`
5. Code Review 通过后合并
6. 合并后部署到生产环境

---

## Build & Deploy

### Docker 部署 (推荐)

每个服务目录下均有 `Dockerfile`，使用 Docker Compose 编排：

```bash
# 构建所有服务
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f <service-name>
```

### 手动部署

**Frontend**:
```bash
pnpm build          # 输出到 frontend/dist/
# 将 dist/ 部署到 Nginx 或 CDN
```

**Backend**:
```bash
cd backend
mvn clean package -DskipTests
# 各微服务 target/*.jar 部署到服务器
java -javaagent:opentelemetry-javaagent.jar \
     -Dotel.service.name=business-service \
     -Dotel.exporter.otlp.endpoint=http://otel-collector:4317 \
     -jar service/business/target/business.jar
```

---

## Infrastructure

### 可观测性 (OpenTelemetry)

本项目采用 OpenTelemetry 统一可观测方案：

```
微服务 (Java)
  ↓ OTLP
OTel Collector
  ├─ Trace  → Tempo
  ├─ Metric → Prometheus
  └─ Log    → Loki
  ↓
Grafana (统一展示)
```

- Java 服务通过 OTel JavaAgent 无侵入埋点
- 前端通过 OTel Web SDK 埋点
- 所有服务统一通过 OTLP 协议发送至 OTel Collector

### 公共组件

| 组件 | 说明 |
|------|------|
| TDSQL | 关系型数据库，兼容 MySQL 协议 |
| Redis 7 | 缓存与消息 |
| Nacos 3 | 服务注册、配置中心 |
| 拓尔思图数据库 | 图数据库 |
| Milvus | 向量数据库 |
| Kafka | 消息队列 |
| RustFS | 对象存储 |
| NFS | 文件系统 |

### 项目组共建能力

| 能力 | 说明 |
|------|------|
| 统一用户中心 | 登录、鉴权、用户信息 |
| 流程表单中心 | 对接中 |
| 大模型调用 | 超大规模智算引擎模型服务 |
| 短信和邮件 | 统一出口封装 |
