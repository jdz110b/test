"""
文件处理服务
"""

import os
import logging
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from utils.file_parser import get_parser

logger = logging.getLogger(__name__)


class FileService:
    """文件处理服务"""
    
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_uploaded_file(self, file, filename: str) -> str:
        """保存上传的文件"""
        secure_name = secure_filename(filename)
        filepath = os.path.join(self.upload_folder, secure_name)
        file.save(filepath)
        logger.info(f"文件保存成功: {filepath}")
        return filepath
    
    def parse_corpus_file(self, filepath: str, corpus_type: str) -> List[Dict[str, Any]]:
        """解析语料文件"""
        try:
            parser = get_parser(corpus_type, filepath)
            corpus_list = parser.parse()
            logger.info(f"成功解析语料文件: {filepath}, 类型: {corpus_type}, 数量: {len(corpus_list)}")
            return corpus_list
        except Exception as e:
            logger.error(f"解析语料文件失败: {e}")
            return []
    
    def validate_corpus(self, corpus_list: List[Dict[str, Any]], corpus_type: str) -> tuple[bool, str]:
        """验证语料数据"""
        if not corpus_list:
            return False, "语料数据为空"
        
        if corpus_type == 'question':
            # 验证Question语料
            for i, item in enumerate(corpus_list):
                if 'question' not in item or not item['question'].strip():
                    return False, f"第 {i+1} 条记录缺少question字段或question为空"
        
        elif corpus_type == 'qa':
            # 验证QA对语料
            for i, item in enumerate(corpus_list):
                if 'question' not in item or not item['question'].strip():
                    return False, f"第 {i+1} 条记录缺少question字段或question为空"
                if 'answer' not in item or not item['answer'].strip():
                    return False, f"第 {i+1} 条记录缺少answer字段或answer为空"
        
        return True, "验证通过"
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """获取文件信息"""
        if not os.path.exists(filepath):
            return {}
        
        file_stat = os.stat(filepath)
        return {
            'filename': os.path.basename(filepath),
            'size': file_stat.st_size,
            'created_time': file_stat.st_ctime,
            'modified_time': file_stat.st_mtime,
            'extension': os.path.splitext(filepath)[1].lower()
        }
    
    def delete_file(self, filepath: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"文件删除成功: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """列出所有上传的文件"""
        files = []
        try:
            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                if os.path.isfile(filepath):
                    file_info = self.get_file_info(filepath)
                    files.append(file_info)
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
        
        return files
