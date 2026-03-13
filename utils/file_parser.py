"""
文件解析器 - 支持CSV、TXT等文件格式
"""

import pandas as pd
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FileParser:
    """文件解析器基类"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file_extension = os.path.splitext(filepath)[1].lower()
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析文件，返回语料列表"""
        raise NotImplementedError("子类必须实现parse方法")
    
    def validate(self) -> bool:
        """验证文件格式和内容"""
        if not os.path.exists(self.filepath):
            logger.error(f"文件不存在: {self.filepath}")
            return False
        
        if self.file_extension not in ['.csv', '.txt']:
            logger.error(f"不支持的文件格式: {self.file_extension}")
            return False
        
        return True


class CSVParser(FileParser):
    """CSV文件解析器"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析CSV文件"""
        if not self.validate():
            return []
        
        try:
            # 读取CSV文件
            df = pd.read_csv(self.filepath, encoding='utf-8')
            
            # 转换为字典列表
            corpus_list = df.to_dict('records')
            
            logger.info(f"成功解析CSV文件: {self.filepath}, 共 {len(corpus_list)} 条记录")
            return corpus_list
            
        except Exception as e:
            logger.error(f"解析CSV文件失败: {e}")
            return []


class TXTParser(FileParser):
    """TXT文件解析器"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析TXT文件"""
        if not self.validate():
            return []
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按行分割
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            # 转换为字典列表
            corpus_list = [{'content': line, 'line_number': i+1} 
                          for i, line in enumerate(lines)]
            
            logger.info(f"成功解析TXT文件: {self.filepath}, 共 {len(corpus_list)} 条记录")
            return corpus_list
            
        except Exception as e:
            logger.error(f"解析TXT文件失败: {e}")
            return []


class QuestionCorpusParser(FileParser):
    """Question语料解析器"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析Question语料"""
        if self.file_extension == '.csv':
            parser = CSVParser(self.filepath)
            corpus_list = parser.parse()
            
            # 验证必要的列
            if corpus_list and 'question' not in corpus_list[0]:
                logger.error("CSV文件缺少'question'列")
                return []
            
            return corpus_list
            
        elif self.file_extension == '.txt':
            parser = TXTParser(self.filepath)
            corpus_list = parser.parse()
            
            # 将content字段重命名为question
            for item in corpus_list:
                item['question'] = item.pop('content')
            
            return corpus_list
        
        else:
            logger.error(f"不支持的文件格式: {self.file_extension}")
            return []


class QACorpusParser(FileParser):
    """QA对语料解析器"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """解析QA对语料"""
        if self.file_extension == '.csv':
            parser = CSVParser(self.filepath)
            corpus_list = parser.parse()
            
            # 验证必要的列
            if corpus_list:
                if 'question' not in corpus_list[0] or 'answer' not in corpus_list[0]:
                    logger.error("CSV文件缺少'question'或'answer'列")
                    return []
            
            return corpus_list
            
        elif self.file_extension == '.txt':
            parser = TXTParser(self.filepath)
            corpus_list = parser.parse()
            
            # 尝试解析QA对格式（假设每行是"问题|答案"格式）
            qa_pairs = []
            for item in corpus_list:
                content = item['content']
                if '|' in content:
                    parts = content.split('|', 1)
                    if len(parts) == 2:
                        qa_pairs.append({
                            'question': parts[0].strip(),
                            'answer': parts[1].strip(),
                            'line_number': item['line_number']
                        })
                else:
                    logger.warning(f"无法解析QA对格式: {content}")
            
            logger.info(f"成功解析 {len(qa_pairs)} 对QA")
            return qa_pairs
        
        else:
            logger.error(f"不支持的文件格式: {self.file_extension}")
            return []


def get_parser(corpus_type: str, filepath: str) -> FileParser:
    """根据语料类型获取相应的解析器"""
    parsers = {
        'question': QuestionCorpusParser,
        'qa': QACorpusParser
    }
    
    parser_class = parsers.get(corpus_type)
    if not parser_class:
        raise ValueError(f"不支持的语料类型: {corpus_type}")
    
    return parser_class(filepath)
