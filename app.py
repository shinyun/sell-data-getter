#!/usr/bin/env python3
"""
电商热销数据分析系统主应用
"""
import asyncio
import uvicorn
from web.api import app
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """主函数"""
    logger.info(f"启动 {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"前端界面: http://{settings.HOST}:{settings.PORT}/static/index.html")
    
    # 启动服务器
    uvicorn.run(
        "web.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
        log_level="info" if not settings.DEBUG else "debug"
    )

if __name__ == "__main__":
    main()