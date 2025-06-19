"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config.settings import settings
from database.models import Base
import os

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 创建数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """获取数据库会话（同步版本）"""
    return SessionLocal()

def init_database():
    """初始化数据库"""
    from database.models import Platform, Category
    
    # 创建表
    create_tables()
    
    # 初始化基础数据
    db = get_db_session()
    
    try:
        # 检查是否已有数据
        if db.query(Platform).count() == 0:
            # 初始化平台数据
            platforms = [
                Platform(name="amazon", display_name="Amazon", base_url="https://www.amazon.com"),
                Platform(name="temu", display_name="Temu", base_url="https://www.temu.com"),
                Platform(name="ebay", display_name="eBay", base_url="https://www.ebay.com"),
                Platform(name="tiktok_shop", display_name="TikTok Shop", base_url="https://shop.tiktok.com"),
            ]
            
            for platform in platforms:
                db.add(platform)
            
            # 初始化分类数据
            categories = [
                # 一级分类
                Category(name="mens-clothing", display_name="男装", level=1),
                Category(name="electronics", display_name="电子产品", level=1),
                Category(name="home-garden", display_name="家居园艺", level=1),
                Category(name="sports", display_name="运动户外", level=1),
                Category(name="beauty", display_name="美妆个护", level=1),
                Category(name="automotive", display_name="汽车用品", level=1),
                Category(name="books", display_name="图书音像", level=1),
                Category(name="toys", display_name="玩具游戏", level=1),
            ]
            
            for category in categories:
                db.add(category)
            
            db.commit()
            print("数据库初始化完成")
        
        # 添加二级分类
        if db.query(Category).filter(Category.level == 2).count() == 0:
            # 获取一级分类
            mens_clothing = db.query(Category).filter(Category.name == "mens-clothing").first()
            electronics = db.query(Category).filter(Category.name == "electronics").first()
            
            if mens_clothing:
                subcategories = [
                    Category(name="mens-shirts", display_name="男士衬衫", parent_id=mens_clothing.id, level=2),
                    Category(name="mens-pants", display_name="男士裤装", parent_id=mens_clothing.id, level=2),
                    Category(name="mens-jackets", display_name="男士外套", parent_id=mens_clothing.id, level=2),
                    Category(name="mens-shoes", display_name="男士鞋靴", parent_id=mens_clothing.id, level=2),
                    Category(name="mens-accessories", display_name="男士配饰", parent_id=mens_clothing.id, level=2),
                ]
                
                for subcategory in subcategories:
                    db.add(subcategory)
            
            if electronics:
                subcategories = [
                    Category(name="smartphones", display_name="智能手机", parent_id=electronics.id, level=2),
                    Category(name="laptops", display_name="笔记本电脑", parent_id=electronics.id, level=2),
                    Category(name="headphones", display_name="耳机音响", parent_id=electronics.id, level=2),
                    Category(name="smart-home", display_name="智能家居", parent_id=electronics.id, level=2),
                    Category(name="gaming", display_name="游戏设备", parent_id=electronics.id, level=2),
                ]
                
                for subcategory in subcategories:
                    db.add(subcategory)
            
            db.commit()
            print("分类数据初始化完成")
            
    except Exception as e:
        print(f"数据库初始化错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()