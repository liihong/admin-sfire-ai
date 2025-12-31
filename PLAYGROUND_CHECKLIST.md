# 智能体调试中心（Playground）检查清单

## ✅ 已完成的检查项

### 1. 代码实现检查
- ✅ 所有组件文件已创建
- ✅ TypeScript类型定义完整
- ✅ 无编译错误

### 2. API接口检查
- ✅ SSE认证方式已修复：使用标准 `Authorization: Bearer token` header
- ✅ API地址：`${VITE_API_URL}/v1/ai/chat/stream`
- ✅ 保存配置接口：使用 `updateAgent` API
- ✅ 获取智能体详情：使用 `getAgentDetail` API

### 3. 功能完整性检查
- ✅ 保存配置时保留原始数据（description、sortOrder、status）
- ✅ 路由跳转：`/agent/playground/:id`
- ✅ 左右分屏布局可拖拽调整
- ✅ Markdown渲染（基础实现）

## ⚠️ 需要手动配置的项

### 1. 后端路由配置（重要）
需要在后端菜单管理系统中添加以下菜单项：
- **路径**：`/agent/playground/:id`
- **组件路径**：`/agent/playground/index`
- **菜单名称**：智能体调试中心（或隐藏菜单）
- **建议**：设置为隐藏菜单（isHide: true），因为这是通过ID动态访问的页面

### 2. 后端API接口验证
确保后端有以下接口：

#### 2.1 SSE流式对话接口
- **路径**：`POST /v1/ai/chat/stream`
- **认证**：Bearer Token（`Authorization: Bearer <token>`）
- **请求体**：
  ```json
  {
    "messages": [...],
    "model": "string",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stream": true
  }
  ```
- **响应**：Server-Sent Events (SSE) 流式数据

#### 2.2 智能体详情接口
- **路径**：`GET /v1/agents/:id`
- **已存在**：✅ 已验证

#### 2.3 更新智能体接口
- **路径**：`PUT /v1/agents/:id`
- **已存在**：✅ 已验证

#### 2.4 获取模型列表接口
- **路径**：`GET /v1/agents/models`
- **已存在**：✅ 已验证

### 3. 环境变量检查
确保 `.env` 文件中配置了：
```env
VITE_API_URL=/api
```

### 4. Markdown渲染优化（可选）
当前使用简单的字符串替换实现Markdown渲染。如需更强大的功能，可以：

1. 安装 `markdown-it`：
   ```bash
   npm install markdown-it
   npm install --save-dev @types/markdown-it
   ```

2. 在 `ChatPanel.vue` 中替换 `renderMarkdown` 函数

## 🔍 测试检查项

### 功能测试
- [ ] 点击智能体卡片的"调试"按钮，能正确跳转
- [ ] 左侧配置面板能正常显示和编辑
- [ ] 右侧聊天面板能正常发送消息
- [ ] SSE流式输出正常工作（打字机效果）
- [ ] 保存配置功能正常
- [ ] 左右分屏拖拽调整宽度正常

### 兼容性测试
- [ ] 不同浏览器（Chrome、Firefox、Safari、Edge）
- [ ] 不同屏幕尺寸（响应式布局）

## 📝 注意事项

1. **路由权限**：Playground页面需要通过菜单系统配置访问权限
2. **API认证**：SSE请求使用Bearer Token认证，确保后端支持
3. **错误处理**：所有API调用都有错误处理，但建议添加更详细的错误提示
4. **性能优化**：大量消息时可能需要虚拟滚动（当前未实现）

## 🐛 已知问题

无

## ✨ 后续优化建议

1. 添加消息历史记录（持久化）
2. 添加代码高亮（使用 highlight.js）
3. 添加导出对话功能
4. 添加参数预设模板
5. 优化Markdown渲染（使用 markdown-it 库）
6. 添加消息搜索功能

