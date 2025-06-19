#!/usr/bin/env python3
"""
创建演示数据
"""
import random
from datetime import datetime, timedelta
from database.database import get_db_session
from database.models import Product, Platform, Category, SalesData, PriceHistory

def create_demo_data():
    """创建演示数据"""
    db = get_db_session()
    
    try:
        # 获取平台和分类
        amazon = db.query(Platform).filter(Platform.name == "amazon").first()
        temu = db.query(Platform).filter(Platform.name == "temu").first()
        
        mens_clothing = db.query(Category).filter(Category.name == "mens-clothing").first()
        electronics = db.query(Category).filter(Category.name == "electronics").first()
        
        # 创建示例商品
        demo_products = [
            {
                "platform_id": amazon.id,
                "category_id": mens_clothing.id,
                "title": "Men's Classic Cotton T-Shirt - Comfortable Fit",
                "description": "High-quality cotton t-shirt perfect for everyday wear",
                "current_price": 19.99,
                "original_price": 29.99,
                "sales_count": 1250,
                "review_count": 342,
                "rating": 4.5,
                "product_url": "https://amazon.com/mens-cotton-tshirt",
                "image_url": "https://via.placeholder.com/300x300?text=T-Shirt",
                "brand": "ComfortWear"
            },
            {
                "platform_id": amazon.id,
                "category_id": mens_clothing.id,
                "title": "Men's Slim Fit Jeans - Dark Wash",
                "description": "Premium denim jeans with modern slim fit",
                "current_price": 49.99,
                "original_price": 79.99,
                "sales_count": 890,
                "review_count": 156,
                "rating": 4.3,
                "product_url": "https://amazon.com/mens-slim-jeans",
                "image_url": "https://via.placeholder.com/300x300?text=Jeans",
                "brand": "DenimCo"
            },
            {
                "platform_id": temu.id,
                "category_id": electronics.id,
                "title": "Wireless Bluetooth Earbuds - Premium Sound",
                "description": "High-quality wireless earbuds with noise cancellation",
                "current_price": 29.99,
                "original_price": 59.99,
                "sales_count": 2340,
                "review_count": 567,
                "rating": 4.7,
                "product_url": "https://temu.com/wireless-earbuds",
                "image_url": "https://via.placeholder.com/300x300?text=Earbuds",
                "brand": "SoundTech"
            },
            {
                "platform_id": temu.id,
                "category_id": electronics.id,
                "title": "Smartphone Stand - Adjustable Desktop Holder",
                "description": "Universal phone stand for desk and table use",
                "current_price": 12.99,
                "original_price": 19.99,
                "sales_count": 1890,
                "review_count": 234,
                "rating": 4.4,
                "product_url": "https://temu.com/phone-stand",
                "image_url": "https://via.placeholder.com/300x300?text=Phone+Stand",
                "brand": "TechAccessories"
            },
            {
                "platform_id": amazon.id,
                "category_id": mens_clothing.id,
                "title": "Men's Winter Jacket - Waterproof & Warm",
                "description": "Heavy-duty winter jacket with thermal insulation",
                "current_price": 89.99,
                "original_price": 129.99,
                "sales_count": 456,
                "review_count": 89,
                "rating": 4.6,
                "product_url": "https://amazon.com/winter-jacket",
                "image_url": "https://via.placeholder.com/300x300?text=Jacket",
                "brand": "WinterGear"
            }
        ]
        
        # 创建商品
        created_products = []
        for product_data in demo_products:
            product = Product(**product_data)
            db.add(product)
            db.flush()  # 获取ID
            created_products.append(product)
        
        # 创建价格历史数据
        for product in created_products:
            base_price = product.current_price
            for i in range(30):  # 30天的价格历史
                date = datetime.utcnow() - timedelta(days=i)
                # 价格在基础价格的±20%范围内波动
                price_variation = random.uniform(-0.2, 0.2)
                price = base_price * (1 + price_variation)
                
                price_history = PriceHistory(
                    product_id=product.id,
                    price=round(price, 2),
                    original_price=product.original_price,
                    discount_rate=(product.original_price - price) / product.original_price if product.original_price else 0,
                    recorded_at=date
                )
                db.add(price_history)
        
        # 创建销售数据
        for product in created_products:
            for period in ["15min", "1hour", "1day", "1week"]:
                if period == "15min":
                    period_start = datetime.utcnow() - timedelta(minutes=15)
                    period_end = datetime.utcnow()
                    sales = random.randint(1, 10)
                elif period == "1hour":
                    period_start = datetime.utcnow() - timedelta(hours=1)
                    period_end = datetime.utcnow()
                    sales = random.randint(5, 50)
                elif period == "1day":
                    period_start = datetime.utcnow() - timedelta(days=1)
                    period_end = datetime.utcnow()
                    sales = random.randint(20, 200)
                else:  # 1week
                    period_start = datetime.utcnow() - timedelta(weeks=1)
                    period_end = datetime.utcnow()
                    sales = random.randint(100, 1000)
                
                sales_data = SalesData(
                    product_id=product.id,
                    sales_count=sales,
                    revenue=sales * product.current_price,
                    view_count=sales * random.randint(10, 50),
                    conversion_rate=random.uniform(0.02, 0.15),
                    review_count=product.review_count,
                    rating=product.rating,
                    positive_rate=random.uniform(0.8, 0.95),
                    time_period=period,
                    period_start=period_start,
                    period_end=period_end
                )
                db.add(sales_data)
        
        db.commit()
        print(f"成功创建 {len(created_products)} 个演示商品及相关数据")
        
    except Exception as e:
        print(f"创建演示数据失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()