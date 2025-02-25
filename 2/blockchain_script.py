import os
import random
import time
from pymongo import MongoClient
from decimal import Decimal
from flask import Flask, jsonify

# 初始化 Flask 应用
app = Flask(__name__)

# MongoDB 连接配置
ORIGINAL_DB_URI = "mongodb://localhost:27017/"  # 原链MongoDB连接
MIGRATED_DB_URI = "mongodb://localhost:27017/"  # 迁移链MongoDB连接

# MongoDB 数据库和集合名称
original_client = MongoClient(ORIGINAL_DB_URI)
migrated_client = MongoClient(MIGRATED_DB_URI)

original_db = original_client["eos_blockchain"]
migrated_db = migrated_client["eos_blockchain"]

original_header_collection = original_db["block_headers"]
migrated_header_collection = migrated_db["block_headers"]

original_transaction_collection = original_db["transactions"]
migrated_transaction_collection = migrated_db["transactions"]

original_state_collection = original_db["state_database"]
migrated_state_collection = migrated_db["state_database"]

# 全局变量来存储日志信息
logs = []

# 校验区块信息
def check_block_consistency(sampled_blocks):
    """校验区块头信息一致性以及区块号顺序"""
    block_times = {}  # 记录每个区块的校验时长
    # 按照区块号排序
    sampled_blocks.sort(key=lambda x: x["block_number"])

    # 校验区块号顺序
    for i in range(1, len(sampled_blocks)):
        if sampled_blocks[i]["block_number"] <= sampled_blocks[i - 1]["block_number"]:
            logs.append(f"区块号顺序错误: 区块 {sampled_blocks[i-1]['block_number']} 和区块 {sampled_blocks[i]['block_number']} 顺序颠倒")

    for original_block in sampled_blocks:
        start_time = time.time()  # 记录开始时间
        
        migrated_block = migrated_header_collection.find_one({"block_number": original_block["block_number"]})

        if not migrated_block:
            logs.append(f"区块 {original_block['block_number']} 不存在于迁移链")
            continue

        if (original_block['block_id'] != migrated_block['block_id'] or
            original_block['timestamp'] != migrated_block['timestamp'] or
            original_block['producer'] != migrated_block['producer'] or
            original_block['transaction_count'] != migrated_block['transaction_count']):
            logs.append(f"区块 {original_block['block_number']} 在原链和迁移链不一致")
            logs.append(f"原链区块ID: {original_block['block_id']} 有误")
            logs.append(f"原链时间戳: {original_block['timestamp']} 有误")
            logs.append(f"原链生产者: {original_block['producer']} 有误")
            logs.append(f"原链交易数量: {original_block['transaction_count']} 有误")

        end_time = time.time()  # 记录结束时间
        block_times[original_block['block_number']] = end_time - start_time  # 计算时长并存储
    
    return block_times

# 校验交易信息
def check_transaction_consistency(sampled_blocks):
    """校验交易信息一致性"""
    block_times = {}  # 记录每个区块的校验时长
    for original_block in sampled_blocks:
        start_time = time.time()  # 记录开始时间
        
        # 获取该区块下的所有交易
        original_transactions = original_transaction_collection.find({"block_number": original_block["block_number"]})
        for original_tx in original_transactions:
            migrated_tx = migrated_transaction_collection.find_one({"tx_id": original_tx["tx_id"]})

            if not migrated_tx:
                logs.append(f"交易 {original_tx['tx_id']} 不存在于迁移链")
                continue

            if (original_tx['sender'] != migrated_tx['sender'] or
                original_tx['receiver'] != migrated_tx['receiver'] or
                original_tx['actions'] != migrated_tx['actions']):
                logs.append(f"交易 {original_tx['tx_id']} 在原链和迁移链不一致")
                logs.append(f"原链发送者: {original_tx['sender']} 有误")
                logs.append(f"原链接收者: {original_tx['receiver']} 有误")
                logs.append(f"原链操作: {original_tx['actions']} 有误")
        
        end_time = time.time()  # 记录结束时间
        block_times[original_block['block_number']] = end_time - start_time  # 计算时长并存储
    
    return block_times

# 校验账户状态信息
def check_account_state_consistency(sampled_blocks):
    """校验账户状态信息一致性"""
    block_times = {}  # 记录每个区块的校验时长
    for original_block in sampled_blocks:
        start_time = time.time()  # 记录开始时间
        
        # 获取该区块下的所有账户
        original_accounts = original_state_collection.find({"block_number": original_block["block_number"]})
        for original_account in original_accounts:
            migrated_account = migrated_state_collection.find_one({"account_address": original_account["account_address"]})

            if not migrated_account:
                logs.append(f"账户 {original_account['account_address']} 不存在于迁移链")
                continue

            if (original_account['balance'] != migrated_account['balance'] or
                original_account['permissions'] != migrated_account['permissions'] or
                original_account['contract_address'] != migrated_account['contract_address'] or
                original_account['contract_code'] != migrated_account['contract_code']):
                logs.append(f"账户 {original_account['account_address']} 在原链和迁移链不一致")
                logs.append(f"原链余额: {original_account['balance']} 有误")
                logs.append(f"原链权限: {original_account['permissions']} 有误")
                logs.append(f"原链地址: {original_account['contract_address']} 有误")
                logs.append(f"原链合约代码: {original_account['contract_code']} 有误")

        end_time = time.time()  # 记录结束时间
        block_times[original_block['block_number']] = end_time - start_time  # 计算时长并存储

    return block_times

# 主校验逻辑
def verify_data_consistency():
    original_blocks = list(original_header_collection.find())
    
    # 随机抽取 30% 的区块进行校验
    sampled_blocks = random.sample(original_blocks, int(len(original_blocks) * 0.3))

    print("开始校验区块头信息...")
    block_times = check_block_consistency(sampled_blocks)

    print("\n开始校验交易信息...")
    transaction_times = check_transaction_consistency(sampled_blocks)

    print("\n开始校验账户状态信息...")
    account_times = check_account_state_consistency(sampled_blocks)

    # 汇总并输出每个区块的总时长
    print("\n每个区块号的校验时长：")
    for block_number in block_times:
        total_time = block_times[block_number] + transaction_times.get(block_number, 0) + account_times.get(block_number, 0)
        logs.append(f"区块 {block_number} 的校验总时长: {total_time:.4f} 秒")

    logs.append("校验完成！")

# 路由：获取日志和校验报告
@app.route("/get_report", methods=["GET"])
def get_report():
    return jsonify({"logs": logs})

# 执行校验并启动 Web 服务
if __name__ == "__main__":
    verify_data_consistency()
    app.run(debug=True)
