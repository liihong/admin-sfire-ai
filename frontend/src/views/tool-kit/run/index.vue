<template>
  <div class="tool-run">
    <component :is="entry" v-if="entry" />
    <el-empty v-else description="未注册该工具页面，请联系管理员检查 toolRegistry 与数据库 code 是否一致" />
  </div>
</template>

<script setup lang="ts" name="ToolKitRun">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { resolveToolPage } from "@/config/toolRegistry";

const route = useRoute();
const code = computed(() => String(route.params.code || ""));
const entry = computed(() => resolveToolPage(code.value));
</script>

<style scoped lang="scss">
.tool-run {
  min-height: 320px;
}
</style>
