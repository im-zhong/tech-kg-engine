# Tech KG Engine - Agent 开发指南

## 项目身份

技术知识图谱引擎，单体应用，前后端分离。不是微服务架构。

## 核心约束

### 后端 (Java)

- **单体应用**: 只有一个 `pom.xml`，一个 `Application.java`，不要创建多模块结构
- **包管理**: 添加依赖只改 `backend/pom.xml`，版本号放 `<properties>`
- **Java 21**: 可以使用 record、sealed class、text block、pattern matching 等新特性
- **SpringBlade**: 使用 `R<T>` 作为 Controller 统一返回类型，使用 `@BladeLogger` 记录日志
- **不要手写 getter/setter**: 统一使用 Lombok `@Data`
- **Service 命名**: 接口 `IXxxService`，实现 `XxxServiceImpl`

### 前端 (Vue 3)

- **`<script setup lang="ts">`**: 必须使用组合式 API + TypeScript
- **pnpm**: 不要使用 npm 或 yarn
- **API 代理**: 前端通过 `/api` 前缀访问后端，Vite 自动代理到 `localhost:9000`

## 质量检查命令

### 后端（在 backend/ 目录）

```bash
# 编译检查
mvn compile

# 运行测试
mvn test

# 编译 + 安装到本地仓库
mvn install -DskipTests
```

### 前端（在 frontend/ 目录）

```bash
# 类型检查
npx vue-tsc --noEmit

# Lint 检查 + 自动修复
npx eslint src/ --fix

# 格式化
npx prettier --write src/

# 完整构建（含类型检查）
pnpm build
```

## 代码修改后必做

1. **后端**: `mvn compile` 确认编译通过
2. **前端**: `npx eslint src/ --fix && npx vue-tsc --noEmit` 确认无类型错误
3. 如果有测试: 跑测试确认通过

## 环境感知

### 无 Docker 环境

后端可以用 `local` profile 启动（H2 内嵌数据库，无需任何外部服务）:

```bash
cd backend && mvn spring-boot:run -Dspring-boot.run.profiles=local
```

### 有 Docker 环境

```bash
docker compose up -d
cd backend && mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

## 配置文件定位

| 文件 | 位置 | 用途 |
|------|------|------|
| 后端主配置 | `backend/src/main/resources/application.yml` | 端口、应用名 |
| 后端开发配置 | `backend/src/main/resources/application-dev.yml` | MySQL/Redis/Kafka/Milvus |
| 后端本地配置 | `backend/src/main/resources/application-local.yml` | H2、禁用 Nacos |
| 前端 Vite 配置 | `frontend/vite.config.ts` | API 代理、构建选项 |
| Docker 服务 | `docker-compose.yml` | MySQL/Redis/Kafka/Milvus |

## 常见陷阱

- SpringBlade 要求 `blade.env` 属性，在 `bootstrap.yml` 中定义
- Nacos 相关自动配置在无 Nacos 服务器时会导致启动失败，`local` 和 `dev` profile 已排除
- `application-dev.yml` 中 `spring.main.allow-bean-definition-overriding: true` 必须保留（解决 SpringBlade Sentinel bean 冲突）
- 前端 API 调用必须走 `/api` 前缀，不要直接写 `http://localhost:9000`
