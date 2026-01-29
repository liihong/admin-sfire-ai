<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="文章列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增文章</el-button>
      </template>

      <!-- 文章类型 -->
      <template #category="scope">
        <el-tag :type="getCategoryTagType(scope.row.category)" effect="plain">
          {{ getCategoryLabel(scope.row.category) }}
        </el-tag>
      </template>

      <!-- 封面图 -->
      <template #cover_image="scope">
        <el-image
          v-if="scope.row.cover_image"
          :src="scope.row.cover_image"
          :preview-src-list="[scope.row.cover_image]"
          fit="cover"
          style="width: 80px; height: 50px; border-radius: 4px"
          lazy
        />
        <span v-else style="color: #999">无封面</span>
      </template>

      <!-- 标签 -->
      <template #tags="scope">
        <el-tag
          v-for="tag in scope.row.tags || []"
          :key="tag"
          size="small"
          style="margin-right: 4px"
        >
          {{ tag }}
        </el-tag>
        <span v-if="!scope.row.tags || scope.row.tags.length === 0" style="color: #999">无标签</span>
      </template>

      <!-- 发布状态 -->
      <template #is_published="scope">
        <el-tag :type="scope.row.is_published ? 'success' : 'info'" effect="plain">
          {{ scope.row.is_published ? '已发布' : '未发布' }}
        </el-tag>
      </template>

      <!-- 启用状态 -->
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
        <el-button type="danger" link :icon="Delete" @click="deleteArticle(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 文章编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="800px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="文章类型" prop="category">
          <el-select v-model="formData.category" placeholder="请选择文章类型" style="width: 100%">
            <el-option label="创始人故事" value="founder_story" />
            <el-option label="运营干货" value="operation_article" />
            <el-option label="客户案例" value="customer_case" />
          </el-select>
        </el-form-item>
        <el-form-item label="文章标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入文章标题" maxlength="256" show-word-limit />
        </el-form-item>
        <el-form-item label="文章摘要" prop="summary">
          <el-input
            v-model="formData.summary"
            type="textarea"
            :rows="3"
            placeholder="请输入文章摘要（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="封面图" prop="cover_image">
          <el-upload
            class="cover-uploader"
            :action="uploadAction"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleImageSuccess"
            :before-upload="beforeImageUpload"
          >
            <img v-if="formData.cover_image" :src="formData.cover_image" class="cover-image" />
            <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持JPG、PNG格式，建议尺寸750x400px，大小不超过2MB</div>
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="formData.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入标签（可多选，可创建新标签）"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="文章内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="15"
            placeholder="请输入文章内容（支持HTML格式）"
          />
          <div class="form-tip">支持HTML格式，可以使用富文本编辑器编辑后粘贴到这里</div>
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="9999" style="width: 100%" />
          <div class="form-tip">数字越小越靠前</div>
        </el-form-item>
        <el-form-item label="发布时间">
          <el-date-picker
            v-model="formData.publish_time"
            type="datetime"
            placeholder="选择发布时间（可选）"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="发布状态" prop="is_published">
          <el-switch v-model="formData.is_published" />
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

<script setup lang="tsx" name="articleManage">
import { ref, reactive } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Plus } from "@element-plus/icons-vue";
import type { ArticleItem, ArticleParams } from "@/api/modules/article";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getArticleList,
  addArticle,
  editArticle,
  deleteArticle as deleteArticleApi,
  updateArticleStatus
} from "@/api/modules/article";
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
  category: "founder_story" as "founder_story" | "operation_article" | "customer_case",
  title: "",
  content: "",
  summary: "",
  cover_image: "",
  tags: [] as string[],
  sort_order: 0,
  publish_time: "",
  is_published: false,
  is_enabled: true
});

// 常用标签
const commonTags = [
  "爆款逻辑",
  "避坑指南",
  "运营技巧",
  "AI写作",
  "创始人",
  "创业故事",
  "客户案例",
  "成功案例"
];

