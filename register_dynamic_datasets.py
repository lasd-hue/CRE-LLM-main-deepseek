import json

# 读取现有的 dataset_info.json
with open('data/dataset_info.json', 'r', encoding='utf-8') as f:
    dataset_info = json.load(f)

# 添加新的动态提示数据集
new_datasets = {
    "finre_dynamic_fixed_v2": {
        "file_name": "FinRE/train_dynamic_fixed_v2.json",
        "columns": {
            "prompt": "instruction",
            "query": "input",
            "response": "output", 
            "history": ""
        }
    },
    "sanwen_dynamic_fixed_v2": {
        "file_name": "SanWen/train_dynamic_fixed_v2.json",
        "columns": {
            "prompt": "instruction",
            "query": "input",
            "response": "output",
            "history": ""
        }
    }
}

# 更新数据集信息
dataset_info.update(new_datasets)

# 保存回文件
with open('data/dataset_info.json', 'w', encoding='utf-8') as f:
    json.dump(dataset_info, f, ensure_ascii=False, indent=2)

print("动态提示数据集注册完成！")
print("新增的数据集：")
for name in new_datasets.keys():
    print(f"- {name}")