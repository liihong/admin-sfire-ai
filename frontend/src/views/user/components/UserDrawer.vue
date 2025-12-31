<template>
  <el-drawer v-model="drawerVisible" :title="drawerProps.title" :destroy-on-close="true" size="500px">
    <el-form
      ref="formRef"
      :model="drawerProps.row"
      :rules="rules"
      :disabled="drawerProps.isView"
      label-width="100px"
      label-suffix=" :"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="drawerProps.row!.username" placeholder="请输入用户名" clearable />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="drawerProps.row!.phone" placeholder="请输入手机号" clearable />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="drawerProps.row!.email" placeholder="请输入邮箱" clearable />
      </el-form-item>
      <el-form-item label="用户等级" prop="level">
        <el-select v-model="drawerProps.row!.level" placeholder="请选择用户等级" style="width: 100%">
          <el-option
            v-for="item in levelOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          >
            <span :style="{ color: item.color }">{{ item.label }}</span>
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="用户状态" prop="status">
        <el-radio-group v-model="drawerProps.row!.status">
          <el-radio :value="1">正常</el-radio>
          <el-radio :value="0">封禁</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="drawerProps.row!.remark"
          type="textarea"
          placeholder="请输入备注"
          :rows="4"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="drawerVisible = false">取消</el-button>
      <el-button v-if="!drawerProps.isView" type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts" name="UserDrawer">
import { ref, reactive } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { User } from "@/api/interface";
import { addUser, editUser } from "@/api/modules/userManage";
import { USER_LEVEL_CONFIG } from "@/config";

// 等级选项
const levelOptions = Object.entries(USER_LEVEL_CONFIG).map(([key, value]) => ({
  value: Number(key) as User.LevelType,
  label: value.label,
  color: value.color
}));

interface DrawerProps {
  title: string;
  isView: boolean;
  row: Partial<User.ResUserList>;
  getTableList?: () => void;
}

const drawerVisible = ref(false);
const loading = ref(false);
const formRef = ref<FormInstance>();

const drawerProps = ref<DrawerProps>({
  title: "",
  isView: false,
  row: {}
});

// 表单校验规则
const rules = reactive<FormRules>({
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 2, max: 20, message: "用户名长度为 2-20 个字符", trigger: "blur" }
  ],
  phone: [
    { required: true, message: "请输入手机号", trigger: "blur" },
    { pattern: /^1[3-9]\d{9}$/, message: "请输入正确的手机号", trigger: "blur" }
  ],
  email: [{ type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }],
  level: [{ required: true, message: "请选择用户等级", trigger: "change" }],
  status: [{ required: true, message: "请选择用户状态", trigger: "change" }]
});

// 接收父组件传递的参数
const acceptParams = (params: DrawerProps) => {
  drawerProps.value = params;
  drawerVisible.value = true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();

  loading.value = true;
  try {
    const api = drawerProps.value.title === "新增" ? addUser : editUser;
    await api(drawerProps.value.row);
    ElMessage.success(`${drawerProps.value.title}成功`);
    drawerProps.value.getTableList?.();
    drawerVisible.value = false;
  } finally {
    loading.value = false;
  }
};

defineExpose({ acceptParams });
</script>



