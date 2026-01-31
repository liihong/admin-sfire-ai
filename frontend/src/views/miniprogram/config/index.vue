<template>
  <div class="config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">首页配置</span>
          <el-button type="primary" :icon="Check" :loading="saving" @click="handleSaveAll">保存全部</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="configForm" label-width="150px" label-position="left">
        <!-- 基础信息 -->
        <el-divider content-position="left">基础信息</el-divider>
        
        <el-form-item label="首页标题">
          <el-input
            v-model="configForm.home_title"
            placeholder="请输入首页标题"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="首页副标题">
          <el-input
            v-model="configForm.home_subtitle"
            placeholder="请输入首页副标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="首页背景图">
          <el-upload
            class="background-uploader"
            :action="uploadAction"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleBackgroundSuccess"
            :before-upload="beforeImageUpload"
          >
            <img v-if="configForm.home_background" :src="configForm.home_background" class="background-image" />
            <el-icon v-else class="background-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持JPG、PNG格式，建议尺寸1920x1080px，大小不超过5MB</div>
        </el-form-item>

        <!-- 推荐模块 -->
        <el-divider content-position="left">推荐模块</el-divider>
        
        <el-form-item label="推荐模块列表">
          <div class="module-list">
            <div
              v-for="(module, index) in featuredModules"
              :key="index"
              class="module-item"
            >
              <el-input
v-model="module.label"
                placeholder="模块名称"
style="width: 150px; margin-right: 10px"
              />
              <el-input
                v-model="module.icon"
placeholder="图标名称" style="width: 150px; margin-right: 10px"
              />
              <el-input
v-model="module.route" placeholder="跳转路由" style="width: 200px; margin-right: 10px" />
              <el-input-number v-model="module.iconSize" placeholder="图标大小" :min="10" :max="100"
                style="width: 120px; margin-right: 10px"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeModule(index)"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              plain
              @click="addModule"
              style="margin-top: 10px"
            >
              添加模块
            </el-button>
          </div>
        </el-form-item>

        <!-- 快捷链接 -->
        <el-divider content-position="left">快捷链接</el-divider>
        
        <el-form-item label="快捷链接列表">
          <div class="link-list">
            <div
              v-for="(link, index) in quickLinks"
              :key="index"
              class="link-item"
            >
              <el-input
                v-model="link.title"
                placeholder="链接标题"
                style="width: 200px; margin-right: 10px"
              />
              <el-input
                v-model="link.url"
                placeholder="链接地址"
                style="width: 350px; margin-right: 10px"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeLink(index)"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              plain
              @click="addLink"
              style="margin-top: 10px"
            >
              添加链接
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts" name="homeConfig">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, FormInstance } from "element-plus";
import { Check, Plus, Delete } from "@element-plus/icons-vue";
import { getAllConfigs, batchUpdateConfigs } from "@/api/modules/homeConfig";
import { getToken } from "@/utils/auth";

const formRef = ref<FormInstance>();
const saving = ref(false);

// 配置表单
const configForm = reactive({
  home_title: "",
  home_subtitle: "",
  home_background: ""
});

// 推荐模块列表（兼容两种格式：{ name, icon, link } 和 { icon, label, route, iconSize }）
const featuredModules = ref<Array<{
  name?: string;
  icon: string;
  link?: string;
  label?: string;
  route?: string;
  iconSize?: number;
}>>([]);

// 快捷链接列表
const quickLinks = ref<Array<{ title: string; url: string }>>([]);

