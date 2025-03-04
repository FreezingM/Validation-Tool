import os
import random
import time
from pymongo import MongoClient
from decimal import Decimal
from flask import Flask, request, jsonify

# 初始化 Flask 应用
app = Flask(__name__)

# MongoDB 连接配置
ORIGINAL_DB_URI = "mongodb://localhost:27017/"
MIGRATED_DB_URI = "mongodb://localhost:27017/"

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

original_log_collection = original_db["block_logs"]
migrated_log_collection = migrated_db["block_logs"]

# 全局日志存储
logs = {
    "block_header_logs": [],
    "transaction_logs": [],
    "account_state_logs": [],
    "block_log_logs": [],
    "missing_blocks": [],
    "misordered_blocks": [],
    "block_validation_time": {},
    "gas_logs": []
}

# 判断是否是同构链
def is_homogeneous_chain():
    original_metadata = original_db["metadata"].find_one({})
    migrated_metadata = migrated_db["metadata"].find_one({})
    
    if not original_metadata or not migrated_metadata:
        return False  # 默认认为是异构链
    
    return original_metadata.get("chain_type") == migrated_metadata.get("chain_type")

HOMOGENEOUS_CHAIN = is_homogeneous_chain()

# 校验冗余数据（仅同构链）
def check_redundant_data(original, migrated, fields, log_category, entity_id):
    if HOMOGENEOUS_CHAIN:
        for field in fields:
            if original.get(field) != migrated.get(field):
                logs[log_category].append(f"{entity_id} 的 {field} 不一致")

# 校验数值型数据（适用于异构链）
def check_numeric_data(original, migrated, fields, log_category, entity_id):
    for field in fields:
        if isinstance(original.get(field), (int, float, Decimal)) and isinstance(migrated.get(field), (int, float, Decimal)):
            if original.get(field) != migrated.get(field):
                logs[log_category].append(f"{entity_id} 的 {field} 数值不一致")

# 校验区块头一致性
def check_block_consistency(sampled_blocks):
    missing_block_numbers = []
    misordered_blocks = []

    # 获取迁移链的所有区块，并按照 block_number 排序
    migrated_blocks = list(migrated_header_collection.find({"block_number": {"$in": [b["block_number"] for b in sampled_blocks]}}))
    migrated_blocks.sort(key=lambda x: x["block_number"])

    previous_block_number = None
    for original_block in sampled_blocks:
        start_time = time.time()  # 记录开始时间

        migrated_block = migrated_header_collection.find_one({"block_number": original_block["block_number"]})
        if not migrated_block:
            logs["block_header_logs"].append(f"区块 {original_block['block_number']} 不存在于迁移链")
            missing_block_numbers.append(original_block["block_number"])
            logs["block_validation_time"][original_block["block_number"]] = time.time() - start_time
            continue
        check_redundant_data(original_block, migrated_block, ["block_id", "timestamp", "producer", "transaction_count"], "block_header_logs", f"区块 {original_block['block_number']}")

        # 检查区块顺序是否被改变
        if previous_block_number is not None and migrated_block["block_number"] < previous_block_number:
            logs["block_header_logs"].append(f"区块 {migrated_block['block_number']} 在迁移链中顺序异常")
            misordered_blocks.append(migrated_block["block_number"])
        previous_block_number = migrated_block["block_number"]

        end_time = time.time() 
        logs["block_validation_time"][original_block["block_number"]] = end_time - start_time  # 计算耗时
    
    # 记录丢失和乱序的区块
    logs["missing_blocks"] = missing_block_numbers
    logs["misordered_blocks"] = misordered_blocks
    print(f"丢失的区块列表: {missing_block_numbers}")
    print(f"顺序异常的区块列表: {misordered_blocks}")

