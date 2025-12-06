"""
Pachong 爬虫插件
================
提供多站点新闻爬取功能，支持：
- 27+ 预设站点（搜索引擎、政府网站、央媒、门户、财经、科技、地方媒体）
- 自定义站点配置
- 多站点并行采集
- 动态选择器解析

使用方式：
    from app.plugins.pachong import PachongPlugin
    plugin = PachongPlugin()
    results = plugin.crawl("关键词", sources=["baidu_news", "xinhua"])
"""

from flask import Blueprint

# 创建蓝图
pachong_bp = Blueprint('pachong', __name__, url_prefix='/pachong', template_folder='templates')

# 导入路由
from . import routes

# 导出
from .crawler import PachongCrawler
from .presets import CRAWLER_PRESETS, get_preset, get_all_presets, get_preset_list
from .plugin import PachongPlugin

__all__ = [
    'pachong_bp',
    'PachongCrawler',
    'PachongPlugin',
    'CRAWLER_PRESETS',
    'get_preset',
    'get_all_presets',
    'get_preset_list'
]

__version__ = '1.0.0'
__author__ = 'GovInfoCheck Team'
