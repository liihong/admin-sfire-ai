<template>
  <div class="mp-project">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <div class="title-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="title-text">
            <h1>我的项目</h1>
            <p>管理您的所有项目，轻松切换工作空间</p>
          </div>
        </div>
        <el-button type="primary" class="create-btn" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          <span>创建项目</span>
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
        <p>加载中...</p>
      </div>

      <div v-else-if="projects.length === 0" class="empty-container">
        <div class="empty-icon">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <h3>暂无项目</h3>
        <p>创建您的第一个项目，开始精彩旅程</p>
        <el-button type="primary" class="create-btn" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          <span>创建第一个项目</span>
        </el-button>
      </div>

      <div class="project-grid" v-else>
        <div
          v-for="(project, index) in projects"
          :key="project.id"
          class="project-card"
          :class="{ 'is-active': project.isActive }"
          :style="{ '--delay': index * 0.08 + 's', '--gradient': getAvatarGradient(index) }"
        >
          <!-- 卡片顶部渐变区域 -->
          <div class="card-header">
            <!-- 左上角装饰线 -->
            <div class="header-line"></div>
            <!-- 激活状态角标 -->
            <div v-if="project.isActive" class="active-corner">
              <el-icon><Check /></el-icon>
            </div>
            <!-- 项目首字母 -->
            <div class="project-initial">{{ project.name.charAt(0) }}</div>
            <!-- 项目名称 -->
            <h2 class="project-name">{{ project.name }}</h2>
          </div>

          <!-- 卡片内容区域 -->
          <div class="card-body">
            <!-- 项目信息标题 -->
            <h4 class="section-title">项目信息</h4>
            
            <!-- 项目详情 -->
            <div class="info-text">
              <p><strong>行业赛道</strong> {{ project.industry }}</p>
              <p><strong>语气风格</strong> {{ project.tone }}</p>
              <p v-if="project.ipPersona" class="persona-text"><strong>IP人设</strong> {{ project.ipPersona }}</p>
            </div>

            <!-- 主操作按钮 -->
            <button class="primary-action" @click="handleSwitch(project)">
              切换项目
            </button>

            <!-- 底部操作图标 -->
            <div class="action-icons">
              <button class="icon-btn edit" @click="handleEdit(project)" title="编辑">
                <el-icon><Edit /></el-icon>
              </button>
              <button class="icon-btn delete" @click="handleDelete(project)" title="删除">
                <el-icon><Delete /></el-icon>
              </button>
              <span class="update-time">
                <el-icon><Clock /></el-icon>
                {{ formatTime(project.updatedAt) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="行业赛道" prop="industry">
          <el-select v-model="formData.industry" placeholder="请选择行业赛道" style="width: 100%">
            <el-option
              v-for="item in industryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="语气风格" prop="tone">
          <el-select v-model="formData.tone" placeholder="请选择语气风格" style="width: 100%">
            <el-option
              v-for="item in toneOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="IP人设" prop="ipPersona">
          <el-input
            v-model="formData.ipPersona"
            type="textarea"
            :rows="3"
            placeholder="请输入IP人设描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="MPProject">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, ElForm } from "element-plus";
import {
  Plus,
  Loading,
  Briefcase,
  ChatDotRound,
  User,
  Folder,
  FolderOpened,
  Check,
  Clock,
  Switch,
  Edit,
  Delete
} from "@element-plus/icons-vue";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import {
  getMPProjectListApi,
  createMPProjectApi,
  updateMPProjectApi,
  deleteMPProjectApi,
  switchMPProjectApi,
  getMPProjectOptionsApi
} from "@/api/modules/miniprogram";
import type { MPProject, CreateMPProjectRequest, UpdateMPProjectRequest } from "@/api/modules/miniprogram";
import dayjs from "dayjs";

// 头像渐变色配置
const avatarGradients = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
  "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
];

// 获取头像渐变色
const getAvatarGradient = (index: number) => {
  return avatarGradients[index % avatarGradients.length];
};

const mpUserStore = useMPUserStore();

const loading = ref(false);
const projects = ref<MPProject[]>([]);

const dialogVisible = ref(false);
const dialogTitle = ref("创建项目");
const submitLoading = ref(false);
const formRef = ref<InstanceType<typeof ElForm>>();
const currentProject = ref<MPProject | null>(null);

const formData = reactive<CreateMPProjectRequest>({
  name: "",
  industry: "",
  tone: "",
  ipPersona: ""
});

const formRules = {
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
  industry: [{ required: true, message: "请选择行业赛道", trigger: "change" }],
  tone: [{ required: true, message: "请选择语气风格", trigger: "change" }]
};

const industryOptions = ref<Array<{ label: string; value: string }>>([]);
const toneOptions = ref<Array<{ label: string; value: string }>>([]);

// 获取项目列表
const fetchProjects = async () => {
  loading.value = true;
  try {
    const { data } = await getMPProjectListApi();
    if (data?.projects) {
      projects.value = data.projects;
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "获取项目列表失败");
  } finally {
    loading.value = false;
  }
};

// 获取项目选项
const fetchProjectOptions = async () => {
  try {
    const { data } = await getMPProjectOptionsApi();
    if (data) {
      industryOptions.value = data.industries || [];
      toneOptions.value = data.tones || [];
    }
  } catch (error: any) {
    console.error("获取项目选项失败:", error);
  }
};

// 创建项目
const handleCreate = () => {
  dialogTitle.value = "创建项目";
  currentProject.value = null;
  Object.assign(formData, {
    name: "",
    industry: "",
    tone: "",
    ipPersona: ""
  });
  dialogVisible.value = true;
};

// 编辑项目
const handleEdit = (project: MPProject) => {
  dialogTitle.value = "编辑项目";
  currentProject.value = project;
  Object.assign(formData, {
    name: project.name,
    industry: project.industry,
    tone: project.tone,
    ipPersona: project.ipPersona || ""
  });
  dialogVisible.value = true;
};

// 切换项目
const handleSwitch = async (project: MPProject) => {
  try {
    await ElMessageBox.confirm(`确定要切换到项目"${project.name}"吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "info"
    });

    const { data } = await switchMPProjectApi({ project_id: String(project.id) });
    if (data?.success) {
      ElMessage.success("切换成功");
      await fetchProjects();
    }
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "切换失败");
    }
  }
};

// 删除项目
const handleDelete = async (project: MPProject) => {
  try {
    await ElMessageBox.confirm(`确定要删除项目"${project.name}"吗？此操作不可恢复！`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });

    await deleteMPProjectApi(project.id);
    ElMessage.success("删除成功");
    await fetchProjects();
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "删除失败");
    }
  }
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async valid => {
    if (!valid) return;

    submitLoading.value = true;
    try {
      if (currentProject.value) {
        // 更新项目
        await updateMPProjectApi(currentProject.value.id, formData as UpdateMPProjectRequest);
        ElMessage.success("更新成功");
      } else {
        // 创建项目
        await createMPProjectApi(formData);
        ElMessage.success("创建成功");
      }
      dialogVisible.value = false;
      await fetchProjects();
    } catch (error: any) {
      ElMessage.error(error?.msg || "操作失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

// 关闭对话框
const handleDialogClose = () => {
  formRef.value?.resetFields();
  currentProject.value = null;
};

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format("YYYY-MM-DD HH:mm");
};

onMounted(async () => {
  await fetchProjectOptions();
  await fetchProjects();
});
</script>

<style scoped lang="scss">
.mp-project {
  min-height: 100vh;
  padding-bottom: 40px;

  // 页面头部 - 简化版
  .page-header {
    padding: 32px 40px;
    margin-bottom: 32px;

    .header-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 16px;

      .title-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: #fff;
      }

      .title-text {
        h1 {
          margin: 0 0 4px 0;
          font-size: 22px;
          font-weight: 700;
          color: #1f2937;
        }

        p {
          margin: 0;
          font-size: 13px;
          color: #6b7280;
        }
      }
    }

    .create-btn {
      height: 42px;
      padding: 0 24px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 8px;
      background: #3b82f6;
      border: none;
      transition: all 0.2s ease;

      &:hover {
        background: #2563eb;
      }

      .el-icon {
        margin-right: 6px;
      }
    }
  }

  // 主内容区
  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 40px;
  }

  // 加载状态
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 0;

    .loading-spinner {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;

      .el-icon {
        font-size: 28px;
        color: #fff;
      }
    }

    p {
      font-size: 14px;
      color: #6b7280;
      margin: 0;
    }
  }

  // 空状态
  .empty-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 0;

    .empty-icon {
      width: 100px;
      height: 100px;
      background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
      border-radius: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 20px;

      .el-icon {
        font-size: 44px;
        color: #9ca3af;
      }
    }

    h3 {
      margin: 0 0 8px 0;
      font-size: 18px;
      font-weight: 600;
      color: #374151;
    }

    p {
      margin: 0 0 24px 0;
      font-size: 14px;
      color: #9ca3af;
    }

    .create-btn {
      height: 42px;
      padding: 0 28px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 8px;
      background: #3b82f6;
      border: none;

      .el-icon {
        margin-right: 6px;
      }
    }
  }

  // 项目网格
  .project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
  }

  // 项目卡片 - 参考设计风格
  .project-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    animation: cardSlideIn 0.4s ease-out backwards;
    animation-delay: var(--delay);

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
    }

    // 激活状态边框
    &.is-active {
      box-shadow: 0 2px 12px rgba(59, 130, 246, 0.2), 0 0 0 2px #3b82f6;
    }

    // 卡片顶部渐变区域
    .card-header {
      background: var(--gradient);
      padding: 28px 24px 32px;
      position: relative;
      min-height: 180px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;

      // 左上角装饰线
      .header-line {
        position: absolute;
        top: 20px;
        left: 20px;
        width: 32px;
        height: 3px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 2px;
      }

      // 激活角标
      .active-corner {
        position: absolute;
        top: 16px;
        right: 16px;
        width: 28px;
        height: 28px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;

        .el-icon {
          font-size: 14px;
          color: #10b981;
        }
      }

      // 项目首字母
      .project-initial {
        font-size: 72px;
        font-weight: 300;
        color: rgba(0, 0, 0, 0.25);
        line-height: 1;
        position: absolute;
        right: 24px;
        bottom: 20px;
        font-family: "Georgia", serif;
      }

      // 项目名称
      .project-name {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        color: #1f2937;
        line-height: 1.3;
        position: relative;
        z-index: 1;
        max-width: 70%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    // 卡片内容区域
    .card-body {
      background: #fff;
      padding: 24px;

      // 标题
      .section-title {
        margin: 0 0 12px 0;
        font-size: 15px;
        font-weight: 700;
        color: #1f2937;
      }

      // 信息文本
      .info-text {
        margin: 0 0 20px 0;

        p {
          margin: 0 0 6px 0;
          font-size: 14px;
          color: #4b5563;
          line-height: 1.6;

          strong {
            color: #6b7280;
            font-weight: 500;
            margin-right: 8px;
          }

          &:last-child {
            margin-bottom: 0;
          }
        }

        .persona-text {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }

      // 主操作按钮
      .primary-action {
        display: inline-block;
        padding: 10px 24px;
        background: #3b82f6;
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 20px;

        &:hover {
          background: #2563eb;
        }
      }

      // 底部操作图标
      .action-icons {
        display: flex;
        align-items: center;
        gap: 8px;
        padding-top: 16px;
        border-top: 1px solid #f3f4f6;

        .icon-btn {
          width: 36px;
          height: 36px;
          border: none;
          background: #f9fafb;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          color: #6b7280;

          .el-icon {
            font-size: 16px;
          }

          &.edit:hover {
            background: #fef3c7;
            color: #d97706;
          }

          &.delete:hover {
            background: #fee2e2;
            color: #dc2626;
          }
        }

        .update-time {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #9ca3af;

          .el-icon {
            font-size: 12px;
          }
        }
      }
    }
  }
}

// 卡片入场动画
@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 响应式适配
@media (max-width: 768px) {
  .mp-project {
    .page-header {
      padding: 24px 20px;

      .header-content {
        flex-direction: column;
        gap: 16px;
        text-align: center;
      }

      .header-title {
        flex-direction: column;
        gap: 12px;
      }
    }

    .main-content {
      padding: 0 16px;
    }

    .project-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }

    .project-card {
      .card-header {
        min-height: 160px;
        padding: 24px 20px 28px;

        .project-initial {
          font-size: 56px;
        }

        .project-name {
          font-size: 20px;
        }
      }

      .card-body {
        padding: 20px;
      }
    }
  }
}
</style>


