# 语料评测平台

## 项目概述

一个基于Python的语料评测平台，支持多种文件格式的语料导入、大模型智能分类、答案生成和评分功能。

## 功能特性

### 1. 语料文件导入
- 支持CSV、TXT等多种文件格式
- 支持Question语料和QA对语料导入

### 2. Question语料智能分类
- 客观/主观分类
- 难度等级分类
- 联网知识检索Question识别
- 客观Question答案生成
- 支持自定义分类类型
- 支持Prompt配置

### 3. QA对语料评测
- Answer智能打分
- 识别无法打分的Answer

### 4. 大模型灵活接入
- 支持API配置
- 支持Access Key配置
- 支持多种大模型接入

## 技术栈

- **后端**: Python 3.8+
- **Web框架**: Flask
- **数据处理**: Pandas
- **大模型调用**: OpenAI API / 自定义API
- **文件处理**: csv, io
- **前端**: HTML + CSS + JavaScript (可选)

## 项目结构

```
corpus-evaluation-platform/
├── app.py                      # Flask应用主文件
├── config.py                   # 配置文件
├── requirements.txt            # 依赖包
├── models/                     # 数据模型
│   ├── corpus.py              # 语料模型
│   └── evaluation.py          # 评测模型
├── services/                   # 业务逻辑
│   ├── file_service.py        # 文件处理服务
│   ├── llm_service.py         # 大模型调用服务
│   ├── classification_service.py  # 分类服务
│   └── evaluation_service.py  # 评测服务
├── utils/                      # 工具类
│   ├── file_parser.py         # 文件解析器
│   └── prompt_manager.py      # Prompt管理器
├── templates/                  # 前端模板
│   ├── index.html             # 首页
│   ├── upload.html            # 上传页面
│   └── evaluation.html        # 评测页面
├── static/                     # 静态资源
│   ├── css/
│   └── js/
├── uploads/                    # 上传文件目录
├── data/                       # 数据目录
└── README.md                   # 项目说明
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置大模型

编辑 `config.py` 文件，配置大模型API信息：

```python
LLM_API_URL = "your_api_url"
LLM_API_KEY = "your_api_key"
```

### 运行应用

```bash
python app.py
```

访问 `http://localhost:5000` 使用平台。

## 使用说明

### 1. 上传语料文件
- 支持CSV、TXT格式
- 选择语料类型（Question或QA对）

### 2. 配置分类参数
- 设置分类类型
- 配置Prompt模板
- 选择大模型

### 3. 执行评测
- 点击开始评测按钮
- 查看评测结果

### 4. 导出结果
- 支持导出评测结果为CSV格式

## API接口

### 上传语料文件
```
POST /api/upload
```

### 开始评测
```
POST /api/evaluate
```

### 获取评测结果
```
GET /api/results/{evaluation_id}
```

## 配置说明

### Prompt配置
支持自定义Prompt模板，用于大模型调用。

### 分类配置
支持自定义分类类型和标准。

## 开发计划

- [x] 项目架构设计
- [ ] 语料文件导入模块
- [ ] Question语料分类功能
- [ ] 客观Question答案生成
- [ ] 联网知识检索识别
- [ ] QA对语料评测
- [ ] 大模型接入模块
- [ ] Prompt配置管理
- [ ] Web界面开发
- [ ] 功能测试
- [ ] 部署和上传

## 许可证

MIT License

## 作者

AoneClaw Agent
