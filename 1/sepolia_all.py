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

    # 设置区块范围为最新的100个区块
    start_block_number = latest_block_number - 99  # 获取最新100个区块

    # 打开 CSV 文件进行写入（分别存储区块头信息、交易内容、状态数据库信息）
    with open('block_header_info.csv', mode='a', newline='') as header_file, \
         open('transaction_info.csv', mode='a', newline='') as transaction_file, \
         open('state_database_info.csv', mode='a', newline='') as state_file:

        # 创建 CSV 写入器
        header_writer = csv.writer(header_file)
        transaction_writer = csv.writer(transaction_file)
        state_writer = csv.writer(state_file)

        header_writer.writerow([
            "Block Number", "Transaction Count", "Block Size"
        ])

        transaction_writer.writerow([
            "Block Number", "Sender", "Receiver", "Amount"
        ])

        state_writer.writerow([
            "Block Number", "Account Address", "Balance", "Contract Address", "Contract Bytecode"
        ])

        # 获取指定范围内的区块信息
        for block_num in range(start_block_number, latest_block_number + 1):  # 包括最新区块
            # 获取区块详细信息（不获取交易详细信息，以节省资源）
            block_details = w3.eth.get_block(block_num, full_transactions=True)

            # 提取区块头信息
            block_number = block_details['number']  # 区块号，表示该区块在链中的位置
            transaction_count = len(block_details['transactions'])  # 该区块的交易数量
            block_size = block_details['size']  # 区块大小（字节）

            # 写入区块头信息到 CSV 文件
            header_writer.writerow([block_number, transaction_count, block_size])
            print(f"区块头信息: {block_number} 已写入到 block_header_info.csv 文件中")

            # 提取交易内容
            for tx in block_details['transactions']:
                sender = tx['from']  # 发送方地址
                receiver = tx['to']  # 接收方地址
                amount = w3.from_wei(tx['value'], 'ether')  # 交易金额（转换为以太币单位）

                # 写入交易信息到 CSV 文件
                transaction_writer.writerow([block_number, sender, receiver, amount])
                print(f"交易信息: 区块 {block_number} 的交易已写入到 transaction_info.csv 文件中")

            # 提取状态数据库信息：查询账户余额和合约字节码
            # 假设我们关注所有已发生交易的账户
            account_addresses = set()  # 用集合去重
            for tx in block_details['transactions']:
                account_addresses.add(tx['from'])
                if tx['to'] is not None:
                    account_addresses.add(tx['to'])

            # 获取账户余额和合约字节码
            for address in account_addresses:
                balance = w3.eth.get_balance(address)  # 获取账户余额（单位为 Wei）
                contract_bytecode = w3.eth.get_code(address).hex()  # 获取合约字节码（如果是合约地址的话）

                # 仅在合约存在时保存字节码
                if contract_bytecode != '0x':
                    contract_bytecode = contract_bytecode[:50]  # 截断字节码以便存储

                # 写入状态数据库信息到 CSV 文件
                state_writer.writerow([block_number, address, w3.from_wei(balance, 'ether'), address, contract_bytecode])
                print(f"状态信息: 区块 {block_number} 地址 {address} 的余额和字节码已写入到 state_database_info.csv 文件中")

        header_writer.writerow([])  # 空行
        transaction_writer.writerow([])  # 空行
        state_writer.writerow([])  # 空行

        print("数据已成功追加到 block_header_info.csv、transaction_info.csv 和 state_database_info.csv 文件中")

except Exception as e:
    print(f"连接失败，错误信息：{e}")
