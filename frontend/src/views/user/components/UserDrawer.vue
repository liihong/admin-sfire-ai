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
      <el-form-item v-if="drawerProps.title === '新增'" label="密码" prop="password">
        <el-input
          v-model="drawerProps.row!.password"
          type="password"
          placeholder="请输入密码（6-50个字符）"
          show-password
          clearable
        />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="drawerProps.row!.phone" placeholder="请输入手机号" clearable />
      </el-form-item>
      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="drawerProps.row!.nickname" placeholder="请输入昵称" clearable />
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
      <el-form-item v-if="drawerProps.title !== '新增'" label="用户状态" prop="status">
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
import type { User } from "@/api/interface";
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
    { min: 2, max: 64, message: "用户名长度为 2-64 个字符", trigger: "blur" }
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 50, message: "密码长度为 6-50 个字符", trigger: "blur" }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: "请输入正确的手机号", trigger: "blur" }
  ],
  level: [{ required: true, message: "请选择用户等级", trigger: "change" }]
});

// 接收父组件传递的参数
const acceptParams = (params: DrawerProps) => {
  // 初始化表单数据
  const rowData: any = {
    username: params.row?.username || "",
    phone: params.row?.phone || "",
    nickname: params.row?.nickname || "",
    remark: params.row?.remark || "",
    level: params.row?.level !== undefined ? params.row.level : 0,
    status: params.row?.status !== undefined ? params.row.status : 1,
  };
  
  // 如果是新增，添加密码字段
  if (params.title === "新增") {
    rowData.password = "";
  }
  
  drawerProps.value = {
    ...params,
    row: rowData
  };
  drawerVisible.value = true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();

  loading.value = true;
  try {
    const isNew = drawerProps.value.title === "新增";
    const api = isNew ? addUser : editUser;
    
    // 准备提交数据
    const submitData: any = {
      username: drawerProps.value.row!.username,
      phone: drawerProps.value.row!.phone || null,
      nickname: drawerProps.value.row!.nickname || null,
      remark: drawerProps.value.row!.remark || null,
    };
    
    if (isNew) {
      // 新增用户：需要密码和等级
      submitData.password = drawerProps.value.row!.password;
      // 将前端数字等级转换为后端字符串等级
      const levelMap: Record<number, string> = {
        0: "normal",
        1: "member",
        2: "partner"
      };
      submitData.level = levelMap[drawerProps.value.row!.level as number] || "normal";
    } else {
      // 编辑用户：可以更新等级和状态
      if (drawerProps.value.row!.level !== undefined) {
        const levelMap: Record<number, string> = {
          0: "normal",
          1: "member",
          2: "partner"
        };
        submitData.level = levelMap[drawerProps.value.row!.level as number];
      }
      if (drawerProps.value.row!.status !== undefined) {
        submitData.is_active = drawerProps.value.row!.status === 1;
      }
    }
    
    await api(isNew ? submitData : { ...submitData, id: drawerProps.value.row!.id });
    ElMessage.success(`${drawerProps.value.title}成功`);
    drawerProps.value.getTableList?.();
    drawerVisible.value = false;
  } catch (error: any) {
    ElMessage.error(error.message || `${drawerProps.value.title}失败`);
  } finally {
    loading.value = false;
  }
};

defineExpose({ acceptParams });
</script>



