"""
定时任务调度器
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from scrapers.amazon_scraper import AmazonScraper
from scrapers.temu_scraper import TemuScraper
from analysis.data_analyzer import DataAnalyzer
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.analyzer = DataAnalyzer()
        self.is_running = False
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行中")
            return
        
        # 添加爬虫任务
        self._add_scraping_jobs()
        
        # 添加分析任务
        self._add_analysis_jobs()
        
        # 启动调度器
        self.scheduler.start()
        self.is_running = True
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("任务调度器已停止")
    
    def _add_scraping_jobs(self):
        """添加爬虫任务"""
        platforms = settings.PLATFORMS
        
        for platform_name, config in platforms.items():
            if not config.get("enabled", False):
                continue
            
            update_interval = config.get("update_interval", 3600)  # 默认1小时
            
            # 添加定时爬虫任务
            self.scheduler.add_job(
                func=self._run_scraper,
                trigger=IntervalTrigger(seconds=update_interval),
                args=[platform_name],
                id=f"scraper_{platform_name}",
                name=f"{platform_name.title()} 爬虫任务",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5分钟容错时间
            )
            
            logger.info(f"已添加 {platform_name} 爬虫任务，更新间隔: {update_interval}秒")
    
    def _add_analysis_jobs(self):
        """添加分析任务"""
        # 15分钟分析任务
        self.scheduler.add_job(
            func=self._run_analysis,
            trigger=IntervalTrigger(minutes=15),
            args=["15min"],
            id="analysis_15min",
            name="15分钟数据分析",
            max_instances=1
        )
        
        # 1小时分析任务
        self.scheduler.add_job(
            func=self._run_analysis,
            trigger=IntervalTrigger(hours=1),
            args=["1hour"],
            id="analysis_1hour",
            name="1小时数据分析",
            max_instances=1
        )
        
        # 每日分析任务（凌晨2点执行）
        self.scheduler.add_job(
            func=self._run_analysis,
            trigger=CronTrigger(hour=2, minute=0),
            args=["1day"],
            id="analysis_daily",
            name="每日数据分析",
            max_instances=1
        )
        
        # 每周分析任务（周一凌晨3点执行）
        self.scheduler.add_job(
            func=self._run_analysis,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),
            args=["1week"],
            id="analysis_weekly",
            name="每周数据分析",
            max_instances=1
        )
        
        # 每月分析任务（每月1号凌晨4点执行）
        self.scheduler.add_job(
            func=self._run_analysis,
            trigger=CronTrigger(day=1, hour=4, minute=0),
            args=["1month"],
            id="analysis_monthly",
            name="每月数据分析",
            max_instances=1
        )
        
        logger.info("已添加所有分析任务")
    
    async def _run_scraper(self, platform_name: str):
        """运行爬虫任务"""
        try:
            logger.info(f"开始执行 {platform_name} 爬虫任务")
            
            if platform_name == "amazon":
                async with AmazonScraper() as scraper:
                    results = await scraper.scrape_all_categories()
                    total_products = sum(len(products) for products in results.values())
                    logger.info(f"Amazon 爬虫完成，获取 {total_products} 个商品")
            
            elif platform_name == "temu":
                async with TemuScraper() as scraper:
                    results = await scraper.scrape_all_categories()
                    total_products = sum(len(products) for products in results.values())
                    logger.info(f"Temu 爬虫完成，获取 {total_products} 个商品")
            
            # TODO: 添加其他平台的爬虫
            else:
                logger.warning(f"暂不支持平台: {platform_name}")
            
        except Exception as e:
            logger.error(f"执行 {platform_name} 爬虫任务时发生错误: {e}")
    
    async def _run_analysis(self, time_period: str):
        """运行分析任务"""
        try:
            logger.info(f"开始执行 {time_period} 数据分析任务")
            
            # 分析热门商品
            trending_products = self.analyzer.analyze_trending_products(time_period, 50)
            logger.info(f"分析完成，找到 {len(trending_products)} 个热门商品")
            
            # 分析分类趋势
            category_trends = self.analyzer.analyze_category_trends(time_period)
            logger.info(f"分析完成，找到 {len(category_trends)} 个分类趋势")
            
            # 如果是每日分析，生成市场洞察报告
            if time_period == "1day":
                insights = self.analyzer.get_market_insights("1week")
                logger.info("市场洞察报告生成完成")
            
        except Exception as e:
            logger.error(f"执行 {time_period} 分析任务时发生错误: {e}")
    
    def add_custom_job(self, func, trigger, job_id: str, name: str, **kwargs):
        """添加自定义任务"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                **kwargs
            )
            logger.info(f"已添加自定义任务: {name}")
        except Exception as e:
            logger.error(f"添加自定义任务失败: {e}")
    
    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"已移除任务: {job_id}")
        except Exception as e:
            logger.error(f"移除任务失败: {e}")
    
    def get_jobs(self):
        """获取所有任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def pause_job(self, job_id: str):
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"已暂停任务: {job_id}")
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
    
    def resume_job(self, job_id: str):
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"已恢复任务: {job_id}")
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
    
    async def run_job_now(self, job_id: str):
        """立即执行任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                if "scraper" in job_id:
                    platform_name = job_id.replace("scraper_", "")
                    await self._run_scraper(platform_name)
                elif "analysis" in job_id:
                    time_period = job_id.replace("analysis_", "")
                    await self._run_analysis(time_period)
                else:
                    logger.warning(f"不支持立即执行的任务类型: {job_id}")
            else:
                logger.error(f"任务不存在: {job_id}")
        except Exception as e:
            logger.error(f"立即执行任务失败: {e}")

# 全局调度器实例
scheduler = TaskScheduler()

# 使用示例
async def main():
    """测试调度器"""
    scheduler.start()
    
    try:
        # 运行一段时间
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())