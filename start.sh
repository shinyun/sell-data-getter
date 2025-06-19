#!/bin/bash

# 电商热销数据分析系统启动脚本

echo "🚀 启动电商热销数据分析系统..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python -c "from database.database import init_database; init_database()"

# 创建演示数据（可选）
read -p "是否创建演示数据？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 创建演示数据..."
    python demo_data.py
fi

# 构建前端（如果需要）
if [ -f "package.json" ]; then
    echo "🔨 构建前端..."
    npm install
    npm run build
fi

# 启动服务
echo "🌟 启动服务..."
echo "📍 API文档: http://localhost:12000/docs"
echo "🖥️ 前端界面: http://localhost:12000/static/index.html"
echo "❤️ 健康检查: http://localhost:12000/api/health"
echo ""
echo "按 Ctrl+C 停止服务"

python app.py