# Validation-Tool readme文件

# 区块链数据迁移校验工具  项目介绍
    本工具是为解决区块链数据迁移过程中的数据一致性和完整性校验而开发。 
    用户可以使用友好的操作界面，对选择的区块以及校验范围进行校验。过程可分为数据获取和数据校验两个部分。
    开发者：[赖峥、王艺璇、强婉筼、于泽琪]  
 
# 环境依赖
    python版本：python3
    MongoDB：
 
# 目录结构描述

├── README.md // 说明文档

├── .venv // Python虚拟环境目录

│

├── 1 // 数据获取模块目录

│ ├── pycache // Python字节码缓存目录

│ ├── Eos.py // Eosio数据获取

│ ├── Ganache.py // Ganache测试网数据获取

│ ├── main.py // 主程序入口

│ └── Sepolia.py // Sepolia测试网数据获取

│

├── 2 // 验证规则模块目录

│ └── Validation_Rules.py // 验证规则定义文件

│

└── 3 // 用户访问工具目录

├── index.html // 主页面

├── script.js // JavaScript脚本

└── styles.css // 样式表文件
 
# 使用说明
 
 
 
# 版本内容更新
## v1.0.0: 
    1.实现gen文件的拷贝、合并
    
    2.实现common文件的合并
    
    3.实现指定版本的include、src、lib文件的拷贝
## v1.0.1: 
    1.

    2.

    3.

