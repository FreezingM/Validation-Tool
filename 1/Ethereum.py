import requests
import csv
from web3 import Web3

# 设置代理
proxy = {
    'http': 'http://localhost:7890',
    'https': 'http://localhost:7890'
}

# 连接到 Infura
infura_url = 'https://mainnet.infura.io/v3/142d8db9e3a340f0addbf5882edae001'
session = requests.Session()
session.proxies.update(proxy)

w3 = Web3(Web3.HTTPProvider(infura_url, session=session))

# 验证连接
try:
    # 获取最新区块号
    latest_block_number = w3.eth.block_number
    print(f"最新区块号: {latest_block_number}")

    # 设置要获取的区块数
    num_blocks = 10  # 例如获取最新的10个区块

    # 打开 CSV 文件进行写入
    with open('record.csv', mode='w', newline='') as file:
        writer = csv.writer(file)

        # 写入 CSV 文件的标题行
        writer.writerow(["Block Number", "Block Hash", "Timestamp", "Transaction Count", "Gas Used", "Gas Limit"])

        # 获取多个区块信息
        for block_num in range(latest_block_number, latest_block_number - num_blocks, -1):
            # 获取区块详细信息
            block_details = w3.eth.get_block(block_num, full_transactions=False)

            # 提取关键信息
            block_number = block_details['number']
            block_hash = block_details['hash'].hex()
            timestamp = block_details['timestamp']
            transaction_count = len(block_details['transactions'])
            gas_used = block_details['gasUsed']
            gas_limit = block_details['gasLimit']

            # 写入 CSV 文件
            writer.writerow([block_number, block_hash, timestamp, transaction_count, gas_used, gas_limit])
            print(f"区块 {block_number} 信息已写入文件")

    print("数据已成功保存到 record.csv 文件中")

except Exception as e:
    print(f"连接失败，错误信息：{e}")
