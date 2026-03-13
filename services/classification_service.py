"""
分类服务 - Question语料分类
"""

import logging
from typing import List, Dict, Any, Optional
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ClassificationService:
    """分类服务"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def classify_question(self, question: str, classification_type: str,
                         prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """对单个Question进行分类"""
        try:
            result = self.llm_service.classify_question(
                question, classification_type, prompt_template
            )
            
            return {
                'question': question,
                'classification_type': classification_type,
                'result': result,
                'success': True
            }
        except Exception as e:
            logger.error(f"分类失败: {e}")
            return {
                'question': question,
                'classification_type': classification_type,
                'result': '分类失败',
                'success': False,
                'error': str(e)
            }
    
    def batch_classify_questions(self, questions: List[str], 
                                classification_type: str,
                                prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量分类Question"""
        results = []
        for i, question in enumerate(questions):
            logger.info(f"正在分类第 {i+1}/{len(questions)} 个问题")
            result = self.classify_question(question, classification_type, prompt_template)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"批量分类完成: {success_count}/{len(questions)} 成功")
        
        return results
    
    def classify_corpus(self, corpus_list: List[Dict[str, Any]], 
                       classification_types: List[str],
                       prompt_templates: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """对语料列表进行多种分类"""
        results = []
        
        for i, item in enumerate(corpus_list):
            question = item.get('question', '')
            if not question:
                logger.warning(f"第 {i+1} 条记录缺少question字段")
                continue
            
            result_item = {
                'original_data': item,
                'classifications': {}
            }
            
            # 对每种分类类型进行分类
            for classification_type in classification_types:
                prompt_template = prompt_templates.get(classification_type) if prompt_templates else None
                classification_result = self.classify_question(
                    question, classification_type, prompt_template
                )
                result_item['classifications'][classification_type] = classification_result
            
            results.append(result_item)
        
        logger.info(f"语料分类完成: {len(results)} 条记录")
        return results
    
    def classify_objective_subjective(self, question: str) -> str:
        """分类客观/主观"""
        return self.llm_service.classify_question(
            question, 'objective_subjective'
        )
    
    def classify_difficulty_level(self, question: str) -> str:
        """分类难度等级"""
        return self.llm_service.classify_question(
            question, 'difficulty_level'
        )
    
    def classify_network_search(self, question: str) -> str:
        """分类是否需要联网搜索"""
        return self.llm_service.classify_question(
            question, 'network_search'
        )
    
    def comprehensive_classify(self, question: str) -> Dict[str, str]:
        """综合分类（包含所有分类类型）"""
        return {
            'objective_subjective': self.classify_objective_subjective(question),
            'difficulty_level': self.classify_difficulty_level(question),
            'network_search': self.classify_network_search(question)
        }
    
    def filter_by_classification(self, corpus_list: List[Dict[str, Any]], 
                                classification_type: str,
                                filter_value: str) -> List[Dict[str, Any]]:
        """根据分类结果过滤语料"""
        filtered = []
        for item in corpus_list:
            classifications = item.get('classifications', {})
            if classification_type in classifications:
                result = classifications[classification_type].get('result', '')
                if result == filter_value:
                    filtered.append(item)
        
        logger.info(f"过滤结果: {len(filtered)}/{len(corpus_list)} 条记录")
        return filtered
    
    def get_classification_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取分类统计信息"""
        stats = {}
        
        for result in results:
            classifications = result.get('classifications', {})
            for classification_type, classification_result in classifications.items():
                if classification_type not in stats:
                    stats[classification_type] = {}
                
                result_value = classification_result.get('result', '分类失败')
                stats[classification_type][result_value] = stats[classification_type].get(result_value, 0) + 1
        
        return stats
