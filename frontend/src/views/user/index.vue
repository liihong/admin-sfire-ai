<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="用户列表"
      :columns="columns"
      :request-api="getTableList"
      :init-param="initParam"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader="scope">
        <el-button v-auth="'add'" type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增用户</el-button>
        <el-button v-auth="'export'" type="primary" :icon="Download" plain @click="downloadFile">导出数据</el-button>
        <el-button
          type="danger"
          :icon="Delete"
          plain
          :disabled="!scope.isSelected"
          @click="batchDelete(scope.selectedListIds)"
        >
          批量删除
        </el-button>
      </template>

      <!-- 用户等级 -->
      <template #level="scope">
        <el-tag :type="getLevelTagType(scope.row.level)" effect="dark">
          {{ getLevelLabel(scope.row.level) }}
        </el-tag>
      </template>

      <!-- 算力概览 -->
      <template #computePower="scope">
        <div class="compute-info">
          <div class="compute-balance">
            <span class="balance-value">{{ formatNumber(scope.row.computePower.balance) }}</span>
            <span class="balance-label">可用</span>
          </div>
          <el-divider direction="vertical" />
          <div class="compute-frozen" v-if="scope.row.computePower.frozen > 0">
            <span class="frozen-value">{{ formatNumber(scope.row.computePower.frozen) }}</span>
            <span class="frozen-label">冻结</span>
          </div>
          <el-tooltip :content="`累计消耗: ${formatNumber(scope.row.computePower.totalConsumed)}`" placement="top">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>

      <!-- 用户状态 -->
      <template #status="scope">
        <el-switch
          v-model="scope.row.status"
          :active-value="1"
          :inactive-value="0"
          :active-text="scope.row.status === 1 ? '正常' : '封禁'"
          :loading="statusLoading === scope.row.id"
          @change="handleStatusChange(scope.row)"
        />
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="Coin" @click="openRechargeDialog(scope.row)">充值</el-button>
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button type="primary" link :icon="User" @click="viewUserProfile(scope.row)">画像</el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteAccount(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 用户编辑抽屉 -->
    <UserDrawer ref="drawerRef" />

    <!-- 算力充值弹窗 -->
    <el-dialog v-model="rechargeVisible" title="算力充值" width="500px" destroy-on-close>
      <el-form ref="rechargeFormRef" :model="rechargeForm" :rules="rechargeRules" label-width="100px">
        <el-form-item label="用户">
          <el-input :value="currentUser?.username" disabled />
        </el-form-item>
        <el-form-item label="当前余额">
          <el-input :value="formatNumber(currentUser?.computePower?.balance || 0)" disabled>
            <template #suffix>算力点</template>
          </el-input>
        </el-form-item>
        <el-form-item label="充值金额" prop="amount">
          <el-input-number
            v-model="rechargeForm.amount"
            :min="1"
            :max="1000000"
            :step="100"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="rechargeForm.remark" type="textarea" placeholder="请输入充值备注" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rechargeVisible = false">取消</el-button>
        <el-button type="primary" :loading="rechargeLoading" @click="handleRecharge">确认充值</el-button>
      </template>
    </el-dialog>

    <!-- 用户画像抽屉 -->
    <el-drawer v-model="profileVisible" title="用户画像" size="600px" destroy-on-close>
      <UserProfile v-if="profileVisible && currentUser" :user-id="currentUser.id" />
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="userManage">
import { ref, reactive } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Download, User, Coin, InfoFilled } from "@element-plus/icons-vue";
import { User as UserType } from "@/api/interface";
import { useHandleData } from "@/hooks/useHandleData";
import { useDownload } from "@/hooks/useDownload";
import ProTable from "@/components/ProTable/index.vue";
import UserDrawer from "./components/UserDrawer.vue";
import UserProfile from "./components/UserProfile.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { USER_LEVEL_CONFIG } from "@/config";
import {
  getUserList,
  deleteUser,
  changeUserStatus,
  rechargeUserCompute,
  getUserLevelOptions,
  getUserStatusOptions,
  exportUserData
} from "@/api/modules/userManage";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 初始化参数
const initParam = reactive({});

// 数据回调处理
const dataCallback = (data: any) => {
  return {
    list: data.list,
    total: data.total
  };
};

// 获取表格数据
const getTableList = (params: any) => {
  const newParams = { ...params };
  if (newParams.createTime) {
    newParams.startTime = newParams.createTime[0];
    newParams.endTime = newParams.createTime[1];
    delete newParams.createTime;
  }
  return getUserList(newParams);
};

// 等级标签类型
const getLevelTagType = (level: UserType.LevelType) => {
  const typeMap: Record<UserType.LevelType, string> = {
    0: "info",
    1: "warning",
    2: "danger"
  };
  return typeMap[level] || "info";
};

// 等级标签文本
const getLevelLabel = (level: UserType.LevelType) => {
  return USER_LEVEL_CONFIG[level]?.label || "未知";
};

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + "万";
  }
  return num.toLocaleString();
};

