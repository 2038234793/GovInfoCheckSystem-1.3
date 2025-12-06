"""
Pachong 插件主类
提供统一的爬虫接口
"""

import threading
import logging
from typing import List, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class PachongPlugin:
    """
    Pachong 爬虫插件
    
    提供多站点新闻爬取功能，支持：
    - 预设站点快速使用
    - 自定义站点配置
    - 多站点并行采集
    - 进度回调
    
    使用示例：
        plugin = PachongPlugin()
        
        # 使用预设站点
        results = plugin.crawl("关键词", sources=["baidu_news", "xinhua"])
        
        # 使用自定义配置
        config = {
            "name": "自定义站点",
            "base_url": "https://example.com/search",
            "params": {"keyword_param": "q"},
            "selectors": {"container": ".item", "title": "h3 a"}
        }
        results = plugin.crawl_with_config("关键词", config)
    """
    
    def __init__(self):
        """初始化插件"""
        self.version = "1.0.0"
        self.name = "Pachong"
        self.description = "多站点新闻爬虫插件"
    
    def get_available_sources(self) -> List[Dict]:
        """
        获取所有可用的预设站点
        
        Returns:
            list: 站点列表，每项包含 key, name, category
        """
        from .presets import get_preset_list
        return get_preset_list()
    
    def get_source_config(self, source_key: str) -> Optional[Dict]:
        """
        获取指定站点的配置
        
        Args:
            source_key: 站点标识
            
        Returns:
            dict: 站点配置，不存在则返回 None
        """
        from .presets import get_preset
        return get_preset(source_key)
    
    def get_categories(self) -> Dict:
        """
        获取站点分类信息
        
        Returns:
            dict: 分类信息
        """
        from .presets import get_categories
        return get_categories()
    
    def crawl(
        self, 
        keyword: str, 
        sources: List[str] = None,
        limit: int = 30,
        max_pages: int = 3,
        parallel: bool = True,
        on_progress: Callable = None
    ) -> List[Dict]:
        """
        执行爬取
        
        Args:
            keyword: 搜索关键词
            sources: 站点列表（预设key），默认使用百度新闻
            limit: 每个站点最大结果数
            max_pages: 每个站点最大页数
            parallel: 是否并行爬取
            on_progress: 进度回调函数 fn(source_name, items_count)
            
        Returns:
            list: 爬取结果列表
        """
        from .presets import get_preset
        from .crawler import PachongCrawler
        
        if not sources:
            sources = ["baidu_news"]
        
        if not keyword:
            logger.warning("PachongPlugin: keyword is empty")
            return []
        
        results = []
        lock = threading.Lock()
        
        def crawl_source(source_key):
            config = get_preset(source_key)
            if not config:
                logger.warning(f"PachongPlugin: source '{source_key}' not found")
                return
            
            crawler = PachongCrawler(config)
            items = crawler.crawl(keyword, limit=limit, max_pages=max_pages)
            
            # 标记来源
            for item in items:
                item['source_key'] = source_key
                item['source_name'] = config.get('name', source_key)
            
            with lock:
                results.extend(items)
                if on_progress:
                    try:
                        on_progress(config.get('name', source_key), len(items))
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")
        
        if parallel and len(sources) > 1:
            # 并行爬取
            threads = []
            for source_key in sources:
                t = threading.Thread(target=crawl_source, args=(source_key,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=120)
        else:
            # 串行爬取
            for source_key in sources:
                crawl_source(source_key)
        
        logger.info(f"PachongPlugin: total {len(results)} items from {len(sources)} sources")
        return results
    
    def crawl_with_config(
        self,
        keyword: str,
        config: Dict,
        limit: int = 30,
        max_pages: int = 3
    ) -> List[Dict]:
        """
        使用自定义配置爬取
        
        Args:
            keyword: 搜索关键词
            config: 爬虫配置
            limit: 最大结果数
            max_pages: 最大页数
            
        Returns:
            list: 爬取结果列表
        """
        from .crawler import PachongCrawler
        
        if not keyword:
            return []
        
        crawler = PachongCrawler(config)
        items = crawler.crawl(keyword, limit=limit, max_pages=max_pages)
        
        # 标记来源
        for item in items:
            item['source_name'] = config.get('name', '自定义站点')
        
        return items
    
    def test_config(self, config: Dict, keyword: str = "测试") -> Dict:
        """
        测试爬虫配置
        
        Args:
            config: 爬虫配置
            keyword: 测试关键词
            
        Returns:
            dict: 测试结果，包含 success, items, error
        """
        try:
            items = self.crawl_with_config(keyword, config, limit=5, max_pages=1)
            return {
                "success": True,
                "items": items,
                "count": len(items),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "items": [],
                "count": 0,
                "error": str(e)
            }
