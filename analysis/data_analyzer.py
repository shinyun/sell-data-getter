"""
数据分析模块
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database.database import get_db_session
from database.models import (
    Product, SalesData, TrendingProduct, CategoryTrend, 
    Platform, Category, PriceHistory
)
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        self.db = get_db_session()
        self.analysis_config = settings.ANALYSIS_CONFIG
        self.time_intervals = self.analysis_config["time_intervals"]
        self.trending_threshold = self.analysis_config["trending_threshold"]
        self.hot_product_min_sales = self.analysis_config["hot_product_min_sales"]
        self.category_weights = self.analysis_config["category_weights"]
    
    def __del__(self):
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    def analyze_trending_products(self, time_period: str = "1day", limit: int = 50) -> List[Dict[str, Any]]:
        """分析热门商品"""
        try:
            # 计算时间范围
            period_start, period_end = self._get_time_range(time_period)
            
            # 查询商品数据
            query = self.db.query(
                Product,
                func.coalesce(func.sum(SalesData.sales_count), 0).label('total_sales'),
                func.coalesce(func.avg(SalesData.rating), Product.rating).label('avg_rating'),
                func.coalesce(func.sum(SalesData.view_count), 0).label('total_views'),
                Platform.display_name.label('platform_name'),
                Category.display_name.label('category_name')
            ).join(Platform, Product.platform_id == Platform.id)\
             .join(Category, Product.category_id == Category.id)\
             .outerjoin(SalesData, and_(
                 Product.id == SalesData.product_id,
                 SalesData.period_start >= period_start,
                 SalesData.period_end <= period_end
             )).group_by(Product.id)\
             .having(func.coalesce(func.sum(SalesData.sales_count), Product.sales_count) >= self.hot_product_min_sales)\
             .order_by(func.coalesce(func.sum(SalesData.sales_count), Product.sales_count).desc())\
             .limit(limit)
            
            results = []
            for row in query.all():
                product, total_sales, avg_rating, total_views, platform_name, category_name = row
                
                # 计算热度评分
                trending_score = self._calculate_trending_score(
                    sales_count=total_sales or product.sales_count or 0,
                    rating=avg_rating or 0,
                    view_count=total_views or 0,
                    category_name=category_name
                )
                
                # 计算增长率
                growth_rate = self._calculate_growth_rate(product.id, time_period)
                
                results.append({
                    'product_id': product.id,
                    'title': product.title,
                    'current_price': product.current_price,
                    'original_price': product.original_price,
                    'platform_name': platform_name,
                    'category_name': category_name,
                    'total_sales': total_sales or product.sales_count or 0,
                    'avg_rating': round(avg_rating or product.rating or 0, 2),
                    'total_views': total_views or 0,
                    'trending_score': round(trending_score, 2),
                    'growth_rate': round(growth_rate, 2),
                    'product_url': product.product_url,
                    'image_url': product.image_url,
                    'last_updated': product.last_updated
                })
            
            # 保存热门商品数据
            self._save_trending_products(results, time_period, period_start, period_end)
            
            logger.info(f"分析完成，找到 {len(results)} 个热门商品")
            return results
            
        except Exception as e:
            logger.error(f"分析热门商品时发生错误: {e}")
            return []
    
    def analyze_category_trends(self, time_period: str = "1day") -> List[Dict[str, Any]]:
        """分析品类趋势"""
        try:
            period_start, period_end = self._get_time_range(time_period)
            
            # 查询分类数据
            query = self.db.query(
                Category,
                Platform,
                func.count(Product.id).label('product_count'),
                func.coalesce(func.sum(SalesData.sales_count), func.sum(Product.sales_count)).label('total_sales'),
                func.coalesce(func.avg(Product.current_price), 0).label('avg_price'),
                func.coalesce(func.avg(SalesData.rating), func.avg(Product.rating)).label('avg_rating')
            ).join(Product, Category.id == Product.category_id)\
             .join(Platform, Product.platform_id == Platform.id)\
             .outerjoin(SalesData, and_(
                 Product.id == SalesData.product_id,
                 SalesData.period_start >= period_start,
                 SalesData.period_end <= period_end
             )).group_by(Category.id, Platform.id)\
             .having(func.count(Product.id) > 0)
            
            results = []
            for row in query.all():
                category, platform, product_count, total_sales, avg_price, avg_rating = row
                
                # 计算热度评分
                heat_score = self._calculate_category_heat_score(
                    product_count=product_count,
                    total_sales=total_sales or 0,
                    avg_price=avg_price or 0,
                    category_name=category.name
                )
                
                # 计算增长率
                growth_rate = self._calculate_category_growth_rate(category.id, platform.id, time_period)
                
                results.append({
                    'category_id': category.id,
                    'category_name': category.display_name,
                    'platform_id': platform.id,
                    'platform_name': platform.display_name,
                    'product_count': product_count,
                    'total_sales': total_sales or 0,
                    'avg_price': round(avg_price or 0, 2),
                    'avg_rating': round(avg_rating or 0, 2),
                    'heat_score': round(heat_score, 2),
                    'growth_rate': round(growth_rate, 2)
                })
            
            # 按热度评分排序
            results.sort(key=lambda x: x['heat_score'], reverse=True)
            
            # 保存分类趋势数据
            self._save_category_trends(results, time_period, period_start, period_end)
            
            logger.info(f"分析完成，找到 {len(results)} 个分类趋势")
            return results
            
        except Exception as e:
            logger.error(f"分析分类趋势时发生错误: {e}")
            return []
    
    def analyze_price_trends(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """分析商品价格趋势"""
        try:
            # 获取价格历史数据
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            price_history = self.db.query(PriceHistory)\
                .filter(PriceHistory.product_id == product_id)\
                .filter(PriceHistory.recorded_at >= start_date)\
                .order_by(PriceHistory.recorded_at)\
                .all()
            
            if not price_history:
                return {'error': '没有找到价格历史数据'}
            
            # 转换为DataFrame进行分析
            df = pd.DataFrame([{
                'date': ph.recorded_at,
                'price': ph.price,
                'original_price': ph.original_price,
                'discount_rate': ph.discount_rate
            } for ph in price_history])
            
            # 计算统计指标
            current_price = df['price'].iloc[-1]
            min_price = df['price'].min()
            max_price = df['price'].max()
            avg_price = df['price'].mean()
            price_volatility = df['price'].std()
            
            # 计算价格趋势
            if len(df) > 1:
                price_change = current_price - df['price'].iloc[0]
                price_change_rate = (price_change / df['price'].iloc[0]) * 100
            else:
                price_change = 0
                price_change_rate = 0
            
            # 预测未来价格趋势
            trend_direction = self._predict_price_trend(df['price'].values)
            
            return {
                'product_id': product_id,
                'current_price': round(current_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'avg_price': round(avg_price, 2),
                'price_volatility': round(price_volatility, 2),
                'price_change': round(price_change, 2),
                'price_change_rate': round(price_change_rate, 2),
                'trend_direction': trend_direction,
                'data_points': len(df),
                'analysis_period': f'{days} days'
            }
            
        except Exception as e:
            logger.error(f"分析价格趋势时发生错误: {e}")
            return {'error': str(e)}
    
    def get_product_recommendations(self, category_name: str = None, max_price: float = None, 
                                  min_rating: float = 4.0, limit: int = 20) -> List[Dict[str, Any]]:
        """获取商品推荐"""
        try:
            query = self.db.query(Product, Platform.display_name, Category.display_name)\
                .join(Platform, Product.platform_id == Platform.id)\
                .join(Category, Product.category_id == Category.id)\
                .filter(Product.is_available == True)
            
            # 应用过滤条件
            if category_name:
                query = query.filter(Category.name == category_name)
            
            if max_price:
                query = query.filter(Product.current_price <= max_price)
            
            if min_rating:
                query = query.filter(Product.rating >= min_rating)
            
            # 按综合评分排序
            products = query.all()
            
            recommendations = []
            for product, platform_name, category_name in products:
                # 计算推荐评分
                recommendation_score = self._calculate_recommendation_score(product)
                
                recommendations.append({
                    'product_id': product.id,
                    'title': product.title,
                    'current_price': product.current_price,
                    'original_price': product.original_price,
                    'platform_name': platform_name,
                    'category_name': category_name,
                    'rating': product.rating,
                    'review_count': product.review_count,
                    'sales_count': product.sales_count,
                    'recommendation_score': round(recommendation_score, 2),
                    'product_url': product.product_url,
                    'image_url': product.image_url
                })
            
            # 按推荐评分排序
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"获取商品推荐时发生错误: {e}")
            return []
    
    def get_market_insights(self, time_period: str = "1week") -> Dict[str, Any]:
        """获取市场洞察"""
        try:
            period_start, period_end = self._get_time_range(time_period)
            
            # 总体统计
            total_products = self.db.query(Product).filter(Product.is_available == True).count()
            total_platforms = self.db.query(Platform).filter(Platform.is_active == True).count()
            total_categories = self.db.query(Category).filter(Category.is_active == True).count()
            
            # 价格分析
            price_stats = self.db.query(
                func.avg(Product.current_price).label('avg_price'),
                func.min(Product.current_price).label('min_price'),
                func.max(Product.current_price).label('max_price')
            ).filter(Product.current_price.isnot(None)).first()
            
            # 热门平台
            platform_stats = self.db.query(
                Platform.display_name,
                func.count(Product.id).label('product_count'),
                func.avg(Product.rating).label('avg_rating')
            ).join(Product, Platform.id == Product.platform_id)\
             .group_by(Platform.id)\
             .order_by(func.count(Product.id).desc())\
             .all()
            
            # 热门分类
            category_stats = self.db.query(
                Category.display_name,
                func.count(Product.id).label('product_count'),
                func.avg(Product.current_price).label('avg_price')
            ).join(Product, Category.id == Product.category_id)\
             .group_by(Category.id)\
             .order_by(func.count(Product.id).desc())\
             .limit(10)\
             .all()
            
            return {
                'overview': {
                    'total_products': total_products,
                    'total_platforms': total_platforms,
                    'total_categories': total_categories,
                    'analysis_period': time_period
                },
                'price_analysis': {
                    'avg_price': round(price_stats.avg_price or 0, 2),
                    'min_price': round(price_stats.min_price or 0, 2),
                    'max_price': round(price_stats.max_price or 0, 2)
                },
                'platform_ranking': [
                    {
                        'platform_name': name,
                        'product_count': count,
                        'avg_rating': round(rating or 0, 2)
                    }
                    for name, count, rating in platform_stats
                ],
                'category_ranking': [
                    {
                        'category_name': name,
                        'product_count': count,
                        'avg_price': round(price or 0, 2)
                    }
                    for name, count, price in category_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"获取市场洞察时发生错误: {e}")
            return {}
    
    def _get_time_range(self, time_period: str) -> Tuple[datetime, datetime]:
        """获取时间范围"""
        end_time = datetime.utcnow()
        
        if time_period == "15min":
            start_time = end_time - timedelta(minutes=15)
        elif time_period == "1hour":
            start_time = end_time - timedelta(hours=1)
        elif time_period == "1day":
            start_time = end_time - timedelta(days=1)
        elif time_period == "1week":
            start_time = end_time - timedelta(weeks=1)
        elif time_period == "1month":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        return start_time, end_time
    
    def _calculate_trending_score(self, sales_count: int, rating: float, 
                                view_count: int, category_name: str) -> float:
        """计算热度评分"""
        # 基础评分
        sales_score = min(sales_count / 1000, 1.0) * 40  # 销量权重40%
        rating_score = (rating / 5.0) * 30  # 评分权重30%
        view_score = min(view_count / 10000, 1.0) * 20  # 浏览量权重20%
        
        # 分类权重
        category_weight = self.category_weights.get(category_name, 0.5)
        category_score = category_weight * 10  # 分类权重10%
        
        return sales_score + rating_score + view_score + category_score
    
    def _calculate_category_heat_score(self, product_count: int, total_sales: int, 
                                     avg_price: float, category_name: str) -> float:
        """计算分类热度评分"""
        # 商品数量评分
        count_score = min(product_count / 100, 1.0) * 30
        
        # 销量评分
        sales_score = min(total_sales / 10000, 1.0) * 40
        
        # 价格评分（价格适中的分类得分更高）
        if 10 <= avg_price <= 100:
            price_score = 20
        elif 5 <= avg_price <= 200:
            price_score = 15
        else:
            price_score = 10
        
        # 分类权重
        category_weight = self.category_weights.get(category_name, 0.5)
        category_score = category_weight * 10
        
        return count_score + sales_score + price_score + category_score
    
    def _calculate_growth_rate(self, product_id: int, time_period: str) -> float:
        """计算增长率"""
        try:
            # 获取当前周期和上一周期的销量数据
            current_start, current_end = self._get_time_range(time_period)
            prev_start = current_start - (current_end - current_start)
            prev_end = current_start
            
            current_sales = self.db.query(func.sum(SalesData.sales_count))\
                .filter(SalesData.product_id == product_id)\
                .filter(SalesData.period_start >= current_start)\
                .filter(SalesData.period_end <= current_end)\
                .scalar() or 0
            
            prev_sales = self.db.query(func.sum(SalesData.sales_count))\
                .filter(SalesData.product_id == product_id)\
                .filter(SalesData.period_start >= prev_start)\
                .filter(SalesData.period_end <= prev_end)\
                .scalar() or 0
            
            if prev_sales > 0:
                return ((current_sales - prev_sales) / prev_sales) * 100
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_category_growth_rate(self, category_id: int, platform_id: int, time_period: str) -> float:
        """计算分类增长率"""
        try:
            current_start, current_end = self._get_time_range(time_period)
            prev_start = current_start - (current_end - current_start)
            prev_end = current_start
            
            # 查询当前周期的分类趋势数据
            current_trend = self.db.query(CategoryTrend)\
                .filter(CategoryTrend.category_id == category_id)\
                .filter(CategoryTrend.platform_id == platform_id)\
                .filter(CategoryTrend.period_start >= current_start)\
                .first()
            
            prev_trend = self.db.query(CategoryTrend)\
                .filter(CategoryTrend.category_id == category_id)\
                .filter(CategoryTrend.platform_id == platform_id)\
                .filter(CategoryTrend.period_start >= prev_start)\
                .filter(CategoryTrend.period_end <= prev_end)\
                .first()
            
            if current_trend and prev_trend and prev_trend.total_sales > 0:
                return ((current_trend.total_sales - prev_trend.total_sales) / prev_trend.total_sales) * 100
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _predict_price_trend(self, prices: np.ndarray) -> str:
        """预测价格趋势"""
        if len(prices) < 3:
            return "insufficient_data"
        
        # 简单的线性回归预测
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        if slope > 0.1:
            return "rising"
        elif slope < -0.1:
            return "falling"
        else:
            return "stable"
    
    def _calculate_recommendation_score(self, product: Product) -> float:
        """计算推荐评分"""
        # 评分权重30%
        rating_score = (product.rating or 0) / 5.0 * 30
        
        # 销量权重25%
        sales_score = min((product.sales_count or 0) / 1000, 1.0) * 25
        
        # 评价数量权重20%
        review_score = min((product.review_count or 0) / 500, 1.0) * 20
        
        # 价格合理性权重15%
        if product.current_price and product.original_price:
            discount_rate = (product.original_price - product.current_price) / product.original_price
            price_score = min(discount_rate * 2, 1.0) * 15
        else:
            price_score = 10
        
        # 新鲜度权重10%
        if product.last_updated:
            days_since_update = (datetime.utcnow() - product.last_updated).days
            freshness_score = max(0, (7 - days_since_update) / 7) * 10
        else:
            freshness_score = 5
        
        return rating_score + sales_score + review_score + price_score + freshness_score
    
    def _save_trending_products(self, products: List[Dict], time_period: str, 
                              period_start: datetime, period_end: datetime):
        """保存热门商品数据"""
        try:
            for i, product in enumerate(products):
                trending_product = TrendingProduct(
                    product_id=product['product_id'],
                    platform_id=self.db.query(Platform).filter(Platform.display_name == product['platform_name']).first().id,
                    category_id=self.db.query(Category).filter(Category.display_name == product['category_name']).first().id,
                    trending_score=product['trending_score'],
                    rank_position=i + 1,
                    growth_rate=product['growth_rate'],
                    time_period=time_period,
                    period_start=period_start,
                    period_end=period_end
                )
                self.db.add(trending_product)
            
            self.db.commit()
        except Exception as e:
            logger.error(f"保存热门商品数据时发生错误: {e}")
            self.db.rollback()
    
    def _save_category_trends(self, trends: List[Dict], time_period: str, 
                            period_start: datetime, period_end: datetime):
        """保存分类趋势数据"""
        try:
            for trend in trends:
                category_trend = CategoryTrend(
                    category_id=trend['category_id'],
                    platform_id=trend['platform_id'],
                    product_count=trend['product_count'],
                    total_sales=trend['total_sales'],
                    avg_price=trend['avg_price'],
                    avg_rating=trend['avg_rating'],
                    heat_score=trend['heat_score'],
                    growth_rate=trend['growth_rate'],
                    time_period=time_period,
                    period_start=period_start,
                    period_end=period_end
                )
                self.db.add(category_trend)
            
            self.db.commit()
        except Exception as e:
            logger.error(f"保存分类趋势数据时发生错误: {e}")
            self.db.rollback()

# 使用示例
if __name__ == "__main__":
    analyzer = DataAnalyzer()
    
    # 分析热门商品
    trending_products = analyzer.analyze_trending_products("1day", 20)
    print(f"找到 {len(trending_products)} 个热门商品")
    
    # 分析分类趋势
    category_trends = analyzer.analyze_category_trends("1day")
    print(f"找到 {len(category_trends)} 个分类趋势")
    
    # 获取市场洞察
    insights = analyzer.get_market_insights("1week")
    print("市场洞察:", insights)