# 校验交易一致性
def check_transaction_consistency(sampled_blocks):
    for original_block in sampled_blocks:
        original_transactions = original_transaction_collection.find({"block_number": original_block["block_number"]})
        for original_tx in original_transactions:
            migrated_tx = migrated_transaction_collection.find_one({"tx_id": original_tx["tx_id"]})
            if not migrated_tx:
                logs["transaction_logs"].append(f"交易 {original_tx['tx_id']} 不存在于迁移链")
                continue
            check_redundant_data(original_tx, migrated_tx, ["sender", "receiver", "actions"], "transaction_logs", f"交易 {original_tx['tx_id']}")

# 校验账户状态一致性（新增 RAM 信息校验）
def check_account_state_consistency(sampled_blocks):
    for original_block in sampled_blocks:
        original_accounts = original_state_collection.find({"block_number": original_block["block_number"]})
        for original_account in original_accounts:
            migrated_account = migrated_state_collection.find_one({"account_address": original_account["account_address"]})
            if not migrated_account:
                logs["account_state_logs"].append(f"账户 {original_account['account_address']} 不存在于迁移链")
                continue
            check_redundant_data(original_account, migrated_account, ["balance", "permissions", "contract_address", "contract_code", "ram_quota", "ram_usage"], "account_state_logs", f"账户 {original_account['account_address']}")

# 校验 Gas 费用
def check_gas_consistency(original_gas_collection, migrated_gas_collection, sampled_blocks):
    for original_block in sampled_blocks:
        original_gas = original_gas_collection.find_one({"block_number": original_block["block_number"]})
        migrated_gas = migrated_gas_collection.find_one({"block_number": original_block["block_number"]})
        
        if not migrated_gas:
            logs["gas_logs"].append(f"区块 {original_block['block_number']} 在迁移链上找不到 Gas 数据")
            continue
        
        check_redundant_data(original_gas, migrated_gas, ["gas_limit", "gas_used"], "gas_logs", f"区块 {original_block['block_number']}")

# 校验区块日志一致性（新增 address, data, topics 校验）
def check_block_logs(sampled_blocks):
    for original_block in sampled_blocks:
        original_logs = original_log_collection.find({"block_number": original_block["block_number"]})
        for original_log in original_logs:
            migrated_log = migrated_log_collection.find_one({"log_index": original_log["log_index"]})
            if not migrated_log:
                logs["block_log_logs"].append(f"日志 {original_log['log_index']} 不存在于迁移链")
                continue
            check_redundant_data(original_log, migrated_log, ["log_index", "address", "data", "topics"], "block_log_logs", f"日志 {original_log['log_index']}")

# 数据一致性校验
def verify_data_consistency(start_block, end_block, sampling_mode="sample"):
    if "block_validation_time" not in logs:
        logs["block_validation_time"] = {}  # 只在第一次调用时初始化
    query = {"block_number": {"$gte": start_block, "$lte": end_block}}
    original_blocks = list(original_header_collection.find(query))
    
    sampled_blocks = random.sample(original_blocks, max(1, int(len(original_blocks) * 0.3))) if len(original_blocks) > 1 else original_blocks
    
    check_block_consistency(sampled_blocks)
    check_transaction_consistency(sampled_blocks)
    check_account_state_consistency(sampled_blocks)
    check_block_logs(sampled_blocks)
    print("校验完成！")

# 处理 API 请求
@app.route("/api", methods=["POST"])
def handle_request():
    try:
        data = request.get_json()
        network_type = data.get("network_type", "").lower()
        start_block = int(data.get("start_block", 0))
        end_block = int(data.get("end_block", 0))
        sampling_mode = data.get("sampling_mode", "sample")  # 直接使用前端传入的 sampling_mode
        
        # 读取目标链数据
        target_network_type = data.get("target_network_type", "").lower()
        target_start_block = int(data.get("target_start_block", 0))
        target_end_block = int(data.get("target_end_block", 0))
        
        verify_data_consistency(start_block, end_block, sampling_mode)
        
        return jsonify({
            "message": "报告生成成功",
            "logs": logs,
            "sampling_mode": sampling_mode,
            "missing_blocks": logs["missing_blocks"],
            "misordered_blocks": logs["misordered_blocks"],
            "block_validation_time": logs.get("block_validation_time", {})  
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
