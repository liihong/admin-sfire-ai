<template>
  <div class="conversation-history">
    <div class="history-header">
      <h3 class="title">会话历史</h3>
      <el-button
        type="primary"
        size="small"
        @click="handleCreateNew"
        :icon="Plus"
      >
        新建会话
      </el-button>
    </div>

    <!-- 搜索框 -->
    <div class="search-box">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索会话..."
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
      />
    </div>

    <!-- 会话列表 -->
    <div class="conversation-list" v-loading="loading">
      <div
        v-for="conversation in filteredConversations"
        :key="conversation.id"
        class="conversation-item"
        :class="{ active: conversation.id === currentConversationId }"
        @click="handleSelectConversation(conversation)"
      >
        <div class="conversation-content">
          <div class="conversation-title">{{ conversation.title }}</div>
          <div class="conversation-meta">
            <span class="message-count">{{ conversation.message_count }}条消息</span>
            <span class="time">{{ formatTime(conversation.updated_at || conversation.created_at) }}</span>
          </div>
        </div>
        <div class="conversation-actions">
          <el-dropdown @command="handleCommand" trigger="click">
            <el-button
              type="text"
              :icon="MoreFilled"
              @click.stop
            />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="{ action: 'rename', id: conversation.id }">
                  重命名
                </el-dropdown-item>
                <el-dropdown-item
                  :command="{ action: 'archive', id: conversation.id }"
                  :divided="false"
                >
                  {{ conversation.status === 'archived' ? '取消归档' : '归档' }}
                </el-dropdown-item>
                <el-dropdown-item
                  :command="{ action: 'delete', id: conversation.id }"
                  divided
                >
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!loading && filteredConversations.length === 0"
        description="暂无会话"
        :image-size="80"
      />
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="prev, pager, next, sizes"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        small
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, MoreFilled } from "@element-plus/icons-vue";
import {
  getMPConversationListApi,
  deleteMPConversationApi,
  archiveMPConversationApi,
  updateMPConversationTitleApi,
  type MPConversation,
} from "@/api/modules/miniprogram";
import { useIPCreationStore } from "@/stores/modules/ipCreation";

const emit = defineEmits<{
  select: [conversation: MPConversation];
  create: [];
}>();

const ipCreationStore = useIPCreationStore();

// 状态
const loading = ref(false);
const conversations = ref<MPConversation[]>([]);
const searchKeyword = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 当前选中的会话ID
const currentConversationId = computed(() => ipCreationStore.currentConversationId);

// 当前激活的项目（用于过滤会话）
const activeProject = computed(() => ipCreationStore.activeProject);

// 过滤后的会话列表
const filteredConversations = computed(() => {
  if (!searchKeyword.value) {
    return conversations.value;
  }
  const keyword = searchKeyword.value.toLowerCase();
  return conversations.value.filter(
    (conv) => conv.title.toLowerCase().includes(keyword)
  );
});

// 加载会话列表（根据当前项目过滤）
const loadConversations = async () => {
  // #region agent log
  fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ConversationHistory.vue:loadConversations:entry',message:'loadConversations called',data:{activeProjectId:activeProject.value?.id,stack:new Error().stack?.split('\n').slice(1,4).join(' <- ')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1-H4'})}).catch(()=>{});
  // #endregion
  loading.value = true;
  try {
    // 构建查询参数，根据当前项目过滤
    const params: any = {
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      status: "active", // 只显示活跃会话
    };
    
    // 如果有激活的项目，则按项目过滤
    if (activeProject.value?.id) {
      params.project_id = Number(activeProject.value.id);
    }
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ConversationHistory.vue:loadConversations:beforeApi',message:'calling API',data:{params},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1-H4'})}).catch(()=>{});
    // #endregion
    const response = await getMPConversationListApi(params);

    // API 返回的结构处理
    const code = String(response.code);
    if (code === "200" && response.data) {
      conversations.value = response.data.list || [];
      total.value = response.data.total || 0;
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载会话列表失败");
  } finally {
    loading.value = false;
  }
};

// 选择会话
const handleSelectConversation = (conversation: MPConversation) => {
  ipCreationStore.setCurrentConversationId(conversation.id);
  emit("select", conversation);
};

