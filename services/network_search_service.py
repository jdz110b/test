"""
联网知识检索识别服务
"""

import logging
from typing import List, Dict, Any, Optional
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class NetworkSearchService:
    """联网知识检索识别服务"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def identify_network_search_question(self, question: str,
                                        prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """识别Question是否需要联网知识检索"""
        try:
            result = self.llm_service.classify_question(
                question, 'network_search', prompt_template
            )
            
            needs_network = result == '需要联网'
            
            return {
                'question': question,
                'needs_network_search': needs_network,
                'classification_result': result,
                'success': True
            }
        except Exception as e:
            logger.error(f"联网检索识别失败: {e}")
            return {
                'question': question,
                'needs_network_search': False,
                'classification_result': '识别失败',
                'success': False,
                'error': str(e)
            }
    
    def batch_identify_network_search_questions(self, questions: List[str],
                                               prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量识别Question是否需要联网知识检索"""
        results = []
        for i, question in enumerate(questions):
            logger.info(f"正在识别第 {i+1}/{len(questions)} 个问题的联网检索需求")
            result = self.identify_network_search_question(question, prompt_template)
            results.append(result)
        
        needs_network_count = sum(1 for r in results if r.get('needs_network_search', False))
        logger.info(f"批量联网检索识别完成: {needs_network_count}/{len(questions)} 需要联网")
        
        return results
    
    def identify_network_search_in_corpus(self, corpus_list: List[Dict[str, Any]],
                                         prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """在语料列表中识别需要联网知识检索的Question"""
        results = []
        
        for i, item in enumerate(corpus_list):
            question = item.get('question', '')
            if not question:
                logger.warning(f"第 {i+1} 条记录缺少question字段")
                continue
            
            identification_result = self.identify_network_search_question(question, prompt_template)
            
            results.append({
                'original_data': item,
                'network_search_identification': identification_result
            })
        
        needs_network_count = sum(1 for r in results if r['network_search_identification'].get('needs_network_search', False))
        logger.info(f"语料联网检索识别完成: {needs_network_count}/{len(results)} 需要联网")
        
        return results
    
    def filter_network_search_questions(self, corpus_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出需要联网知识检索的Question"""
        filtered = []
        for item in corpus_list:
            identification = item.get('network_search_identification', {})
            if identification.get('needs_network_search', False):
                filtered.append(item)
        
        logger.info(f"过滤出需要联网检索的问题: {len(filtered)} 个")
        return filtered
    
    def filter_non_network_search_questions(self, corpus_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出不需要联网知识检索的Question"""
        filtered = []
        for item in corpus_list:
            identification = item.get('network_search_identification', {})
            if not identification.get('needs_network_search', False):
                filtered.append(item)
        
        logger.info(f"过滤出不需要联网检索的问题: {len(filtered)} 个")
        return filtered
    
    def analyze_network_search_patterns(self, corpus_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析联网知识检索的模式"""
        total = len(corpus_list)
        needs_network = sum(1 for item in corpus_list 
                          if item.get('network_search_identification', {}).get('needs_network_search', False))
        
        # 分析问题特征
        keywords_analysis = self._analyze_keywords(corpus_list)
        
        return {
            'total_questions': total,
            'needs_network_count': needs_network,
            'needs_network_percentage': f"{(needs_network/total*100):.2f}%" if total > 0 else "0%",
            'keywords_analysis': keywords_analysis
        }
    
    def _analyze_keywords(self, corpus_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析关键词模式"""
        network_questions = []
        non_network_questions = []
        
        for item in corpus_list:
            question = item.get('original_data', {}).get('question', '')
            if item.get('network_search_identification', {}).get('needs_network_search', False):
                network_questions.append(question)
            else:
                non_network_questions.append(question)
        
        # 简单的关键词分析
        network_keywords = self._extract_common_keywords(network_questions)
        non_network_keywords = self._extract_common_keywords(non_network_questions)
        
        return {
            'network_search_keywords': network_keywords,
            'non_network_search_keywords': non_network_keywords
        }
    
    def _extract_common_keywords(self, questions: List[str]) -> List[str]:
        """提取常见关键词"""
        import re
        from collections import Counter
        
        # 简单的关键词提取
        all_words = []
        for question in questions:
            # 提取中文和英文单词
            words = re.findall(r'[一-鿿]+|[a-zA-Z]+', question)
            all_words.extend(words)
        
        # 统计词频
        word_counts = Counter(all_words)
        
        # 返回最常见的10个词
        return [word for word, count in word_counts.most_common(10)]
    
    def generate_network_search_report(self, corpus_list: List[Dict[str, Any]]) -> str:
        """生成联网知识检索报告"""
        analysis = self.analyze_network_search_patterns(corpus_list)
        
        report = f"""
联网知识检索识别报告
======================

总问题数: {analysis['total_questions']}
需要联网检索: {analysis['needs_network_count']} ({analysis['needs_network_percentage']})
不需要联网检索: {analysis['total_questions'] - analysis['needs_network_count']}

联网检索常见关键词:
{', '.join(analysis['keywords_analysis']['network_search_keywords'])}

非联网检索常见关键词:
{', '.join(analysis['keywords_analysis']['non_network_search_keywords'])}
"""
        return report
    
    def export_network_search_results(self, corpus_list: List[Dict[str, Any]], 
                                     output_file: str) -> bool:
        """导出联网知识检索结果"""
        try:
            import csv
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(['问题', '是否需要联网检索', '分类结果'])
                
                # 写入数据
                for item in corpus_list:
                    question = item.get('original_data', {}).get('question', '')
                    identification = item.get('network_search_identification', {})
                    
                    writer.writerow([
                        question,
                        '是' if identification.get('needs_network_search', False) else '否',
                        identification.get('classification_result', '')
                    ])
            
            logger.info(f"联网检索结果已导出到: {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出联网检索结果失败: {e}")
            return False
