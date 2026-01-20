<template>
  <div class="routing-debug">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-page-header @back="handleBack">
        <template #content>
          <div class="header-content">
            <el-icon :size="20" style="margin-right: 8px"><MagicStick /></el-icon>
            <span class="title">智能路由调试</span>
            <el-tag v-if="agentData" style="margin-left: 12px">{{ agentData.name }}</el-tag>
          </div>
        </template>
      </el-page-header>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：输入区域 -->
      <el-card class="input-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><EditPen /></el-icon>
            <span>模拟用户输入</span>
          </div>
        </template>

        <el-form :model="testForm" label-width="100px">
          <el-form-item label="用户输入">
            <el-input
              v-model="testForm.user_input"
              type="textarea"
              :rows="4"
              placeholder="输入模拟的用户问题，例如：帮我写一个餐饮招商的脚本"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-divider>路由参数配置</el-divider>

          <el-form-item label="使用向量检索">
            <el-switch v-model="testForm.use_vector" />
            <span class="form-tip">使用向量相似度匹配（关闭则使用关键词匹配）</span>
          </el-form-item>

          <el-form-item label="Top-K">
            <el-input-number v-model="testForm.top_k" :min="1" :max="10" :step="1" />
            <span class="form-tip">选择最相关的K个技能</span>
          </el-form-item>

          <el-form-item label="相似度阈值">
            <el-slider v-model="testForm.threshold" :min="0" :max="1" :step="0.05" show-input :show-input-controls="false" />
            <span class="form-tip">相似度阈值（0-1），值越高匹配越严格</span>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :icon="Cpu" :loading="testing" @click="handleRoutingTest" style="width: 100%">
              {{ testing ? "路由测试中..." : "开始路由测试" }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 右侧：结果展示 -->
      <el-card class="result-card" shadow="never" v-if="testResult">
        <template #header>
          <div class="card-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>路由结果</span>
            <el-tag v-if="testResult" :type="getRoutingMethodType(testResult.routing_method)" style="margin-left: 12px">
              {{ testResult.routing_method === "vector" ? "向量检索" : "关键词匹配" }}
            </el-tag>
          </div>
        </template>

        <!-- Token对比 -->
        <div class="token-comparison">
          <el-statistic title="全量Token" :value="testResult.token_comparison.full" />
          <el-statistic title="路由后Token" :value="testResult.token_comparison.routed" />
          <el-statistic
            title="节省比例"
            :value="testResult.token_comparison.saved_percent"
            suffix="%"
            :value-style="{ color: savedPercentColor }"
          />
        </div>

        <!-- 选中的技能 -->
        <el-divider content-position="left">
          <el-icon color="#67C23A"><CircleCheck /></el-icon>
          选中的技能（{{ testResult.selected_skills.length }}个）
        </el-divider>
        <el-table :data="testResult.selected_skills" max-height="200" stripe>
          <el-table-column prop="name" label="技能名称" width="180" />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }">
              <el-tag :type="getCategoryType(row.category)" size="small">{{ row.category }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="similarity" label="相似度" width="120">
            <template #default="{ row }">
              <el-tag :type="getSimilarityType(row.similarity)">{{ (row.similarity * 100).toFixed(1) }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="meta_description" label="特征描述" show-overflow-tooltip />
        </el-table>

        <!-- 未选中的技能 -->
        <el-divider content-position="left">
          <el-icon color="#F56C6C"><CircleClose /></el-icon>
          未选中的技能（{{ testResult.rejected_skills.length }}个）
        </el-divider>
        <el-table :data="testResult.rejected_skills" max-height="200" stripe v-if="testResult.rejected_skills.length > 0">
          <el-table-column prop="name" label="技能名称" width="180" />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }">
              <el-tag :type="getCategoryType(row.category)" size="small">{{ row.category }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="similarity" label="相似度" width="120">
            <template #default="{ row }">
              <el-tag type="info">{{ (row.similarity * 100).toFixed(1) }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="meta_description" label="特征描述" show-overflow-tooltip />
        </el-table>
        <el-empty v-else description="所有技能均被选中" :image-size="80" />

        <!-- 最终Prompt -->
        <el-divider content-position="left">
          <el-icon><Document /></el-icon>
          最终组装的Prompt
        </el-divider>
        <div class="prompt-preview">
          <el-input :model-value="testResult.final_prompt" type="textarea" :rows="8" readonly placeholder="暂无Prompt" />
          <div class="prompt-actions">
            <el-button :icon="DocumentCopy" @click="handleCopyPrompt">复制Prompt</el-button>
            <el-button :icon="Download" @click="handleExportPrompt">导出</el-button>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-card v-else class="result-card" shadow="never">
        <el-empty description='请输入用户输入并点击"开始路由测试"'>
          <template #image>
            <el-icon :size="100" color="#909399">
              <MagicStick />
            </el-icon>
          </template>
        </el-empty>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts" name="AgentRoutingDebug">
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  MagicStick,
  EditPen,
  Cpu,
  DataAnalysis,
  CircleCheck,
  CircleClose,
  Document,
  DocumentCopy,
  Download
} from "@element-plus/icons-vue";
import { getAgentDetailV2, previewRouting } from "@/api/modules/skillAssembly";
import type { AgentV2 } from "@/api/interface";

const route = useRoute();
const router = useRouter();

// Agent数据
const agentData = ref<AgentV2.ResAgentItem | null>(null);

// 测试表单
const testForm = reactive({
  user_input: "",
  use_vector: true,
  top_k: 3,
  threshold: 0.7
});

// 测试结果
const testResult = ref<AgentV2.ResRoutingPreview | null>(null);
const testing = ref(false);

// 节省比例颜色
const savedPercentColor = computed(() => {
  if (!testResult.value) return "";
  const percent = testResult.value.token_comparison.saved_percent;
  if (percent >= 50) return "#67C23A"; // 绿色
  if (percent >= 30) return "#E6A23C"; // 橙色
  return "#F56C6C"; // 红色
});

// 加载Agent详情
const loadAgentDetail = async () => {
  const id = Number(route.params.id);
  try {
    const response = await getAgentDetailV2(id);
    agentData.value = response.data;

    // 如果Agent启用了智能路由，预填充路由描述
    if (agentData.value.is_routing_enabled === 1 && agentData.value.routing_description) {
      testForm.user_input = `示例：${agentData.value.routing_description}`;
    }
  } catch (error) {
    console.error("加载Agent详情失败:", error);
    ElMessage.error("加载Agent详情失败");
  }
};

// 执行路由测试
const handleRoutingTest = async () => {
  if (!testForm.user_input.trim()) {
    ElMessage.warning("请输入用户输入");
    return;
  }

  testing.value = true;
  try {
    const id = Number(route.params.id);
    const response = await previewRouting(id, testForm);
    testResult.value = response.data;
    ElMessage.success("路由测试完成");
  } catch (error: any) {
    console.error("路由测试失败:", error);
    const errorMsg = error?.msg || error?.message || "路由测试失败";
    ElMessage.error(errorMsg);
  } finally {
    testing.value = false;
  }
};

// 复制Prompt
const handleCopyPrompt = () => {
  if (!testResult.value) return;
  navigator.clipboard
    .writeText(testResult.value.final_prompt)
    .then(() => {
      ElMessage.success("已复制到剪贴板");
    })
    .catch(() => {
      ElMessage.error("复制失败");
    });
};

// 导出Prompt
const handleExportPrompt = () => {
  if (!testResult.value) return;

  const blob = new Blob([testResult.value.final_prompt], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `prompt_${agentData.value?.name || "agent"}_${Date.now()}.txt`;
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("导出成功");
};

// 返回上一页
const handleBack = () => {
  router.back();
};

// 获取相似度标签类型
const getSimilarityType = (similarity: number) => {
  if (similarity >= 0.8) return "success";
  if (similarity >= 0.6) return "info";
  if (similarity >= 0.4) return "warning";
  return "info";
};

// 获取分类标签类型
const getCategoryType = (category: string) => {
  const typeMap: Record<string, any> = {
    model: "primary",
    hook: "success",
    rule: "warning",
    audit: "danger"
  };
  return typeMap[category] || "";
};

// 获取路由方法标签类型
const getRoutingMethodType = (method: "vector" | "keywords") => {
  return method === "vector" ? "success" : "info";
};

// 初始化
onMounted(() => {
  loadAgentDetail();
});
</script>

<style scoped lang="scss">
.routing-debug {
  padding: 20px;
  min-height: calc(100vh - 100px);

  .page-header {
    margin-bottom: 20px;

    .header-content {
      display: flex;
      align-items: center;
      font-size: 18px;
      font-weight: 600;

      .title {
        flex: 1;
      }
    }
  }

  .main-content {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 20px;
    align-items: start;

    .input-card,
    .result-card {
      .card-header {
        display: flex;
        align-items: center;
        font-weight: 600;

        .el-icon {
          margin-right: 8px;
        }
      }
    }

    .input-card {
      position: sticky;
      top: 20px;

      .form-tip {
        margin-left: 12px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      .el-divider {
        margin: 24px 0 20px 0;
      }
    }

    .result-card {
      min-height: 600px;

      .token-comparison {
        display: flex;
        justify-content: space-around;
        padding: 20px 0;
        background: var(--el-fill-color-light);
        border-radius: 8px;
        margin-bottom: 20px;
      }

      .el-divider {
        margin: 24px 0;
        font-weight: 600;
      }

      .prompt-preview {
        .prompt-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 12px;
        }
      }
    }
  }
}

// 响应式布局
@media (max-width: 1200px) {
  .routing-debug {
    .main-content {
      grid-template-columns: 1fr;

      .input-card {
        position: static;
      }
    }
  }
}
</style>
