# 电商热销数据分析系统使用指南

## 系统概述

这是一个专业的电商平台热销数据爬取和分析工具，支持多平台数据采集、多维度统计分析和智能选品推荐。

## 功能特性

### 🛒 支持平台
- **Amazon** - 美区亚马逊热销商品数据
- **Temu** - 拼多多海外版商品数据  
- **eBay** - 拍卖和固定价格商品数据
- **TikTok Shop** - 抖音电商平台数据

### 📊 数据分析维度
- **时间维度**: 15分钟、1小时、1天、1周、1月
- **品类分析**: 各类目热度排行和趋势
- **商品分析**: 热门商品识别和价格监控
- **选品推荐**: 基于多维度数据的智能推荐

## 快速开始

### 1. 启动系统

```bash
# 进入项目目录
cd /workspace/sell-data-getter

# 启动后端服务
python app.py
```

系统启动后，你可以访问：

- **API文档**: http://localhost:12000/docs
- **前端界面**: http://localhost:12000/static/index.html
- **健康检查**: http://localhost:12000/api/health

### 2. 访问前端界面

打开浏览器访问 `http://localhost:12000/static/index.html`

界面包含以下模块：
- **仪表板**: 系统概览和关键指标
- **热门商品**: 实时热销商品排行
- **分类趋势**: 各品类热度分析
- **价格分析**: 商品价格趋势监控
- **选品推荐**: 智能选品建议
- **任务管理**: 爬虫任务调度管理

### 3. API使用

#### 获取热门商品
```bash
curl "http://localhost:12000/api/trending-products?time_period=1day&limit=20"
```

#### 获取分类趋势
```bash
curl "http://localhost:12000/api/category-trends?time_period=1day"
```

#### 获取商品列表
```bash
curl "http://localhost:12000/api/products?limit=50"
```

#### 获取统计概览
```bash
curl "http://localhost:12000/api/stats/overview"
```

#### 获取市场洞察
```bash
curl "http://localhost:12000/api/market-insights?time_period=1week"
```

## 系统配置

### 爬虫配置

编辑 `config/settings.py` 文件来配置爬虫参数：

```python
PLATFORMS = {
    "amazon": {
        "enabled": True,
        "update_interval": 3600,  # 1小时更新一次
        "max_pages": 10
    },
    "temu": {
        "enabled": True, 
        "update_interval": 3600,
        "max_pages": 10
    }
}
```

### 分析配置

```python
ANALYSIS_CONFIG = {
    "time_intervals": ["15min", "1hour", "1day", "1week", "1month"],
    "trending_threshold": 0.2,
    "hot_product_min_sales": 100,
    "category_weights": {
        "mens-clothing": 1.0,
        "electronics": 0.8
    }
}
```

## 任务管理

### 查看定时任务
```bash
curl "http://localhost:12000/api/jobs"
```

### 立即执行任务
```bash
curl -X POST "http://localhost:12000/api/jobs/scraper_amazon/run"
```

### 暂停任务
```bash
curl -X POST "http://localhost:12000/api/jobs/scraper_amazon/pause"
```

## 数据库

系统使用SQLite数据库存储数据，数据库文件位于 `data/ecommerce_data.db`

主要数据表：
- `products` - 商品信息
- `platforms` - 平台信息
- `categories` - 分类信息
- `sales_data` - 销售数据
- `price_history` - 价格历史
- `trending_products` - 热门商品
- `category_trends` - 分类趋势

## 演示数据

系统包含演示数据，可以运行以下命令创建测试数据：

```bash
python demo_data.py
```

这将创建5个示例商品及相关的价格历史和销售数据。

## 注意事项

### 合规使用
- 遵守各平台的robots.txt规则
- 设置合理的请求间隔避免被封IP
- 仅用于合法的商业分析目的

### 性能优化
- 根据需要调整爬虫并发数和请求间隔
- 定期清理历史数据避免数据库过大
- 使用代理池提高爬取效率

### 数据准确性
- 数据仅供参考，实际决策需结合多方信息
- 定期验证数据准确性
- 关注平台政策变化对数据的影响

## 故障排除

### 常见问题

1. **爬虫无法获取数据**
   - 检查网络连接
   - 验证目标网站是否可访问
   - 检查User-Agent和请求头设置

2. **数据库连接错误**
   - 确保数据库文件权限正确
   - 检查数据库路径配置

3. **前端页面无法加载**
   - 确保静态文件已正确构建
   - 检查端口是否被占用

### 日志查看

系统日志保存在 `logs/app.log`，可以通过以下命令查看：

```bash
tail -f logs/app.log
```

## 扩展开发

### 添加新平台

1. 在 `scrapers/` 目录下创建新的爬虫类
2. 继承 `BaseScraper` 类
3. 实现 `scrape_category` 和 `_extract_product_info` 方法
4. 在配置文件中添加平台配置

### 自定义分析算法

1. 在 `analysis/` 目录下扩展 `DataAnalyzer` 类
2. 添加新的分析方法
3. 在API中暴露新的分析接口

### 前端界面定制

1. 修改 `frontend/src/` 下的Vue组件
2. 运行 `npm run build` 重新构建
3. 重启后端服务

## 技术支持

如有问题或建议，请查看：
- 系统日志文件
- API文档 (http://localhost:12000/docs)
- 项目README文件

---

**免责声明**: 本系统仅供学习和研究使用，使用者需自行承担数据使用的法律责任。