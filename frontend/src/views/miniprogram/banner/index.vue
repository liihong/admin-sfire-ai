<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="Banner列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增Banner</el-button>
      </template>

      <!-- Banner图片 -->
      <template #image_url="scope">
        <el-image
          :src="scope.row.image_url"
          :preview-src-list="[scope.row.image_url]"
          fit="cover"
          style="width: 80px; height: 50px; border-radius: 4px"
          lazy
        />
      </template>

      <!-- 链接类型 -->
      <template #link_type="scope">
        <el-tag :type="getLinkTypeTagType(scope.row.link_type)" effect="plain">
          {{ getLinkTypeLabel(scope.row.link_type) }}
        </el-tag>
      </template>

      <!-- 位置 -->
      <template #position="scope">
        <el-tag :type="getPositionTagType(scope.row.position)" effect="plain">
          {{ getPositionLabel(scope.row.position) }}
        </el-tag>
      </template>

      <!-- 状态 -->
      <template #is_enabled="scope">
        <el-switch
          v-model="scope.row.is_enabled"
          :active-value="true"
          :inactive-value="false"
          :loading="statusLoading === scope.row.id"
          @change="handleStatusChange(scope.row)"
        />
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteBanner(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- Banner编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="Banner标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入Banner标题" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="Banner图片" prop="image_url">
          <el-upload
            class="banner-uploader"
            :action="uploadAction"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleImageSuccess"
            :before-upload="beforeImageUpload"
          >
            <img v-if="formData.image_url" :src="formData.image_url" class="banner-image" />
            <el-icon v-else class="banner-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持JPG、PNG格式，建议尺寸750x300px，大小不超过2MB</div>
        </el-form-item>
        <el-form-item label="链接类型" prop="link_type">
          <el-select v-model="formData.link_type" placeholder="请选择链接类型" style="width: 100%">
            <el-option label="无链接" value="none" />
            <el-option label="内部链接" value="internal" />
            <el-option label="外部链接" value="external" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="formData.link_type !== 'none'" label="跳转链接" prop="link_url">
          <el-input v-model="formData.link_url" placeholder="请输入跳转链接" maxlength="512" />
        </el-form-item>
        <el-form-item label="Banner位置" prop="position">
          <el-select v-model="formData.position" placeholder="请选择Banner位置" style="width: 100%">
            <el-option label="首页顶部" value="home_top" />
            <el-option label="首页中部" value="home_middle" />
            <el-option label="首页底部" value="home_bottom" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="9999" style="width: 100%" />
          <div class="form-tip">数字越小越靠前</div>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="formData.start_time"
            type="datetime"
            placeholder="选择开始时间（可选）"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="formData.end_time"
            type="datetime"
            placeholder="选择结束时间（可选）"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_enabled">
          <el-switch v-model="formData.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="bannerManage">
import { ref, reactive } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Plus } from "@element-plus/icons-vue";
import type { BannerItem, BannerParams } from "@/api/modules/banner";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getBannerList,
  addBanner,
  editBanner,
  deleteBanner as deleteBannerApi,
  updateBannerStatus
} from "@/api/modules/banner";
import { getToken } from "@/utils/auth";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 抽屉相关
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const statusLoading = ref<number | null>(null);

// 表单数据
const formData = reactive({
  id: 0,
  title: "",
  image_url: "",
  link_url: "",
  link_type: "none" as "none" | "internal" | "external",
  position: "home_top" as "home_top" | "home_middle" | "home_bottom",
  sort_order: 0,
  start_time: "",
  end_time: "",
  is_enabled: true
});

