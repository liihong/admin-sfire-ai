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
      <el-form-item label="用户等级" prop="levelCode">
        <el-select v-model="drawerProps.row!.levelCode" placeholder="请选择用户等级" style="width: 100%">
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
      <!-- 会员到期时间（仅VIP等级显示） -->
      <el-form-item
        v-if="isVipLevel"
        label="会员到期时间"
        prop="vipExpireDate"
      >
        <div style="width: 100%">
          <!-- 快捷选项 -->
          <div style="margin-bottom: 8px; display: flex; gap: 8px">
            <el-button size="small" @click="setVipExpireDate('month')">月度会员</el-button>
            <el-button size="small" @click="setVipExpireDate('quarter')">季度会员</el-button>
            <el-button size="small" @click="setVipExpireDate('year')">年度会员</el-button>
          </div>
          <el-date-picker
            v-model="drawerProps.row!.vipExpireDate"
            type="date"
            placeholder="请选择会员到期时间"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            :disabled-date="(date: Date) => {
              const today = new Date();
              today.setHours(0, 0, 0, 0);
              return date < today;
            }"
            @change="handleVipExpireDateChange"
          />
        </div>
        <div style="font-size: 12px; color: var(--el-color-warning); margin-top: 4px">
          提示：到期时间为空时，将自动降级为普通用户
        </div>
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
import { ref, reactive, onMounted, computed, watch } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import type { User } from "@/api/interface";
import { addUser, editUser, getUserLevelOptions } from "@/api/modules/user";
import dayjs from "dayjs";

// 等级选项（从API获取）
const levelOptions = ref<Array<{ label: string; value: string; color?: string }>>([]);

// 初始化等级选项
const initLevelOptions = async () => {
  try {
    const { data } = await getUserLevelOptions();
    levelOptions.value = data.map((item: User.ResLevel) => ({
      label: item.label,
      value: item.value,
      color: item.color
    }));
  } catch (error) {
    console.error("获取用户等级选项失败:", error);
    ElMessage.error("获取用户等级选项失败");
  }
};

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

// 判断当前选择的等级是否为VIP等级
const isVipLevel = computed(() => {
  const levelCode = drawerProps.value.row?.levelCode;
  return levelCode === "vip" || levelCode === "svip" || levelCode === "max";
});

// 设置VIP到期时间（快捷选项）
const setVipExpireDate = (type: "month" | "quarter" | "year") => {
  if (!drawerProps.value.row) return;
  
  const today = dayjs();
  let expireDate: string;
  
  switch (type) {
    case "month":
      // 月度会员：当前日期 + 1个月
      expireDate = today.add(1, "month").format("YYYY-MM-DD");
      break;
    case "quarter":
      // 季度会员：当前日期 + 3个月
      expireDate = today.add(3, "month").format("YYYY-MM-DD");
      break;
    case "year":
      // 年度会员：当前日期 + 1年
      expireDate = today.add(1, "year").format("YYYY-MM-DD");
      break;
    default:
      return;
  }
  
  drawerProps.value.row.vipExpireDate = expireDate;
};

// 处理VIP到期时间变化
const handleVipExpireDateChange = (value: string | null) => {
  // 如果到期时间为空，且当前是VIP等级，则自动降级为普通用户
  if (!value && isVipLevel.value && drawerProps.value.row) {
    drawerProps.value.row.levelCode = "normal";
    ElMessage.warning("到期时间为空，已自动降级为普通用户");
  }
};

// 监听等级变化：当从VIP改为普通用户时，清空到期时间
watch(
  () => drawerProps.value.row?.levelCode,
  (newLevel, oldLevel) => {
    const wasVip = oldLevel === "vip" || oldLevel === "svip" || oldLevel === "max";
    const isVip = newLevel === "vip" || newLevel === "svip" || newLevel === "max";
    
    // 如果从VIP改为非VIP，清空到期时间
    if (wasVip && !isVip && drawerProps.value.row) {
      drawerProps.value.row.vipExpireDate = "";
    }
  }
);

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
  levelCode: [{ required: true, message: "请选择用户等级", trigger: "change" }]
});

// 接收父组件传递的参数
const acceptParams = async (params: DrawerProps) => {
  // 每次打开抽屉时重新加载等级选项，确保数据最新
  await initLevelOptions();
  
  // 初始化表单数据
  const rowData: any = {
    username: params.row?.username || "",
    phone: params.row?.phone || "",
    nickname: params.row?.nickname || "",
    remark: params.row?.remark || "",
    levelCode: params.row?.levelCode || "normal", // 使用levelCode，默认为normal
    vipExpireDate: params.row?.vipExpireDate || "", // VIP到期时间
    status: params.row?.status !== undefined ? params.row.status : 1,
  };
  
  // 保留 id 字段（编辑时需要）
  if (params.row?.id) {
    rowData.id = params.row.id;
  }
  
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
      // 如果选择了VIP等级但没有设置到期时间，则降级为普通用户
      const levelCode = drawerProps.value.row!.levelCode || "normal";
      const isVip = levelCode === "vip" || levelCode === "svip" || levelCode === "max";
      if (isVip && !drawerProps.value.row!.vipExpireDate) {
        submitData.level_code = "normal";
        submitData.vip_expire_date = null;
      } else {
        submitData.level_code = levelCode;
        if (isVip && drawerProps.value.row!.vipExpireDate) {
          submitData.vip_expire_date = drawerProps.value.row!.vipExpireDate;
        }
      }
    } else {
      // 编辑用户：可以更新等级和状态
      if (drawerProps.value.row!.levelCode) {
        submitData.level_code = drawerProps.value.row!.levelCode;
      }
      if (drawerProps.value.row!.status !== undefined) {
        submitData.is_active = drawerProps.value.row!.status === 1;
      }
      // 处理VIP到期时间和等级
      // 如果到期时间为空，且当前是VIP等级，则降级为普通用户
      if (isVipLevel.value && !drawerProps.value.row!.vipExpireDate) {
        // 到期时间为空，降级为普通用户
        submitData.level_code = "normal";
        submitData.vip_expire_date = null;
      } else if (isVipLevel.value && drawerProps.value.row!.vipExpireDate) {
        // VIP等级且设置了到期时间
        submitData.vip_expire_date = drawerProps.value.row!.vipExpireDate;
      } else if (!isVipLevel.value) {
        // 非VIP等级：清空到期时间
        submitData.vip_expire_date = null;
      }
    }
    
    const finalData = isNew ? submitData : { ...submitData, id: drawerProps.value.row!.id };
    await api(finalData);
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



