"""
智能体相关常量配置
"""
# 预设模板列表
PROMPT_TEMPLATES = [
    {
        "id": "1",
        "name": "通用助手",
        "content": "你是一个有用的AI助手，能够回答各种问题并提供帮助。",
        "category": "通用"
    },
    {
        "id": "2",
        "name": "代码助手",
        "content": "你是一个专业的编程助手，擅长编写、调试和优化代码。请提供清晰、可执行的代码示例。",
        "category": "编程"
    },
    {
        "id": "3",
        "name": "写作助手",
        "content": "你是一个专业的写作助手，能够帮助用户创作各种类型的文本内容，包括文章、故事、诗歌等。",
        "category": "写作"
    },
    {
        "id": "4",
        "name": "翻译助手",
        "content": "你是一个专业的翻译助手，能够准确翻译各种语言的内容，保持原意和风格。",
        "category": "翻译"
    },
    {
        "id": "5",
        "name": "数据分析师",
        "content": "你是一个数据分析专家，能够分析数据、生成报告并提供数据驱动的建议。",
        "category": "分析"
    },
]

# 可用模型列表
AVAILABLE_MODELS = [
    {
        "id": "gpt-4",
        "name": "GPT-4",
        "maxTokens": 8192
    },
    {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "maxTokens": 4096
    },
    {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "maxTokens": 128000
    },
]