// 表格列配置
const columns = reactive<ColumnProps<UserType.ResUserList>[]>([
  { type: "selection", fixed: "left", width: 50 },
  { type: "index", label: "#", width: 60 },
  {
    prop: "username",
    label: "用户名",
    width: 120,
    search: { el: "input", tooltip: "支持模糊搜索" }
  },
  {
    prop: "phone",
    label: "手机号",
    width: 130,
    search: { el: "input" }
  },
  {
    prop: "level",
    label: "等级",
    width: 100,
    enum: getUserLevelOptions,
    fieldNames: { label: "label", value: "value" },
    search: { el: "select", props: { filterable: true } }
  },
  {
    prop: "computePower",
    label: "算力概览",
    width: 180
  },
  {
    prop: "inviterName",
    label: "邀请人",
    width: 100
  },
  {
    prop: "createTime",
    label: "注册时间",
    width: 180,
    search: {
      el: "date-picker",
      span: 2,
      props: { type: "datetimerange", valueFormat: "YYYY-MM-DD HH:mm:ss" }
    }
  },
  {
    prop: "lastLoginTime",
    label: "最后登录",
    width: 180
  },
  {
    prop: "status",
    label: "状态",
    width: 100,
    enum: getUserStatusOptions,
    fieldNames: { label: "userLabel", value: "userValue" },
    search: { el: "select" }
  },
  { prop: "operation", label: "操作", fixed: "right", width: 260 }
]);

// 状态切换 loading
const statusLoading = ref<string>("");

// 切换用户状态
const handleStatusChange = async (row: UserType.ResUserList) => {
  const newStatus = row.status === 1 ? 0 : 1;
  const action = newStatus === 1 ? "解封" : "封禁";

  try {
    await ElMessageBox.confirm(`确定要${action}用户【${row.username}】吗？`, "提示", {
      type: "warning"
    });

    statusLoading.value = row.id;
    await changeUserStatus({ id: row.id, status: newStatus });
    ElMessage.success(`${action}成功`);
    proTable.value?.getTableList();
  } catch {
    row.status = row.status === 1 ? 1 : 0; // 恢复原状态
  } finally {
    statusLoading.value = "";
  }
};

// 删除用户
const deleteAccount = async (row: UserType.ResUserList) => {
  await useHandleData(deleteUser, { id: [row.id] }, `删除用户【${row.username}】`);
  proTable.value?.getTableList();
};

// 批量删除
const batchDelete = async (ids: string[]) => {
  await useHandleData(deleteUser, { id: ids }, "删除所选用户");
  proTable.value?.clearSelection();
  proTable.value?.getTableList();
};

// 导出数据
const downloadFile = async () => {
  ElMessageBox.confirm("确认导出用户数据?", "温馨提示", { type: "warning" }).then(() =>
    useDownload(exportUserData, "用户列表", proTable.value?.searchParam)
  );
};

// ==================== 用户编辑抽屉 ====================
const drawerRef = ref<InstanceType<typeof UserDrawer> | null>(null);

const openDrawer = (title: string, row: Partial<UserType.ResUserList> = {}) => {
  const params = {
    title,
    isView: title === "查看",
    row: { ...row },
    getTableList: proTable.value?.getTableList
  };
  drawerRef.value?.acceptParams(params);
};

// ==================== 算力充值 ====================
const rechargeVisible = ref(false);
const rechargeLoading = ref(false);
const currentUser = ref<UserType.ResUserList | null>(null);
const rechargeFormRef = ref<FormInstance>();
const rechargeForm = reactive({
  amount: 100,
  remark: ""
});

const rechargeRules: FormRules = {
  amount: [{ required: true, message: "请输入充值金额", trigger: "blur" }]
};

const openRechargeDialog = (row: UserType.ResUserList) => {
  currentUser.value = row;
  rechargeForm.amount = 100;
  rechargeForm.remark = "";
  rechargeVisible.value = true;
};

const handleRecharge = async () => {
  if (!rechargeFormRef.value || !currentUser.value) return;

  await rechargeFormRef.value.validate();
  rechargeLoading.value = true;

  try {
    await rechargeUserCompute({
      userId: currentUser.value.id,
      amount: rechargeForm.amount,
      remark: rechargeForm.remark
    });
    ElMessage.success("充值成功");
    rechargeVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    rechargeLoading.value = false;
  }
};

// ==================== 用户画像 ====================
const profileVisible = ref(false);

const viewUserProfile = (row: UserType.ResUserList) => {
  currentUser.value = row;
  profileVisible.value = true;
};
</script>

<style scoped lang="scss">
.compute-info {
  display: flex;
  align-items: center;
  gap: 8px;

  .compute-balance,
  .compute-frozen {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .balance-value {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-color-primary);
    font-family: "DIN", sans-serif;
  }

  .balance-label,
  .frozen-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .frozen-value {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-color-warning);
    font-family: "DIN", sans-serif;
  }

  .info-icon {
    cursor: pointer;
    color: var(--el-text-color-placeholder);

    &:hover {
      color: var(--el-color-primary);
    }
  }
}
</style>


