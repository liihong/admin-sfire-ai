<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="工单列表"
      :columns="columns"
      :request-api="getTableList"
      :init-param="initParam"
      :data-callback="dataCallback"
    >
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openCreateDialog">新建工单</el-button>
      </template>

      <!-- 工单类型 -->
      <template #type="scope">
        <el-tag :type="scope.row.type === 'membership' ? 'warning' : 'success'">
          {{ scope.row.type === "membership" ? "开通会员" : "充值算力" }}
        </el-tag>
      </template>

      <!-- 工单状态 -->
      <template #status="scope">
        <el-tag :type="getStatusTagType(scope.row.status)">
          {{ getStatusLabel(scope.row.status) }}
        </el-tag>
      </template>

      <!-- 目标用户：手机号 + 微信名称 -->
      <template #user="scope">
        <span>{{ scope.row.user?.phone || scope.row.user_id }}</span>
        <span v-if="scope.row.user?.nickname" class="text-secondary"> {{ scope.row.user.nickname }}</span>
      </template>

      <!-- 会员工单财务信息 -->
      <template #financeInfo="scope">
        <template v-if="scope.row.type === 'membership'">
          <div v-if="scope.row.is_paid !== undefined">
            <el-tag :type="scope.row.is_paid ? 'success' : 'info'" size="small">
              {{ scope.row.is_paid ? "已收费" : "未收费" }}
            </el-tag>
          </div>
          <div v-if="scope.row.period_type" class="text-secondary text-sm">
            {{ (periodTypeMap[scope.row.period_type] || scope.row.period_type) }}会员
          </div>
          <div v-if="scope.row.payment_method" class="text-secondary text-sm">
            {{ scope.row.payment_method }}
          </div>
        </template>
        <template v-else>
          <span v-if="scope.row.extra_data?.amount">
            +{{ scope.row.extra_data.amount }} 算力
          </span>
        </template>
      </template>

      <!-- 操作 -->
      <template #operation="scope">
        <el-button
          v-if="scope.row.status === 'pending'"
          type="primary"
          link
          :icon="Check"
          @click="handleTicket(scope.row)"
        >
          处理
        </el-button>
      </template>
    </ProTable>

    <!-- 新建工单弹窗 -->
    <el-dialog
      v-model="createVisible"
      title="新建工单"
      width="560px"
      destroy-on-close
      @close="resetCreateForm"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="120px">
        <el-form-item label="工单类型" prop="type">
          <el-radio-group v-model="createForm.type">
            <el-radio value="membership">开通会员</el-radio>
            <el-radio value="recharge">充值算力</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="目标用户" prop="user_id">
          <el-select
            v-model="createForm.user_id"
            filterable
            remote
            placeholder="输入手机号搜索用户"
            :remote-method="searchUsers"
            :loading="userSearchLoading"
            style="width: 100%"
            value-key="id"
          >
            <el-option
              v-for="u in userOptions"
              :key="u.id"
              :label="`${u.phone || u.username || u.id}${u.nickname ? ' ' + u.nickname : ''}`"
              :value="parseInt(u.id)"
            />
          </el-select>
        </el-form-item>

        <!-- 会员工单字段 -->
        <template v-if="createForm.type === 'membership'">
          <el-form-item label="目标等级" prop="membership.level_code">
            <el-select v-model="createForm.membership!.level_code" placeholder="请选择" style="width: 100%">
              <el-option label="个人创作者 (VIP)" value="vip" />
              <el-option label="小工作室 (SVIP)" value="svip" />
              <el-option label="矩阵大佬 (MAX)" value="max" />
            </el-select>
          </el-form-item>
          <el-form-item label="VIP到期时间" prop="membership.vip_expire_date">
            <el-date-picker
              v-model="createForm.membership!.vip_expire_date"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="是否已收费" prop="membership.is_paid">
            <el-radio-group v-model="createForm.membership!.is_paid">
              <el-radio :value="true">已收费</el-radio>
              <el-radio :value="false">未收费</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="收费方式" prop="membership.payment_method">
            <el-input
              v-model="createForm.membership!.payment_method"
              placeholder="如：微信、支付宝、对公转账"
              clearable
            />
          </el-form-item>
          <el-form-item label="会员周期" prop="membership.period_type">
            <el-radio-group v-model="createForm.membership!.period_type">
              <el-radio value="monthly">月度会员</el-radio>
              <el-radio value="quarterly">季度会员</el-radio>
              <el-radio value="yearly">年度会员</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="凭证" prop="membership.voucher">
            <el-input
              v-model="createForm.membership!.voucher"
              type="textarea"
              placeholder="凭证说明或图片URL"
              :rows="2"
            />
          </el-form-item>
        </template>

        <!-- 充值工单字段 -->
        <template v-else>
          <el-form-item label="充值金额" prop="recharge.amount">
            <el-input-number
              v-model="createForm.recharge!.amount"
              :min="1"
              :max="1000000"
              :step="100"
              controls-position="right"
              style="width: 100%"
            />
            <span class="ml-2 text-secondary">算力点</span>
          </el-form-item>
        </template>

        <el-form-item label="备注" prop="remark">
          <el-input v-model="createForm.remark" type="textarea" placeholder="选填" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="tsx" name="financeTicket">
