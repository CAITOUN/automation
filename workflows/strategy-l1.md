# Strategy Level 1 — 冒烟测试

## 目标
验证接口基本可用。最小覆盖，最快执行。

## 生成规则

每个 endpoint 生成 **1 个** test 函数：

### 正常请求 + 基本断言
```python
def test_{name}_smoke(client, auth_headers):
    """冒烟测试：{summary}"""
    resp = client.{method}(
        "/api/user/login",
        headers=auth_headers,
        json={request_body_default_values}
    )
    assert resp.status_code == 200
    assert resp.text  # 响应体非空
```

### 特点
- 只测正常场景
- request body 使用默认值/示例值
- path/query 参数使用占位值（如 `{id}` → `1`）
- 只断言状态码 + 响应体非空
- 不校验字段类型
- 不测异常场景

### 适用场景
- 快速验证接口是否通
- CI 冒烟检查
- 接口刚开发完的连通性验证