// 表单验证规则
const formRules: FormRules = {
  title: [{ required: true, message: "请输入Banner标题", trigger: "blur" }],
  image_url: [{ required: true, message: "请上传Banner图片", trigger: "change" }],
  link_url: [
    {
      validator: (rule, value, callback) => {
        if (formData.link_type !== "none" && !value) {
          callback(new Error("请输入跳转链接"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

const formRef = ref<FormInstance>();

// 上传配置
const uploadAction = import.meta.env.VITE_API_URL + "/v1/admin/upload";
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`
};

// 数据回调处理
const dataCallback = (data: any) => {
  return {
    list: data.list,
    total: data.total
  };
};

// 获取表格数据
const getTableList = (params: any) => {
  const newParams: BannerParams = {
    pageNum: params.pageNum,
    pageSize: params.pageSize,
    title: params.title,
    position: params.position,
    is_enabled: params.is_enabled
  };
  return getBannerList(newParams);
};

// 链接类型标签
const getLinkTypeTagType = (type: string): "success" | "warning" | "info" | "primary" | "danger" => {
  const typeMap: Record<string, "success" | "warning" | "info" | "primary" | "danger"> = {
    none: "info",
    internal: "success",
    external: "warning"
  };
  return typeMap[type] || "info";
};

const getLinkTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    none: "无链接",
    internal: "内部链接",
    external: "外部链接"
  };
  return labelMap[type] || type;
};

// 位置标签
const getPositionTagType = (position: string): "success" | "warning" | "info" | "primary" | "danger" => {
  const typeMap: Record<string, "success" | "warning" | "info" | "primary" | "danger"> = {
    home_top: "danger",
    home_middle: "warning",
    home_bottom: "info"
  };
  return typeMap[position] || "info";
};

const getPositionLabel = (position: string) => {
  const labelMap: Record<string, string> = {
    home_top: "首页顶部",
    home_middle: "首页中部",
    home_bottom: "首页底部"
  };
  return labelMap[position] || position;
};

// 打开抽屉
const openDrawer = (title: string, row?: BannerItem) => {
  drawerTitle.value = title;
  isEdit.value = !!row;
  
  if (row) {
    Object.assign(formData, {
      id: row.id,
      title: row.title,
      image_url: row.image_url,
      link_url: row.link_url || "",
      link_type: row.link_type,
      position: row.position,
      sort_order: row.sort_order,
      start_time: row.start_time || "",
      end_time: row.end_time || "",
      is_enabled: row.is_enabled
    });
  } else {
    Object.assign(formData, {
      id: 0,
      title: "",
      image_url: "",
      link_url: "",
      link_type: "none",
      position: "home_top",
      sort_order: 0,
      start_time: "",
      end_time: "",
      is_enabled: true
    });
  }
  
  drawerVisible.value = true;
};

// 图片上传成功
const handleImageSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    formData.image_url = response.data.url || response.data;
    ElMessage.success("图片上传成功");
  } else {
    ElMessage.error(response.msg || "图片上传失败");
  }
};

// 图片上传前验证
const beforeImageUpload = (file: File) => {
  const isImage = file.type.startsWith("image/");
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }
  if (!isLt2M) {
    ElMessage.error("图片大小不能超过2MB！");
    return false;
  }
  return true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        const params: any = {
          title: formData.title,
          image_url: formData.image_url,
          link_type: formData.link_type,
          position: formData.position,
          sort_order: formData.sort_order,
          is_enabled: formData.is_enabled
        };
        
        if (formData.link_type !== "none" && formData.link_url) {
          params.link_url = formData.link_url;
        }
        
        if (formData.start_time) {
          params.start_time = formData.start_time;
        }
        
        if (formData.end_time) {
          params.end_time = formData.end_time;
        }
        
        if (isEdit.value) {
          await editBanner({ id: formData.id, ...params });
          ElMessage.success("更新成功");
        } else {
          await addBanner(params);
          ElMessage.success("创建成功");
        }
        
        drawerVisible.value = false;
        proTable.value?.getTableList();
      } catch (error) {
        console.error(error);
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

// 删除Banner
const deleteBanner = async (row: BannerItem) => {
  await useHandleData(deleteBannerApi, row.id, `删除Banner "${row.title}"`).then(() => {
    proTable.value?.getTableList();
  });
};

// 状态切换
const handleStatusChange = async (row: BannerItem) => {
  statusLoading.value = row.id;
  try {
    await updateBannerStatus({ id: row.id, is_enabled: row.is_enabled });
    ElMessage.success(row.is_enabled ? "已启用" : "已禁用");
  } catch (error) {
    row.is_enabled = !row.is_enabled; // 回滚状态
    console.error(error);
  } finally {
    statusLoading.value = null;
  }
};

// 表格列配置
const columns = reactive<ColumnProps<BannerItem>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "image_url",
    label: "Banner图片",
    width: 120
  },
  {
    prop: "title",
    label: "标题",
    width: 200,
    search: { el: "input", tooltip: "支持模糊搜索" }
  },
  {
    prop: "link_type",
    label: "链接类型",
    width: 120
  },
  {
    prop: "position",
    label: "位置",
    width: 120,
    search: {
      el: "select",
      props: {
        filterable: true,
        options: [
          { label: "首页顶部", value: "home_top" },
          { label: "首页中部", value: "home_middle" },
          { label: "首页底部", value: "home_bottom" }
        ]
      }
    }
  },
  {
    prop: "sort_order",
    label: "排序",
    width: 100
  },
  {
    prop: "is_enabled",
    label: "状态",
    width: 100,
    search: {
      el: "select",
      props: {
        filterable: true,
        options: [
          { label: "启用", value: true },
          { label: "禁用", value: false }
        ]
      }
    }
  },
  {
    prop: "created_at",
    label: "创建时间",
    width: 180
  },
  { prop: "operation", label: "操作", fixed: "right", width: 150 }
]);
</script>

<style scoped lang="scss">
.banner-uploader {
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

.banner-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 100px;
  text-align: center;
  line-height: 100px;
}

.banner-image {
  width: 178px;
  height: 100px;
  display: block;
  object-fit: cover;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>

