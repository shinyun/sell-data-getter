"""
Amazon爬虫
"""
import asyncio
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from config.settings import AMAZON_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class AmazonScraper(BaseScraper):
    """Amazon商品爬虫"""
    
    def __init__(self):
        super().__init__("amazon")
        self.base_url = "https://www.amazon.com"
        self.search_urls = AMAZON_CONFIG["search_urls"]
        self.selectors = AMAZON_CONFIG["selectors"]
    
    async def scrape_category(self, category: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """爬取指定分类的商品"""
        if category not in self.search_urls:
            logger.warning(f"不支持的分类: {category}")
            return []
        
        base_search_url = self.search_urls[category]
        all_products = []
        
        for page in range(1, max_pages + 1):
            try:
                # 构建分页URL
                if "?" in base_search_url:
                    page_url = f"{base_search_url}&page={page}"
                else:
                    page_url = f"{base_search_url}?page={page}"
                
                logger.info(f"爬取Amazon {category} 第 {page} 页")
                
                html = await self._make_request(page_url)
                if not html:
                    logger.warning(f"无法获取页面内容: {page_url}")
                    continue
                
                soup = self._parse_html(html)
                products = self._extract_product_info(soup, self.base_url)
                
                if not products:
                    logger.info(f"第 {page} 页没有找到商品，可能已到最后一页")
                    break
                
                all_products.extend(products)
                logger.info(f"第 {page} 页获取到 {len(products)} 个商品")
                
                # 检查是否有下一页
                if not self._has_next_page(soup):
                    logger.info("已到达最后一页")
                    break
                
            except Exception as e:
                logger.error(f"爬取第 {page} 页时发生错误: {e}")
                continue
        
        logger.info(f"Amazon {category} 分类爬取完成，总计 {len(all_products)} 个商品")
        return all_products
    
    def _extract_product_info(self, soup: BeautifulSoup, base_url: str = "") -> List[Dict[str, Any]]:
        """从Amazon页面提取商品信息"""
        products = []
        
        # Amazon搜索结果容器
        product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for container in product_containers:
            try:
                product_data = {}
                
                # 商品标题
                title_elem = container.select_one(self.selectors["product_title"])
                if title_elem:
                    product_data['title'] = self._clean_text(title_elem.get_text())
                else:
                    continue  # 没有标题的跳过
                
                # 商品链接
                link_elem = container.select_one(self.selectors["product_link"])
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href.startswith('/'):
                        product_data['product_url'] = base_url + href
                    else:
                        product_data['product_url'] = href
                
                # 商品价格
                price_elem = container.select_one(self.selectors["product_price"])
                if price_elem:
                    price_text = price_elem.get_text()
                    product_data['current_price'] = self._parse_price(price_text)
                
                # 原价（如果有折扣）
                original_price_elem = container.select_one('.a-price.a-text-price .a-offscreen')
                if original_price_elem:
                    original_price_text = original_price_elem.get_text()
                    product_data['original_price'] = self._parse_price(original_price_text)
                
                # 商品评分
                rating_elem = container.select_one(self.selectors["product_rating"])
                if rating_elem:
                    rating_text = rating_elem.get('alt', '')
                    product_data['rating'] = self._parse_rating(rating_text)
                
                # 评价数量
                review_count_elem = container.select_one('a[href*="#customerReviews"] span')
                if review_count_elem:
                    review_text = review_count_elem.get_text()
                    product_data['review_count'] = self._parse_sales_count(review_text)
                
                # 商品图片
                img_elem = container.select_one(self.selectors["product_image"])
                if img_elem:
                    product_data['image_url'] = img_elem.get('src') or img_elem.get('data-src')
                
                # 品牌信息
                brand_elem = container.select_one('span.a-size-base-plus')
                if brand_elem:
                    product_data['brand'] = self._clean_text(brand_elem.get_text())
                
                # 是否有Prime标识
                prime_elem = container.select_one('[aria-label*="Prime"]')
                product_data['has_prime'] = prime_elem is not None
                
                # 是否有折扣
                discount_elem = container.select_one('.a-badge-text')
                if discount_elem and '%' in discount_elem.get_text():
                    discount_text = discount_elem.get_text()
                    product_data['discount_rate'] = self._parse_discount(discount_text)
                
                # 设置默认值
                product_data.setdefault('currency', 'USD')
                product_data.setdefault('is_available', True)
                
                # 只保存有效的商品数据
                if product_data.get('title') and product_data.get('current_price'):
                    products.append(product_data)
                
            except Exception as e:
                logger.error(f"解析商品信息时发生错误: {e}")
                continue
        
        return products
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """检查是否有下一页"""
        next_button = soup.select_one('a[aria-label="Go to next page"]')
        return next_button is not None and not next_button.get('aria-disabled')
    
    def _parse_discount(self, discount_text: str) -> float:
        """解析折扣率"""
        import re
        match = re.search(r'(\d+)%', discount_text)
        if match:
            return float(match.group(1)) / 100
        return 0.0
    
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """获取商品详细信息"""
        html = await self._make_request(product_url)
        if not html:
            return {}
        
        soup = self._parse_html(html)
        details = {}
        
        try:
            # 商品描述
            desc_elem = soup.select_one('#feature-bullets ul')
            if desc_elem:
                details['description'] = self._clean_text(desc_elem.get_text())
            
            # ASIN
            asin_elem = soup.select_one('[data-asin]')
            if asin_elem:
                details['sku'] = asin_elem.get('data-asin')
            
            # 销量排名
            rank_elem = soup.select_one('#SalesRank, #detailBulletsWrapper_feature_div')
            if rank_elem:
                rank_text = rank_elem.get_text()
                details['sales_rank'] = self._parse_sales_rank(rank_text)
            
            # 库存状态
            stock_elem = soup.select_one('#availability span')
            if stock_elem:
                stock_text = stock_elem.get_text().lower()
                details['is_available'] = 'in stock' in stock_text
            
        except Exception as e:
            logger.error(f"获取商品详情时发生错误: {e}")
        
        return details
    
    def _parse_sales_rank(self, rank_text: str) -> int:
        """解析销量排名"""
        import re
        match = re.search(r'#([\d,]+)', rank_text)
        if match:
            return int(match.group(1).replace(',', ''))
        return 0

# 使用示例
async def main():
    async with AmazonScraper() as scraper:
        # 爬取男装分类
        products = await scraper.scrape_category("mens-clothing", max_pages=3)
        print(f"获取到 {len(products)} 个商品")
        
        for product in products[:5]:  # 显示前5个商品
            print(f"标题: {product.get('title')}")
            print(f"价格: ${product.get('current_price')}")
            print(f"评分: {product.get('rating')}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())