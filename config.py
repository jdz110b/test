"""
语料评测平台配置文件
"""

# Flask配置
SECRET_KEY = 'your-secret-key-here'
DEBUG = True

# 大模型配置
LLM_CONFIG = {
    'api_url': 'https://api.openai.com/v1/chat/completions',  # 默认OpenAI API
    'api_key': 'your-api-key-here',
    'model': 'gpt-3.5-turbo',
    'timeout': 30,
    'max_retries': 3
}

# 支持的大模型列表
SUPPORTED_MODELS = {
    'openai': {
        'name': 'OpenAI GPT',
        'api_url': 'https://api.openai.com/v1/chat/completions',
        'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
    },
    'custom': {
        'name': '自定义API',
        'api_url': '',  # 用户自定义
        'models': []
    }
}

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 数据库配置（如果需要）
# DATABASE_URL = 'sqlite:///corpus_evaluation.db'

# 分类配置
CLASSIFICATION_CONFIG = {
    'objective_subjective': {
        'types': ['客观', '主观'],
        'prompt_template': '请判断以下问题是客观题还是主观题：\n\n问题：{question}\n\n请只回答"客观"或"主观"。'
    },
    'difficulty_level': {
        'types': ['简单', '中等', '困难'],
        'prompt_template': '请判断以下问题的难度等级：\n\n问题：{question}\n\n请只回答"简单"、"中等"或"困难"。'
    },
    'network_search': {
        'types': ['需要联网', '不需要联网'],
        'prompt_template': '请判断以下问题是否需要联网搜索知识：\n\n问题：{question}\n\n请只回答"需要联网"或"不需要联网"。'
    }
}

# 答案生成配置
ANSWER_GENERATION_CONFIG = {
    'prompt_template': '请为以下客观问题提供准确答案：\n\n问题：{question}\n\n答案：',
    'max_tokens': 500
}

# Answer打分配置
ANSWER_SCORING_CONFIG = {
    'prompt_template': '请对以下答案进行打分（0-100分）：\n\n问题：{question}\n\n参考答案：{reference_answer}\n\n学生答案：{student_answer}\n\n请给出分数和简要评语。',
    'scoring_criteria': {
        'accuracy': 0.4,      # 准确性
        'completeness': 0.3,  # 完整性
        'clarity': 0.2,       # 清晰度
        'logic': 0.1          # 逻辑性
    }
}

# Prompt配置
PROMPT_TEMPLATES = {
    'classification': {
        'objective_subjective': '请判断以下问题是客观题还是主观题：\n\n问题：{question}\n\n请只回答"客观"或"主观"。',
        'difficulty_level': '请判断以下问题的难度等级：\n\n问题：{question}\n\n请只回答"简单"、"中等"或"困难"。',
        'network_search': '请判断以下问题是否需要联网搜索知识：\n\n问题：{question}\n\n请只回答"需要联网"或"不需要联网"。'
    },
    'answer_generation': '请为以下客观问题提供准确答案：\n\n问题：{question}\n\n答案：',
    'answer_scoring': '请对以下答案进行打分（0-100分）：\n\n问题：{question}\n\n参考答案：{reference_answer}\n\n学生答案：{student_answer}\n\n请给出分数和简要评语。'
}

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'default',
            'level': 'INFO'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'DEBUG'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}
