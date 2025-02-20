import os
import requests
import csv
from web3 import Web3
from pymongo import MongoClient  # 导入 pymongo
from decimal import Decimal

# 设置代理
proxy = {
    # 'http': 'http://localhost:7890',  # 使用本地代理（可以换成其他代理地址）
    # 'https': 'http://localhost:7890'  # 使用本地代理（可以换成其他代理地址）
}

# 连接到 Ganache 本地测试网络
ganache_url = 'http://127.0.0.1:7545'  # Ganache 本地测试网络的 RPC 地址
session = requests.Session()
session.proxies.update(proxy)

# 初始化 Web3 实例
w3 = Web3(Web3.HTTPProvider(ganache_url, session=session))

# 检查连接是否成功
if not w3.is_connected():
    print("无法连接到 Ganache 本地测试网络！")
else:
    print("成功连接到 Ganache 本地测试网络！")

# MongoDB 连接配置
client = MongoClient("mongodb://localhost:27017/")  # 默认连接本地 MongoDB
db = client["ganache_blockchain"]  # 创建数据库
header_collection = db["block_headers"]  # 区块头信息集合
transaction_collection = db["transactions"]  # 交易信息集合
state_collection = db["state_database"]  # 状态信息集合

# 存储最新已处理区块号的文件
LAST_BLOCK_FILE = "ganache_last_processed_block.txt"


# 读取上次已处理的最新区块号
def get_last_processed_block():
    if os.path.exists(LAST_BLOCK_FILE):
        with open(LAST_BLOCK_FILE, "r") as f:
            return int(f.read().strip())  # 读取并转换为整数
    return None  # 如果文件不存在，返回 None


# 写入最新的已处理区块号
def save_last_processed_block(block_number):
    with open(LAST_BLOCK_FILE, "w") as f:
        f.write(str(block_number))  # 记录最新的区块号


# 遍历字典或列表，递归转换所有 Decimal 为 float
def convert_decimal_to_float(data):
    if isinstance(data, dict):  # 如果数据是字典
        for key, value in data.items():
            data[key] = convert_decimal_to_float(value)
    elif isinstance(data, list):  # 如果数据是列表
        data = [convert_decimal_to_float(item) for item in data]
    elif isinstance(data, Decimal):  # 如果数据是 Decimal 类型
        data = float(data)  # 转换为 float
    return data


# 程序主逻辑
try:
    # 获取最新区块号
    latest_block_number = w3.eth.block_number
    print(f"最新区块号: {latest_block_number}")

    # 确定起始区块号
    last_processed_block = get_last_processed_block()
    if last_processed_block is None:  # 首次运行
        # start_block_number = latest_block_number - 9  # 获取最新10个区块
        start_block_number = latest_block_number
    else:
        start_block_number = last_processed_block + 1  # 断点续传，从下一个区块继续

    # 遍历区块
    for block_num in range(start_block_number, latest_block_number + 1):
        # 获取区块信息
        block_details = w3.eth.get_block(block_num, full_transactions=True)

        # 提取区块头信息
        block_number = block_details['number']
        transaction_count = len(block_details['transactions'])
        block_size = block_details['size']

        # 将区块头信息存储到 MongoDB
        block_header = {
            "block_number": block_number,
            "transaction_count": transaction_count,
            "block_size": block_size
        }
        block_header = convert_decimal_to_float(block_header)  # 转换 Decimal 为 float
        header_collection.insert_one(block_header)
        print(f"区块头信息: {block_number} 已存储到 MongoDB")

        account_addresses = set()
        for tx in block_details['transactions']:
            sender = tx['from']
            receiver = tx['to']
            amount = w3.from_wei(tx['value'], 'ether')

            # 将交易信息存储到 MongoDB
            transaction = {
                "block_number": block_number,
                "sender": sender,
                "receiver": receiver,
                "amount": amount
            }
            transaction = convert_decimal_to_float(transaction)  # 转换 Decimal 为 float
            transaction_collection.insert_one(transaction)
            account_addresses.add(sender)
            if receiver:
                account_addresses.add(receiver)
            print(f"交易信息: 区块 {block_number} 交易已存储到 MongoDB")

        # 提取状态数据库信息并存储到 MongoDB
        for address in account_addresses:
            balance = w3.eth.get_balance(address)
            contract_bytecode = w3.eth.get_code(address).hex()
            if contract_bytecode == "0x":
                contract_bytecode = "N/A"

            # 存储状态信息到 MongoDB
            state_info = {
                "block_number": block_number,
                "account_address": address,
                "balance": w3.from_wei(balance, 'ether'),
                "contract_address": address,
                "contract_bytecode": contract_bytecode[:50]
            }
            state_info = convert_decimal_to_float(state_info)  # 转换 Decimal 为 float
            state_collection.insert_one(state_info)
            print(f"状态信息: 区块 {block_number} 地址 {address} 已存储到 MongoDB")

        # 记录当前已处理的最新区块号
        save_last_processed_block(block_number)

    print("数据已成功存储到 MongoDB 中！")

except Exception as e:
    print(f"发生错误，连接失败: {e}")