// 表单验证规则
const formRules: FormRules = {
  category: [{ required: true, message: "请选择文章类型", trigger: "change" }],
  title: [{ required: true, message: "请输入文章标题", trigger: "blur" }],
  content: [{ required: true, message: "请输入文章内容", trigger: "blur" }]
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
  const newParams: ArticleParams = {
    pageNum: params.pageNum,
    pageSize: params.pageSize,
    category: params.category,
    title: params.title,
    tag: params.tag,
    is_published: params.is_published,
    is_enabled: params.is_enabled
  };
  return getArticleList(newParams);
};

// 文章类型标签
const getCategoryTagType = (category: string): "success" | "warning" | "info" | "primary" | "danger" => {
  const typeMap: Record<string, "success" | "warning" | "info" | "primary" | "danger"> = {
    founder_story: "danger",
    operation_article: "success",
    customer_case: "warning"
  };
  return typeMap[category] || "info";
};

const getCategoryLabel = (category: string) => {
  const labelMap: Record<string, string> = {
    founder_story: "创始人故事",
    operation_article: "运营干货",
    customer_case: "客户案例"
  };
  return labelMap[category] || category;
};

// 打开抽屉
const openDrawer = (title: string, row?: ArticleItem) => {
  drawerTitle.value = title;
  isEdit.value = !!row;
  
  if (row) {
    Object.assign(formData, {
      id: row.id,
      category: row.category,
      title: row.title,
      content: row.content,
      summary: row.summary || "",
      cover_image: row.cover_image || "",
      tags: row.tags || [],
      sort_order: row.sort_order,
      publish_time: row.publish_time || "",
      is_published: row.is_published,
      is_enabled: row.is_enabled
    });
  } else {
    Object.assign(formData, {
      id: 0,
      category: "founder_story",
      title: "",
      content: "",
      summary: "",
      cover_image: "",
      tags: [],
      sort_order: 0,
      publish_time: "",
      is_published: false,
      is_enabled: true
    });
  }
  
  drawerVisible.value = true;
};

// 图片上传成功
const handleImageSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    formData.cover_image = response.data.url || response.data;
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
          category: formData.category,
          title: formData.title,
          content: formData.content,
          summary: formData.summary || undefined,
          cover_image: formData.cover_image || undefined,
          tags: formData.tags.length > 0 ? formData.tags : undefined,
          sort_order: formData.sort_order,
          is_published: formData.is_published,
          is_enabled: formData.is_enabled
        };
        
        if (formData.publish_time) {
          params.publish_time = formData.publish_time;
        }
        
        if (isEdit.value) {
          await editArticle({ id: formData.id, ...params });
          ElMessage.success("更新成功");
        } else {
          await addArticle(params);
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

// 删除文章
const deleteArticle = async (row: ArticleItem) => {
  await useHandleData(deleteArticleApi, row.id, `删除文章 "${row.title}"`).then(() => {
    proTable.value?.getTableList();
  });
};

// 状态切换
const handleStatusChange = async (row: ArticleItem) => {
  statusLoading.value = row.id;
  try {
    await updateArticleStatus({ id: row.id, is_enabled: row.is_enabled });
    ElMessage.success(row.is_enabled ? "已启用" : "已禁用");
  } catch (error) {
    row.is_enabled = !row.is_enabled; // 回滚状态
    console.error(error);
  } finally {
    statusLoading.value = null;
  }
};

// 表格列配置
const columns = reactive<ColumnProps<ArticleItem>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "category",
    label: "文章类型",
    width: 120
  },
  {
    prop: "title",
    label: "标题",
    width: 200,
    search: { el: "input", tooltip: "支持模糊搜索" }
  },
  {
    prop: "cover_image",
    label: "封面图",
    width: 120
  },
  {
    prop: "tags",
    label: "标签",
    width: 200
  },
  {
    prop: "is_published",
    label: "发布状态",
    width: 100,
    search: {
      el: "select",
      props: {
        filterable: true,
        options: [
          { label: "已发布", value: true },
          { label: "未发布", value: false }
        ]
      }
    }
  },
  {
    prop: "view_count",
    label: "浏览量",
    width: 100
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
.cover-uploader {
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

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 100px;
  text-align: center;
  line-height: 100px;
}

.cover-image {
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



