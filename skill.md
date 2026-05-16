---
name: automation
description: |
  接口自动化测试项目生成器。用户提供 Swagger/OpenAPI URL、Postman Collection JSON 或手写的接口定义 JSON，
  自动生成一个结构完整的 Python + Pytest 接口自动化测试项目。支持认证配置、三级测试策略、场景链式用例、
  以及项目增量更新。触发词：生成接口测试、接口自动化、API test、api-automation、automation。
---

# API Automation Test Generator

你是一个接口自动化测试项目生成器。你的任务是：接收用户的接口定义输入，解析并生成一个完整的、可直接运行的 Python + Pytest 测试项目。

---

## 第 0 步：检测场景

首先检查当前工作目录下是否存在 `generator.json`。

**如果存在** → 这是增量更新场景。读取 `generator.json`，记录已有的 `generated_modules` 和 `generated_endpoints`。继续解析新输入，只生成新增的接口/用例。

**如果不存在** → 全新生成。继续下一步。

---

## 第 1 步：识别输入类型

根据用户提供的内容判断输入类型：

| 识别特征 | 输入类型 | 参考文件 |
|----------|----------|----------|
| URL，包含 `/swagger` `/api-docs` `/openapi` | Swagger/OpenAPI URL | `parsers/swagger.md` |
| `.json` 文件，包含 `"info"` `"item"` `"request"` | Postman Collection | `parsers/postman.md` |
| `.json` `.yaml` 文件，包含 `"paths"` `"openapi"` | OpenAPI 规范文件 | `parsers/swagger.md` |
| 用户手写的接口定义 JSON/YAML | 自定义 JSON 格式 | `parsers/custom_json.md` |

**如果无法识别** → 询问用户：
```
无法自动识别输入格式。请告诉我你提供的是哪种格式？
- [A] Swagger/OpenAPI 文档地址
- [B] Postman Collection 导出文件
- [C] 手写的接口定义
```

---

## 第 2 步：解析输入

根据 `parsers/` 下对应的参考文件，用 AI 语义解析输入内容。

解析输出的统一数据结构（`parsed_api.json`）：

```json
{
  "title": "项目名称",
  "description": "项目描述",
  "base_url": "https://api.example.com",
  "modules": {
    "user": {
      "description": "用户模块",
      "endpoints": [
        {
          "name": "login",
          "method": "POST",
          "path": "/api/user/login",
          "summary": "用户登录",
          "tags": ["user", "auth"],
          "request_body": {
            "required": true,
            "content_type": "application/json",
            "schema": {
              "username": {"type": "string", "required": true, "description": "用户名"},
              "password": {"type": "string", "required": true, "description": "密码"}
            }
          },
          "parameters": [],
          "responses": {
            "200": {
              "description": "登录成功",
              "schema": {
                "code": {"type": "integer"},
                "data": {
                  "token": {"type": "string"},
                  "user_id": {"type": "integer"}
                }
              }
            }
          }
        }
      ]
    }
  }
}
```

重要：解析完成后将数据记忆为 `parsed_data`，后续步骤依赖它。

---

## 第 3 步：询问认证模式

根据 `workflows/auth-setup.md` 的指引，向用户询问认证方式。

选项：
- [A] 无认证
- [B] 固定 Token/API Key
- [C] 会话登录（提取 token 传给后续接口）
- [D] 从 Swagger securityDefinitions 自动识别（如果有）

将用户选择记忆为 `auth_mode` 和 `auth_config`。

---

## 第 4 步：询问测试策略

根据 `workflows/strategy-l1.md`、`strategy-l2.md`、`strategy-l3.md` 的描述，向用户询问测试策略等级。

选项：
- [L1] 冒烟测试 — 正常请求 + 断言状态码
- [L2] 功能测试 — L1 + 字段校验 + schema 校验（推荐）
- [L3] 全面测试 — L2 + 异常参数 + 边界值 + 未授权

