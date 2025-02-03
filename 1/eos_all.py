import requests
import csv

# 设置代理（可以根据需要开启代理）
# proxy = {
#     'http': 'http://localhost:7890',  # 使用本地代理（可以换成其他代理地址）
#     'https': 'http://localhost:7890'  # 使用本地代理（可以换成其他代理地址）
# }

# 设置 EOS RPC URL（此处使用公共节点）
eos_rpc_url = "https://eos.greymass.com"  # 可以替换为自己的 EOS 节点或者其他公共节点
session = requests.Session()

# session.proxies.update(proxy)

# 获取最新区块信息
def get_latest_block():
    """获取最新区块信息，包括最新区块的号"""
    url = f"{eos_rpc_url}/v1/chain/get_info"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # 返回区块链状态的 JSON 响应
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 获取区块详细信息
def get_block(block_num):
    """根据区块号获取指定区块的详细信息"""
    url = f"{eos_rpc_url}/v1/chain/get_block"
    payload = {
        "block_num_or_id": block_num  # 通过区块号或区块 ID 获取区块信息
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()  # 返回区块的 JSON 响应
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 保存区块信息到 CSV 文件
def save_block_info_to_csv(block_info):
    """将区块信息保存到 CSV 文件"""
    with open('eos_all.csv', mode='a', newline='') as file:
        writer = csv.writer(file)

        # 写入 CSV 文件的标题行
        writer.writerow([
            "Block Number", "Block ID", "Timestamp", "Producer", "Transaction Count",
            "Transactions", "Previous Block ID", "Block Size", "Actions"
        ])

        for block in block_info:
            # 提取区块信息
            block_number = block['block_num']  # 区块号
            block_id = block['id']  # 区块 ID
            timestamp = block['timestamp']  # 区块时间戳，表示区块创建的时间
            producer = block['producer']  # 区块生产者（谁生产了该区块）
            transaction_count = len(block['transactions'])  # 当前区块的交易数量
            transactions = block['transactions']  # 当前区块的所有交易信息
            previous_block_id = block['previous']  # 上一个区块的 ID
            block_size = block['block_size'] if 'block_size' in block else 'N/A'  # 区块大小
            actions = block['actions'] if 'actions' in block else 'N/A'  # 执行的动作（如果有）

            # 将区块信息写入文件
            writer.writerow([block_number, block_id, timestamp, producer, transaction_count,
                             transactions, previous_block_id, block_size, actions])

            print(f"区块 {block_number} 信息已写入文件")

        # 插入一个空行
        writer.writerow([])  # 空行

# 获取指定区块范围的数据
def get_blocks_in_range(start_block_num, end_block_num):
    """获取指定区块范围内的区块信息"""
    block_info_list = []
    for block_num in range(start_block_num, end_block_num + 1):  # 包括 end_block_num
        block_info = get_block(block_num)  # 获取指定区块的详细信息
        if block_info:
            block_info_list.append(block_info)  # 将区块信息添加到列表中
        else:
            print(f"无法获取区块 {block_num} 的信息")
    return block_info_list

# 主函数
try:
    latest_block_info = get_latest_block()  # 获取最新的区块信息
    if latest_block_info:
        latest_block_num = latest_block_info['head_block_num']  # 获取最新区块的区块号
        print(f"最新区块号: {latest_block_num}")

        # 设置开始区块号和结束区块号
        start_block_number = 1000000  # 设置开始区块号
        end_block_number = 1000100    # 设置结束区块号

        # 获取指定范围内的区块信息
        block_info_list = get_blocks_in_range(start_block_number, end_block_number)

        # 保存区块信息到 CSV
        save_block_info_to_csv(block_info_list)

    print("数据已成功保存到 eos_all.csv 文件中")

except Exception as e:
    print(f"获取数据时发生错误: {e}")
