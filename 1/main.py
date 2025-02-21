from flask import Flask, request, jsonify
from eos import fetch_eos_data
from sepolia import fetch_sepolia_data
from ganache import fetch_ganache_data

app = Flask(__name__)


# 根据输入选择网络并调用对应的函数
def fetch_data_from_network(network_type, start_block, end_block):
    if network_type == "eos":
        fetch_eos_data(start_block, end_block)
    elif network_type == "sepolia":
        fetch_sepolia_data(start_block, end_block)
    elif network_type == "ganache":
        fetch_ganache_data(start_block, end_block)
    else:
        return "无效的网络类型", 400  # 返回一个 400 错误，表示无效的网络类型

@app.route('/api', methods=['POST'])
def handle_request():
    try:
        # 获取前端传递的 JSON 数据
        data = request.get_json()
        network_type = data.get('network_type')
        start_block = int(data.get('start_block'))
        end_block = int(data.get('end_block'))

        # 调用 fetch_data_from_network 函数处理数据
        fetch_data_from_network(network_type, start_block, end_block)

        # 返回成功响应
        return jsonify({"message": "报告生成成功"}), 200
    except Exception as e:
        # 处理异常并返回错误信息
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)