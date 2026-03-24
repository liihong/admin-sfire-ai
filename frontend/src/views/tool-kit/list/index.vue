<template>
  <div class="tool-kit-list">
    <div class="page-head">
      <h2 class="title">工具包列表</h2>
      <p class="desc">选择工具进入使用页（仅展示已启用项）</p>
    </div>
    <el-row v-loading="loading" :gutter="20" class="grid">
      <el-col v-for="tool in list" :key="tool.id" :xs="24" :sm="12" :md="8">
        <el-card class="card" shadow="hover" @click="go(tool.code)">
          <div class="inner">
            <div class="icon-wrap">
              <el-icon :size="36">
                <component :is="iconCmp(tool.icon)" />
              </el-icon>
            </div>
            <h3 class="name">{{ tool.name }}</h3>
            <p class="sub">{{ tool.description || "—" }}</p>
            <el-button type="primary" link>进入使用</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && !list.length" description="暂无可用工具" />
  </div>
</template>

<script setup lang="ts" name="ToolKitList">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import * as Icons from "@element-plus/icons-vue";
import { getAdminToolPackageList } from "@/api/modules/toolPackage";
import type { ToolPackageItem } from "@/api/modules/toolPackage";
import { ElMessage } from "element-plus";

const router = useRouter();
const loading = ref(false);
const list = ref<ToolPackageItem[]>([]);

const iconCmp = (name: string) => {
  const ic = (Icons as Record<string, unknown>)[name];
  return ic || Icons.Box;
};

const load = async () => {
  loading.value = true;
  try {
    const res = await getAdminToolPackageList({
      pageNum: 1,
      pageSize: 500,
      status: 1
    });
    list.value = res.data?.list ?? [];
  } catch (e: unknown) {
    const err = e as { msg?: string };
    ElMessage.error(err?.msg || "加载失败");
  } finally {
    loading.value = false;
  }
};

const go = (code: string) => {
  router.push({ name: "toolKitRun", params: { code } });
};

onMounted(load);
</script>

<style scoped lang="scss">
.tool-kit-list {
  max-width: 1100px;
  margin: 0 auto;
}

.page-head {
  margin-bottom: 24px;
  .title {
    font-size: 22px;
    font-weight: 600;
    margin: 0 0 8px 0;
  }
  .desc {
    margin: 0;
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }
}

.card {
  cursor: pointer;
  margin-bottom: 16px;
  transition: transform 0.2s;
  &:hover {
    transform: translateY(-3px);
  }
}

.inner {
  text-align: center;
  padding: 8px 0;
}

.icon-wrap {
  width: 72px;
  height: 72px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.name {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.sub {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  min-height: 40px;
  line-height: 1.45;
  margin: 0 0 8px 0;
}
</style>
