import os
import requests
from pymongo import MongoClient
from decimal import Decimal

# EOS 公共 RPC 节点
EOS_RPC_URL = "https://eos.greymass.com"

# MongoDB 连接配置
client = MongoClient("mongodb://localhost:27017/")  # 默认连接本地 MongoDB
db = client["eos_blockchain"]  # 创建数据库
header_collection = db["block_headers"]  # 区块头信息集合
transaction_collection = db["transactions"]  # 交易信息集合
state_collection = db["state_database"]  # 状态信息集合

# 存储最新已处理区块号的文件
LAST_EOS_BLOCK_FILE = "eos_last_processed_block.txt"


# 读取上次已处理的最新区块号
def get_last_processed_block():
    if os.path.exists(LAST_EOS_BLOCK_FILE):
        with open(LAST_EOS_BLOCK_FILE, "r") as f:
            return int(f.read().strip())  # 读取并转换为整数
    return None  # 如果文件不存在，返回 None


# 写入最新的已处理区块号
def save_last_processed_block(block_number):
    with open(LAST_EOS_BLOCK_FILE, "w") as f:
        f.write(str(block_number))  # 记录最新的区块号


# 获取最新区块号
def get_latest_block():
    """获取最新区块信息"""
    url = f"{EOS_RPC_URL}/v1/chain/get_info"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["head_block_num"]  # 返回最新区块号
    print(f"请求失败: {response.status_code}")
    return None


# 获取区块详细信息
def get_block(block_num):
    """获取指定区块的详细信息"""
    url = f"{EOS_RPC_URL}/v1/chain/get_block"
    payload = {"block_num_or_id": block_num}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()  # 返回区块信息
    print(f"获取区块 {block_num} 失败: {response.status_code}")
    return None


# 获取账户余额
def get_account_balance(account_name):
    """获取账户余额"""
    url = f"{EOS_RPC_URL}/v1/chain/get_account"
    payload = {"account_name": account_name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        account_data = response.json()

        # 检查账户数据中是否包含 core_liquid_balance
        balances = {}
        if 'core_liquid_balance' in account_data:
            # 如果有 core_liquid_balance，提取该余额
            balances['EOS'] = account_data['core_liquid_balance']
        else:
            balances['EOS'] = '0.0'  # 如果没有余额，设置为 '0.0'

        # 提取其他代币余额（如果有的话）
        if 'assets' in account_data:
            for asset in account_data['assets']:
                symbol = asset['symbol']
                balances[symbol] = asset['amount']

        return balances

    print(f"无法获取账户 {account_name} 的余额")
    return {}


# 获取账户权限
def get_account_permissions(account_name):
    """获取账户权限"""
    url = f"{EOS_RPC_URL}/v1/chain/get_account"
    payload = {"account_name": account_name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        account_data = response.json()
        permissions = account_data['permissions']  # 获取权限信息
        return permissions
    print(f"无法获取账户 {account_name} 的权限")
    return []


# 获取合约代码
def get_contract_code(account_name):
    """获取账户合约代码"""
    url = f"{EOS_RPC_URL}/v1/chain/get_code"
    payload = {"account_name": account_name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()  # 返回合约代码
    print(f"无法获取账户 {account_name} 的合约代码")
    return {}


# 主逻辑
try:
    # 获取 EOS 最新区块号
    latest_block_number = get_latest_block()
    if latest_block_number is None:
        print("无法获取最新区块号，程序终止。")
        exit()

    print(f"EOS 最新区块号: {latest_block_number}")

    # 确定起始区块号
    last_processed_block = get_last_processed_block()
    if last_processed_block is None:  # 首次运行
        start_block_number = latest_block_number - 9  # 获取最新10个区块
    else:
        start_block_number = last_processed_block + 1  # 断点续传

    # 遍历区块
    for block_num in range(start_block_number, latest_block_number + 1):
        block_details = get_block(block_num)
        if not block_details:
            continue  # 如果获取失败，跳过

        # 提取区块头信息
        block_number = block_details['block_num']
        block_id = block_details['id']
        timestamp = block_details['timestamp']
        producer = block_details['producer']
        transaction_count = len(block_details['transactions'])

        # 将区块头信息存储到 MongoDB
        block_header = {
            "block_number": block_number,
            "block_id": block_id,
            "timestamp": timestamp,
            "producer": producer,
            "transaction_count": transaction_count
        }
        header_collection.insert_one(block_header)
        print(f"区块头信息: {block_number} 已存储到 MongoDB")

        # 处理交易信息
        unique_accounts = set()  # 记录涉及的账户
        for tx in block_details['transactions']:
            tx_id = tx['trx']['id'] if isinstance(tx['trx'], dict) else "N/A"  # 获取交易 ID
            actions = tx['trx'].get('transaction', {}).get('actions', []) if isinstance(tx['trx'], dict) else []

            sender = "N/A"
            receiver = "N/A"
            action_details = []

            for action in actions:
                sender = action['authorization'][0]['actor'] if 'authorization' in action and action['authorization'] else "N/A"
                receiver = action['account']
                action_details.append(f"{action['name']}({action.get('data', {})})")

            # 将交易信息存储到 MongoDB
            transaction = {
                "block_number": block_number,
                "tx_id": tx_id,
                "sender": sender,
                "receiver": receiver,
                "actions": "; ".join(action_details)
            }
            transaction_collection.insert_one(transaction)
            print(f"交易信息: 区块 {block_number} 交易 {tx_id} 已存储到 MongoDB")

            # 记录账户用于后续状态查询
            unique_accounts.add(sender)
            unique_accounts.add(receiver)

        # 处理状态数据库信息
        for account in unique_accounts:
            # 获取账户余额
            balance = get_account_balance(account)

            # 获取账户权限
            permissions = get_account_permissions(account)

            # 获取合约代码
            contract_code = get_contract_code(account)
            contract_address = account

            # 将信息存储到 MongoDB
            state_info = {
                "block_number": block_number,
                "account_address": account,
                "balance": balance.get('EOS', '0.0'),
                "permissions": str(permissions),
                "contract_address": contract_address,
                "contract_code": str(contract_code.get('code_hash', 'N/A'))[:50]
            }
            state_collection.insert_one(state_info)
            print(f"状态信息: 区块 {block_number} 账户 {account} 已存储到 MongoDB")

        # 记录当前已处理的最新区块号
        save_last_processed_block(block_number)

    print("数据已成功存储到 MongoDB 中！")

except Exception as e:
    print(f"发生错误，连接失败: {e}")
