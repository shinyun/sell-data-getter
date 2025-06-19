"""
基础爬虫类
"""
import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from config.settings import settings
from utils.logger import get_logger
from database.database import get_db_session
from database.models import Product, ScrapingLog, Platform, Category
from datetime import datetime

logger = get_logger(__name__)

class BaseScraper(ABC):
    """基础爬虫类"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.ua = UserAgent()
        self.session = None
        self.db = get_db_session()
        self.platform = self._get_platform()
        self.scraping_log = None
        
        # 爬虫配置
        self.config = settings.SCRAPER_CONFIG
        self.request_delay = self.config.get("request_delay", 2)
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
        
    def _get_platform(self) -> Optional[Platform]:
        """获取平台信息"""
        return self.db.query(Platform).filter(Platform.name == self.platform_name).first()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
        if self.db:
            self.db.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': random.choice(self.config["user_agents"]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def _make_request(self, url: str, **kwargs) -> Optional[str]:
        """发起HTTP请求"""
        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.request_delay)
                
                async with self.session.get(url, **kwargs) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"成功获取页面: {url}")
                        return content
                    elif response.status == 429:
                        # 被限流，增加等待时间
                        wait_time = (attempt + 1) * 10
                        logger.warning(f"被限流，等待 {wait_time} 秒后重试")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"请求失败，状态码: {response.status}, URL: {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"请求超时，第 {attempt + 1} 次尝试: {url}")
            except Exception as e:
                logger.error(f"请求异常，第 {attempt + 1} 次尝试: {url}, 错误: {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(random.uniform(1, 3))
        
        logger.error(f"请求失败，已达到最大重试次数: {url}")
        return None
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, 'html.parser')
    
    def _start_scraping_log(self, category_name: str = None) -> ScrapingLog:
        """开始爬取日志记录"""
        category = None
        if category_name:
            category = self.db.query(Category).filter(Category.name == category_name).first()
        
        log = ScrapingLog(
            platform_id=self.platform.id if self.platform else None,
            category_id=category.id if category else None,
            task_id=f"{self.platform_name}_{int(time.time())}",
            status="running",
            started_at=datetime.utcnow()
        )
        
        self.db.add(log)
        self.db.commit()
        self.scraping_log = log
        return log
    
    def _update_scraping_log(self, status: str, products_scraped: int = 0, error_message: str = None):
        """更新爬取日志"""
        if self.scraping_log:
            self.scraping_log.status = status
            self.scraping_log.products_scraped = products_scraped
            self.scraping_log.completed_at = datetime.utcnow()
            
            if self.scraping_log.started_at:
                duration = (self.scraping_log.completed_at - self.scraping_log.started_at).total_seconds()
                self.scraping_log.duration = int(duration)
            
            if error_message:
                self.scraping_log.error_message = error_message
                self.scraping_log.errors_count = 1
            
            self.db.commit()
    
    def _save_product(self, product_data: Dict[str, Any], category_name: str) -> Optional[Product]:
        """保存商品数据"""
        try:
            category = self.db.query(Category).filter(Category.name == category_name).first()
            if not category:
                logger.warning(f"分类不存在: {category_name}")
                return None
            
            # 检查商品是否已存在
            existing_product = self.db.query(Product).filter(
                Product.platform_id == self.platform.id,
                Product.title == product_data.get('title'),
                Product.product_url == product_data.get('product_url')
            ).first()
            
            if existing_product:
                # 更新现有商品
                for key, value in product_data.items():
                    if hasattr(existing_product, key) and value is not None:
                        setattr(existing_product, key, value)
                existing_product.last_updated = datetime.utcnow()
                self.db.commit()
                return existing_product
            else:
                # 创建新商品
                product = Product(
                    platform_id=self.platform.id,
                    category_id=category.id,
                    **product_data,
                    first_seen=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                
                self.db.add(product)
                self.db.commit()
                return product
                
        except Exception as e:
            logger.error(f"保存商品数据失败: {e}")
            self.db.rollback()
            return None
    
    @abstractmethod
    async def scrape_category(self, category: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """爬取指定分类的商品数据"""
        pass
    
    @abstractmethod
    def _extract_product_info(self, soup: BeautifulSoup, base_url: str = "") -> List[Dict[str, Any]]:
        """从页面提取商品信息"""
        pass
    
    async def scrape_all_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """爬取所有配置的分类"""
        platform_config = settings.PLATFORMS.get(self.platform_name, {})
        categories = platform_config.get("categories", [])
        max_pages = platform_config.get("max_pages", 10)
        
        results = {}
        total_products = 0
        
        # 开始爬取日志
        self._start_scraping_log()
        
        try:
            for category in categories:
                logger.info(f"开始爬取分类: {category}")
                category_products = await self.scrape_category(category, max_pages)
                results[category] = category_products
                total_products += len(category_products)
                
                # 保存商品数据
                for product_data in category_products:
                    self._save_product(product_data, category)
                
                logger.info(f"分类 {category} 爬取完成，获得 {len(category_products)} 个商品")
            
            # 更新爬取日志
            self._update_scraping_log("success", total_products)
            logger.info(f"平台 {self.platform_name} 爬取完成，总计 {total_products} 个商品")
            
        except Exception as e:
            error_msg = f"爬取过程中发生错误: {e}"
            logger.error(error_msg)
            self._update_scraping_log("failed", total_products, error_msg)
            raise
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        return text.strip().replace('\n', ' ').replace('\r', ' ')
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """解析价格"""
        if not price_text:
            return None
        
        # 移除货币符号和其他字符，只保留数字和小数点
        import re
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                pass
        return None
    
    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """解析评分"""
        if not rating_text:
            return None
        
        import re
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            try:
                rating = float(rating_match.group(1))
                return min(rating, 5.0)  # 限制最高5分
            except ValueError:
                pass
        return None
    
    def _parse_sales_count(self, sales_text: str) -> Optional[int]:
        """解析销量"""
        if not sales_text:
            return None
        
        import re
        # 处理各种销量格式：1000+, 1k+, 1.5k+, sold 100+
        sales_text = sales_text.lower()
        
        if 'k' in sales_text:
            match = re.search(r'(\d+\.?\d*)k', sales_text)
            if match:
                return int(float(match.group(1)) * 1000)
        
        match = re.search(r'(\d+)', sales_text)
        if match:
            return int(match.group(1))
        
        return None