"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Platform(Base):
    """电商平台表"""
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # amazon, temu, ebay, tiktok_shop
    display_name = Column(String(100), nullable=False)
    base_url = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    products = relationship("Product", back_populates="platform")

class Category(Base):
    """商品分类表"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=1)  # 分类层级
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    parent = relationship("Category", remote_side=[id])
    products = relationship("Product", back_populates="category")

class Product(Base):
    """商品信息表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # 商品基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text)
    sku = Column(String(100))  # 商品SKU
    brand = Column(String(100))
    
    # 价格信息
    current_price = Column(Float)
    original_price = Column(Float)
    currency = Column(String(10), default="USD")
    
    # 销售信息
    sales_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    
    # 链接和图片
    product_url = Column(String(1000))
    image_url = Column(String(1000))
    
    # 状态信息
    is_available = Column(Boolean, default=True)
    is_trending = Column(Boolean, default=False)
    
    # 时间戳
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    platform = relationship("Platform", back_populates="products")
    category = relationship("Category", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    sales_data = relationship("SalesData", back_populates="product")
    
    # 索引
    __table_args__ = (
        Index('idx_platform_category', 'platform_id', 'category_id'),
        Index('idx_trending', 'is_trending'),
        Index('idx_last_updated', 'last_updated'),
    )

class PriceHistory(Base):
    """价格历史表"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_rate = Column(Float)  # 折扣率
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    product = relationship("Product", back_populates="price_history")
    
    # 索引
    __table_args__ = (
        Index('idx_product_time', 'product_id', 'recorded_at'),
    )

class SalesData(Base):
    """销售数据表"""
    __tablename__ = "sales_data"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # 销售指标
    sales_count = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    view_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    # 评价指标
    review_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    positive_rate = Column(Float, default=0.0)
    
    # 时间维度
    time_period = Column(String(20))  # 15min, 1hour, 1day, 1week, 1month
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    product = relationship("Product", back_populates="sales_data")
    
    # 索引
    __table_args__ = (
        Index('idx_product_period', 'product_id', 'time_period', 'period_start'),
        Index('idx_period_range', 'period_start', 'period_end'),
    )

class TrendingProduct(Base):
    """热门商品表"""
    __tablename__ = "trending_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # 热度指标
    trending_score = Column(Float, default=0.0)  # 热度评分
    rank_position = Column(Integer)  # 排名位置
    growth_rate = Column(Float, default=0.0)  # 增长率
    
    # 时间维度
    time_period = Column(String(20))  # 15min, 1hour, 1day, 1week, 1month
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_trending_period', 'time_period', 'period_start'),
        Index('idx_trending_score', 'trending_score'),
        Index('idx_rank_position', 'rank_position'),
    )

class CategoryTrend(Base):
    """品类趋势表"""
    __tablename__ = "category_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    
    # 趋势指标
    product_count = Column(Integer, default=0)  # 商品数量
    total_sales = Column(Integer, default=0)  # 总销量
    avg_price = Column(Float, default=0.0)  # 平均价格
    avg_rating = Column(Float, default=0.0)  # 平均评分
    
    # 热度指标
    heat_score = Column(Float, default=0.0)  # 热度评分
    growth_rate = Column(Float, default=0.0)  # 增长率
    
    # 时间维度
    time_period = Column(String(20))
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_category_period', 'category_id', 'time_period', 'period_start'),
        Index('idx_heat_score', 'heat_score'),
    )

class ScrapingLog(Base):
    """爬取日志表"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # 爬取信息
    task_id = Column(String(100))  # 任务ID
    status = Column(String(20))  # success, failed, running
    products_scraped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # 时间信息
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration = Column(Integer)  # 持续时间（秒）
    
    # 错误信息
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_platform_status', 'platform_id', 'status'),
        Index('idx_started_at', 'started_at'),
    )

class UserPreference(Base):
    """用户偏好设置表"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default")  # 支持多用户
    
    # 偏好设置
    preferred_categories = Column(Text)  # JSON格式存储
    preferred_platforms = Column(Text)  # JSON格式存储
    price_range_min = Column(Float, default=0.0)
    price_range_max = Column(Float, default=1000.0)
    
    # 通知设置
    enable_notifications = Column(Boolean, default=True)
    notification_threshold = Column(Float, default=0.5)  # 热度阈值
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_preferred_categories(self):
        """获取偏好分类列表"""
        if self.preferred_categories:
            return json.loads(self.preferred_categories)
        return []
    
    def set_preferred_categories(self, categories):
        """设置偏好分类列表"""
        self.preferred_categories = json.dumps(categories)
    
    def get_preferred_platforms(self):
        """获取偏好平台列表"""
        if self.preferred_platforms:
            return json.loads(self.preferred_platforms)
        return []
    
    def set_preferred_platforms(self, platforms):
        """设置偏好平台列表"""
        self.preferred_platforms = json.dumps(platforms)