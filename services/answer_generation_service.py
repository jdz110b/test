"""
答案生成服务 - 为客观Question生成答案
"""

import logging
from typing import List, Dict, Any, Optional
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AnswerGenerationService:
    """答案生成服务"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def generate_answer(self, question: str, 
                       prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """为单个Question生成答案"""
        try:
            answer = self.llm_service.generate_answer(question, prompt_template)
            
            return {
                'question': question,
                'answer': answer,
                'success': True
            }
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return {
                'question': question,
                'answer': '答案生成失败',
                'success': False,
                'error': str(e)
            }
    
    def batch_generate_answers(self, questions: List[str],
                              prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量生成答案"""
        results = []
        for i, question in enumerate(questions):
            logger.info(f"正在生成第 {i+1}/{len(questions)} 个问题的答案")
            result = self.generate_answer(question, prompt_template)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"批量答案生成完成: {success_count}/{len(questions)} 成功")
        
        return results
    
    def generate_answers_for_objective_questions(self, corpus_list: List[Dict[str, Any]],
                                                 prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """为客观Question生成答案"""
        results = []
        
        for i, item in enumerate(corpus_list):
            question = item.get('question', '')
            if not question:
                logger.warning(f"第 {i+1} 条记录缺少question字段")
                continue
            
            # 检查是否为客观题
            classifications = item.get('classifications', {})
            objective_result = classifications.get('objective_subjective', {}).get('result', '')
            
            if objective_result == '客观':
                logger.info(f"为客观题生成答案: {question[:50]}...")
                answer_result = self.generate_answer(question, prompt_template)
                results.append({
                    'original_data': item,
                    'answer_generation': answer_result
                })
            else:
                logger.info(f"跳过主观题: {question[:50]}...")
                results.append({
                    'original_data': item,
                    'answer_generation': {
                        'question': question,
                        'answer': '主观题，无需生成答案',
                        'success': True,
                        'skipped': True
                    }
                })
        
        logger.info(f"客观题答案生成完成: {len(results)} 条记录")
        return results
    
    def generate_comprehensive_answers(self, corpus_list: List[Dict[str, Any]],
                                      prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """综合答案生成（包含分类和答案生成）"""
        results = []
        
        for i, item in enumerate(corpus_list):
            question = item.get('question', '')
            if not question:
                logger.warning(f"第 {i+1} 条记录缺少question字段")
                continue
            
            result_item = {
                'original_data': item,
                'classifications': item.get('classifications', {}),
                'answer_generation': None
            }
            
            # 检查是否为客观题
            classifications = item.get('classifications', {})
            objective_result = classifications.get('objective_subjective', {}).get('result', '')
            
            if objective_result == '客观':
                logger.info(f"为客观题生成答案: {question[:50]}...")
                answer_result = self.generate_answer(question, prompt_template)
                result_item['answer_generation'] = answer_result
            else:
                logger.info(f"跳过主观题: {question[:50]}...")
                result_item['answer_generation'] = {
                    'question': question,
                    'answer': '主观题，无需生成答案',
                    'success': True,
                    'skipped': True
                }
            
            results.append(result_item)
        
        logger.info(f"综合答案生成完成: {len(results)} 条记录")
        return results
    
    def validate_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """验证答案质量"""
        validation_prompt = f'''请验证以下答案的质量：

问题：{question}

答案：{answer}

请评估：
1. 答案是否准确？
2. 答案是否完整？
3. 答案是否清晰？

请给出评分（0-100分）和简要评语。'''
        
        try:
            result = self.llm_service.call_llm(validation_prompt)
            score = self.llm_service._extract_score(result)
            
            return {
                'question': question,
                'answer': answer,
                'validation_score': score,
                'validation_comment': result,
                'is_valid': score >= 60
            }
        except Exception as e:
            logger.error(f"答案验证失败: {e}")
            return {
                'question': question,
                'answer': answer,
                'validation_score': 0,
                'validation_comment': f"验证失败: {str(e)}",
                'is_valid': False
            }
    
    def get_answer_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取答案生成统计信息"""
        total = len(results)
        success = sum(1 for r in results if r.get('success', False))
        failed = total - success
        skipped = sum(1 for r in results if r.get('skipped', False))
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'skipped': skipped,
            'success_rate': f"{(success/total*100):.2f}%" if total > 0 else "0%"
        }
