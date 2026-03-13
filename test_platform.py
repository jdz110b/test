#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语料评测平台 - 测试脚本
"""

import sys
import os
import unittest
import tempfile
import json
from io import StringIO

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_parser import FileParser, CSVParser, TXTParser, QuestionCorpusParser, QACorpusParser
from services.file_service import FileService
from services.llm_service import LLMService
from services.classification_service import ClassificationService
from services.answer_generation_service import AnswerGenerationService
from services.network_search_service import NetworkSearchService
from services.evaluation_service import EvaluationService
from utils.prompt_manager import PromptManager


class TestFileParser(unittest.TestCase):
    """测试文件解析器"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_csv_parser(self):
        """测试CSV解析器"""
        # 创建测试CSV文件
        csv_file = os.path.join(self.temp_dir, 'test.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('question,answer\n')
            f.write('什么是人工智能？,人工智能是计算机科学的一个分支\n')
            f.write('什么是机器学习？,机器学习是人工智能的一个子领域\n')
        
        parser = CSVParser(csv_file)
        results = parser.parse()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['question'], '什么是人工智能？')
        self.assertEqual(results[0]['answer'], '人工智能是计算机科学的一个分支')
    
    def test_txt_parser(self):
        """测试TXT解析器"""
        # 创建测试TXT文件
        txt_file = os.path.join(self.temp_dir, 'test.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write('什么是人工智能？\n')
            f.write('什么是机器学习？\n')
        
        parser = TXTParser(txt_file)
        results = parser.parse()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['content'], '什么是人工智能？')
        self.assertEqual(results[1]['content'], '什么是机器学习？')
    
    def test_question_corpus_parser(self):
        """测试Question语料解析器"""
        # 创建测试CSV文件
        csv_file = os.path.join(self.temp_dir, 'questions.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('question\n')
            f.write('什么是人工智能？\n')
            f.write('什么是机器学习？\n')
        
        parser = QuestionCorpusParser(csv_file)
        results = parser.parse()
        
        self.assertEqual(len(results), 2)
        self.assertIn('question', results[0])
        self.assertEqual(results[0]['question'], '什么是人工智能？')
    
    def test_qa_corpus_parser(self):
        """测试QA对语料解析器"""
        # 创建测试CSV文件
        csv_file = os.path.join(self.temp_dir, 'qa.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('question,answer\n')
            f.write('什么是人工智能？,人工智能是计算机科学的一个分支\n')
            f.write('什么是机器学习？,机器学习是人工智能的一个子领域\n')
        
        parser = QACorpusParser(csv_file)
        results = parser.parse()
        
        self.assertEqual(len(results), 2)
        self.assertIn('question', results[0])
        self.assertIn('answer', results[0])


class TestPromptManager(unittest.TestCase):
    """测试Prompt管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.prompt_manager = PromptManager(self.temp_file.name)
    
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
    
    def test_get_prompt(self):
        """测试获取Prompt"""
        prompt = self.prompt_manager.get_prompt('classification', 'objective_subjective')
        self.assertIsNotNone(prompt)
        self.assertIn('question', prompt)
    
    def test_set_prompt(self):
        """测试设置Prompt"""
        result = self.prompt_manager.set_prompt(
            'test_category',
            'test_prompt',
            '测试问题：{question}',
            '测试Prompt',
            '这是一个测试'
        )
        self.assertTrue(result)
        
        prompt = self.prompt_manager.get_prompt('test_category', 'test_prompt')
        self.assertEqual(prompt, '测试问题：{question}')
    
    def test_format_prompt(self):
        """测试格式化Prompt"""
        formatted = self.prompt_manager.format_prompt(
            'classification',
            'objective_subjective',
            question='什么是人工智能？'
        )
        self.assertIsNotNone(formatted)
        self.assertIn('什么是人工智能？', formatted)


class TestLLMService(unittest.TestCase):
    """测试大模型服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'timeout': 30,
            'max_retries': 3
        }
        self.llm_service = LLMService(self.config)
    
    def test_extract_score(self):
        """测试分数提取"""
        # 测试各种分数格式
        test_cases = [
            ('分数：85分', 85),
            ('score: 90', 90),
            ('95/100', 95),
            ('给出分数：80分', 80),
            ('无法打分', 0)
        ]
        
        for text, expected_score in test_cases:
            score = self.llm_service._extract_score(text)
            self.assertEqual(score, expected_score, f"Failed for text: {text}")


class TestClassificationService(unittest.TestCase):
    """测试分类服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'timeout': 30,
            'max_retries': 3
        }
        self.llm_service = LLMService(self.config)
        self.classification_service = ClassificationService(self.llm_service)
    
    def test_classify_question(self):
        """测试Question分类"""
        # 这里只是测试方法调用，实际需要mock大模型调用
        question = "什么是人工智能？"
        result = self.classification_service.classify_question(
            question, 'objective_subjective'
        )
        
        # 验证返回结构
        self.assertIn('question', result)
        self.assertIn('classification_type', result)
        self.assertIn('result', result)


class TestAnswerGenerationService(unittest.TestCase):
    """测试答案生成服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'timeout': 30,
            'max_retries': 3
        }
        self.llm_service = LLMService(self.config)
        self.answer_generation_service = AnswerGenerationService(self.llm_service)
    
    def test_generate_answer(self):
        """测试答案生成"""
        question = "什么是人工智能？"
        result = self.answer_generation_service.generate_answer(question)
        
        # 验证返回结构
        self.assertIn('question', result)
        self.assertIn('answer', result)
        self.assertIn('success', result)


class TestNetworkSearchService(unittest.TestCase):
    """测试联网知识检索服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'timeout': 30,
            'max_retries': 3
        }
        self.llm_service = LLMService(self.config)
        self.network_search_service = NetworkSearchService(self.llm_service)
    
    def test_identify_network_search_question(self):
        """测试联网知识检索识别"""
        question = "2024年最新的AI技术发展如何？"
        result = self.network_search_service.identify_network_search_question(question)
        
        # 验证返回结构
        self.assertIn('question', result)
        self.assertIn('needs_network_search', result)
        self.assertIn('success', result)


class TestEvaluationService(unittest.TestCase):
    """测试评测服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'timeout': 30,
            'max_retries': 3
        }
        self.llm_service = LLMService(self.config)
        self.evaluation_service = EvaluationService(self.llm_service)
    
    def test_score_answer(self):
        """测试Answer打分"""
        question = "什么是人工智能？"
        reference_answer = "人工智能是计算机科学的一个分支"
        student_answer = "人工智能是计算机科学的一个分支"
        
        result = self.evaluation_service.score_answer(
            question, reference_answer, student_answer
        )
        
        # 验证返回结构
        self.assertIn('question', result)
        self.assertIn('score', result)
        self.assertIn('comment', result)
        self.assertIn('can_score', result)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestFileParser))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptManager))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMService))
    suite.addTests(loader.loadTestsFromTestCase(TestClassificationService))
    suite.addTests(loader.loadTestsFromTestCase(TestAnswerGenerationService))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestEvaluationService))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
