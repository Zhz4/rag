#!/bin/bash

# 初始化数据库
echo "正在初始化数据库..."
python scripts/init_db.py

# 检查上一个命令的执行状态
if [ $? -ne 0 ]; then
    echo "数据库初始化失败"
    exit 1
fi

# 启动主应用
echo "启动主应用..."
python main.py 