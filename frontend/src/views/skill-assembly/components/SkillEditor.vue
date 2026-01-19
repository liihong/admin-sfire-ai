<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑技能' : '新增技能'"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      label-position="right"
    >
      <el-form-item label="技能名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入技能名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="分类" prop="category">
        <el-select v-model="formData.category" placeholder="请选择分类" style="width: 100%">
          <el-option label="Model" value="model">
            <div>
              <div>Model</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">脚本模型</div>
            </div>
          </el-option>
          <el-option label="Hook" value="hook">
            <div>
              <div>Hook</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">开头公式</div>
            </div>
          </el-option>
          <el-option label="Rule" value="rule">
            <div>
              <div>Rule</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">规则约束</div>
            </div>
          </el-option>
          <el-option label="Audit" value="audit">
            <div>
              <div>Audit</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">审核标准</div>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="特征描述" prop="meta_description">
        <el-input
          v-model="formData.meta_description"
          type="textarea"
          :rows="2"
          placeholder="简述技能特征，用于路由匹配（可选）"
          maxlength="200"
          show-word-limit
        />
        <div class="form-tip">用于智能路由匹配，描述该技能的适用场景</div>
      </el-form-item>

      <el-form-item label="技能内容" prop="content">
        <el-input
          v-model="formData.content"
          type="textarea"
          :rows="10"
          placeholder="输入实际的Prompt片段，支持变量：{{variable_name}}"
          maxlength="5000"
          show-word-limit
        />
        <div class="form-tip">
          支持变量格式：<code>{{变量名}}</code>，例如：<code>{{brand_name}}</code>、<code>{{industry}}</code>
        </div>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio :label="1">启用</el-radio>
          <el-radio :label="0">禁用</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { createSkill, updateSkill } from "@/api/modules/skillAssembly";
import { Skill } from "@/api/interface";

interface Props {
  visible: boolean;
  skillData?: Skill.ResSkillItem | null;
}

interface Emits {
  (e: "update:visible", value: boolean): void;
  (e: "submit"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const formRef = ref<FormInstance>();
const submitting = ref(false);

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit("update:visible", val)
});

const isEdit = computed(() => !!props.skillData?.id);

const formData = reactive({
  id: undefined as number | undefined,
  name: "",
  category: "model" as Skill.CategoryType,
  meta_description: "",
  content: "",
  status: 1
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入技能名称", trigger: "blur" }],
  category: [{ required: true, message: "请选择分类", trigger: "change" }],
  content: [{ required: true, message: "请输入技能内容", trigger: "blur" }]
};

// 监听skillData变化，初始化表单
watch(
  () => props.skillData,
  (data) => {
    if (data) {
      Object.assign(formData, {
        id: data.id,
        name: data.name,
        category: data.category,
        meta_description: data.meta_description || "",
        content: data.content,
        status: data.status
      });
    } else {
      resetForm();
    }
  },
  { immediate: true }
);

const resetForm = () => {
  formData.id = undefined;
  formData.name = "";
  formData.category = "model";
  formData.meta_description = "";
  formData.content = "";
  formData.status = 1;
  formRef.value?.clearValidate();
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();
  submitting.value = true;

  try {
    if (isEdit.value) {
      await updateSkill(formData.id!, formData);
      ElMessage.success("更新成功");
    } else {
      await createSkill(formData);
      ElMessage.success("创建成功");
    }
    emit("submit");
  } catch (error) {
    console.error("提交失败:", error);
    ElMessage.error("操作失败，请重试");
  } finally {
    submitting.value = false;
  }
};

const handleClose = () => {
  emit("update:visible", false);
};
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
  line-height: 1.5;

  code {
    background-color: var(--el-fill-color-light);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "Courier New", monospace;
    color: var(--el-color-primary);
  }
}
</style>
