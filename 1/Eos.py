import os
import requests
import time
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# MongoDB 连接配置
client = MongoClient("mongodb://localhost:27017/")
db = client["eos_blockchain"]
header_collection = db["block_headers"]
transaction_collection = db["transactions"]
state_collection = db["state_database"]
block_info_collection = db["block_info"]  # 记录最新已处理区块号

# 全局缓存队列
HEADER_CACHE = Queue()
TRANSACTION_CACHE = Queue()
STATE_CACHE = Queue()

# 批量存储阈值
BATCH_SIZE = 50
MAX_WORKERS = 3
RETRY_TIMES = 3


# 请求封装，增加重试机制
def request_with_retry(url, payload=None, method="POST"):
    for retry in range(RETRY_TIMES):
        try:
            if method == "POST":
                response = requests.post(url, json=payload, timeout=10)
            else:
                response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            print(f"请求失败 {response.status_code}, 重试 {retry + 1}/{RETRY_TIMES}")
            time.sleep(2)
        except Exception as e:
            print(f"请求异常: {e}")
        time.sleep(2)
    return None


# 读取最新区块号
def get_latest_block(eos_rpc_url):
    url = f"{eos_rpc_url}/v1/chain/get_info"
    return request_with_retry(url, method="GET")["head_block_num"]


# 读取上次已处理的最新区块号
def get_last_processed_block():
    block_info = block_info_collection.find_one({"type": "last_processed_block"})
    if block_info:
        return block_info["block_number"]
    return None


# 保存最新已处理区块号
def save_last_processed_block(block_number):
    block_info_collection.update_one(
        {"type": "last_processed_block"},
        {"$set": {"block_number": block_number}},
        upsert=True
    )


# 保存缓存数据
def save_to_db(collection, cache):
    data = []
    while not cache.empty():
        data.append(cache.get())
    if data:
        collection.insert_many(data)
        print(f"已批量插入 {len(data)} 条数据")


# 获取区块详细信息
def get_block(eos_rpc_url, block_num):
    url = f"{eos_rpc_url}/v1/chain/get_block"
    payload = {"block_num_or_id": block_num}
    return request_with_retry(url, payload)


# 获取账户余额
def get_account_balance(eos_rpc_url, account_name):
    url = f"{eos_rpc_url}/v1/chain/get_account"
    payload = {"account_name": account_name}
    account_data = request_with_retry(url, payload)

    if account_data:
        return account_data.get("core_liquid_balance", "0.0")
    return "0.0"


# 获取账户权限
def get_account_permissions(eos_rpc_url, account_name):
    url = f"{eos_rpc_url}/v1/chain/get_account"
    payload = {"account_name": account_name}
    account_data = request_with_retry(url, payload)

    if account_data:
        return account_data.get("permissions", [])
    return []


# 获取合约代码
def get_contract_code(eos_rpc_url, account_name):
    url = f"{eos_rpc_url}/v1/chain/get_code"
    payload = {"account_name": account_name}
    contract_data = request_with_retry(url, payload)

    if contract_data:
        return contract_data.get("code_hash", "N/A")
    return "N/A"


# 处理区块数据
def process_block(eos_rpc_url, block_num):
    block = get_block(eos_rpc_url, block_num)
    if not block:
        return

    # 区块头信息
    block_header = {
        "block_number": block["block_num"],
        "timestamp": block["timestamp"],
        "producer": block["producer"],
        "transaction_count": len(block["transactions"])
    }
    HEADER_CACHE.put(block_header)

    unique_accounts = set()

    # 解析交易信息
    for tx in block["transactions"]:
        if isinstance(tx["trx"], dict):
            tx_id = tx["trx"]["id"]
            actions = tx["trx"]["transaction"]["actions"]
            for action in actions:
                sender = action["authorization"][0]["actor"]
                receiver = action["account"]
                transaction = {
                    "block_number": block["block_num"],
                    "tx_id": tx_id,
                    "sender": sender,
                    "receiver": receiver,
                    "action": action["name"],
                    "action_data": action["data"]
                }
                TRANSACTION_CACHE.put(transaction)
                unique_accounts.add(sender)
                unique_accounts.add(receiver)

    # 批量插入
    if HEADER_CACHE.qsize() >= BATCH_SIZE:
        save_to_db(header_collection, HEADER_CACHE)

    if TRANSACTION_CACHE.qsize() >= BATCH_SIZE:
        save_to_db(transaction_collection, TRANSACTION_CACHE)

    # 账户状态信息
    for account in unique_accounts:
        balance = get_account_balance(eos_rpc_url, account)
        permissions = get_account_permissions(eos_rpc_url, account)
        contract_code = get_contract_code(eos_rpc_url, account)

        state_info = {
            "block_number": block["block_num"],
            "account_address": account,
            "balance": balance,
            "permissions": permissions,
            "contract_code": contract_code[:50]
        }
        STATE_CACHE.put(state_info)

        if STATE_CACHE.qsize() >= BATCH_SIZE:
            save_to_db(state_collection, STATE_CACHE)

    save_last_processed_block(block_num)


# 主函数
def fetch_eos_data(eos_rpc_url, start_block, end_block):
    print(f"开始爬取区块数据 {start_block} - {end_block}")
    last_block = get_last_processed_block()
    if last_block is not None:
        print(f"上次已处理的最新区块号: {last_block}")
        start_block = max(start_block, last_block + 1)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_block, eos_rpc_url, block): block for block in range(start_block, end_block + 1)}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"区块 {futures[future]} 处理异常: {e}")

    save_to_db(header_collection, HEADER_CACHE)
    save_to_db(transaction_collection, TRANSACTION_CACHE)
    save_to_db(state_collection, STATE_CACHE)
    print("数据全部爬取完成")

if __name__ == '__main__':
    # eos_rpc_url = input("请输入EOS RPC URL: ")
    # start_block = int(input("请输入起始区块号: "))
    # end_block = int(input("请输入结束区块号: "))
    # fetch_eos_data(eos_rpc_url, start_block, end_block)

    eos_rpc_url = "https://eos.greymass.com"  # EOS 节点地址
    # eos_rpc_url = "https://eos.api.eosnation.io"  # EOS 节点地址
    fetch_eos_data(eos_rpc_url, 422947650, 422947660)