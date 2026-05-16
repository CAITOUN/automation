# Auth Setup Workflow

## 目标
询问用户并确定认证配置，生成对应的 conftest.py fixture。

## 询问流程

```
🔐 认证配置
检测到接口需要认证，请选择认证方式：

[A] 无认证 — 接口无需任何认证
[B] 固定 Token/API Key — 在 .env 配置固定凭证，每次请求自动带上
[C] 会话登录 — 先调 login 接口获取 token，再传给后续接口
[D] 从文档自动识别（如果 Swagger/Postman 中有定义）
```

---

## 各模式处理

### [A] 无认证
- `auth_mode = "none"`
- conftest 中不注入 auth header
- 跳过认证相关生成

### [B] 固定 Token / API Key
询问：
```
请提供 Token/API Key 的配置信息：
- Header 名称（如 Authorization、X-API-Key）：
- Token 前缀（如 Bearer，无则留空）：
- .env 中的变量名（如 API_KEY）：
```

生成逻辑：
- 在 `.env.example` 中添加对应变量
- conftest.py 中：
  ```python
  @pytest.fixture(scope="session")
  def auth_headers(settings):
      token = settings.API_KEY
      return {"Authorization": f"Bearer {token}"}
  ```
- base_client 自动注入 auth_headers

### [C] 会话登录
这是最复杂的模式。询问：
```
请选择作为登录的接口（从解析结果中列出 POST 接口）：
[A] POST /api/user/login
[B] POST /api/auth/signin
[C] 其他（请指定 path）

请提供从登录响应中提取 token 的 JSON 路径：
示例：data.token / data.access_token / headers.Set-Cookie

Token 放在后续请求的哪里：
[A] Header: Authorization: Bearer {token}
[B] Header: X-Auth-Token: {token}
[C] Cookie
```

生成逻辑：
- conftest.py 中生成 `auth_token` session-scoped fixture：
  ```python
  @pytest.fixture(scope="session")
  def auth_token(settings, base_url):
      resp = requests.post(f"{base_url}/api/user/login", json={
          "username": settings.LOGIN_USERNAME,
          "password": settings.LOGIN_PASSWORD
      })
      assert resp.status_code == 200
      return resp.json()["data"]["token"]
  
  @pytest.fixture
  def auth_headers(auth_token):
      return {"Authorization": f"Bearer {auth_token}"}
  ```
- `.env.example` 中添加 LOGIN_USERNAME、LOGIN_PASSWORD
- base_client 自动注入 auth_headers

### [D] 自动识别
如果 Swagger/OpenAPI 中有 `securitySchemes` / `securityDefinitions`：
- 展示识别到的认证方式列表
- 让用户确认或修改
- 然后按对应模式（B 或 C）处理

---

## 生成认证相关 fixture

不管哪种模式，conftest.py 中统一暴露一个 `auth_headers` fixture：

```python
# 模式 A
@pytest.fixture
def auth_headers():
    return {}

# 模式 B
@pytest.fixture
def auth_headers(settings):
    return {"Authorization": f"Bearer {settings.API_KEY}"}

# 模式 C
@pytest.fixture(scope="session")
def auth_token(settings, base_url):
    # ... login logic
    return token

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```

base_client 始终调用 `auth_headers` fixture，无需关心具体模式。

## .env.example 追加

根据模式追加对应变量：
```
# 模式 B
API_KEY=your_api_key_here

# 模式 C
LOGIN_USERNAME=admin
LOGIN_PASSWORD=your_password_here
```