import { ref, reactive, watch } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Check } from "@element-plus/icons-vue";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getTicketList,
  createTicket,
  handleTicket as handleTicketApi,
  type TicketItem,
  type TicketCreateParams
} from "@/api/modules/ticket";
import { getUserList } from "@/api/modules/user";

const proTable = ref<ProTableInstance>();
const initParam = reactive({});

const dataCallback = (data: { list: TicketItem[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: Record<string, unknown>) => {
  return getTicketList({
    pageNum: params.pageNum as number,
    pageSize: params.pageSize as number,
    type: params.type as "membership" | "recharge" | undefined,
    status: params.status as string | undefined,
    user_id: params.user_id as number | undefined
  });
};

const getStatusTagType = (status: string) => {
  const map: Record<string, string> = {
    pending: "warning",
    processing: "primary",
    completed: "success",
    rejected: "info",
    failed: "danger"
  };
  return map[status] || "info";
};

const periodTypeMap: Record<string, string> = {
  monthly: "月度",
  quarterly: "季度",
  yearly: "年度"
};

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: "待处理",
    processing: "处理中",
    completed: "已完成",
    rejected: "已拒绝",
    failed: "处理失败"
  };
  return map[status] || status;
};

const typeOptions = [
  { label: "开通会员", value: "membership" },
  { label: "充值算力", value: "recharge" }
];
const statusOptions = [
  { label: "待处理", value: "pending" },
  { label: "处理中", value: "processing" },
  { label: "已完成", value: "completed" },
  { label: "已拒绝", value: "rejected" },
  { label: "处理失败", value: "failed" }
];

const columns = reactive<ColumnProps<TicketItem>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "type",
    label: "类型",
    width: 100,
    search: { el: "select", options: typeOptions, fieldNames: { label: "label", value: "value" } }
  },
  {
    prop: "status",
    label: "状态",
    width: 100,
    search: { el: "select", options: statusOptions, fieldNames: { label: "label", value: "value" } }
  },
  { prop: "user", label: "目标用户", width: 160 },
  { prop: "financeInfo", label: "财务/金额", width: 140 },
  { prop: "creator", label: "创建人", width: 100, render: (scope: any) => scope.row.creator?.username || "-" },
  { prop: "handler", label: "处理人", width: 100, render: (scope: any) => scope.row.handler?.username || "-" },
  { prop: "created_at", label: "创建时间", width: 180 },
  { prop: "operation", label: "操作", fixed: "right", width: 100 }
]);

// 新建工单
const createVisible = ref(false);
const createLoading = ref(false);
const createFormRef = ref<FormInstance>();
const createForm = reactive<TicketCreateParams & { membership?: any; recharge?: any }>({
  type: "membership",
  user_id: 0,
  membership: {
    level_code: "vip",
    vip_expire_date: "",
    is_paid: false,
    payment_method: "",
    voucher: "",
    period_type: "monthly"
  },
  recharge: { amount: 100 },
  remark: ""
});

