"""
语料评测平台 - Flask应用主文件（完整版）
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import logging
from logging.config import dictConfig
import json
from werkzeug.utils import secure_filename

from config import (
    LLM_CONFIG, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, 
    MAX_CONTENT_LENGTH, LOGGING_CONFIG
)
from services.file_service import FileService
from services.llm_service import LLMService
from services.classification_service import ClassificationService
from services.answer_generation_service import AnswerGenerationService
from services.network_search_service import NetworkSearchService
from services.evaluation_service import EvaluationService
from services.llm_config_service import LLMConfigService
from utils.prompt_manager import PromptManager

# 配置日志
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保必要的目录存在
for directory in [UPLOAD_FOLDER, 'logs', 'data', 'templates', 'static']:
    os.makedirs(directory, exist_ok=True)

# 初始化服务
file_service = FileService(UPLOAD_FOLDER)
llm_service = LLMService(LLM_CONFIG)
classification_service = ClassificationService(llm_service)
answer_generation_service = AnswerGenerationService(llm_service)
network_search_service = NetworkSearchService(llm_service)
evaluation_service = EvaluationService(llm_service)
llm_config_service = LLMConfigService()
prompt_manager = PromptManager()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/upload')
def upload():
    """上传页面"""
    return render_template('upload.html')

@app.route('/evaluation')
def evaluation():
    """评测页面"""
    return render_template('evaluation.html')

@app.route('/config')
def config():
    """配置页面"""
    return render_template('config.html')

# ==================== API接口 ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    return jsonify({
        'supported_models': {
            'openai': {
                'name': 'OpenAI GPT',
                'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            }
        },
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'max_file_size': MAX_CONTENT_LENGTH
    })

@app.route('/api/llm/config', methods=['GET', 'POST'])
def llm_config():
    """获取或设置大模型配置"""
    if request.method == 'GET':
        config = llm_config_service.get_current_config()
        if config:
            # 不返回敏感信息
            safe_config = {
                'api_url': config.get('api_url', ''),
                'model': config.get('model', ''),
                'timeout': config.get('timeout', 30),
                'max_retries': config.get('max_retries', 3),
                'temperature': config.get('temperature', 0.7),
                'max_tokens': config.get('max_tokens', 1000)
            }
            return jsonify(safe_config)
        else:
            return jsonify({'error': '没有找到配置'}), 404
    else:
        # 更新配置
        data = request.json
        config_name = data.get('config_name', 'default')
        
        # 验证配置
        validation_result = llm_config_service.validate_config(data)
        if not validation_result['valid']:
            return jsonify({'error': '配置验证失败', 'details': validation_result}), 400
        
        # 更新或添加配置
        if llm_config_service.get_config(config_name):
            llm_config_service.update_config(config_name, data)
        else:
            llm_config_service.add_config(config_name, data)
        
        # 设置为当前配置
        llm_config_service.set_current_config(config_name)
        llm_config_service.save_configs()
        
        # 更新LLM服务配置
        llm_service.update_config(data)
        
        logger.info(f"LLM配置已更新: {config_name}")
        return jsonify({'success': True, 'message': '配置已更新'})

@app.route('/api/llm/configs', methods=['GET'])
def list_llm_configs():
    """列出所有大模型配置"""
    configs = llm_config_service.list_configs()
    return jsonify(configs)

@app.route('/api/llm/config/<config_name>', methods=['DELETE'])
def delete_llm_config(config_name):
    """删除大模型配置"""
    if llm_config_service.delete_config(config_name):
        llm_config_service.save_configs()
        return jsonify({'success': True, 'message': '配置已删除'})
    else:
        return jsonify({'error': '删除配置失败'}), 400

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传语料文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 保存文件
        filepath = file_service.save_uploaded_file(file, file.filename)
        
        # 获取语料类型
        corpus_type = request.form.get('corpus_type', 'question')
        
        # 解析文件
        corpus_list = file_service.parse_corpus_file(filepath, corpus_type)
        
        # 验证语料
        is_valid, message = file_service.validate_corpus(corpus_list, corpus_type)
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        logger.info(f"文件上传成功: {file.filename}, 类型: {corpus_type}, 数量: {len(corpus_list)}")
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'corpus_type': corpus_type,
            'count': len(corpus_list),
            'message': '文件上传成功'
        })
    else:
        return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/api/classify', methods=['POST'])
def classify_questions():
    """分类Question"""
    data = request.json
    
    if 'filename' not in data:
        return jsonify({'error': '缺少文件名'}), 400
    
    if 'classification_types' not in data:
        return jsonify({'error': '缺少分类类型'}), 400
    
    filename = data['filename']
    classification_types = data['classification_types']
    prompt_templates = data.get('prompt_templates', {})
    
    # 解析文件
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    corpus_list = file_service.parse_corpus_file(filepath, 'question')
    
    # 执行分类
    results = classification_service.classify_corpus(
        corpus_list, classification_types, prompt_templates
    )
    
    # 获取统计信息
    stats = classification_service.get_classification_statistics(results)
    
    logger.info(f"分类完成: {filename}, 类型: {classification_types}")
    
    return jsonify({
        'success': True,
        'results': results,
        'statistics': stats
    })

@app.route('/api/generate-answers', methods=['POST'])
def generate_answers():
    """生成答案"""
    data = request.json
    
    if 'filename' not in data:
        return jsonify({'error': '缺少文件名'}), 400
    
    filename = data['filename']
    prompt_template = data.get('prompt_template')
    
    # 解析文件
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    corpus_list = file_service.parse_corpus_file(filepath, 'question')
    
    # 先进行分类
    classified_corpus = classification_service.classify_corpus(
        corpus_list, ['objective_subjective']
    )
    
    # 生成答案
    results = answer_generation_service.generate_answers_for_objective_questions(
        classified_corpus, prompt_template
    )
    
    # 获取统计信息
    stats = answer_generation_service.get_answer_statistics(
        [r['answer_generation'] for r in results]
    )
    
    logger.info(f"答案生成完成: {filename}")
    
    return jsonify({
        'success': True,
        'results': results,
        'statistics': stats
    })

@app.route('/api/identify-network-search', methods=['POST'])
def identify_network_search():
    """识别联网知识检索Question"""
    data = request.json
    
    if 'filename' not in data:
        return jsonify({'error': '缺少文件名'}), 400
    
    filename = data['filename']
    prompt_template = data.get('prompt_template')
    
    # 解析文件
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    corpus_list = file_service.parse_corpus_file(filepath, 'question')
    
    # 识别联网检索
    results = network_search_service.identify_network_search_in_corpus(
        corpus_list, prompt_template
    )
    
    # 获取分析报告
    report = network_search_service.generate_network_search_report(results)
    
    logger.info(f"联网检索识别完成: {filename}")
    
    return jsonify({
        'success': True,
        'results': results,
        'report': report
    })

@app.route('/api/evaluate-qa', methods=['POST'])
def evaluate_qa():
    """评测QA对"""
    data = request.json
    
    if 'filename' not in data:
        return jsonify({'error': '缺少文件名'}), 400
    
    filename = data['filename']
    prompt_template = data.get('prompt_template')
    
    # 解析文件
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    corpus_list = file_service.parse_corpus_file(filepath, 'qa')
    
    # 执行评测
    results = evaluation_service.evaluate_qa_corpus(
        corpus_list, prompt_template
    )
    
    # 获取统计信息
    stats = evaluation_service.get_evaluation_statistics(results)
    
    # 识别无法打分的答案
    unscorable = evaluation_service.identify_unscorable_answers(results)
    
    logger.info(f"QA评测完成: {filename}")
    
    return jsonify({
        'success': True,
        'results': results,
        'statistics': stats,
        'unscorable_count': len(unscorable)
    })

@app.route('/api/prompts', methods=['GET', 'POST'])
def manage_prompts():
    """管理Prompt模板"""
    if request.method == 'GET':
        category = request.args.get('category')
        prompts = prompt_manager.list_prompts(category)
        return jsonify(prompts)
    else:
        # 更新或添加Prompt
        data = request.json
        category = data.get('category')
        prompt_name = data.get('prompt_name')
        template = data.get('template')
        name = data.get('name')
        description = data.get('description')
        
        if prompt_manager.set_prompt(category, prompt_name, template, name, description):
            prompt_manager.save_prompts()
            return jsonify({'success': True, 'message': 'Prompt模板已更新'})
        else:
            return jsonify({'error': '更新Prompt模板失败'}), 400

@app.route('/api/prompts/<category>/<prompt_name>', methods=['DELETE'])
def delete_prompt(category, prompt_name):
    """删除Prompt模板"""
    if prompt_manager.delete_prompt(category, prompt_name):
        prompt_manager.save_prompts()
        return jsonify({'success': True, 'message': 'Prompt模板已删除'})
    else:
        return jsonify({'error': '删除Prompt模板失败'}), 400

@app.route('/api/export-results', methods=['POST'])
def export_results():
    """导出结果"""
    data = request.json
    
    if 'results' not in data:
        return jsonify({'error': '缺少结果数据'}), 400
    
    if 'export_type' not in data:
        return jsonify({'error': '缺少导出类型'}), 400
    
    results = data['results']
    export_type = data['export_type']
    
    # 生成导出文件
    output_file = f"data/export_{export_type}_{os.urandom(8).hex()}.csv"
    
    try:
        if export_type == 'network_search':
            network_search_service.export_network_search_results(results, output_file)
        elif export_type == 'evaluation':
            evaluation_service.export_evaluation_results(results, output_file)
        else:
            return jsonify({'error': '不支持的导出类型'}), 400
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'message': '结果已导出'
        })
    except Exception as e:
        logger.error(f"导出结果失败: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({'error': '下载失败'}), 404

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    logger.info("启动语料评测平台...")
    app.run(host='0.0.0.0', port=5000, debug=True)