// 上传配置
const uploadAction = import.meta.env.VITE_API_URL + "/api/v1/admin/upload";
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`
};

/**
 * 将 JavaScript 对象字面量格式转换为有效的 JSON 格式
 * 处理情况：
 * 1. 属性名没有引号: { icon: "value" } -> { "icon": "value" }
 * 2. 单引号字符串: { 'icon': 'value' } -> { "icon": "value" }
 * 3. 混合格式
 */
const normalizeJsObjectToJson = (jsStr: string): string => {
  let normalized = jsStr.trim();

  // 如果已经是有效的 JSON，直接返回
  try {
    JSON.parse(normalized);
    return normalized;
  } catch (e) {
    // 继续处理
  }

  // 处理属性名没有引号的情况
  // 匹配模式: 属性名（字母、数字、下划线）后跟冒号
  // 例如: icon: 或 iconSize: 或 icon_size:
  normalized = normalized.replace(
    /(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/g,
    (match, spaces, propName) => {
      // 检查是否在字符串内（简单检查）
      const beforeMatch = normalized.substring(0, normalized.indexOf(match));
      const singleQuotes = (beforeMatch.match(/'/g) || []).length;
      const doubleQuotes = (beforeMatch.match(/"/g) || []).length;
      // 如果单引号或双引号数量是奇数，说明在字符串内，不处理
      if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
        return match;
      }
      return `${spaces}"${propName}":`;
    }
  );

  // 处理单引号字符串，转换为双引号
  normalized = normalized.replace(/'/g, '"');

  return normalized;
};

/**
 * 解析配置值（支持 JSON 和 JavaScript 对象字面量格式）
 */
const parseConfigValue = (configValue: string | undefined): any => {
  if (!configValue) {
    return null;
  }

  const trimmed = configValue.trim();
  if (!trimmed) {
    return null;
  }

  // 先尝试标准 JSON 解析
  try {
    return JSON.parse(trimmed);
  } catch (e) {
    // JSON 解析失败，尝试修复 JavaScript 对象字面量格式
    try {
      const normalized = normalizeJsObjectToJson(trimmed);
      return JSON.parse(normalized);
    } catch (e2) {
      console.error("解析配置值失败:", e2, "原始值:", trimmed.substring(0, 200));
      return null;
    }
  }
};

// 加载配置数据
const loadConfigs = async () => {
  try {
    const response = await getAllConfigs();
    if (String(response.code) === "200" && response.data) {
      const configs = response.data.list || [];
      
      // 解析配置值
      configs.forEach((config) => {
        if (config.config_key === "home_title") {
          configForm.home_title = config.config_value || "";
        } else if (config.config_key === "home_subtitle") {
          configForm.home_subtitle = config.config_value || "";
        } else if (config.config_key === "home_background") {
          configForm.home_background = config.config_value || "";
        } else if (config.config_key === "featured_modules") {
          const parsed = parseConfigValue(config.config_value);
          if (Array.isArray(parsed)) {
            featuredModules.value = parsed;
          } else {
            featuredModules.value = [];
          }
        } else if (config.config_key === "quick_links") {
          const parsed = parseConfigValue(config.config_value);
          if (Array.isArray(parsed)) {
            quickLinks.value = parsed;
          } else {
            quickLinks.value = [];
          }
        }
      });
    }
  } catch (error) {
    console.error("加载配置失败:", error);
    ElMessage.error("加载配置失败");
  }
};

// 保存全部配置
const handleSaveAll = async () => {
  saving.value = true;
  try {
    // 规范化推荐模块数据，确保字段统一
    const normalizedModules = featuredModules.value.map((module) => {
      // 兼容旧格式，统一转换为新格式
      return {
        icon: module.icon || "",
        label: module.label || module.name || "",
        route: module.route || module.link || "",
        iconSize: module.iconSize || 20
      };
    });

    const configs = [
      {
        config_key: "home_title",
        config_value: configForm.home_title,
        config_type: "string" as const
      },
      {
        config_key: "home_subtitle",
        config_value: configForm.home_subtitle,
        config_type: "string" as const
      },
      {
        config_key: "home_background",
        config_value: configForm.home_background,
        config_type: "string" as const
      },
      {
        config_key: "featured_modules",
        config_value: JSON.stringify(normalizedModules),
        config_type: "array" as const
      },
      {
        config_key: "quick_links",
        config_value: JSON.stringify(quickLinks.value),
        config_type: "array" as const
      }
    ];

    const response = await batchUpdateConfigs(configs);
    if (String(response.code) === "200") {
      ElMessage.success("保存成功");
      // 重新加载配置以确保数据同步
      await loadConfigs();
    } else {
      ElMessage.error(response.msg || "保存失败");
    }
  } catch (error) {
    console.error("保存配置失败:", error);
    ElMessage.error("保存配置失败");
  } finally {
    saving.value = false;
  }
};

// 背景图上传成功
const handleBackgroundSuccess = (response: any) => {
  if (String(response.code) === "200" && response.data) {
    configForm.home_background = response.data.url || response.data;
    ElMessage.success("背景图上传成功");
  } else {
    ElMessage.error(response.msg || "背景图上传失败");
  }
};

// 图片上传前验证
const beforeImageUpload = (file: File) => {
  const isImage = file.type.startsWith("image/");
  const isLt5M = file.size / 1024 / 1024 < 5;

  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }
  if (!isLt5M) {
    ElMessage.error("图片大小不能超过5MB！");
    return false;
  }
  return true;
};

// 添加推荐模块
const addModule = () => {
  featuredModules.value.push({
    icon: "",
    label: "",
    route: "",
    iconSize: 20
  });
};

// 删除推荐模块
const removeModule = (index: number) => {
  featuredModules.value.splice(index, 1);
};

// 添加快捷链接
const addLink = () => {
  quickLinks.value.push({
    title: "",
    url: ""
  });
};

// 删除快捷链接
const removeLink = (index: number) => {
  quickLinks.value.splice(index, 1);
};

onMounted(() => {
  loadConfigs();
});
</script>

<style scoped lang="scss">
.config-container {
  padding: 20px;
}

.config-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-title {
    font-size: 18px;
    font-weight: 600;
  }
}

.background-uploader {
  :deep(.el-upload) {
    border: 1px dashed var(--el-border-color);
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: var(--el-transition-duration-fast);

    &:hover {
      border-color: var(--el-color-primary);
    }
  }
}

.background-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 300px;
  height: 150px;
  text-align: center;
  line-height: 150px;
}

.background-image {
  width: 300px;
  height: 150px;
  display: block;
  object-fit: cover;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.module-list,
.link-list {
  width: 100%;
}

.module-item,
.link-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

:deep(.el-divider) {
  margin: 30px 0 20px 0;
}
</style>

