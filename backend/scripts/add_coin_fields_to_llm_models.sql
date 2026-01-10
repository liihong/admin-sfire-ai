-- 为 llm_models 表增加算力计算配置字段
-- 执行时间: 2025-01-10

-- 1. 增加模型倍率系数字段
ALTER TABLE llm_models
ADD COLUMN rate_multiplier DECIMAL(4,2) DEFAULT 1.00
COMMENT '模型倍率系数 (用于算力计算)';

-- 2. 增加基础调度费字段
ALTER TABLE llm_models
ADD COLUMN base_fee DECIMAL(16,4) DEFAULT 10.0000
COMMENT '基础调度费(火源币),无论请求是否成功,只要通过内容审查就扣除';

-- 3. 增加输入Token权重字段
ALTER TABLE llm_models
ADD COLUMN input_weight DECIMAL(4,2) DEFAULT 1.00
COMMENT '输入Token权重,相对便宜';

-- 4. 增加输出Token权重字段
ALTER TABLE llm_models
ADD COLUMN output_weight DECIMAL(4,2) DEFAULT 3.00
COMMENT '输出Token权重,较贵,是价值核心';

-- 5. 增加单次请求最大Token数字段
ALTER TABLE llm_models
ADD COLUMN max_tokens_per_request INT DEFAULT 4096
COMMENT '单次请求最大Token数,用于预冻结估算';

-- 6. 为现有模型设置默认值
UPDATE llm_models
SET
    rate_multiplier = 1.00,
    base_fee = 10.0000,
    input_weight = 1.00,
    output_weight = 3.00,
    max_tokens_per_request = 4096
WHERE rate_multiplier IS NULL;

-- 7. 创建索引以提高查询性能
CREATE INDEX ix_llm_models_rate_multiplier ON llm_models(rate_multiplier);
