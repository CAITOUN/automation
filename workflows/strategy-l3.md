# Strategy Level 3 — 全面测试

## 目标
最大化覆盖。包含所有 L2 用例 + 异常参数 + 边界值 + 未授权测试。

## 生成规则

每个 endpoint 生成 **5-8 个** test 函数：

### L2 用例（3个）
正常请求 + Schema + 响应时间（同 strategy-l2.md）

### 4. 必填参数缺失
```python
def test_{name}_missing_required_params(client, auth_headers):
    """全面测试：{summary} - 缺少必填参数"""
    # 逐个移除每个 required 参数
    resp = client.{method}(
        "/api/user/login",
        headers=auth_headers,
        json={"password": "123456"}  # 缺少 username
    )
    assert resp.status_code in [400, 422]
    body = resp.json()
    assert "message" in body or "error" in body
```

### 5. 参数类型错误
```python
def test_{name}_invalid_param_types(client, auth_headers):
    """全面测试：{summary} - 参数类型错误"""
    resp = client.{method}(
        "/api/user/login",
        headers=auth_headers,
        json={"username": 12345, "password": True}  # 类型错误
    )
    assert resp.status_code in [400, 422]
```

### 6. 边界值测试
```python
def test_{name}_boundary_values(client, auth_headers):
    """全面测试：{summary} - 边界值"""
    test_cases = [
        # (username, password, expected_status)
        ("", "123456", 400),           # 空字符串
        ("a" * 256, "123456", 400),    # 超长字符串
        ("admin", "", 400),            # 空密码
        ("<script>alert(1)</script>", "123456", 400),  # XSS
        ("admin'--", "123456", 400),   # SQL 注入尝试
    ]
    for username, password, expected in test_cases:
        resp = client.{method}(
            "/api/user/login",
            headers=auth_headers,
            json={"username": username, "password": password}
        )
        assert resp.status_code == expected, f"Failed for username={username}"
```

### 7. 未授权访问
```python
def test_{name}_unauthorized(client):
    """全面测试：{summary} - 未授权访问"""
    resp = client.{method}(
        "/api/user/1",  # 需要认证的接口
        # 不传 auth_headers
    )
    assert resp.status_code in [401, 403]
```

### 8. 资源不存在（GET/PUT/DELETE 接口）
```python
def test_{name}_not_found(client, auth_headers):
    """全面测试：{summary} - 资源不存在"""
    resp = client.get("/api/user/999999", headers=auth_headers)
    assert resp.status_code == 404
```

### 9. 重复操作（POST 创建类接口）
```python
def test_{name}_duplicate_create(client, auth_headers):
    """全面测试：{summary} - 重复创建"""
    payload = {"name": "test_user", "email": "test@example.com"}
    
    # 第一次创建
    resp1 = client.post("/api/user", headers=auth_headers, json=payload)
    assert resp1.status_code == 201
    
    # 第二次创建（相同数据）
    resp2 = client.post("/api/user", headers=auth_headers, json=payload)
    assert resp2.status_code in [409, 422]
```

## 生成策略

- L3 对每个 endpoint 都生成上述全部用例
- 边界值测试用例根据参数类型调整（string → 空/超长/特殊字符，int → 负数/零/超大值）
- 如果接口是 GET（无 request body），跳过参数类型错误测试
- 如果接口是公开的（无 auth），跳过未授权测试

## 数据生成到 data/

边界值数据会自动提取到 `data/{module}_data.py`：
```python
import pytest

# 边界值测试数据
LOGIN_BOUNDARY_DATA = [
    ("", "123456", 400, "空用户名"),
    ("a" * 256, "123456", 400, "超长用户名"),
    ("admin", "", 400, "空密码"),
]
```
用例中使用 `@pytest.mark.parametrize` 引用。
