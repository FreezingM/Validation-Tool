import pandas as pd

# 读取原链与迁移链数据集
original_data = pd.read_csv('/Users/qiangwan/Desktop/blockchain/record.csv')
migrated_data = pd.read_csv('/Users/qiangwan/Desktop/blockchain/record2.csv')

# 抽取原链和迁移链中共同的交易ID
common_transaction_ids = original_data['Block Number'].isin(migrated_data['Block Number'])
original_common_data = original_data[common_transaction_ids]
migrated_common_data = migrated_data[common_transaction_ids]

# 对共同交易ID的数据进行抽样
sampled_original_data = original_common_data.sample(frac=0.8)
sampled_migrated_data = migrated_common_data.loc[sampled_original_data.index]

def check_migration_accuracy(sampled_original_data, sampled_migrated_data):
    # 检查哈希是否一致
    sampled_original_data['Block Hash'] = sampled_original_data['Block Hash'] == sampled_migrated_data['Block Hash']

    # 检查时间戳是否一致
    sampled_original_data['Timestamp'] = sampled_original_data['Timestamp'] == sampled_migrated_data['Timestamp']
    
    # 检查交易数量是否一致
    sampled_original_data['Transaction Count'] = sampled_original_data['Transaction Count'] == sampled_migrated_data['Transaction Count']

    #检查消耗资源是否一致
    sampled_original_data['Gas Used'] = sampled_original_data['Gas Used'] == sampled_migrated_data['Gas Used']

    #检查最大消耗量是否一致
    sampled_original_data['Gas Limit'] = sampled_original_data['Gas Limit'] == sampled_migrated_data['Gas Limit']
    
    return sampled_original_data

# 进行一致性校验
checked_data = check_migration_accuracy(sampled_original_data, sampled_migrated_data)

# 查看校验结果
print(checked_data[['Block Number', 'Block Hash', 'Timestamp', 'Transaction Count', 'Gas Used', 'Gas Limit']])
