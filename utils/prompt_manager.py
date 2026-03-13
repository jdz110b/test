"""
Prompt管理器 - 管理和配置Prompt模板
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PromptManager:
    """Prompt管理器"""
    
    def __init__(self, config_file: str = 'data/prompts.json'):
        self.config_file = config_file
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """从文件加载Prompt配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                logger.info(f"成功加载Prompt配置: {self.config_file}")
                return prompts
            except Exception as e:
                logger.error(f"加载Prompt配置失败: {e}")
                return self._get_default_prompts()
        else:
            logger.info("Prompt配置文件不存在，使用默认配置")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """获取默认Prompt配置"""
        return {
            'classification': {
                'objective_subjective': {
                    'name': '客观/主观分类',
                    'template': '请判断以下问题是客观题还是主观题：\n\n问题：{question}\n\n请只回答"客观"或"主观"。',
                    'description': '判断问题是客观题还是主观题'
                },
                'difficulty_level': {
                    'name': '难度等级分类',
                    'template': '请判断以下问题的难度等级：\n\n问题：{question}\n\n请只回答"简单"、"中等"或"困难"。',
                    'description': '判断问题的难度等级'
                },
                'network_search': {
                    'name': '联网知识检索识别',
                    'template': '请判断以下问题是否需要联网搜索知识：\n\n问题：{question}\n\n请只回答"需要联网"或"不需要联网"。',
                    'description': '判断问题是否需要联网搜索知识'
                }
            },
            'answer_generation': {
                'default': {
                    'name': '默认答案生成',
                    'template': '请为以下客观问题提供准确答案：\n\n问题：{question}\n\n答案：',
                    'description': '为客观问题生成准确答案'
                }
            },
            'answer_scoring': {
                'default': {
                    'name': '默认答案打分',
                    'template': '请对以下答案进行打分（0-100分）：\n\n问题：{question}\n\n参考答案：{reference_answer}\n\n学生答案：{student_answer}\n\n请给出分数和简要评语。',
                    'description': '对答案进行打分和评价'
                }
            }
        }
    
    def save_prompts(self) -> bool:
        """保存Prompt配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存Prompt配置: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存Prompt配置失败: {e}")
            return False
    
    def get_prompt(self, category: str, prompt_name: str) -> Optional[str]:
        """获取指定Prompt模板"""
        try:
            return self.prompts[category][prompt_name]['template']
        except KeyError:
            logger.error(f"Prompt不存在: {category}.{prompt_name}")
            return None
    
    def set_prompt(self, category: str, prompt_name: str, template: str,
                   name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """设置Prompt模板"""
        try:
            if category not in self.prompts:
                self.prompts[category] = {}
            
            self.prompts[category][prompt_name] = {
                'template': template,
                'name': name or prompt_name,
                'description': description or ''
            }
            
            logger.info(f"成功设置Prompt: {category}.{prompt_name}")
            return True
        except Exception as e:
            logger.error(f"设置Prompt失败: {e}")
            return False
    
    def delete_prompt(self, category: str, prompt_name: str) -> bool:
        """删除Prompt模板"""
        try:
            if category in self.prompts and prompt_name in self.prompts[category]:
                del self.prompts[category][prompt_name]
                logger.info(f"成功删除Prompt: {category}.{prompt_name}")
                return True
            else:
                logger.error(f"Prompt不存在: {category}.{prompt_name}")
                return False
        except Exception as e:
            logger.error(f"删除Prompt失败: {e}")
            return False
    
    def list_prompts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """列出Prompt模板"""
        if category:
            return self.prompts.get(category, {})
        return self.prompts
    
    def get_all_prompt_names(self) -> List[str]:
        """获取所有Prompt名称"""
        names = []
        for category, prompts in self.prompts.items():
            for prompt_name, prompt_data in prompts.items():
                names.append(f"{category}.{prompt_name}")
        return names
    
    def format_prompt(self, category: str, prompt_name: str, **kwargs) -> Optional[str]:
        """格式化Prompt模板"""
        template = self.get_prompt(category, prompt_name)
        if template:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                logger.error(f"格式化Prompt失败，缺少参数: {e}")
                return None
        return None
    
    def validate_prompt(self, template: str, required_params: List[str]) -> Dict[str, Any]:
        """验证Prompt模板"""
        import re
        
        # 提取模板中的参数
        params = re.findall(r'\{(\w+)\}', template)
        
        missing_params = [p for p in required_params if p not in params]
        extra_params = [p for p in params if p not in required_params]
        
        return {
            'valid': len(missing_params) == 0,
            'missing_params': missing_params,
            'extra_params': extra_params,
            'all_params': params
        }
    
    def export_prompts(self, output_file: str) -> bool:
        """导出Prompt配置"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=2)
            logger.info(f"成功导出Prompt配置: {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出Prompt配置失败: {e}")
            return False
    
    def import_prompts(self, input_file: str) -> bool:
        """导入Prompt配置"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                imported_prompts = json.load(f)
            
            # 合并导入的Prompt
            for category, prompts in imported_prompts.items():
                if category not in self.prompts:
                    self.prompts[category] = {}
                self.prompts[category].update(prompts)
            
            logger.info(f"成功导入Prompt配置: {input_file}")
            return True
        except Exception as e:
            logger.error(f"导入Prompt配置失败: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """重置为默认Prompt配置"""
        self.prompts = self._get_default_prompts()
        logger.info("已重置为默认Prompt配置")
        return True
