# OpenAPI 规范字段映射参考

## Swagger 2.0 ↔ OpenAPI 3.x 差异

### 整体结构
| 字段 | Swagger 2.0 | OpenAPI 3.x |
|------|-------------|-------------|
| 版本声明 | `swagger: "2.0"` | `openapi: "3.x.x"` |
| 服务器地址 | `host` + `basePath` + `schemes` | `servers[].url` |
| 路径定义 | `paths` | `paths` |
| 参数定义 | `parameters`（全局+路径级） | `components.parameters` |
| 响应定义 | `responses` | `components.responses` |
| Schema 定义 | `definitions` | `components.schemas` |
| 认证定义 | `securityDefinitions` | `components.securitySchemes` |

### 字段提取对照

#### base_url
```
# Swagger 2.0
schemes[0] + "://" + host + basePath

# OpenAPI 3.x
servers[0].url  (可能是相对路径或包含变量如 {baseUrl})
```

#### 参数
```
# Swagger 2.0
parameters:
  - name: userId
    in: path        # path | query | header | body | formData
    required: true
    type: string    # string | number | integer | boolean | array | file
    description: 用户ID

# OpenAPI 3.x
parameters:
  - name: userId
    in: path
    required: true
    schema:
      type: string
    description: 用户ID
```
差异：Swagger 2.0 的 `type` 直接在 param 上；OpenAPI 3.x 的 `type` 在 `schema.type` 里。

#### Request Body
```
# Swagger 2.0 (body parameter)
parameters:
  - in: body
    name: body
    schema:
      $ref: "#/definitions/User"

# OpenAPI 3.x
requestBody:
  required: true
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/User"
```
差异：Swagger 2.0 用 `in: body` 的 parameter；OpenAPI 3.x 有独立的 `requestBody`。

#### 响应
```
# Swagger 2.0
responses:
  "200":
    description: 成功
    schema:
      $ref: "#/definitions/User"

# OpenAPI 3.x
responses:
  "200":
    description: 成功
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/User"
```
差异：Swagger 2.0 直接 `schema`；OpenAPI 3.x 是 `content.{mediaType}.schema`。

### $ref 展开规则

```
Swagger 2.0:  #/definitions/X  → spec.definitions.X
OpenAPI 3.x:  #/components/schemas/X → spec.components.schemas.X

常见 $ref 路径：
- #/definitions/User
- #/components/schemas/User
- #/components/parameters/userId
- #/components/responses/NotFound
- #/components/requestBodies/UserBody
```

### 安全/认证定义映射

```
# Swagger 2.0 — securityDefinitions
securityDefinitions:
  ApiKeyAuth:
    type: apiKey          → apiKey
    in: header            → 放在 Header
    name: X-API-Key       → Header 名称
  BearerAuth:
    type: apiKey
    in: header
    name: Authorization   → Bearer token

# OpenAPI 3.x — components/securitySchemes
securitySchemes:
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
  BearerAuth:
    type: http
    scheme: bearer        → Bearer token
  OAuth2:
    type: oauth2
    flows: {...}
```

### 忽略字段
解析时安全忽略以下字段（不参与生成）：
- `deprecated: true` 的接口
- `x-*` 扩展字段（除非明显有用）
- `externalDocs`
- `example` / `examples`（Swagger 的示例值，可选地用作测试数据）
