# Custom JSON Parser

## 输入场景
用户提供手写的接口定义 JSON/YAML 文件，或直接在对话中描述接口列表。

## 接受的最小格式

```json
{
  "title": "项目名称",
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
          "request_body": {
            "username": "string",
            "password": "string"
          },
          "response": {
            "code": 0,
            "data": { "token": "string", "user_id": 1 }
          }
        }
      ]
    }
  }
}
```

## 解析逻辑

### 1. 基础信息
- `title` → 项目名称
- `description` (可选) → 项目描述
- `base_url` → 被测服务地址

### 2. 模块与接口
遍历 `modules`，对每个 endpoint：

1. **生成 func_name**：`name` 转 snake_case（如 `"userLogin"` → `"user_login"`）
2. **提取 HTTP method**：`method` 转大写
3. **提取 path params**：从 `path` 的正则 `\{(\w+)\}` 匹配（如 `/api/user/{userId}` → `userId`）
4. **生成 path_fstring**：path 原样保留（含 `{param}` 部分，作为 f-string 模板）
5. **提取 content_type**：
   - 如果 endpoint 有 `content_type` 字段 → 直接使用
   - 如果没有，根据 method 推断：
     - POST/PUT/PATCH 通常 → `"json"`
     - 如果有 `files` 参数 → `"multipart"`
     - 如果有 `form` 标记 → `"form"`
   - GET/DELETE 通常 → `null`（无 body），如有 query 参数 → `has_query_params: true`
6. **提取 request_body**：如果 content_type 非 null，将字段映射为参数
   - 对象格式 `{"field": "type"}` → 提取 field 名和类型
   - 默认值推断：`"string"` → `""`, `"integer"` → `0`, `"boolean"` → `False`
   - 设置 `has_body: true`

### 2-续. 接口变量补充

每个 endpoint 额外计算：
| 变量 | 来源 | 说明 |
|------|------|------|
| `content_type` | 字段或推断 | `"json"` / `"form"` / `"multipart"` / `null` |
| `has_body` | content_type 非 null | `true` / `false` |
| `has_query_params` | parameters 中有 query 类型 | `true` / `false` |
| `has_file` | content_type == "multipart" | `true` / `false` |
   - 类型映射：`"string"` → `"string"`, `"integer"` → `"integer"`, `1` → `"integer"`, `"text"` → `"string"`
7. **确定 expected_ok_status**：
   - POST → `201`
   - GET/PUT/PATCH/DELETE → `200`

### 3. 生成 body_default
将所有 request_body 字段的值替换为类型推断的默认值：

```python
# request_body: {"username": "string", "password": "string"}
# → body_default = {"username": "", "password": ""}
# 
# request_body: {"product_id": "integer", "quantity": 1, "address": "string"}
# → body_default = {"product_id": 0, "quantity": 0, "address": ""}
```

### 4. 生成 field_checks
根据 response 结构递归生成 assert 语句。对每个 response 字段：
```
response = {"code": 0, "data": {"token": "string", "user_id": 1}}
→
assert "code" in body
assert "data" in body
assert "token" in body["data"] and isinstance(body["data"]["token"], str)
assert "user_id" in body["data"] and isinstance(body["data"]["user_id"], int)
```

### 5. 最小化输入
如果用户只是简单描述接口（如"测一下 /api/user/login，POST，传 username 和 password"），AI 应：
- 推断 `title` = "API Tests"
- 推断 `base_url` = "https://api.example.com"（提醒用户修改）
- 推断 `method` = "POST"
- 从描述中提取参数
- 推断 `module` = "default"

## 输出
整理为 `parsed_data`（格式见 skill.md 第 2 步），额外计算字段：
- `module_class_name`：模块名转 PascalCase（`"user"` → `"User"`）
- `endpoint.func_name`：snake_case
- `endpoint.path_fstring`：含 `{var}` 的 f-string 路径
- `endpoint.path_params`：路径中的变量列表
- `endpoint.all_params`：path_params（无 query params 时）
- `endpoint.body_default`：Python dict 字面量字符串
- `endpoint.field_checks`：assert 语句列表
- `endpoint.response_schema`：Python dict 字面量（用于 assert_schema）
- `endpoint.expected_ok_status`：200 或 201
