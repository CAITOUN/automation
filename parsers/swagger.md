# Swagger / OpenAPI Parser

## 输入场景
用户提供一个 Swagger/OpenAPI 文档地址（如 `https://api.example.com/v2/api-docs`）或本地 OpenAPI JSON/YAML 文件。

## 获取方式

### 场景 A：URL
使用 Python 的 `requests` 库拉取（在 AI 内部模拟，或告知用户手动提供内容）：

```python
import requests
resp = requests.get("<用户提供的URL>")
spec = resp.json()  # OpenAPI 3.x 或 Swagger 2.0
```

如果不能直接拉取（网络隔离），请用户手动提供 `curl` 输出或文件内容。

### 场景 B：本地文件
直接读取用户提供的 JSON/YAML 文件内容。

## 解析逻辑

### 1. 识别版本
- `"openapi": "3.x.x"` → OpenAPI 3.x
- `"swagger": "2.0"` → Swagger 2.0
- 解析逻辑兼容两者，差异处见 `openapi_spec.md`

### 2. 提取 base_url

**OpenAPI 3.x：**
```
servers[0].url  → 如 "https://api.example.com/v2"
```
如果 `servers` 有多个，列出让用户选。取第一个作为默认。

**Swagger 2.0：**
```
schemes[0] + "://" + host + basePath  → 如 "https://api.example.com/v2"
```

### 3. 提取项目信息
```json
{
  "title": "spec.info.title",
  "description": "spec.info.description"
}
```

### 4. 解析 paths → modules

遍历 `spec.paths`（如 `/api/user/login`）：

1. **确定模块名**：
   - 从 path 中提取：`/api/{module}/...` → `module`
   - 或从 `tags[0]` 提取
   - 或从 `operationId` 推断
   - 如果都没有 → 归入 `"default"` 模块

2. **解析每个 method（GET/POST/PUT/DELETE/PATCH）**：
   - `name`：`operationId` 或 `{method}_{path_last_segment}`
   - `method`：HTTP method（小写转大写）
   - `path`：原始 path
   - `summary`：`summary` 字段
   - `tags`：`tags` 数组
   - `parameters`：path/query/header 参数
   - `request_body`：`requestBody.content["application/json"].schema`
   - `responses`：提取所有 status code 的 response schema

3. **参数解析**（OpenAPI 3.x）：
   ```
   parameters[].name / in (path|query|header) / required / schema.type / description
   ```

4. **request_body 解析**（OpenAPI 3.x）：
   ```
   requestBody.required
   requestBody.content["application/json"].schema
   → 展开 $ref 引用
   → 提取 properties / required 列表
   ```

5. **responses 解析**：
   主要关注 `200`/`201` 的 response schema，用于生成断言。

### 5. 展开 $ref 引用
Swagger/OpenAPI 大量使用 `$ref` 引用。解析时：
- `"$ref": "#/components/schemas/User"` → 查找 `spec.components.schemas.User`
- 递归展开嵌套引用
- 如果引用无法解析，保留原始 `$ref` 路径并标注 `[未解析]`

### 6. 识别认证方式
检查：
- `spec.components.securitySchemes`（OpenAPI 3.x）
- `spec.securityDefinitions`（Swagger 2.0）

识别类型：
- `apiKey` → Header/Query 中的固定 Key
- `http` + `bearer` → Bearer Token
- `oauth2` → OAuth2 流程

提取后记录到输出，用于 Step 3 询问认证模式时提供默认选项。

## 输出
将解析结果整理为 `parsed_data`（格式见 skill.md 第 2 步），供后续步骤使用。
