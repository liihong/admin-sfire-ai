<template>
  <div class="agent-manage">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="智能体名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入智能体名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="全部" :value="null as any" />
            <el-option label="上架" :value="1" />
            <el-option label="下架" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增智能体</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 智能体列表 -->
    <div class="agent-list">
      <el-card v-for="agent in agentList" :key="agent.id" class="agent-card" shadow="hover" :body-style="{ padding: '20px' }">
        <div class="card-header">
          <div class="agent-info">
            <div class="agent-icon" :style="{ background: isImageUrl(agent.icon) ? 'none' : getIconGradient(agent.icon) }">
              <!-- 如果是图片URL，显示图片；否则显示图标组件 -->
              <img v-if="isImageUrl(agent.icon)" :src="agent.icon" class="icon-img" alt="agent icon" />
              <el-icon v-else :size="32">
                <component :is="getIconComponent(agent.icon)" />
              </el-icon>
            </div>
            <div class="agent-details">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-desc">{{ agent.description || "暂无描述" }}</div>
              <div class="agent-meta">
                <el-tag size="small" :type="agent.status === 1 ? 'success' : 'info'">
                  {{ agent.status === 1 ? "上架" : "下架" }}
                </el-tag>
                <span class="meta-item">模型: {{ agent.model }}</span>
                <span class="meta-item">使用次数: {{ agent.usageCount }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <el-switch
              v-model="agent.status"
              :active-value="1"
              :inactive-value="0"
              :loading="statusLoading === agent.id"
              @change="handleStatusChange(agent)"
            />
          </div>
        </div>

        <div class="card-footer">
          <div class="sort-control">
            <span class="sort-label">排序:</span>
            <el-input-number
              v-model="agent.sortOrder"
              :min="0"
              :max="9999"
              :step="1"
              size="small"
              style="width: 100px"
              @change="handleSortChange(agent)"
            />
          </div>
          <div class="action-buttons">
            <!-- 路由测试按钮：仅在技能组装模式且启用智能路由时显示 -->
            <el-button v-if="agent.agentMode === 1" type="success" link :icon="MagicStick" @click="handleRoutingDebug(agent)">
              路由测试
            </el-button>
            <el-button type="warning" link :icon="Cpu" class="debug-button" @click="handleDebug(agent)">调试</el-button>
            <el-button type="primary" link :icon="EditPen" @click="handleEdit(agent)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(agent)">删除</el-button>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && agentList.length === 0" description="暂无智能体数据" />
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.pageNum"
        v-model:page-size="pagination.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 编辑对话框（全屏） -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" fullscreen :close-on-click-modal="false" destroy-on-close>
      <AgentForm
        v-if="dialogVisible"
        ref="formRef"
        :form-data="currentAgent"
        :is-edit="isEdit"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="agentManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Refresh,
  Plus,
  EditPen,
  Delete,
  ChatDotRound,
  ChatLineRound,
  ChatLineSquare,
  Cpu,
  Document,
  DocumentCopy,
  Files,
  Notebook,
  Reading,
  Tools,
  Setting,
  Operation,
  Management,
  Monitor,
  User,
  UserFilled,
  Avatar,
  Star,
  Brush,
  Picture,
  Film,
  ShoppingCart,
  Box,
  Present,
  Trophy,
  Coin,
  DataBoard,
  PieChart,
  Histogram,
  TrendCharts,
  Odometer,
  Cloudy,
  Upload,
  Download,
  Folder,
  FolderOpened,
  Lock,
  Unlock,
  Key,
  Message,
  Phone,
  Cellphone,
  VideoCamera,
  Notification,
  Bell,
  House,
  Filter,
  Clock,
  Timer,
  Calendar,
  Flag,
  CollectionTag,
  Sunny,
  Moon,
  InfoFilled,
  WarningFilled,
  SuccessFilled,
  MagicStick,
  Connection,
  DataAnalysis,
  Platform
} from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { Agent } from "@/api/interface";
import { getAgentList, deleteAgent, changeAgentStatus, updateAgentSort } from "@/api/modules/agent";
import AgentForm from "./components/AgentForm.vue";

const router = useRouter();

// 搜索表单
const searchForm = reactive({
  name: "",
  status: undefined as 0 | 1 | undefined
});

// 智能体列表
const agentList = ref<Agent.ResAgentItem[]>([]);
const loading = ref(false);
const total = ref(0);

// 分页
const pagination = reactive({
  pageNum: 1,
  pageSize: 10
});

// 状态切换loading
const statusLoading = ref<string>("");

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref("新增智能体");
const isEdit = ref(false);
const currentAgent = ref<Partial<Agent.ResAgentItem>>({});
const formRef = ref<InstanceType<typeof AgentForm> | null>(null);

