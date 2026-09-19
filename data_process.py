import json
import re
import random

class FixedDynamicPromptEngine:
    def __init__(self):
        self.templates = self._init_templates()
    
    def _init_templates(self):
        """初始化多领域提示模板"""
        return {
            "financial": {
                "expert": """作为金融关系分析专家，请分析以下文本中实体间的金融关系：

文本：{text}
实体对：[{entity1}] 和 [{entity2}]

请从金融专业角度分析并输出准确的关系类型。注意：如果关系不明确，请输出"unknown"：""",
                
                "qa": """金融关系提取问题：
问题：[{entity1}] 和 [{entity2}] 之间存在什么金融关系？
文本：{text}

请直接输出关系类型，如果不确定请输出"unknown"：""",
                
                "simple": """提取金融关系：
文本：{text}
实体：[{entity1}] 和 [{entity2}]
关系："""
            },
            "literary": {
                "expert": """作为文学文本分析专家，请分析以下文学作品中实体间的关系：

文本：{text}
分析对象：[{entity1}] 和 [{entity2}]

请从文学角度分析人物、地点或事物之间的关系。注意：如果关系不明确，请输出"unknown"：""",
                
                "descriptive": """请描述以下文学文本中实体间的内在联系：

"{text}"

在这个语境中，[{entity1}] 和 [{entity2}] 的关系是（如果不确定请输出"unknown"）：""",
                
                "simple": """提取文学关系：
文本：{text}
实体：[{entity1}] 和 [{entity2}]
关系："""
            }
        }
    
    def detect_domain(self, text, dataset_type):
        """检测文本领域"""
        return "financial" if dataset_type == "FinRE" else "literary"
    
    def analyze_complexity(self, text):
        """分析文本复杂度 - 放宽阈值"""
        length_score = min(len(text) / 50, 1.0)  # 降低阈值
        comma_count = text.count('，')
        period_count = text.count('。')
        structure_score = min((comma_count + period_count) / 2, 1.0)  # 降低阈值
        
        complex_words = ['虽然', '但是', '然而', '因此', '因为', '所以', '不仅', '而且']
        vocab_score = sum(1 for word in complex_words if word in text) / len(complex_words)
        
        total_score = (length_score * 0.4 + structure_score * 0.4 + vocab_score * 0.2)
        
        if total_score > 0.5:  # 降低阈值
            return "high"
        elif total_score > 0.2:  # 降低阈值
            return "medium"
        else:
            return "low"
    
    def extract_original_text(self, input_text):
        """从input字段中提取原始文本"""
        match = re.match(r'^(.*?)\s*\(\[.*?\]', input_text)
        if match:
            return match.group(1).strip()
        return input_text
    
    def is_valid_entity(self, entity):
        """检查实体是否有效 - 修复版"""
        # 只排除明显无效的实体
        invalid_patterns = [
            r'.*<.*>.*',      # 包含 <>
            r'.*\d+岁.*',     # 包含数字+岁
            r'.*几年.*',       # 包含"几年"
            r'.*没有.*',       # 包含"没有"
            # 注意：移除了长度限制 r'^.{1,2}$'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, entity):
                return False
        
        # 放宽条件：只要包含中文字符且非空就有效
        if len(entity.strip()) < 1:
            return False
            
        if not re.search(r'[\u4e00-\u9fff]', entity):
            return False
            
        return True
    
    def extract_entities_from_input(self, input_text):
        """从input字段中提取实体对"""
        entity_pattern = r'\(\[(.*?)\],\?,\[(.*?)\]\)'
        match = re.search(entity_pattern, input_text)
        if match:
            entity1, entity2 = match.group(1), match.group(2)
            
            if self.is_valid_entity(entity1) and self.is_valid_entity(entity2):
                return entity1, entity2
        
        return None, None
    
    def generate_prompt(self, input_text, dataset_type="FinRE"):
        """生成动态优化提示"""
        original_text = self.extract_original_text(input_text)
        entity1, entity2 = self.extract_entities_from_input(input_text)
        
        if not entity1 or not entity2:
            return "请根据给定句子和实体抽取其关系"
        
        domain = self.detect_domain(original_text, dataset_type)
        complexity = self.analyze_complexity(original_text)
        
        # 优化模板选择
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
        
        template = self.templates[domain][template_type]
        return template.format(text=original_text, entity1=entity1, entity2=entity2)

def process_dataset_fixed(txt_file_path, json_file_path, dataset_type="FinRE"):
    """处理数据集的主函数 - 修复版"""
    
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = []
    output_dict = {}
    prompt_engine = FixedDynamicPromptEngine()

    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 4:
            entity1, entity2, relation, text = parts
            
            entities = [entity1, entity2]
            entity_relation = f'([{entity1}],?,[{entity2}])'
            input_text = text
            for entity in entities:
                input_text = re.sub(re.escape(entity), f'[{entity}]', input_text)
            input_text = input_text + ' ' + entity_relation
            output = f'([{entity1}],{relation},[{entity2}])'
            
            if input_text in output_dict:
                output_dict[input_text] = output_dict[input_text] + ',' + output
            else:
                output_dict[input_text] = output
    
    valid_count = 0
    invalid_count = 0
    
    for input_text, output in output_dict.items():
        instruction = prompt_engine.generate_prompt(input_text, dataset_type)
        entity1, entity2 = prompt_engine.extract_entities_from_input(input_text)
        if entity1 and entity2:
            valid_count += 1
        else:
            invalid_count += 1
            
        item = {
            "instruction": instruction,
            "input": input_text,
            "output": output
        }
        data.append(item)

    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    with open(json_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(json_data)
    
    print(f"处理完成！{dataset_type} 共处理 {len(data)} 条数据")
    print(f"有效实体对: {valid_count}, 无效实体对: {invalid_count}")
    print(f"动态提示应用率: {valid_count/len(data)*100:.1f}%")

def main():
    """主函数"""
    
    print("开始使用修复版处理数据集...")
    
    # 处理FinRE数据集
    process_dataset_fixed(
        'data/FinRE/train.txt', 
        'data/FinRE/train_dynamic_fixed_v2.json', 
        dataset_type="FinRE"
    )
    
    # 处理SanWen数据集
    process_dataset_fixed(
        'data/SanWen/train.txt', 
        'data/SanWen/train_dynamic_fixed_v2.json', 
        dataset_type="SanWen"
    )
    
    print("\n所有数据集处理完成！")
    print("生成的文件：")
    print("- data/FinRE/train_dynamic_fixed_v2.json")
    print("- data/SanWen/train_dynamic_fixed_v2.json")

if __name__ == "__main__":
    main()