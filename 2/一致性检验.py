import pandas as pd

# 读取原链与迁移链数据集
original_data = pd.read_csv('/Users/qiangwan/Desktop/blockchain/record3.csv')
migrated_data = pd.read_csv('/Users/qiangwan/Desktop/blockchain/record5.csv')

# 获取原链与迁移链共同的交易ID
common_transaction_ids = original_data['Block Number'].isin(migrated_data['Block Number'])
original_common_data = original_data[common_transaction_ids]
migrated_common_data = migrated_data[common_transaction_ids]

# 对共同交易ID的数据进行抽样
sampled_original_data = original_common_data.sample(frac=0.3)
sampled_migrated_data = migrated_common_data.loc[sampled_original_data.index]

def check_migration_accuracy(sampled_original_data, sampled_migrated_data):
    # 获取共同的列名
    columns_to_check = sampled_original_data.columns.intersection(sampled_migrated_data.columns)

    for column in columns_to_check:
        # 校验是否一致
        sampled_original_data[column] = sampled_original_data[column] == sampled_migrated_data[column]

    return sampled_original_data

# 一致性校验
checked_data = check_migration_accuracy(sampled_original_data, sampled_migrated_data)

# 示不一致的字段
for index, row in checked_data.iterrows():
    errors = []
    for column, value in row.items():
        if value == False:
            errors.append(column)

# 输出结果
    if errors:
        print(f"第 {index + 1} 行数据，{', '.join(errors)} 有误")
