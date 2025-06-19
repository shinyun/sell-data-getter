"""
日志配置模块
"""
import os
import sys
from loguru import logger
from config.settings import settings

def setup_logger():
    """设置日志配置"""
    # 移除默认的日志处理器
    logger.remove()
    
    # 确保日志目录存在
    log_dir = os.path.dirname(settings.LOG_CONFIG["file_path"])
    os.makedirs(log_dir, exist_ok=True)
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_CONFIG["level"],
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 文件输出
    logger.add(
        settings.LOG_CONFIG["file_path"],
        level=settings.LOG_CONFIG["level"],
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.LOG_CONFIG["max_size"],
        retention=settings.LOG_CONFIG["backup_count"],
        compression="zip",
        encoding="utf-8"
    )
    
    return logger

def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger

# 初始化日志
setup_logger()