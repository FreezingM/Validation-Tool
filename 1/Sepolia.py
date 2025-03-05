import os
import requests
import time
from web3 import Web3
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from decimal import Decimal

# MongoDB 连接配置
client = MongoClient("mongodb://localhost:27017/")
db = client["sepolia_blockchain"]
header_collection = db["block_headers"]
transaction_collection = db["transactions"]
state_collection = db["state_database"]
block_info_collection = db["block_info"]

# 全局缓存队列
HEADER_CACHE = Queue()
TRANSACTION_CACHE = Queue()
STATE_CACHE = Queue()

# 批量存储阈值
BATCH_SIZE = 50
MAX_WORKERS = 3  # 最大线程数
RETRY_TIMES = 3  # 请求重试次数

# 读取上次已处理的最新区块号
def get_last_processed_block():
    block_info = block_info_collection.find_one({"type": "last_processed_block"})
    if block_info:
        return block_info["block_number"]
    return None


# 写入最新的已处理区块号
def save_last_processed_block(block_number):
    block_info_collection.update_one(
        {"type": "last_processed_block"},
        {"$set": {"block_number": block_number}},
        upsert=True
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


# 请求封装，增加重试机制
def request_with_retry(func, *args, **kwargs):
    for retry in range(RETRY_TIMES):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(f"请求异常: {e}, 重试 {retry + 1}/{RETRY_TIMES}")
            time.sleep(2)
    return None


# 批量插入缓存数据到 MongoDB
def save_to_db(collection, cache):
    data = []
    while not cache.empty():
        data.append(convert_decimal_to_float(cache.get()))

    if data:
        collection.insert_many(data)
        print(f"已批量插入 {len(data)} 条数据")


# 处理区块数据
def process_block(w3, block_num):
    block = request_with_retry(w3.eth.get_block, block_num, full_transactions=True)
    if not block:
        return

    block_header = {
        "block_number": block.number,
        "transaction_count": len(block.transactions),
        "block_size": block.size
    }
    HEADER_CACHE.put(block_header)

    unique_accounts = set()
    for tx in block.transactions:
        sender = tx["from"]
        receiver = tx["to"]
        amount = w3.from_wei(tx["value"], 'ether')

        transaction = {
            "block_number": block.number,
            "sender": sender,
            "receiver": receiver,
            "amount": amount
        }
        TRANSACTION_CACHE.put(transaction)

        unique_accounts.add(sender)
        if receiver:
            unique_accounts.add(receiver)

    if HEADER_CACHE.qsize() >= BATCH_SIZE:
        save_to_db(header_collection, HEADER_CACHE)

    if TRANSACTION_CACHE.qsize() >= BATCH_SIZE:
        save_to_db(transaction_collection, TRANSACTION_CACHE)

    for account in unique_accounts:
        balance = request_with_retry(w3.eth.get_balance, account)
        contract_bytecode = w3.eth.get_code(account).hex()
        if contract_bytecode == "0x":
            contract_bytecode = "N/A"

        state_info = {
            "block_number": block.number,
            "account_address": account,
            "balance": w3.from_wei(balance, 'ether'),
            "contract_bytecode": contract_bytecode[:50]
        }
        STATE_CACHE.put(state_info)

        if STATE_CACHE.qsize() >= BATCH_SIZE:
            save_to_db(state_collection, STATE_CACHE)

    # 实时更新最新已处理区块号
    save_last_processed_block(block_num)


# 爬取数据主函数
def fetch_sepolia_data(sepolia_url, start_block, end_block):
    w3 = Web3(Web3.HTTPProvider(sepolia_url))
    latest_block_number = w3.eth.block_number
    print(f"最新区块号: {latest_block_number}")

    last_processed_block = get_last_processed_block()
    if last_processed_block is not None:
        print(f"上次已处理区块号: {last_processed_block}")
        start_block = max(start_block, last_processed_block + 1)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for block_num in range(start_block, end_block + 1):
            futures.append(executor.submit(process_block, w3, block_num))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"任务执行异常: {e}")

    save_to_db(header_collection, HEADER_CACHE)
    save_to_db(transaction_collection, TRANSACTION_CACHE)
    save_to_db(state_collection, STATE_CACHE)
    print("所有区块数据已保存！")

if __name__ == '__main__':
    # sepolia_url = input("请输入URL: ")
    # start_block = int(input("请输入起始区块号: "))
    # end_block = int(input("请输入结束区块号: "))
    # fetch_sepolia_data(sepolia_url, start_block, end_block)
    sepolia_url = input("请输入URL: ")  # https://sepolia.infura.io/v3/142d8db9e3a340f0addbf5882edae001
    fetch_sepolia_data(sepolia_url, 7754523, 7754524)