/**
 * 判断是否为图片URL
 * 支持 http/https 链接和相对路径
 */
const isImageUrl = (icon: string): boolean => {
  if (!icon) return false;
  // 检查是否为 URL（http/https/相对路径）或图片格式
  return (
    icon.startsWith("http://") ||
    icon.startsWith("https://") ||
    icon.startsWith("/") ||
    icon.startsWith("data:image/") ||
    /\.(png|jpg|jpeg|gif|svg|webp|ico)$/i.test(icon)
  );
};

/**
 * 获取图标组件
 * 根据图标标识返回对应的 Element Plus 图标组件
 */
const getIconComponent = (iconName: string) => {
  // 如果没有图标名称，使用默认图标
  if (!iconName) {
    return ChatDotRound;
  }

  // Element Plus 图标映射表 - 支持更多图标
  const iconMap: Record<string, any> = {
    // AI/智能类
    ChatDotRound,
    ChatLineRound,
    ChatLineSquare,
    MagicStick,
    Cpu,
    Connection,
    DataAnalysis,
    Platform,
    // 文档类
    Document,
    DocumentCopy,
    Files,
    Notebook,
    Reading,
    // 工具类
    Tools,
    Setting,
    Operation,
    Management,
    Monitor,
    // 用户类
    User,
    UserFilled,
    Avatar,
    // 创意类
    Star,
    EditPen,
    Brush,
    Picture,
    Film,
    // 业务类
    ShoppingCart,
    Box,
    Present,
    Trophy,
    Coin,
    // 数据类
    DataBoard,
    PieChart,
    Histogram,
    TrendCharts,
    Odometer,
    // 云服务类
    Cloudy,
    Upload,
    Download,
    Folder,
    FolderOpened,
    // 安全类
    Lock,
    Unlock,
    Key,
    // 通信类
    Message,
    Phone,
    Cellphone,
    VideoCamera,
    Notification,
    Bell,
    // 常用类
    House,
    Search,
    Filter,
    Clock,
    Timer,
    Calendar,
    Flag,
    CollectionTag,
    Sunny,
    Moon,
    Link: ChatDotRound,
    Avatar,
    InfoFilled,
    WarningFilled,
    SuccessFilled,
    // 自定义标识映射（兼容旧数据）
    viral_copy_default: Document, // 文案类
    script_default: ChatDotRound, // 脚本类
    marketing_default: ChatDotRound, // 营销类
    chat: ChatDotRound, // 聊天类
    document: Document, // 文档类
    cpu: Cpu, // 计算类
  };

  // 如果在映射表中找到，返回对应图标
  if (iconMap[iconName]) {
    return iconMap[iconName];
  }

  // 默认返回 ChatDotRound
  return ChatDotRound;
};

/**
 * 获取图标渐变背景色
 * 根据图标名称返回对应的渐变色
 */
const getIconGradient = (iconName: string): string => {
  if (!iconName) return "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";

  const gradientMap: Record<string, string> = {
    // AI/智能类 - 紫色、蓝色系
    ChatDotRound: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    ChatLineRound: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    ChatLineSquare: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    MagicStick: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Cpu: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Connection: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    DataAnalysis: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Platform: "linear-gradient(135deg, #434343 0%, #000000 100%)",

    // 文档类 - 蓝色系
    Document: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    DocumentCopy: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Files: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Notebook: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Reading: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",

    // 工具类 - 橙色、深色系
    Tools: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Setting: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Operation: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Management: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Monitor: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",

    // 创意类 - 金色、彩色系
    Star: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    EditPen: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Brush: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Picture: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Film: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",

    // 业务类 - 橙色、金色系
    ShoppingCart: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Box: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Present: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Trophy: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    Coin: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",

    // 数据类 - 彩色系
    DataBoard: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    PieChart: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Histogram: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    TrendCharts: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Odometer: "linear-gradient(135deg, #434343 0%, #000000 100%)",

    // 云服务类 - 蓝绿色系
    Cloudy: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Upload: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Download: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Folder: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    FolderOpened: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",

    // 安全类 - 深色、金色系
    Lock: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Unlock: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Key: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    User: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    UserFilled: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Avatar: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",

    // 通信类 - 彩色系
    Message: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Phone: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Cellphone: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    VideoCamera: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Notification: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Bell: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",

    // 常用类 - 各种颜色
    House: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Search: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Filter: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Clock: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Timer: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Calendar: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Flag: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    CollectionTag: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Sunny: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    Moon: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    InfoFilled: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    WarningFilled: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    SuccessFilled: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  };

  return gradientMap[iconName] || "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";
};

