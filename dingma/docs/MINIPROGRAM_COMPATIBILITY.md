# 微信小程序 API 兼容性说明

本文档记录微信小程序环境中不兼容的 Web API 及替代方案。

## 不兼容的 Web API

### 1. URLSearchParams

**问题**：`new URLSearchParams()` 在微信小程序中会报 `ReferenceError: URLSearchParams is not defined`。

**替代方案**：手动拼接查询字符串

```typescript
// ❌ 不推荐
const params = new URLSearchParams()
params.append('type', 'category')
const query = params.toString()

// ✅ 推荐
const params: string[] = []
if (type) params.push(`type=${encodeURIComponent(type)}`)
const query = params.join('&')
```

**已修复文件**：`src/api/quickEntry.ts`、`src/api/conversation.ts`（使用 data 对象，由 request 工具转换）

### 2. atob / btoa

**问题**：Base64 编解码 API 在小程序中可能不可用。

**替代方案**：`src/stores/auth.ts` 中已使用 `#ifdef H5` 条件编译，小程序走手动 Base64 解码逻辑。

### 3. structuredClone

**问题**：较新的 API，部分小程序基础库可能不支持。

**替代方案**：`src/utils/common.ts` 中已做兼容：

```typescript
if (typeof structuredClone !== 'undefined') {
  return structuredClone(obj)
}
// 降级到 JSON 或递归深拷贝
```

## 推荐做法

1. **查询参数**：使用 `encodeURIComponent` + 数组 `join('&')`，避免 `URLSearchParams`
2. **GET 请求**：可传 `data` 对象给 `request`，工具会自动转为 query string
3. **新 API 使用前**：用 `typeof xxx !== 'undefined'` 做存在性检查
4. **条件编译**：H5 与小程序逻辑差异大时，使用 `#ifdef H5` / `#ifdef MP-WEIXIN`

## 参考

- [微信小程序 JavaScript 支持情况](https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/env.html)
- [uni-app 条件编译](https://uniapp.dcloud.net.cn/tutorial/platform.html)