watch(
  () => createForm.type,
  (val) => {
    if (val === "membership" && !createForm.membership) {
      createForm.membership = {
        level_code: "vip",
        vip_expire_date: "",
        is_paid: false,
        payment_method: "",
        voucher: "",
        period_type: "monthly"
      };
    } else if (val === "recharge" && !createForm.recharge) {
      createForm.recharge = { amount: 100 };
    }
  }
);

const createRules: FormRules = {
  type: [{ required: true, message: "请选择工单类型", trigger: "change" }],
  user_id: [{ required: true, message: "请选择目标用户", trigger: "change" }],
  "membership.level_code": [{ required: true, message: "请选择目标等级", trigger: "change" }],
  "membership.vip_expire_date": [{ required: true, message: "请选择VIP到期时间", trigger: "change" }],
  "membership.is_paid": [{ required: true, message: "请选择是否已收费", trigger: "change" }],
  "membership.period_type": [{ required: true, message: "请选择会员周期", trigger: "change" }],
  "recharge.amount": [{ required: true, message: "请输入充值金额", trigger: "blur" }]
};

const userOptions = ref<Array<{ id: string; username: string; phone?: string; nickname?: string }>>([]);
const userSearchLoading = ref(false);

const searchUsers = async (query: string) => {
  if (!query || query.length < 1) {
    userOptions.value = [];
    return;
  }
  userSearchLoading.value = true;
  try {
    const { data } = await getUserList({
      pageNum: 1,
      pageSize: 20,
      phone: query
    } as any);
    userOptions.value = (data?.list || []).map((u: any) => ({
      id: u.id,
      username: u.username,
      phone: u.phone,
      nickname: u.nickname
    }));
  } catch {
    userOptions.value = [];
  } finally {
    userSearchLoading.value = false;
  }
};

const openCreateDialog = () => {
  createForm.type = "membership";
  createForm.user_id = 0;
  createForm.membership = {
    level_code: "vip",
    vip_expire_date: "",
    is_paid: false,
    payment_method: "",
    voucher: "",
    period_type: "monthly"
  };
  createForm.recharge = { amount: 100 };
  createForm.remark = "";
  userOptions.value = [];
  createVisible.value = true;
};

const resetCreateForm = () => {
  createFormRef.value?.resetFields();
};

const submitCreate = async () => {
  if (!createFormRef.value) return;
  await createFormRef.value.validate();
  createLoading.value = true;
  try {
    const params: TicketCreateParams = {
      type: createForm.type,
      user_id: createForm.user_id,
      remark: createForm.remark || undefined
    };
    if (createForm.type === "membership" && createForm.membership) {
      params.membership = {
        level_code: createForm.membership.level_code,
        vip_expire_date: createForm.membership.vip_expire_date,
        is_paid: createForm.membership.is_paid,
        payment_method: createForm.membership.payment_method || undefined,
        voucher: createForm.membership.voucher || undefined,
        period_type: createForm.membership.period_type
      };
    } else if (createForm.type === "recharge" && createForm.recharge) {
      params.recharge = { amount: createForm.recharge.amount };
    }
    await createTicket(params);
    ElMessage.success("工单创建成功");
    createVisible.value = false;
    proTable.value?.getTableList();
  } finally {
    createLoading.value = false;
  }
};

const handleTicket = async (row: TicketItem) => {
  try {
    await ElMessageBox.confirm(`确定要处理工单 #${row.id} 吗？`, "确认处理", {
      type: "warning"
    });
    await handleTicketApi(row.id);
    ElMessage.success("处理成功");
    proTable.value?.getTableList();
  } catch (e: any) {
    if (e !== "cancel") {
      ElMessage.error(e?.msg || e?.message || "处理失败");
    }
  }
};
</script>

<style scoped lang="scss">
.text-secondary {
  color: var(--el-text-color-secondary);
}
.text-sm {
  font-size: 12px;
}
.ml-2 {
  margin-left: 8px;
}
</style>
