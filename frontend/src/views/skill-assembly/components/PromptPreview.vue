<template>
  <div class="prompt-preview">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">Prompt预览</span>
          <div class="stats">
            <el-tag type="info" size="small">Token: {{ tokenCount }}</el-tag>
            <el-tag type="success" size="small" style="margin-left: 8px">
              技能: {{ skillsUsed?.length || 0 }} 个
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 使用的技能列表 -->
      <div v-if="skillsUsed && skillsUsed.length > 0" class="skills-used">
        <div class="section-title">使用的技能（按顺序）</div>
        <div class="skills-list">
          <div
            v-for="(skill, index) in skillsUsed"
            :key="skill.id"
            class="skill-badge"
          >
            <el-tag :type="getCategoryType(skill.category)" size="small">
              {{ index + 1 }}. {{ skill.name }}
            </el-tag>
            <span class="skill-category">{{ skill.category }}</span>
          </div>
        </div>
      </div>

      <!-- Prompt内容 -->
      <div class="prompt-content">
        <div class="section-title">完整Prompt</div>
        <el-input
          :model-value="prompt"
          type="textarea"
          :rows="15"
          readonly
          class="prompt-textarea"
        />
      </div>

      <!-- Token分布（可选） -->
      <div class="token-info">
        <el-alert
          title="提示"
          type="info"
          :closable="false"
          style="margin-top: 16px"
        >
          <template #default>
            <div>
              <p>当前Prompt的总Token数为：{{ tokenCount }}</p>
              <p v-if="tokenCount > 4000" style="color: var(--el-color-warning); margin-top: 8px">
                ⚠️ Token数超过4000，可能会影响模型的处理效率和成本。
              </p>
              <p v-else style="color: var(--el-color-success); margin-top: 8px">
                ✅ Token数在合理范围内。
              </p>
            </div>
          </template>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  prompt: string;
  tokenCount: number;
  skillsUsed?: Array<{
    id: number;
    name: string;
    category: string;
    order: number;
  }>;
}

const props = defineProps<Props>();

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
</script>

<style scoped lang="scss">
.prompt-preview {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 16px;
      font-weight: bold;
    }

    .stats {
      display: flex;
      gap: 8px;
    }
  }

  .section-title {
    font-size: 14px;
    font-weight: bold;
    color: var(--el-text-color-primary);
    margin-bottom: 12px;
  }

  .skills-used {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--el-border-color);

    .skills-list {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .skill-badge {
      display: flex;
      align-items: center;
      gap: 8px;

      .skill-category {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .prompt-content {
    .prompt-textarea {
      :deep(.el-textarea__inner) {
        font-family: "Courier New", monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--el-text-color-primary);
      }
    }
  }

  .token-info {
    p {
      margin: 4px 0;
    }
  }
}
</style>
