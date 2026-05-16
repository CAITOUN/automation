# Postman Collection Parser

## 输入场景
用户提供 Postman Collection 导出文件（`.json`），通常是 Postman 的 Collection v2.0/v2.1 格式。

## 解析逻辑

### 1. 识别 Postman 版本
- `"info": {"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}` → v2.1
- `"info": {"schema": "https://schema.getpostman.com/json/collection/v2.0.0/collection.json"}` → v2.0

### 2. 提取项目信息
```json
{
  "title": "collection.info.name",
  "description": "collection.info.description"
}
```

### 3. 提取 base_url

Postman 常用变量存储 base_url：
```json
"variable": [
  {"key": "base_url", "value": "https://api.example.com"},
  {"key": "token", "value": ""}
]
```

提取逻辑：
1. 查找 `collection.variable` 中的 `base_url`/`host`/`url` 变量
2. 如果没有变量，从第一个 request URL 中提取 host 部分
3. 记录所有变量（`{{base_url}}` 等），在生成时提示用户配置 .env

### 4. 解析 item → 模块

Postman Collection 有层级结构（文件夹/子文件夹），正好映射为模块：

```
Collection
├── 用户模块/              ← module: user
│   ├── 登录              ← endpoint: POST /api/user/login
│   ├── 获取用户信息       ← endpoint: GET /api/user/{id}
│   └── 更新用户          ← endpoint: PUT /api/user/{id}
├── 订单模块/              ← module: order
│   ├── 创建订单           ← endpoint: POST /api/order
│   └── 查询订单           ← endpoint: GET /api/order/{id}
└── 无文件夹的散装请求      ← module: default
```

解析每个 `item`：
- 如果 `item` 还有子 `item`（文件夹）→ 文件夹名 = 模块名
- 每个 `request` 对象提取：
  - `name`：请求名称
  - `method`：`request.method`
  - `path`：从 `request.url` 提取（去除 `{{base_url}}` 和 query string）
  - `headers`：`request.header[]`
  - `body`：`request.body`（raw/urlencoded/formdata）
  - `auth`：`request.auth` 或 `collection.auth`
  - `query_params`：从 `request.url.query[]` 提取

### 5. 提取请求体 + content_type

Postman body 有多种模式，映射为 content_type：

| Postman mode | content_type | 说明 |
|-------------|-------------|------|
| `raw` (JSON) | `"json"` | `has_body: true` |
| `urlencoded` | `"form"` | `has_body: true` |
| `formdata` | `"multipart"` | `has_body: true`（含文件时标记 file 参数）|
| 无 body（GET） | `null` | `has_body: false`，如有 query 参数则 `has_query_params: true` |

- **raw JSON**（最常见）：`request.body.mode = "raw"` + `request.body.raw`（JSON 字符串）
  - 从 JSON 推断 schema 结构
- **urlencoded**：`request.body.urlencoded[]`
- **formdata**：`request.body.formdata[]`（字段可能是 `type: "file"` → 文件上传）

### 6. 提取认证

检查 `collection.auth` 或 `request.auth`：
```
auth.type:
  - "noauth" → 无认证
  - "apikey" → API Key（in header/query）
  - "bearer" → Bearer Token（记录 token 值或变量）
  - "basic" → HTTP Basic Auth
```

### 7. 提取请求示例作为测试数据

Postman Collection 常包含 example responses。解析 `request.url` 的 query params 和 body 中的具体值作为测试数据：

```json
"test_data": {
  "login": {
    "username": "admin",
    "password": "123456"
  }
}
```

这些值写入 `data/{module}_data.py` 作为参数化数据。

### 8. Postman Pre-request Script / Tests 脚本

如果 Postman 包含 pre-request scripts 或 tests scripts：
- Pre-request script 中的变量设置 → 提示用户这些是链式依赖
- Tests script 中的断言 → 转换为 pytest assert 语句

## 输出
将解析结果整理为 `parsed_data`（格式见 skill.md 第 2 步）。
