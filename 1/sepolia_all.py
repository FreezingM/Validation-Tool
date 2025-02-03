import requests
import csv
from web3 import Web3

# 设置代理
proxy = {
    'http': 'http://localhost:7890',  # 使用本地代理（可以换成其他代理地址）
    'https': 'http://localhost:7890'  # 使用本地代理（可以换成其他代理地址）
}

# 连接到 Sepolia 测试网络（通过 Infura）
infura_url = 'https://sepolia.infura.io/v3/142d8db9e3a340f0addbf5882edae001'  # Infura 提供的连接 Sepolia 测试网的 API URL
session = requests.Session()
session.proxies.update(proxy)

# 初始化 Web3 实例
w3 = Web3(Web3.HTTPProvider(infura_url, session=session))

# 验证连接
try:
    # 获取最新区块号
    latest_block_number = w3.eth.block_number  # 获取当前最新区块的区块号
    print(f"最新区块号: {latest_block_number}")

    # 设置开始区块号和结束区块号
    start_block_number = 1000000  # 设置开始区块号
    end_block_number = 1000100  # 设置结束区块号

    # 确保区块范围有效
    if start_block_number > end_block_number:
        print("错误：开始区块号必须小于或等于结束区块号")
    else:
        # 打开 CSV 文件进行写入（以追加模式打开）
        with open('sepolia_all.csv', mode='a', newline='') as file:
            writer = csv.writer(file)

            # 如果文件为空（即没有标题行），则写入标题行
            file.seek(0, 2)  # 移动文件指针到文件末尾
            writer.writerow([  # 写入标题行
                "Block Number", "Block Hash", "Parent Hash", "Miner", "Timestamp",
                "Transaction Count", "Gas Used", "Gas Limit", "Difficulty", "Nonce",
                "Confirmations", "Size", "Extra Data", "Base Fee Per Gas", "Gas Price",
                "Uncle Hash", "Logs Bloom", "Receipts Root", "State Root", "Sha3 Uncles"
            ])

            # 获取指定范围内的区块信息
            for block_num in range(start_block_number, end_block_number + 1):  # 包括 end_block_number
                # 获取区块详细信息（不获取交易详细信息，以节省资源）
                block_details = w3.eth.get_block(block_num, full_transactions=False)

                # 提取关键信息
                block_number = block_details['number']  # 区块号，表示该区块在链中的位置
                block_hash = block_details['hash'].hex()  # 区块哈希，唯一标识该区块
                parent_hash = block_details[
                    'parentHash'].hex() if 'parentHash' in block_details else 'N/A'  # 父区块哈希，指向前一个区块
                miner = block_details['miner'] if 'miner' in block_details else 'N/A'  # 区块的矿工（生产该区块的账户）
                timestamp = block_details['timestamp']  # 区块的时间戳，表示区块生成的时间（Unix 时间戳）
                transaction_count = len(block_details['transactions'])  # 该区块的交易数量，表示区块内的交易数
                gas_used = block_details['gasUsed']  # 该区块使用的 gas 总量
                gas_limit = block_details['gasLimit']  # 区块的 gas 限制，表示该区块能使用的最大 gas
                difficulty = block_details[
                    'difficulty'] if 'difficulty' in block_details else 'N/A'  # 挖矿难度（对于 Ethereum 1.x 链）
                nonce = block_details['nonce'] if 'nonce' in block_details else 'N/A'  # 区块的 nonce 值，用于证明工作量
                confirmations = block_details[
                    'confirmations'] if 'confirmations' in block_details else 'N/A'  # 区块的确认数，表示该区块被确认的次数

                # 获取额外的信息
                size = block_details['size'] if 'size' in block_details else 'N/A'  # 区块大小（字节）
                extra_data = block_details['extraData'] if 'extraData' in block_details else 'N/A'  # 附加数据
                base_fee_per_gas = block_details[
                    'baseFeePerGas'] if 'baseFeePerGas' in block_details else 'N/A'  # 基础 Gas 费用（EIP-1559）
                gas_price = block_details['gasPrice'] if 'gasPrice' in block_details else 'N/A'  # 每单位 Gas 的价格
                uncle_hash = block_details['uncleHash'] if 'uncleHash' in block_details else 'N/A'  # 叔块哈希
                logs_bloom = block_details['logsBloom'] if 'logsBloom' in block_details else 'N/A'  # 日志布隆过滤器
                receipts_root = block_details['receiptsRoot'] if 'receiptsRoot' in block_details else 'N/A'  # 交易收据根哈希
                state_root = block_details['stateRoot'] if 'stateRoot' in block_details else 'N/A'  # 状态根哈希
                sha3_uncles = block_details['sha3Uncles'] if 'sha3Uncles' in block_details else 'N/A'  # 叔块哈希

                # 写入 CSV 文件
                writer.writerow([  # 将提取的信息写入到 CSV 文件中
                    block_number, block_hash, parent_hash, miner, timestamp,
                    transaction_count, gas_used, gas_limit, difficulty, nonce, confirmations,
                    size, extra_data, base_fee_per_gas, gas_price, uncle_hash,
                    logs_bloom, receipts_root, state_root, sha3_uncles
                ])

                print(f"区块 {block_number} 信息已写入文件")

            # 插入一个空行
            writer.writerow([])  # 空行，方便后续数据的查看

        print("数据已成功追加到 sepolia_all.csv 文件中")

except Exception as e:
    print(f"连接失败，错误信息：{e}")
