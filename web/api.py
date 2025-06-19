"""
Web API接口
"""
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio

from analysis.data_analyzer import DataAnalyzer
from scheduler.task_scheduler import scheduler
from database.database import get_db, Session
from database.models import Product, Platform, Category
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="电商热销数据分析系统API"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic模型
class TrendingProductResponse(BaseModel):
    product_id: int
    title: str
    current_price: Optional[float]
    original_price: Optional[float]
    platform_name: str
    category_name: str
    total_sales: int
    avg_rating: float
    trending_score: float
    growth_rate: float
    product_url: Optional[str]
    image_url: Optional[str]
    last_updated: Optional[datetime]

class CategoryTrendResponse(BaseModel):
    category_id: int
    category_name: str
    platform_id: int
    platform_name: str
    product_count: int
    total_sales: int
    avg_price: float
    avg_rating: float
    heat_score: float
    growth_rate: float

class MarketInsightResponse(BaseModel):
    overview: Dict[str, Any]
    price_analysis: Dict[str, Any]
    platform_ranking: List[Dict[str, Any]]
    category_ranking: List[Dict[str, Any]]

class JobResponse(BaseModel):
    id: str
    name: str
    next_run_time: Optional[datetime]
    trigger: str

# 依赖注入
def get_analyzer():
    return DataAnalyzer()

# API路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """首页"""
    return """
    <html>
        <head>
            <title>电商热销数据分析系统</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>电商热销数据分析系统</h1>
            <p>API文档: <a href="/docs">/docs</a></p>
            <p>前端界面: <a href="/static/index.html">/static/index.html</a></p>
        </body>
    </html>
    """

@app.get("/api/trending-products", response_model=List[TrendingProductResponse])
async def get_trending_products(
    time_period: str = Query("1day", description="时间周期: 15min, 1hour, 1day, 1week, 1month"),
    limit: int = Query(50, description="返回数量限制"),
    analyzer: DataAnalyzer = Depends(get_analyzer)
):
    """获取热门商品"""
    try:
        products = analyzer.analyze_trending_products(time_period, limit)
        return products
    except Exception as e:
        logger.error(f"获取热门商品失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category-trends", response_model=List[CategoryTrendResponse])
async def get_category_trends(
    time_period: str = Query("1day", description="时间周期"),
    analyzer: DataAnalyzer = Depends(get_analyzer)
):
    """获取分类趋势"""
    try:
        trends = analyzer.analyze_category_trends(time_period)
        return trends
    except Exception as e:
        logger.error(f"获取分类趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/price-trends/{product_id}")
async def get_price_trends(
    product_id: int,
    days: int = Query(30, description="分析天数"),
    analyzer: DataAnalyzer = Depends(get_analyzer)
):
    """获取商品价格趋势"""
    try:
        trends = analyzer.analyze_price_trends(product_id, days)
        return trends
    except Exception as e:
        logger.error(f"获取价格趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations(
    category_name: Optional[str] = Query(None, description="分类名称"),
    max_price: Optional[float] = Query(None, description="最大价格"),
    min_rating: float = Query(4.0, description="最小评分"),
    limit: int = Query(20, description="返回数量"),
    analyzer: DataAnalyzer = Depends(get_analyzer)
):
    """获取商品推荐"""
    try:
        recommendations = analyzer.get_product_recommendations(
            category_name, max_price, min_rating, limit
        )
        return recommendations
    except Exception as e:
        logger.error(f"获取商品推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-insights", response_model=MarketInsightResponse)
async def get_market_insights(
    time_period: str = Query("1week", description="时间周期"),
    analyzer: DataAnalyzer = Depends(get_analyzer)
):
    """获取市场洞察"""
    try:
        insights = analyzer.get_market_insights(time_period)
        return insights
    except Exception as e:
        logger.error(f"获取市场洞察失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms")
async def get_platforms(db: Session = Depends(get_db)):
    """获取所有平台"""
    try:
        platforms = db.query(Platform).filter(Platform.is_active == True).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "base_url": p.base_url
            }
            for p in platforms
        ]
    except Exception as e:
        logger.error(f"获取平台列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    try:
        categories = db.query(Category).filter(Category.is_active == True).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "display_name": c.display_name,
                "level": c.level,
                "parent_id": c.parent_id
            }
            for c in categories
        ]
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
async def get_products(
    platform_id: Optional[int] = Query(None, description="平台ID"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    limit: int = Query(100, description="返回数量"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取商品列表"""
    try:
        query = db.query(Product).filter(Product.is_available == True)
        
        if platform_id:
            query = query.filter(Product.platform_id == platform_id)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        products = query.order_by(Product.last_updated.desc())\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        
        return [
            {
                "id": p.id,
                "title": p.title,
                "current_price": p.current_price,
                "original_price": p.original_price,
                "rating": p.rating,
                "sales_count": p.sales_count,
                "product_url": p.product_url,
                "image_url": p.image_url,
                "last_updated": p.last_updated
            }
            for p in products
        ]
    except Exception as e:
        logger.error(f"获取商品列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 任务管理API
@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs():
    """获取所有定时任务"""
    try:
        jobs = scheduler.get_jobs()
        return jobs
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/run")
async def run_job_now(job_id: str, background_tasks: BackgroundTasks):
    """立即执行任务"""
    try:
        background_tasks.add_task(scheduler.run_job_now, job_id)
        return {"message": f"任务 {job_id} 已开始执行"}
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """暂停任务"""
    try:
        scheduler.pause_job(job_id)
        return {"message": f"任务 {job_id} 已暂停"}
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """恢复任务"""
    try:
        scheduler.resume_job(job_id)
        return {"message": f"任务 {job_id} 已恢复"}
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 统计API
@app.get("/api/stats/overview")
async def get_stats_overview(db: Session = Depends(get_db)):
    """获取统计概览"""
    try:
        total_products = db.query(Product).filter(Product.is_available == True).count()
        total_platforms = db.query(Platform).filter(Platform.is_active == True).count()
        total_categories = db.query(Category).filter(Category.is_active == True).count()
        
        # 最近更新的商品
        recent_products = db.query(Product)\
            .filter(Product.is_available == True)\
            .order_by(Product.last_updated.desc())\
            .limit(5)\
            .all()
        
        return {
            "total_products": total_products,
            "total_platforms": total_platforms,
            "total_categories": total_categories,
            "recent_products": [
                {
                    "id": p.id,
                    "title": p.title[:50] + "..." if len(p.title) > 50 else p.title,
                    "current_price": p.current_price,
                    "last_updated": p.last_updated
                }
                for p in recent_products
            ]
        }
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.VERSION,
        "scheduler_running": scheduler.is_running
    }

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("启动电商数据分析系统...")
    
    # 初始化数据库
    from database.database import init_database
    init_database()
    
    # 启动任务调度器
    scheduler.start()
    
    logger.info("系统启动完成")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭电商数据分析系统...")
    
    # 停止任务调度器
    scheduler.stop()
    
    logger.info("系统已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True
    )