// 创建新会话
// 注意：点击新建时不立即创建会话，只是打开对话框显示欢迎语
// 会话会在用户发送第一条消息时由后端自动创建
const handleCreateNew = () => {
  // 清空当前会话ID，表示这是一个新对话（尚未创建）
  ipCreationStore.setCurrentConversationId(null);
  // 触发 create 事件，让父组件处理欢迎语显示等逻辑
  emit("create");
};

// 处理下拉菜单命令
const handleCommand = async (command: { action: string; id: number }) => {
  const { action, id } = command;

  switch (action) {
    case "rename":
      await handleRename(id);
      break;
    case "archive":
      await handleArchive(id);
      break;
    case "delete":
      await handleDelete(id);
      break;
  }
};

// 重命名
const handleRename = async (conversationId: number) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt(
      "请输入新标题",
      "重命名会话",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputPattern: /^.{1,50}$/,
        inputErrorMessage: "标题长度应在1-50个字符之间",
      }
    );

    if (newTitle) {
      const response = await updateMPConversationTitleApi(conversationId, newTitle);
      // API 返回的结构处理
      const code = String(response.code);
      if (code === "200") {
        await loadConversations();
        ElMessage.success("重命名成功");
      }
    }
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "重命名失败");
    }
  }
};

// 归档/取消归档
const handleArchive = async (conversationId: number) => {
  try {
    const response = await archiveMPConversationApi(conversationId);
    // API 返回的结构处理
    const code = String(response.code);
    if (code === "200") {
      await loadConversations();
      ElMessage.success("操作成功");
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "操作失败");
  }
};

// 删除
const handleDelete = async (conversationId: number) => {
  try {
    await ElMessageBox.confirm("确定要删除这个会话吗？", "删除会话", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    const response = await deleteMPConversationApi(conversationId);
    // API 返回的结构处理
    const code = String(response.code);
    if (code === "200") {
      // 如果删除的是当前会话，清空当前会话ID
      if (conversationId === (currentConversationId.value as number | null)) {
        ipCreationStore.setCurrentConversationId(null);
      }
      await loadConversations();
      ElMessage.success("删除成功");
    }
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "删除失败");
    }
  }
};

// 搜索
const handleSearch = () => {
  // 搜索在computed中处理
};

// 分页
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadConversations();
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadConversations();
};

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return "";
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } else if (days === 1) {
    return "昨天";
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  }
};

// 监听当前会话ID变化，自动加载详情（如果需要）
watch(
  () => currentConversationId.value,
  (newId) => {
    // 可以在这里加载会话详情
  }
);

// 监听项目变化，重新加载会话列表
watch(
  () => activeProject.value?.id,
  (newProjectId, oldProjectId) => {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ConversationHistory.vue:watch',message:'watch triggered',data:{newProjectId,oldProjectId,willLoad:String(newProjectId)!==String(oldProjectId)},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'H2-fix'})}).catch(()=>{});
    // #endregion
    // 使用 String() 统一类型比较，避免 number/string 类型差异导致误判
    if (String(newProjectId) !== String(oldProjectId)) {
      // 项目变化时，重置分页并重新加载
      currentPage.value = 1;
      loadConversations();
    }
  }
);

onMounted(() => {
  // #region agent log
  fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ConversationHistory.vue:onMounted',message:'onMounted triggered',data:{activeProjectId:activeProject.value?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1-H3'})}).catch(()=>{});
  // #endregion
  loadConversations();
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.conversation-history {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--ip-os-bg-primary);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--ip-os-border-primary);

  .title {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    color: var(--ip-os-text-primary);
  }
}

.search-box {
  padding: 12px 16px;
  border-bottom: 1px solid var(--ip-os-border-primary);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  @extend .ip-os-scrollbar;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--ip-os-border-secondary);

  &:hover {
    background: var(--ip-os-bg-secondary);
  }

  &.active {
    background: var(--ip-os-bg-tertiary);
    border-left: 3px solid var(--ip-os-accent-primary);
  }

  .conversation-content {
    flex: 1;
    min-width: 0;

    .conversation-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--ip-os-text-primary);
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .conversation-meta {
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: var(--ip-os-text-secondary);

      .message-count {
      }

      .time {
      }
    }
  }

  .conversation-actions {
    opacity: 0;
    transition: opacity 0.2s;
  }

  &:hover .conversation-actions {
    opacity: 1;
  }
}

.pagination {
  padding: 12px 16px;
  border-top: 1px solid var(--ip-os-border-primary);
  display: flex;
  justify-content: center;
}
</style>

