<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="大模型列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增模型</el-button>
      </template>

      <!-- 提供商 -->
      <template #provider="scope">
        <el-tag :type="getProviderTagType(scope.row.provider)" effect="plain">
          {{ getProviderName(scope.row.provider) }}
        </el-tag>
      </template>

      <!-- 状态 -->
      <template #is_enabled="scope">
        <el-tag :type="scope.row.is_enabled ? 'success' : 'danger'" effect="plain">
          {{ scope.row.is_enabled ? "启用" : "禁用" }}
        </el-tag>
      </template>

      <!-- Token 使用量 -->
      <template #total_tokens_used="scope">
        <span>{{ formatNumber(scope.row.total_tokens_used) }}</span>
      </template>

      <!-- 余额 -->
      <template #balance="scope">
        <span v-if="scope.row.balance !== null && scope.row.balance !== undefined">
          ${{ scope.row.balance.toFixed(4) }}
        </span>
        <span v-else class="text-gray-400">未查询</span>
      </template>

      <!-- API Key 状态 -->
      <template #has_api_key="scope">
        <el-tag :type="scope.row.has_api_key ? 'success' : 'warning'" effect="plain">
          {{ scope.row.has_api_key ? "已配置" : "未配置" }}
        </el-tag>
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button type="info" link :icon="Refresh" @click="refreshBalance(scope.row)">刷新余额</el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteModel(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 模型编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入模型显示名称，如：GPT-4o" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="模型标识" prop="model_id">
          <el-input v-model="formData.model_id" placeholder="请输入模型标识，如：gpt-4o" maxlength="128" show-word-limit />
          <div class="form-tip">API 中使用的模型名称</div>
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="formData.provider" placeholder="请选择提供商" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="formData.api_key"
            type="password"
            :placeholder="isEdit ? '留空则不修改 API Key' : '请输入 API Key'"
            maxlength="500"
            show-password
          />
          <div class="form-tip">用于调用 API 的密钥，请妥善保管</div>
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="formData.base_url" placeholder="留空则使用默认 URL" maxlength="512" />
          <div class="form-tip">API 基础 URL，留空将使用提供商默认地址</div>
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="formData.is_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="9999" controls-position="right" style="width: 100%" />
          <div class="form-tip">数值越小，显示越靠前</div>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formData.remark"
            type="textarea"
            placeholder="请输入备注"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="llmModelManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Refresh } from "@element-plus/icons-vue";
import type { LLMModel } from "@/api/interface";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getLLMModelList,
  createLLMModel,
  updateLLMModel,
  deleteLLMModel as deleteLLMModelApi,
  refreshLLMModelBalance
} from "@/api/modules/llmModel";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 数据回调处理
const dataCallback = (data: any) => {
  return {
    list: data.list || [],
    total: data.total || 0
  };
};

// 获取表格数据
const getTableList = (params: LLMModel.ReqLLMModelParams) => {
  return getLLMModelList(params);
};

// 提供商标签类型
const getProviderTagType = (provider: string): "success" | "info" | "warning" | "danger" => {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    openai: "success",
    anthropic: "info",
    deepseek: "warning"
  };
  return typeMap[provider] || "info";
};

// 提供商名称
const getProviderName = (provider: string): string => {
  const nameMap: Record<string, string> = {
    openai: "OpenAI",
    anthropic: "Anthropic",
    deepseek: "DeepSeek"
  };
  return nameMap[provider] || provider;
};

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + "M";
  if (num >= 1000) return (num / 1000).toFixed(2) + "K";
  return num.toString();
};

// 表格列配置
const columns = reactive<ColumnProps<LLMModel.ResLLMModelList>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "id",
    label: "ID",
    width: 80
  },
  {
    prop: "name",
    label: "模型名称",
    width: 150,
    isShow: true,
    search: { el: "input" }
  },
  {
    prop: "model_id",
    label: "模型标识",
    width: 150
  },
  {
    prop: "provider",
    label: "提供商",
    width: 120
  },
  {
    prop: "has_api_key",
    label: "API Key",
    width: 100
  },
  {
    prop: "is_enabled",
    label: "状态",
    width: 100
  },
  {
    prop: "total_tokens_used",
    label: "Token 使用量",
    width: 120
  },
  {
    prop: "balance",
    label: "账户余额",
    width: 120
  },
  {
    prop: "sort_order",
    label: "排序",
    width: 80
  },
  {
    prop: "remark",
    label: "备注",
    minWidth: 200,
    showOverflowTooltip: true
  },
  {
    prop: "created_at",
    label: "创建时间",
    width: 180
  },
  { prop: "operation", label: "操作", fixed: "right", width: 250 }
]);

// ==================== 模型编辑抽屉 ====================
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<LLMModel.ReqLLMModelCreate & LLMModel.ReqLLMModelUpdate & { id?: number }>({
  name: "",
  model_id: "",
  provider: "openai",
  api_key: "",
  base_url: "",
  is_enabled: true,
  sort_order: 0,
  remark: ""
});

const formRules: FormRules = {
  name: [{ required: true, message: "请输入模型名称", trigger: "blur" }],
  model_id: [{ required: true, message: "请输入模型标识", trigger: "blur" }],
  provider: [{ required: true, message: "请选择提供商", trigger: "change" }]
};

const openDrawer = (title: string, row: Partial<LLMModel.ResLLMModelList> = {}) => {
  drawerTitle.value = title;
  isEdit.value = !!row.id;

  // 重置表单
  formData.name = row.name || "";
  formData.model_id = row.model_id || "";
  formData.provider = (row.provider as LLMModel.ProviderType) || "openai";
  formData.api_key = "";
  formData.base_url = row.base_url || "";
  formData.is_enabled = row.is_enabled !== undefined ? row.is_enabled : true;
  formData.sort_order = row.sort_order || 0;
  formData.remark = row.remark || "";
  if (row.id) {
    formData.id = row.id;
  } else {
    delete formData.id;
  }

  drawerVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();
  submitLoading.value = true;

  try {
    if (isEdit.value && formData.id) {
      // 编辑
      const { id, ...updateData } = formData;
      // 如果 API key 为空，则不更新 API key
      if (!updateData.api_key) {
        const { api_key, ...dataWithoutApiKey } = updateData;
        await updateLLMModel(id, dataWithoutApiKey);
      } else {
        await updateLLMModel(id, updateData);
      }
      ElMessage.success("编辑成功");
    } else {
      // 新增
      const { id, ...createData } = formData;
      await createLLMModel(createData as LLMModel.ReqLLMModelCreate);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    proTable.value?.getTableList();
  } catch (error: any) {
    ElMessage.error(error.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};

// 删除模型
const deleteModel = async (row: LLMModel.ResLLMModelList) => {
  await useHandleData(deleteLLMModelApi, row.id, `删除模型【${row.name}】`);
  proTable.value?.getTableList();
};

// 刷新余额
const refreshBalance = async (row: LLMModel.ResLLMModelList) => {
  try {
    const { data } = await refreshLLMModelBalance(row.id);
    if (data?.success) {
      ElMessage.success("余额刷新成功");
      proTable.value?.getTableList();
    } else {
      ElMessage.warning(data?.message || "刷新失败");
    }
  } catch (error: any) {
    ElMessage.error(error.message || "刷新余额失败");
  }
};
</script>

<style scoped lang="scss">
.text-gray-400 {
  color: var(--el-text-color-secondary);
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>

