import os
import requests
from web3 import Web3
from pymongo import MongoClient
from decimal import Decimal

# MongoDB 连接配置
client = MongoClient("mongodb://localhost:27017/")  # 默认连接本地 MongoDB
db = client["sepolia_blockchain"]  # 创建数据库
header_collection = db["block_headers"]  # 区块头信息集合
transaction_collection = db["transactions"]  # 交易信息集合
state_collection = db["state_database"]  # 状态信息集合

# MongoDB 中存储最新已处理区块号的集合
block_info_collection = db["block_info"]


# 读取上次已处理的最新区块号
def get_last_processed_block():
    # 从 MongoDB 中读取最新的区块号
    block_info = block_info_collection.find_one({"type": "last_processed_block"})
    if block_info:
        return block_info["block_number"]
    return None  # 如果没有记录，返回 None


# 写入最新的已处理区块号
def save_last_processed_block(block_number):
    # 将最新的区块号存储到 MongoDB
    block_info_collection.update_one(
        {"type": "last_processed_block"},
        {"$set": {"block_number": block_number}},
        upsert=True  # 如果没有该记录，则插入新记录
    )


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

def fetch_sepolia_data(sepolia_url, start_block, end_block):
    # 初始化 Web3 实例
    w3 = Web3(Web3.HTTPProvider(sepolia_url))

    # 设置代理
    proxy = {
        'http': 'http://localhost:7890',  # 使用本地代理（可以换成其他代理地址）
        'https': 'http://localhost:7890'  # 使用本地代理（可以换成其他代理地址）
    }

    try:
        # 获取最新区块号
        latest_block_number = w3.eth.block_number
        print(f"最新区块号: {latest_block_number}")

        # 读取数据库中记录的最新处理的区块号
        last_processed_block = get_last_processed_block()

        # 如果数据库没有记录，或者 start_block 小于 last_processed_block，则从 start_block 开始
        if last_processed_block is None or start_block <= last_processed_block:
            start_block = last_processed_block + 1 if last_processed_block else start_block

        # 如果结束区块号大于最新区块号，则调整为最新区块号
        if end_block > latest_block_number:
            print(f"结束区块号 {end_block} 大于最新区块号 {latest_block_number}，调整为 {latest_block_number}")
            end_block = latest_block_number

        # 遍历区块
        for block_num in range(start_block, end_block + 1):
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


# if __name__ == '__main__':
#     sepolia_url = input("请输入URL: ")  # https://sepolia.infura.io/v3/142d8db9e3a340f0addbf5882edae001
#     start_block = int(input("请输入起始区块号: "))
#     end_block = int(input("请输入结束区块号: "))
#     fetch_sepolia_data(sepolia_url, start_block, end_block)

