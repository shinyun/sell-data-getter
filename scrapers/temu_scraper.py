"""
Temu爬虫
"""
import asyncio
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from config.settings import TEMU_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class TemuScraper(BaseScraper):
    """Temu商品爬虫"""
    
    def __init__(self):
        super().__init__("temu")
        self.base_url = "https://www.temu.com"
        self.search_urls = TEMU_CONFIG["search_urls"]
        self.selectors = TEMU_CONFIG["selectors"]
    
    def _get_headers(self) -> Dict[str, str]:
        """重写请求头，Temu需要特殊的请求头"""
        headers = super()._get_headers()
        headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.temu.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        return headers
    
    async def scrape_category(self, category: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """爬取指定分类的商品"""
        if category not in self.search_urls:
            logger.warning(f"不支持的分类: {category}")
            return []
        
        base_search_url = self.search_urls[category]
        all_products = []
        
        for page in range(1, max_pages + 1):
            try:
                # Temu的分页参数
                page_url = f"{base_search_url}&page={page}"
                
                logger.info(f"爬取Temu {category} 第 {page} 页")
                
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
                
                # Temu通常会加载更多商品而不是传统分页
                if len(products) < 20:  # 如果商品数量少于预期，可能到了最后
                    break
                
            except Exception as e:
                logger.error(f"爬取第 {page} 页时发生错误: {e}")
                continue
        
        logger.info(f"Temu {category} 分类爬取完成，总计 {len(all_products)} 个商品")
        return all_products
    
    def _extract_product_info(self, soup: BeautifulSoup, base_url: str = "") -> List[Dict[str, Any]]:
        """从Temu页面提取商品信息"""
        products = []
        
        # 尝试多种可能的商品容器选择器
        product_containers = (
            soup.find_all('div', class_=lambda x: x and 'goods-item' in x) or
            soup.find_all('div', class_=lambda x: x and 'product-item' in x) or
            soup.find_all('div', {'data-testid': 'product-item'}) or
            soup.find_all('article') or
            soup.find_all('div', class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['item', 'product', 'goods']))
        )
        
        # 如果没有找到容器，尝试查找JSON数据
        if not product_containers:
            products_from_json = self._extract_from_json(soup)
            if products_from_json:
                return products_from_json
        
        for container in product_containers:
            try:
                product_data = {}
                
                # 商品标题 - 尝试多种选择器
                title_elem = (
                    container.select_one('[data-testid="product-title"]') or
                    container.select_one('.goods-title') or
                    container.select_one('.product-title') or
                    container.select_one('h3') or
                    container.select_one('h2') or
                    container.select_one('[title]')
                )
                
                if title_elem:
                    title = title_elem.get_text() or title_elem.get('title', '')
                    product_data['title'] = self._clean_text(title)
                else:
                    continue  # 没有标题的跳过
                
                # 商品链接
                link_elem = (
                    container.select_one('a[href]') or
                    container.find_parent('a') if container.name != 'a' else container
                )
                
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href.startswith('/'):
                        product_data['product_url'] = base_url + href
                    elif href.startswith('http'):
                        product_data['product_url'] = href
                    else:
                        product_data['product_url'] = base_url + '/' + href
                
                # 商品价格 - Temu通常显示折扣价
                price_elem = (
                    container.select_one('[data-testid="product-price"]') or
                    container.select_one('.goods-price') or
                    container.select_one('.price-current') or
                    container.select_one('.price') or
                    container.select_one('[class*="price"]')
                )
                
                if price_elem:
                    price_text = price_elem.get_text()
                    product_data['current_price'] = self._parse_price(price_text)
                
                # 原价
                original_price_elem = (
                    container.select_one('.price-original') or
                    container.select_one('.original-price') or
                    container.select_one('[class*="original"]')
                )
                
                if original_price_elem:
                    original_price_text = original_price_elem.get_text()
                    product_data['original_price'] = self._parse_price(original_price_text)
                
                # 销量信息
                sales_elem = (
                    container.select_one('[data-testid="sales-count"]') or
                    container.select_one('.sales-count') or
                    container.select_one('[class*="sold"]') or
                    container.select_one('[class*="sales"]')
                )
                
                if sales_elem:
                    sales_text = sales_elem.get_text()
                    product_data['sales_count'] = self._parse_sales_count(sales_text)
                
                # 商品评分
                rating_elem = (
                    container.select_one('[data-testid="rating"]') or
                    container.select_one('.rating') or
                    container.select_one('[class*="star"]')
                )
                
                if rating_elem:
                    rating_text = rating_elem.get_text() or rating_elem.get('aria-label', '')
                    product_data['rating'] = self._parse_rating(rating_text)
                
                # 评价数量
                review_elem = (
                    container.select_one('[data-testid="review-count"]') or
                    container.select_one('.review-count') or
                    container.select_one('[class*="review"]')
                )
                
                if review_elem:
                    review_text = review_elem.get_text()
                    product_data['review_count'] = self._parse_sales_count(review_text)
                
                # 商品图片
                img_elem = (
                    container.select_one('[data-testid="product-image"] img') or
                    container.select_one('img[src]')
                )
                
                if img_elem:
                    img_src = img_elem.get('src') or img_elem.get('data-src')
                    if img_src:
                        if img_src.startswith('//'):
                            product_data['image_url'] = 'https:' + img_src
                        elif img_src.startswith('/'):
                            product_data['image_url'] = base_url + img_src
                        else:
                            product_data['image_url'] = img_src
                
                # 折扣信息
                discount_elem = container.select_one('[class*="discount"], [class*="off"]')
                if discount_elem:
                    discount_text = discount_elem.get_text()
                    product_data['discount_rate'] = self._parse_discount(discount_text)
                
                # 设置默认值
                product_data.setdefault('currency', 'USD')
                product_data.setdefault('is_available', True)
                
                # 只保存有效的商品数据
                if product_data.get('title') and (product_data.get('current_price') or product_data.get('sales_count')):
                    products.append(product_data)
                
            except Exception as e:
                logger.error(f"解析商品信息时发生错误: {e}")
                continue
        
        return products
    
    def _extract_from_json(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从页面中的JSON数据提取商品信息"""
        products = []
        
        # 查找包含商品数据的script标签
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', string=lambda text: text and 'goods' in text.lower()))
        
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    products_data = self._find_products_in_json(data)
                    if products_data:
                        products.extend(products_data)
                        break
            except (json.JSONDecodeError, Exception) as e:
                continue
        
        return products
    
    def _find_products_in_json(self, data: Any) -> List[Dict[str, Any]]:
        """在JSON数据中递归查找商品信息"""
        products = []
        
        if isinstance(data, dict):
            # 检查是否是商品对象
            if self._is_product_object(data):
                product_data = self._parse_product_from_json(data)
                if product_data:
                    products.append(product_data)
            else:
                # 递归查找
                for value in data.values():
                    products.extend(self._find_products_in_json(value))
        
        elif isinstance(data, list):
            for item in data:
                products.extend(self._find_products_in_json(item))
        
        return products
    
    def _is_product_object(self, obj: Dict) -> bool:
        """判断是否是商品对象"""
        product_keys = ['title', 'name', 'price', 'goods_name', 'product_name']
        return any(key in obj for key in product_keys)
    
    def _parse_product_from_json(self, data: Dict) -> Dict[str, Any]:
        """从JSON对象解析商品信息"""
        product_data = {}
        
        # 标题
        title = (data.get('title') or data.get('name') or 
                data.get('goods_name') or data.get('product_name'))
        if title:
            product_data['title'] = self._clean_text(str(title))
        
        # 价格
        price = (data.get('price') or data.get('current_price') or 
                data.get('sale_price'))
        if price:
            product_data['current_price'] = float(price) if isinstance(price, (int, float)) else self._parse_price(str(price))
        
        # 原价
        original_price = data.get('original_price') or data.get('market_price')
        if original_price:
            product_data['original_price'] = float(original_price) if isinstance(original_price, (int, float)) else self._parse_price(str(original_price))
        
        # 销量
        sales = data.get('sales') or data.get('sold_count')
        if sales:
            product_data['sales_count'] = int(sales) if isinstance(sales, (int, float)) else self._parse_sales_count(str(sales))
        
        # 评分
        rating = data.get('rating') or data.get('score')
        if rating:
            product_data['rating'] = float(rating) if isinstance(rating, (int, float)) else self._parse_rating(str(rating))
        
        # 图片
        image = data.get('image') or data.get('thumb') or data.get('picture')
        if image:
            product_data['image_url'] = str(image)
        
        # 链接
        url = data.get('url') or data.get('link') or data.get('goods_url')
        if url:
            product_data['product_url'] = str(url)
        
        return product_data if product_data.get('title') else {}
    
    def _parse_discount(self, discount_text: str) -> float:
        """解析折扣率"""
        import re
        # 匹配 "50% off", "-50%", "50%" 等格式
        match = re.search(r'(\d+)%', discount_text)
        if match:
            return float(match.group(1)) / 100
        return 0.0

# 使用示例
async def main():
    async with TemuScraper() as scraper:
        # 爬取男装分类
        products = await scraper.scrape_category("mens-fashion", max_pages=3)
        print(f"获取到 {len(products)} 个商品")
        
        for product in products[:5]:  # 显示前5个商品
            print(f"标题: {product.get('title')}")
            print(f"价格: ${product.get('current_price')}")
            print(f"销量: {product.get('sales_count')}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())