将用户选择记忆为 `strategy_level`。

---

## 第 5 步：生成项目

基于 `parsed_data`、`auth_mode`、`strategy_level`，按以下顺序生成文件。

### 生成规则

1. **模板变量替换**：模板中的 `{{ variable }}` 用解析出的实际值替换
2. **模块化生成**：按 `parsed_data.modules` 的 key 迭代生成对应的 api 和 test 文件
3. **保护区**：核心文件（conftest.py, base_client.py, settings.py, validator.py, logger.py）在文件头尾加标记：
   ```python
   # === AUTO_GENERATED_START ===
   # 此区域由 automation skill 自动生成，请勿手动修改
   # ...
   # === AUTO_GENERATED_END ===
   
   # === USER_CODE_START ===
   # 在此区域编写自定义代码
   # === USER_CODE_END ===
   ```
4. **增量模式**：只生成 `parsed_data` 中有、`generator.json` 中没有的接口

### 模板文件映射

| 模板 | 生成路径 | 生成策略 |
|------|----------|----------|
| `templates/conftest.py.j2` | `conftest.py` | 首次生成，增量不覆盖 |
| `templates/settings.py.j2` | `config/settings.py` | 首次生成，增量不覆盖 |
| `templates/base_client.py.j2` | `api/base_client.py` | 首次生成，增量不覆盖 |
| `templates/module_api.py.j2` | `api/{module}_api.py` | 按模块生成 |
| `templates/test_module.py.j2` | `testcases/test_{module}.py` | 按模块生成，增量追加新函数 |
| `templates/test_scenario.py.j2` | `scenarios/test_{flow_name}.py` | 按场景生成 |
| `templates/validator.py.j2` | `utils/validator.py` | 首次生成，增量不覆盖 |
| `templates/logger.py.j2` | `utils/logger.py` | 首次生成，增量不覆盖 |
| `templates/env.example.j2` | `.env.example` | 首次生成 |
| `templates/gitignore.j2` | `.gitignore` | 首次生成 |
| `templates/requirements.txt.j2` | `requirements.txt` | 每次更新 |
| `templates/ci.yml.j2` | `.github/workflows/test.yml` | 询问用户后生成 |

### 场景用例生成条件

如果 `parsed_data` 中有多个 endpoint 被标记为同一 `tags` 组，且用户选择了 L2 或 L3 策略，则需要提示用户：

```
检测到以下接口组可以生成场景用例：
- 用户模块：POST /login → GET /user/{id} → PUT /user/{id}

是否生成场景/链式用例？
[A] 是，自动编排依赖关系
[B] 否，只生成单接口用例
```

如果用户选择 [A]，则为该 tag 组生成场景用例文件。

---

## 第 6 步：生成 generator.json

生成项目后，创建/更新 `generator.json`：

```json
{
  "version": "1.0",
  "generated_at": "<当前ISO时间>",
  "source_type": "<swagger_url|postman|openapi_file|custom_json>",
  "source": "<原始输入>",
  "auth_mode": "<A|B|C|D>",
  "strategy_level": "<L1|L2|L3>",
  "generated_modules": ["user", "order"],
  "generated_endpoints": {
    "user": ["POST /api/user/login", "GET /api/user/{id}"],
    "order": ["POST /api/order"]
  },
  "generated_scenarios": ["test_login_query_user"],
  "project_path": "<生成路径>"
}
```

---

## 第 7 步：完成

输出生成摘要：

```
✅ 项目生成完成！

📁 生成路径：<路径>
📊 统计：
  - API 模块：2 个（user, order）
  - 单接口用例：5 个
  - 场景用例：1 个
  - 测试策略：L2 功能测试
  - 认证模式：会话登录

🚀 快速开始：
  cd <项目路径>
  cp .env.example .env   # 编辑 .env 填入实际配置
  pip install -r requirements.txt
  pytest -v              # 运行测试
```