// 获取智能体列表
const fetchAgentList = async () => {
  loading.value = true;
  try {
    const params: any = {
      ...searchForm,
      pageNum: pagination.pageNum,
      pageSize: pagination.pageSize
    };
    const response = await getAgentList(params);
    if (response && response.data) {
      agentList.value = response.data.list || [];
      total.value = response.data.total || 0;
    }
  } catch (error) {
    console.error("获取智能体列表失败:", error);
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.pageNum = 1;
  fetchAgentList();
};

// 重置
const handleReset = () => {
  searchForm.name = "";
  searchForm.status = undefined;
  handleSearch();
};

// 新增
const handleAdd = () => {
  dialogTitle.value = "新增智能体";
  isEdit.value = false;
  currentAgent.value = {};
  dialogVisible.value = true;
};

// 编辑
const handleEdit = (agent: Agent.ResAgentItem) => {
  dialogTitle.value = "编辑智能体";
  isEdit.value = true;
  currentAgent.value = { ...agent };
  dialogVisible.value = true;
};

// 调试
const handleDebug = (agent: Agent.ResAgentItem) => {
  router.push(`/agent/playground/${agent.id}`);
};

// 路由测试（仅技能组装模式显示）
const handleRoutingDebug = (agent: any) => {
  router.push(`/agent/routing-debug/${agent.id}`);
};

// 删除
const handleDelete = async (agent: Agent.ResAgentItem) => {
  try {
    await ElMessageBox.confirm(`确定要删除智能体【${agent.name}】吗？`, "提示", {
      type: "warning"
    });
    await deleteAgent(agent.id);
    ElMessage.success("删除成功");
    fetchAgentList();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
    }
  }
};

// 状态切换
const handleStatusChange = async (agent: Agent.ResAgentItem) => {
  const newStatus = agent.status === 1 ? 1 : 0;
  const action = newStatus === 1 ? "上架" : "下架";

  try {
    statusLoading.value = agent.id;
    await changeAgentStatus(agent.id, newStatus);
    ElMessage.success(`${action}成功`);
  } catch (error) {
    // 恢复原状态
    agent.status = agent.status === 1 ? 0 : 1;
    console.error("状态切换失败:", error);
  } finally {
    statusLoading.value = "";
  }
};

// 排序变更
const handleSortChange = async (agent: Agent.ResAgentItem) => {
  try {
    await updateAgentSort(agent.id, agent.sortOrder);
    ElMessage.success("排序更新成功");
    // 重新获取列表以保持排序
    fetchAgentList();
  } catch (error) {
    console.error("排序更新失败:", error);
  }
};

// 提交表单
const handleSubmit = () => {
  dialogVisible.value = false;
  fetchAgentList();
};

// 分页大小变更
const handleSizeChange = (size: number) => {
  pagination.pageSize = size;
  pagination.pageNum = 1;
  fetchAgentList();
};

// 页码变更
const handlePageChange = (page: number) => {
  pagination.pageNum = page;
  fetchAgentList();
};

// 初始化
onMounted(() => {
  fetchAgentList();
});
</script>

<style scoped lang="scss">
.agent-manage {
  padding: 20px;

  .search-card {
    margin-bottom: 20px;

    .search-form {
      margin-bottom: 0;
    }
  }

  .agent-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 20px;

    .agent-card {
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;

        .agent-info {
          display: flex;
          gap: 16px;
          flex: 1;

          .agent-icon {
            flex-shrink: 0;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;

            .icon-img {
              width: 100%;
              height: 100%;
              object-fit: cover;
              border-radius: 12px;
            }
          }

          .agent-details {
            flex: 1;
            min-width: 0;

            .agent-name {
              font-size: 18px;
              font-weight: 600;
              color: var(--el-text-color-primary);
              margin-bottom: 8px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }

            .agent-desc {
              font-size: 14px;
              color: var(--el-text-color-regular);
              margin-bottom: 12px;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              line-clamp: 2;
              -webkit-box-orient: vertical;
            }

            .agent-meta {
              display: flex;
              align-items: center;
              gap: 12px;
              flex-wrap: wrap;

              .meta-item {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
            }
          }
        }

        .card-actions {
          flex-shrink: 0;
        }
      }

      .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color-lighter);

        .sort-control {
          display: flex;
          align-items: center;
          gap: 8px;

          .sort-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
          }
        }

        .action-buttons {
          display: flex;
          gap: 8px;

          .debug-button {
            position: relative;
            animation: pulse 2s infinite;

            &::before {
              content: "";
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 100%;
              height: 100%;
              border-radius: 4px;
              background-color: var(--el-color-warning);
              opacity: 0.3;
              animation: breathe 2s infinite;
            }
          }
        }
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

@keyframes breathe {
  0%,
  100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.5;
  }
}
</style>
