"""
大模型调用服务
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from config import LLM_CONFIG

logger = logging.getLogger(__name__)


class LLMService:
    """大模型调用服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or LLM_CONFIG
        self.api_url = self.config.get('api_url', '')
        self.api_key = self.config.get('api_key', '')
        self.model = self.config.get('model', 'gpt-3.5-turbo')
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用大模型"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        messages = []
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 提取回复内容
                content = result['choices'][0]['message']['content']
                logger.info(f"大模型调用成功，尝试次数: {attempt + 1}")
                return content
                
            except requests.exceptions.RequestException as e:
                logger.error(f"大模型调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"大模型调用异常: {e}")
                raise
    
    def classify_question(self, question: str, classification_type: str, 
                         prompt_template: Optional[str] = None) -> str:
        """对Question进行分类"""
        if prompt_template:
            prompt = prompt_template.format(question=question)
        else:
            # 默认分类Prompt
            if classification_type == 'objective_subjective':
                prompt = f'请判断以下问题是客观题还是主观题：\n\n问题：{question}\n\n请只回答"客观"或"主观"。'
            elif classification_type == 'difficulty_level':
                prompt = f'请判断以下问题的难度等级：\n\n问题：{question}\n\n请只回答"简单"、"中等"或"困难"。'
            elif classification_type == 'network_search':
                prompt = f'请判断以下问题是否需要联网搜索知识：\n\n问题：{question}\n\n请只回答"需要联网"或"不需要联网"。'
            else:
                prompt = f'请对以下问题进行分类：\n\n问题：{question}\n\n分类类型：{classification_type}'
        
        try:
            result = self.call_llm(prompt)
            # 清理结果，只保留分类标签
            result = result.strip()
            logger.info(f"分类结果: {question[:50]}... -> {result}")
            return result
        except Exception as e:
            logger.error(f"分类失败: {e}")
            return "分类失败"
    
    def generate_answer(self, question: str, prompt_template: Optional[str] = None) -> str:
        """为客观Question生成答案"""
        if prompt_template:
            prompt = prompt_template.format(question=question)
        else:
            prompt = f'请为以下客观问题提供准确答案：\n\n问题：{question}\n\n答案：'
        
        try:
            result = self.call_llm(prompt)
            logger.info(f"答案生成成功: {question[:50]}...")
            return result
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "答案生成失败"
    
    def score_answer(self, question: str, reference_answer: str, 
                    student_answer: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """对Answer进行打分"""
        if prompt_template:
            prompt = prompt_template.format(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer
            )
        else:
            prompt = f'''请对以下答案进行打分（0-100分）：

问题：{question}

参考答案：{reference_answer}

学生答案：{student_answer}

请给出分数和简要评语。'''
        
        try:
            result = self.call_llm(prompt)
            
            # 尝试解析分数
            score = self._extract_score(result)
            
            logger.info(f"打分完成: {question[:50]}... -> {score}")
            
            return {
                'score': score,
                'comment': result,
                'can_score': True
            }
        except Exception as e:
            logger.error(f"打分失败: {e}")
            return {
                'score': 0,
                'comment': f"打分失败: {str(e)}",
                'can_score': False
            }
    
    def _extract_score(self, text: str) -> int:
        """从文本中提取分数"""
        import re
        
        # 尝试匹配数字分数
        patterns = [
            r'(\d+)分',
            r'分数[：:]\s*(\d+)',
            r'score[：:]\s*(\d+)',
            r'(\d{1,3})\s*\/\s*100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                score = int(match.group(1))
                return min(max(score, 0), 100)  # 确保分数在0-100之间
        
        # 如果没有找到分数，返回默认值
        return 0
    
    def batch_classify(self, questions: List[str], classification_type: str,
                      prompt_template: Optional[str] = None) -> List[str]:
        """批量分类Question"""
        results = []
        for question in questions:
            result = self.classify_question(question, classification_type, prompt_template)
            results.append(result)
        return results
    
    def batch_generate_answers(self, questions: List[str], 
                              prompt_template: Optional[str] = None) -> List[str]:
        """批量生成答案"""
        results = []
        for question in questions:
            result = self.generate_answer(question, prompt_template)
            results.append(result)
        return results
    
    def batch_score_answers(self, qa_pairs: List[Dict[str, str]], 
                           prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量打分Answer"""
        results = []
        for qa_pair in qa_pairs:
            result = self.score_answer(
                qa_pair['question'],
                qa_pair['reference_answer'],
                qa_pair['student_answer'],
                prompt_template
            )
            results.append(result)
        return results
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        self.api_url = self.config.get('api_url', '')
        self.api_key = self.config.get('api_key', '')
        self.model = self.config.get('model', 'gpt-3.5-turbo')
        logger.info(f"大模型配置已更新: {self.api_url}, {self.model}")
