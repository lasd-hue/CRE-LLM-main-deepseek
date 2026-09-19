import json
import re

class DebugDynamicPromptEngine:
    def __init__(self):
        self.templates = self._init_templates()
    
    def _init_templates(self):
        """初始化模板 - 与主代码相同"""
        return {
            "financial": {
                "expert": "金融专家提示",
                "qa": "金融问答提示", 
                "simple": "金融简单提示"
            },
            "literary": {
                "expert": "文学专家提示",
                "descriptive": "文学描述提示",
                "simple": "文学简单提示"
            }
        }
    
    def extract_original_text(self, input_text):
        match = re.match(r'^(.*?)\s*\(\[.*?\]', input_text)
        if match:
            return match.group(1).strip()
        return input_text
    
    def is_valid_entity(self, entity):
        invalid_patterns = [
            r'.*<.*>.*',
            r'.*\d+岁.*', 
            r'.*几年.*',
            r'.*没有.*',
            r'^.{1,2}$'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, entity):
                print(f"  实体 '{entity}' 被模式 '{pattern}' 拒绝")
                return False
        
        if not re.search(r'[\u4e00-\u9fff]', entity):
            print(f"  实体 '{entity}' 不包含中文字符")
            return False
            
        print(f"  实体 '{entity}' 有效")
        return True
    
    def extract_entities_from_input(self, input_text):
        entity_pattern = r'\(\[(.*?)\],\?,\[(.*?)\]\)'
        match = re.search(entity_pattern, input_text)
        if match:
            entity1, entity2 = match.group(1), match.group(2)
            print(f"  从input提取到实体: '{entity1}', '{entity2}'")
            
            if self.is_valid_entity(entity1) and self.is_valid_entity(entity2):
                return entity1, entity2
            else:
                print(f"  实体验证失败")
        
        return None, None
    
    def analyze_complexity(self, text):
        length_score = min(len(text) / 60, 1.0)
        comma_count = text.count('，')
        period_count = text.count('。') 
        structure_score = min((comma_count + period_count) / 3, 1.0)
        
        complex_words = ['虽然', '但是', '然而', '因此', '因为', '所以', '不仅', '而且']
        vocab_score = sum(1 for word in complex_words if word in text) / len(complex_words)
        
        total_score = (length_score * 0.5 + structure_score * 0.3 + vocab_score * 0.2)
        
        complexity = "high" if total_score > 0.6 else "medium" if total_score > 0.3 else "low"
        print(f"  文本复杂度: {complexity} (得分: {total_score:.2f})")
        return complexity
    
    def debug_generate_prompt(self, input_text, dataset_type="FinRE"):
        print(f"\n=== 调试: {input_text} ===")
        
        original_text = self.extract_original_text(input_text)
        print(f"  原始文本: '{original_text}'")
        
        entity1, entity2 = self.extract_entities_from_input(input_text)
        
        if not entity1 or not entity2:
            print("  → 使用原始指令（实体提取失败）")
            return "请根据给定句子和实体抽取其关系"
        
        domain = "financial" if dataset_type == "FinRE" else "literary"
        print(f"  领域: {domain}")
        
        complexity = self.analyze_complexity(original_text)
        
        # 模板选择逻辑
        if domain == "financial":
            if complexity == "high":
                template_type = "expert"
            elif complexity == "medium": 
                template_type = "qa"
            else:
                template_type = "simple"
        else:  # literary
            if complexity == "high":
                template_type = "expert"
            elif complexity == "medium":
                template_type = "descriptive" 
            else:
                template_type = "simple"
        
        print(f"  → 使用模板: {template_type}")
        return f"[{template_type}提示]"

def debug_sample_data():
    """调试你的样本数据"""
    engine = DebugDynamicPromptEngine()
    
    samples = [
        # FinRE 样本
        ("[东方航空]AH股临时停牌传将与[上航]合并 ([东方航空],?,[上航])", "FinRE"),
        ("[东方航空]AH股临时停牌传将与[上航]合并 ([上航],?,[东方航空])", "FinRE"), 
        ("目前候审的调味品公司还包括[江苏井神盐化]、[安记食品]、火锅底料等细分领域具有领头羊优势。 ([江苏井神盐化],?,[安记食品])", "FinRE"),
        
        # SanWen 样本
        ("“[幽兰]在[山谷]，本自无人识。 ([幽兰],?,[山谷])", "SanWen"),
        ("穷人的孩子早当家，[母亲]<N>岁时[姥姥]去世了 ([母亲],?,[姥姥])", "SanWen"),
        ("穷人的孩子早当家，[母亲]<N>岁时姥姥去世了 ([母亲],?,[母亲<N>岁时])", "SanWen"),
    ]
    
    for input_text, dataset_type in samples:
        prompt = engine.debug_generate_prompt(input_text, dataset_type)

if __name__ == "__main__":
    debug_sample_data()