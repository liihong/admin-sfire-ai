<template>
  <div class="mp-project">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的项目</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">创建项目</el-button>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="projects.length === 0" class="empty-container">
        <el-empty description="暂无项目">
          <el-button type="primary" @click="handleCreate">创建第一个项目</el-button>
        </el-empty>
      </div>

      <el-row :gutter="20" v-else>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="project in projects" :key="project.id">
          <el-card class="project-card" shadow="hover">
            <div class="project-header">
              <h4 class="project-name">{{ project.name }}</h4>
              <el-tag v-if="project.isActive" type="success" size="small">当前项目</el-tag>
            </div>
            <div class="project-info">
              <p class="project-item">
                <el-icon><Briefcase /></el-icon>
                <span>行业：{{ project.industry }}</span>
              </p>
              <p class="project-item">
                <el-icon><ChatDotRound /></el-icon>
                <span>风格：{{ project.tone }}</span>
              </p>
              <p v-if="project.ipPersona" class="project-item">
                <el-icon><User /></el-icon>
                <span>IP人设：{{ project.ipPersona }}</span>
              </p>
            </div>
            <div class="project-footer">
              <span class="project-time">{{ formatTime(project.updatedAt) }}</span>
              <div class="project-actions">
                <el-button type="primary" link size="small" @click="handleSwitch(project)">
                  切换
                </el-button>
                <el-button type="primary" link size="small" @click="handleEdit(project)">编辑</el-button>
                <el-button type="danger" link size="small" @click="handleDelete(project)">删除</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

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
import { Plus, Loading, Briefcase, ChatDotRound, User } from "@element-plus/icons-vue";
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
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .loading-container,
  .empty-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;
    color: var(--el-text-color-regular);
  }

  .project-card {
    margin-bottom: 20px;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
    }

    .project-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;

      .project-name {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .project-info {
      .project-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 8px 0;
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
    }

    .project-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid var(--el-border-color-lighter);

      .project-time {
        color: var(--el-text-color-secondary);
        font-size: 12px;
      }

      .project-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}
</style>


