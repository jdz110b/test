"""
评测服务 - QA对语料Answer打分
"""

import logging
from typing import List, Dict, Any, Optional
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class EvaluationService:
    """评测服务"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def score_answer(self, question: str, reference_answer: str, 
                    student_answer: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """对单个Answer进行打分"""
        try:
            result = self.llm_service.score_answer(
                question, reference_answer, student_answer, prompt_template
            )
            
            return {
                'question': question,
                'reference_answer': reference_answer,
                'student_answer': student_answer,
                'score': result['score'],
                'comment': result['comment'],
                'can_score': result['can_score'],
                'success': True
            }
        except Exception as e:
            logger.error(f"Answer打分失败: {e}")
            return {
                'question': question,
                'reference_answer': reference_answer,
                'student_answer': student_answer,
                'score': 0,
                'comment': f"打分失败: {str(e)}",
                'can_score': False,
                'success': False,
                'error': str(e)
            }
    
    def batch_score_answers(self, qa_pairs: List[Dict[str, str]],
                           prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """批量打分Answer"""
        results = []
        for i, qa_pair in enumerate(qa_pairs):
            question = qa_pair.get('question', '')
            reference_answer = qa_pair.get('reference_answer', '')
            student_answer = qa_pair.get('student_answer', '')
            
            if not all([question, reference_answer, student_answer]):
                logger.warning(f"第 {i+1} 条QA对缺少必要字段")
                continue
            
            logger.info(f"正在打分第 {i+1}/{len(qa_pairs)} 个答案")
            result = self.score_answer(question, reference_answer, student_answer, prompt_template)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        can_score_count = sum(1 for r in results if r['can_score'])
        logger.info(f"批量打分完成: {success_count}/{len(results)} 成功, {can_score_count} 可打分")
        
        return results
    
    def evaluate_qa_corpus(self, corpus_list: List[Dict[str, Any]],
                          prompt_template: Optional[str] = None) -> List[Dict[str, Any]]:
        """评测QA对语料"""
        results = []
        
        for i, item in enumerate(corpus_list):
            question = item.get('question', '')
            reference_answer = item.get('answer', '')
            
            if not all([question, reference_answer]):
                logger.warning(f"第 {i+1} 条记录缺少必要字段")
                continue
            
            # 假设学生答案就是参考答案（实际应用中可能需要另外提供）
            student_answer = reference_answer
            
            logger.info(f"正在评测第 {i+1}/{len(corpus_list)} 个QA对")
            evaluation_result = self.score_answer(
                question, reference_answer, student_answer, prompt_template
            )
            
            results.append({
                'original_data': item,
                'evaluation': evaluation_result
            })
        
        logger.info(f"QA对语料评测完成: {len(results)} 条记录")
        return results
    
    def identify_unscorable_answers(self, evaluation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别无法打分的Answer"""
        unscorable = []
        for result in evaluation_results:
            evaluation = result.get('evaluation', {})
            if not evaluation.get('can_score', False):
                unscorable.append(result)
        
        logger.info(f"识别出 {len(unscorable)} 个无法打分的Answer")
        return unscorable
    
    def get_evaluation_statistics(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取评测统计信息"""
        total = len(evaluation_results)
        success = sum(1 for r in evaluation_results if r.get('evaluation', {}).get('success', False))
        can_score = sum(1 for r in evaluation_results if r.get('evaluation', {}).get('can_score', False))
        cannot_score = total - can_score
        
        # 计算平均分
        scores = [r['evaluation']['score'] for r in evaluation_results 
                 if r.get('evaluation', {}).get('can_score', False)]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 分数分布
        score_distribution = {
            '优秀 (90-100)': sum(1 for s in scores if 90 <= s <= 100),
            '良好 (80-89)': sum(1 for s in scores if 80 <= s <= 89),
            '中等 (70-79)': sum(1 for s in scores if 70 <= s <= 79),
            '及格 (60-69)': sum(1 for s in scores if 60 <= s <= 69),
            '不及格 (0-59)': sum(1 for s in scores if 0 <= s <= 59)
        }
        
        return {
            'total': total,
            'success': success,
            'can_score': can_score,
            'cannot_score': cannot_score,
            'success_rate': f"{(success/total*100):.2f}%" if total > 0 else "0%",
            'scorable_rate': f"{(can_score/total*100):.2f}%" if total > 0 else "0%",
            'average_score': f"{avg_score:.2f}",
            'score_distribution': score_distribution
        }
    
    def generate_evaluation_report(self, evaluation_results: List[Dict[str, Any]]) -> str:
        """生成评测报告"""
        stats = self.get_evaluation_statistics(evaluation_results)
        
        report = f"""
QA对语料评测报告
================

总评测数: {stats['total']}
成功评测: {stats['success']}
可打分数: {stats['can_score']}
不可打分数: {stats['cannot_score']}

成功率: {stats['success_rate']}
可打分率: {stats['scorable_rate']}
平均分: {stats['average_score']}

分数分布:
"""
        for level, count in stats['score_distribution'].items():
            report += f"  {level}: {count}\n"
        
        return report
    
    def export_evaluation_results(self, evaluation_results: List[Dict[str, Any]], 
                                 output_file: str) -> bool:
        """导出评测结果"""
        try:
            import csv
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(['问题', '参考答案', '学生答案', '分数', '评语', '可打分'])
                
                # 写入数据
                for result in evaluation_results:
                    original_data = result.get('original_data', {})
                    evaluation = result.get('evaluation', {})
                    
                    writer.writerow([
                        original_data.get('question', ''),
                        original_data.get('answer', ''),
                        original_data.get('answer', ''),  # 假设学生答案就是参考答案
                        evaluation.get('score', 0),
                        evaluation.get('comment', ''),
                        '是' if evaluation.get('can_score', False) else '否'
                    ])
            
            logger.info(f"评测结果已导出到: {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出评测结果失败: {e}")
            return False
    
    def compare_answers(self, reference_answer: str, student_answer: str) -> Dict[str, Any]:
        """比较参考答案和学生答案"""
        comparison_prompt = f'''请比较以下两个答案的相似度：

参考答案：{reference_answer}

学生答案：{student_answer}

请评估：
1. 内容相似度（0-100分）
2. 关键点覆盖率
3. 主要差异

请给出详细分析。'''
        
        try:
            result = self.llm_service.call_llm(comparison_prompt)
            
            return {
                'reference_answer': reference_answer,
                'student_answer': student_answer,
                'comparison_result': result,
                'success': True
            }
        except Exception as e:
            logger.error(f"答案比较失败: {e}")
            return {
                'reference_answer': reference_answer,
                'student_answer': student_answer,
                'comparison_result': f"比较失败: {str(e)}",
                'success': False
            }
