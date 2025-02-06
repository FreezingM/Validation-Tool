import pandas as pd

# 读取数据集
def load_data(file_name):
    return pd.read_csv(f"/Users/qiangwan/Desktop/blockchain/{file_name}")

data = {
    "区块头": {"original": load_data("block_header_info.csv"), "migrated": load_data("block_header_info(qianyi).csv")},
    "交易内容": {"original": load_data("transaction_info.csv"), "migrated": load_data("transaction_info(qianyi).csv")},
    "状态数据库": {"original": load_data("state_database_info.csv"), "migrated": load_data("state_database_info(qianyi).csv")},
}

# 处理数据类型、NaN、字符串格式统一
def normalize_data(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip().str.lower()
    if "Balance" in df.columns:
        df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce").fillna(0).astype(float).round(6)
    return df

for key in data:
    for sub_key in ["original", "migrated"]:
        data[key][sub_key] = normalize_data(data[key][sub_key])

# 获取共同的区块号
for key in data:
    common_blocks = data[key]["original"]["Block Number"].isin(data[key]["migrated"]["Block Number"])
    data[key]["original"] = data[key]["original"][common_blocks].reset_index()
    data[key]["migrated"] = data[key]["migrated"][common_blocks].reset_index()

# 按区块号抽样
sampled_blocks = data["区块头"]["original"]["Block Number"].sample(frac=0.3).tolist()

# 过滤所有数据，使其包含所有被抽样的区块
for key in data:
    for sub_key in ["original", "migrated"]:
        data[key][sub_key] = data[key][sub_key][data[key][sub_key]["Block Number"].isin(sampled_blocks)]

# 迁移一致性校验
checked_results = {key: data[key]["original"].fillna("").eq(data[key]["migrated"].fillna(""))
                   for key in data}

# 输出不一致的字段
def print_inconsistencies(checked_data, section_name, original_data):
    errors_by_block = {}
    for idx, row in checked_data.iterrows():
        if not row.all():
            block_number = original_data.loc[idx, "Block Number"]
            csv_row_number = original_data.loc[idx, "index"] + 2
            errors_by_block.setdefault(block_number, []).append(f"第 {csv_row_number} 行 {', '.join(checked_data.columns[~row])} 有误")

    if errors_by_block:
        print(f"{section_name} 错误列表：")
        for block_number, errors in sorted(errors_by_block.items()):
            print(f"区块 {block_number}：\n" + "\n".join(errors))
        print()
    else:
        print(f"{section_name} 没有发现错误。\n")

# 打印校验结果
for key in checked_results:
    print_inconsistencies(checked_results[key], key, data[key]["original"])