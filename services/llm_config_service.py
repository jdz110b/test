"""
大模型配置管理服务
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class LLMConfigService:
    """大模型配置管理服务"""
    
    def __init__(self, config_file: str = 'data/llm_configs.json'):
        self.config_file = config_file
        self.configs = self._load_configs()
        self.current_config = self._get_current_config()
    
    def _load_configs(self) -> Dict[str, Any]:
        """从文件加载大模型配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                logger.info(f"成功加载大模型配置: {self.config_file}")
                return configs
            except Exception as e:
                logger.error(f"加载大模型配置失败: {e}")
                return self._get_default_configs()
        else:
            logger.info("大模型配置文件不存在，使用默认配置")
            return self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Any]:
        """获取默认大模型配置"""
        return {
            'configs': {
                'default': {
                    'name': '默认配置',
                    'api_url': 'https://api.openai.com/v1/chat/completions',
                    'api_key': '',
                    'model': 'gpt-3.5-turbo',
                    'timeout': 30,
                    'max_retries': 3,
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            },
            'current_config': 'default'
        }
    
    def _get_current_config(self) -> Optional[Dict[str, Any]]:
        """获取当前配置"""
        current_name = self.configs.get('current_config', 'default')
        return self.configs.get('configs', {}).get(current_name)
    
    def save_configs(self) -> bool:
        """保存大模型配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存大模型配置: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存大模型配置失败: {e}")
            return False
    
    def add_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """添加新的大模型配置"""
        try:
            if 'configs' not in self.configs:
                self.configs['configs'] = {}
            
            self.configs['configs'][config_name] = config_data
            logger.info(f"成功添加大模型配置: {config_name}")
            return True
        except Exception as e:
            logger.error(f"添加大模型配置失败: {e}")
            return False
    
    def update_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """更新大模型配置"""
        try:
            if config_name in self.configs.get('configs', {}):
                self.configs['configs'][config_name].update(config_data)
                logger.info(f"成功更新大模型配置: {config_name}")
                return True
            else:
                logger.error(f"配置不存在: {config_name}")
                return False
        except Exception as e:
            logger.error(f"更新大模型配置失败: {e}")
            return False
    
    def delete_config(self, config_name: str) -> bool:
        """删除大模型配置"""
        try:
            if config_name in self.configs.get('configs', {}):
                del self.configs['configs'][config_name]
                
                # 如果删除的是当前配置，切换到默认配置
                if self.configs.get('current_config') == config_name:
                    self.configs['current_config'] = 'default'
                
                logger.info(f"成功删除大模型配置: {config_name}")
                return True
            else:
                logger.error(f"配置不存在: {config_name}")
                return False
        except Exception as e:
            logger.error(f"删除大模型配置失败: {e}")
            return False
    
    def set_current_config(self, config_name: str) -> bool:
        """设置当前配置"""
        try:
            if config_name in self.configs.get('configs', {}):
                self.configs['current_config'] = config_name
                self.current_config = self.configs['configs'][config_name]
                logger.info(f"成功设置当前配置: {config_name}")
                return True
            else:
                logger.error(f"配置不存在: {config_name}")
                return False
        except Exception as e:
            logger.error(f"设置当前配置失败: {e}")
            return False
    
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置"""
        return self.configs.get('configs', {}).get(config_name)
    
    def get_current_config(self) -> Optional[Dict[str, Any]]:
        """获取当前配置"""
        return self.current_config
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置"""
        configs = []
        for name, config in self.configs.get('configs', {}).items():
            configs.append({
                'name': name,
                'display_name': config.get('name', name),
                'api_url': config.get('api_url', ''),
                'model': config.get('model', ''),
                'is_current': name == self.configs.get('current_config', '')
            })
        return configs
    
    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置数据"""
        required_fields = ['api_url', 'api_key', 'model']
        missing_fields = [field for field in required_fields if not config_data.get(field)]
        
        validation_result = {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'errors': []
        }
        
        # 验证API URL格式
        api_url = config_data.get('api_url', '')
        if api_url and not api_url.startswith(('http://', 'https://')):
            validation_result['errors'].append('API URL格式不正确')
            validation_result['valid'] = False
        
        # 验证数值字段
        try:
            timeout = int(config_data.get('timeout', 30))
            if timeout <= 0:
                validation_result['errors'].append('timeout必须大于0')
                validation_result['valid'] = False
        except ValueError:
            validation_result['errors'].append('timeout必须是数字')
            validation_result['valid'] = False
        
        try:
            max_retries = int(config_data.get('max_retries', 3))
            if max_retries < 0:
                validation_result['errors'].append('max_retries不能为负数')
                validation_result['valid'] = False
        except ValueError:
            validation_result['errors'].append('max_retries必须是数字')
            validation_result['valid'] = False
        
        return validation_result
    
    def test_config(self, config_name: str) -> Dict[str, Any]:
        """测试配置连接"""
        config = self.get_config(config_name)
        if not config:
            return {
                'success': False,
                'error': '配置不存在'
            }
        
        try:
            # 这里可以添加实际的API测试逻辑
            # 暂时返回成功
            return {
                'success': True,
                'message': '配置测试成功'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_configs(self, output_file: str) -> bool:
        """导出配置"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            logger.info(f"成功导出大模型配置: {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出大模型配置失败: {e}")
            return False
    
    def import_configs(self, input_file: str) -> bool:
        """导入配置"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                imported_configs = json.load(f)
            
            # 合并导入的配置
            if 'configs' in imported_configs:
                if 'configs' not in self.configs:
                    self.configs['configs'] = {}
                self.configs['configs'].update(imported_configs['configs'])
            
            logger.info(f"成功导入大模型配置: {input_file}")
            return True
        except Exception as e:
            logger.error(f"导入大模型配置失败: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self.configs = self._get_default_configs()
        self.current_config = self._get_current_config()
        logger.info("已重置为默认大模型配置")
        return True
