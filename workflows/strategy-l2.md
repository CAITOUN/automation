# Strategy Level 2 — 功能测试（推荐）

## 目标
验证接口功能正确性。包含字段校验和 schema 校验。

## 生成规则

每个 endpoint 生成 **2-3 个** test 函数：

### 1. 正常请求 + 字段断言
```python
def test_{name}_ok(client, auth_headers):
    """功能测试：{summary} - 正常请求"""
    resp = client.{method}(
        "/api/user/login",
        headers=auth_headers,
        json={"username": "admin", "password": "123456"}
    )
    assert resp.status_code == 200
    
    body = resp.json()
    # 断言顶层字段
    assert "code" in body
    assert body["code"] == 0
    assert "data" in body
    
    # 断言核心业务字段存在 + 类型
    data = body["data"]
    assert "token" in data and isinstance(data["token"], str)
    assert "user_id" in data and isinstance(data["user_id"], int)
```

### 2. Response Schema 校验（如果有 schema 定义）
```python
def test_{name}_schema(client, auth_headers):
    """功能测试：{summary} - 响应 Schema 校验"""
    resp = client.{method}(...)
    assert resp.status_code == 200
    
    # 使用 utils/validator.py 的 assert_schema
    expected_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "integer"},
            "data": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user_id": {"type": "integer"}
                },
                "required": ["token", "user_id"]
            }
        }
    }
    assert_schema(resp.json(), expected_schema)
```

### 3. 响应时间断言（可选）
```python
def test_{name}_response_time(client, auth_headers):
    """功能测试：{summary} - 响应时间"""
    resp = client.{method}(...)
    assert_response_time(resp, max_ms=2000)
```

## 字段校验规则

从 `parsed_data` 的 response schema 提取字段并生成断言：
- 所有 `required` 字段 → 生成 `assert "field" in data`
- 字段类型 → 生成 `isinstance(data["field"], expected_type)`
- 嵌套对象 → 递归生成子字段断言

类型映射：
```
string → str
integer → int
number → float
boolean → bool
array → list
object → dict
```

## 场景用例触发条件

如果同一模块的 endpoint 数量 ≥ 2，且用户同意生成场景用例：
- 按 tags 分组，或根据 endpoint 间的依赖关系编排
- 常见链式模式：
  - POST /login → GET /user → PUT /user
  - POST /order → GET /order/{id} → DELETE /order/{id}
- 每个链生成一个 `scenarios/test_{flow_name}.py`
