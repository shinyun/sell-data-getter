"""
系统配置文件
"""
import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """系统设置"""
    
    # 基础配置
    APP_NAME: str = "电商热销数据分析系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 12000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/ecommerce_data.db"
    # DATABASE_URL: str = "postgresql://user:password@localhost/ecommerce_db"
    
    # Redis配置（可选，用于缓存）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 爬虫配置
    SCRAPER_CONFIG: Dict[str, Any] = {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ],
        "request_delay": 2,  # 请求间隔（秒）
        "timeout": 30,
        "max_retries": 3,
        "concurrent_requests": 5
    }
    
    # 平台配置
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "amazon": {
            "enabled": True,
            "base_url": "https://www.amazon.com",
            "categories": ["mens-clothing", "electronics", "home-garden"],
            "max_pages": 10,
            "update_interval": 3600  # 1小时更新一次
        },
        "temu": {
            "enabled": True,
            "base_url": "https://www.temu.com",
            "categories": ["mens-fashion", "electronics", "home"],
            "max_pages": 10,
            "update_interval": 3600
        },
        "ebay": {
            "enabled": True,
            "base_url": "https://www.ebay.com",
            "categories": ["mens-clothing", "electronics", "home-garden"],
            "max_pages": 10,
            "update_interval": 3600
        },
        "tiktok_shop": {
            "enabled": True,
            "base_url": "https://shop.tiktok.com",
            "categories": ["mens-fashion", "electronics", "lifestyle"],
            "max_pages": 10,
            "update_interval": 1800  # 30分钟更新一次
        }
    }
    
    # 数据分析配置
    ANALYSIS_CONFIG: Dict[str, Any] = {
        "time_intervals": ["15min", "1hour", "1day", "1week", "1month"],
        "trending_threshold": 0.2,  # 趋势判断阈值
        "hot_product_min_sales": 100,  # 热门商品最小销量
        "category_weights": {
            "mens-clothing": 1.0,
            "electronics": 0.8,
            "home-garden": 0.6
        }
    }
    
    # 代理配置
    PROXY_CONFIG: Dict[str, Any] = {
        "enabled": False,
        "proxy_list": [
            # "http://proxy1:port",
            # "http://proxy2:port"
        ],
        "rotation_interval": 300  # 5分钟轮换一次
    }
    
    # 日志配置
    LOG_CONFIG: Dict[str, Any] = {
        "level": "INFO",
        "file_path": "./logs/app.log",
        "max_size": "10MB",
        "backup_count": 5
    }
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

# 创建全局设置实例
settings = Settings()

# 平台特定配置
AMAZON_CONFIG = {
    "search_urls": {
        "mens-clothing": "https://www.amazon.com/s?k=mens+clothing&ref=sr_pg_1",
        "electronics": "https://www.amazon.com/s?k=electronics&ref=sr_pg_1"
    },
    "selectors": {
        "product_title": "[data-component-type='s-search-result'] h2 a span",
        "product_price": ".a-price-whole",
        "product_rating": ".a-icon-alt",
        "product_link": "[data-component-type='s-search-result'] h2 a",
        "product_image": ".s-image"
    }
}

TEMU_CONFIG = {
    "search_urls": {
        "mens-fashion": "https://www.temu.com/search_result.html?search_key=mens+fashion",
        "electronics": "https://www.temu.com/search_result.html?search_key=electronics"
    },
    "selectors": {
        "product_title": "._2dz_Ql",
        "product_price": "._1_lHg",
        "product_sales": "._3j8_Iq",
        "product_link": "._2dz_Ql",
        "product_image": "._2dz_Ql img"
    }
}

EBAY_CONFIG = {
    "search_urls": {
        "mens-clothing": "https://www.ebay.com/sch/i.html?_nkw=mens+clothing",
        "electronics": "https://www.ebay.com/sch/i.html?_nkw=electronics"
    },
    "selectors": {
        "product_title": ".s-item__title",
        "product_price": ".s-item__price",
        "product_link": ".s-item__link",
        "product_image": ".s-item__image img"
    }
}

TIKTOK_SHOP_CONFIG = {
    "search_urls": {
        "mens-fashion": "https://shop.tiktok.com/search?keyword=mens+fashion",
        "electronics": "https://shop.tiktok.com/search?keyword=electronics"
    },
    "selectors": {
        "product_title": "[data-testid='product-title']",
        "product_price": "[data-testid='product-price']",
        "product_link": "[data-testid='product-link']",
        "product_image": "[data-testid='product-image'] img"
    }
}