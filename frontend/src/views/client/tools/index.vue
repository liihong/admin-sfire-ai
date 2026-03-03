<template>
  <div class="mp-tools">
    <div class="tools-header">
      <h2 class="tools-title">便捷工具包</h2>
      <p class="tools-desc">选择您需要的工具开始使用</p>
    </div>
    <el-row :gutter="20" class="tools-grid">
      <el-col
        v-for="tool in TOOLS_LIST"
        :key="tool.id"
        :xs="24"
        :sm="12"
        :md="8"
      >
        <el-card class="tool-card" shadow="hover" @click="goToTool(tool.path)">
          <div class="tool-content">
            <div class="tool-icon">
              <el-icon :size="40"><Microphone /></el-icon>
            </div>
            <h3 class="tool-name">{{ tool.name }}</h3>
            <p class="tool-desc">{{ tool.description }}</p>
            <el-button type="primary" link>去使用</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="MPTools">
import { useRouter } from "vue-router";
import { Microphone } from "@element-plus/icons-vue";
import { TOOLS_LIST } from "@/constants/tools";

const router = useRouter();

const goToTool = (path: string) => {
  router.push(path);
};
</script>

<style scoped lang="scss">
.mp-tools {
  max-width: 1200px;
  margin: 0 auto;
}

.tools-header {
  margin-bottom: 24px;

  .tools-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
  }

  .tools-desc {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.tools-grid {
  .tool-card {
    cursor: pointer;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-4px);
    }
  }

  .tool-content {
    text-align: center;
    padding: 8px 0;

    .tool-icon {
      width: 72px;
      height: 72px;
      margin: 0 auto 16px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }

    .tool-name {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
    }

    .tool-desc {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin: 0 0 12px 0;
      line-height: 1.5;
      min-height: 42px;
    }
  }
}
</style>
