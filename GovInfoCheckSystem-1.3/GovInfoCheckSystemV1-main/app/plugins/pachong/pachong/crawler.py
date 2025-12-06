"""
Pachong 爬虫核心模块
提供通用的动态爬虫实现
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import time
import random

logger = logging.getLogger(__name__)


def normalize_url(href, base_url):
    """
    规范化URL，确保返回完整的绝对URL
    
    Args:
        href: 原始链接
        base_url: 基础URL
        
    Returns:
        str: 完整的绝对URL，无效则返回空字符串
    """
    if not href:
        return ""
    
    href = href.strip()
    
    # 跳过无效链接
    if href in ('#', 'javascript:void(0)', 'javascript:;', ''):
        return ""
    
    # 处理跳转链接（如央视网的 link_p.php?targetpage=xxx）
    if 'targetpage=' in href or 'target=' in href or 'url=' in href:
        try:
            from urllib.parse import parse_qs, urlparse as parse_url
            parsed = parse_url(href)
            params = parse_qs(parsed.query)
            # 尝试提取目标URL
            for key in ['targetpage', 'target', 'url', 'link', 'redirect']:
                if key in params and params[key]:
                    target = params[key][0]
                    if target.startswith('http'):
                        return target
        except Exception:
            pass
    
    # 已经是完整URL
    if href.startswith('http://') or href.startswith('https://'):
        return href
    
    # 协议相对URL
    if href.startswith('//'):
        return 'https:' + href
    
    # 相对URL，需要拼接基础URL
    if base_url:
        try:
            parsed = urlparse(base_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            return urljoin(base, href)
        except Exception:
            pass
    
    return ""


class PachongCrawler:
    """
    通用动态爬虫
    支持通过配置文件定义爬取规则
    """
    
    def __init__(self, config):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置字典，包含：
                - base_url: 基础URL
                - headers: 请求头（包含Cookie等）
                - params: URL参数
                - pagination: 分页配置
                - selectors: CSS选择器配置
        """
        self.base_url = config.get("base_url", "")
        self.headers = config.get("headers") or {}
        self.params = config.get("params") or {}
        self.pagination = config.get("pagination") or {}
        self.selectors = config.get("selectors") or {}
        self.name = config.get("name", "未命名爬虫")
        
        # 默认请求头
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
    
    def _parse(self, soup):
        """
        解析页面内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            list: 解析出的新闻列表
        """
        items = []
        cont_sel = self.selectors.get("container")
        title_sel = self.selectors.get("title")
        link_sel = self.selectors.get("link")
        source_sel = self.selectors.get("source")
        img_sel = self.selectors.get("image")
        
        # 尝试多个容器选择器
        containers = []
        if cont_sel:
            for sel in cont_sel.split(','):
                sel = sel.strip()
                if sel:
                    containers.extend(soup.select(sel))
        
        logger.debug(f"PachongCrawler: found {len(containers)} containers")
        
        seen = set()
        for item in containers:
            # 尝试获取标题
            title = ""
            t = None
            if title_sel:
                for sel in title_sel.split(','):
                    sel = sel.strip()
                    if sel:
                        t = item.select_one(sel)
                        if t:
                            title = t.get_text(strip=True)
                            break
            
            # 尝试获取链接
            href = ""
            if link_sel:
                for sel in link_sel.split(','):
                    sel = sel.strip()
                    if sel:
                        a = item.select_one(sel)
                        if a and a.has_attr("href"):
                            href = a.get("href")
                            break
            
            # 如果没找到链接，尝试从标题元素获取
            if not href and t:
                if t.name == 'a' and t.has_attr('href'):
                    href = t.get('href')
                else:
                    parent_a = t.find_parent('a')
                    if parent_a and parent_a.has_attr('href'):
                        href = parent_a.get('href')
            
            # 尝试获取来源
            source = ""
            if source_sel:
                for sel in source_sel.split(','):
                    sel = sel.strip()
                    if sel:
                        s = item.select_one(sel)
                        if s:
                            source = s.get_text(strip=True)
                            break
            
            # 尝试获取图片
            cover = ""
            if img_sel:
                for sel in img_sel.split(','):
                    sel = sel.strip()
                    if sel:
                        img = item.select_one(sel)
                        if img:
                            cover = (img.get("src") or 
                                    img.get("data-src") or 
                                    img.get("data-actualsrc") or "")
                            break
            
            # 只要有标题就保留
            if not title:
                continue
            
            # 规范化URL
            normalized_url = normalize_url(href, self.base_url)
            normalized_cover = normalize_url(cover, self.base_url) if cover else ""
                
            obj = {
                "title": title, 
                "summary": "", 
                "cover": normalized_cover, 
                "url": normalized_url, 
                "source": source
            }
            k = obj["url"] or obj["title"]
            if k in seen:
                continue
            seen.add(k)
            items.append(obj)
        
        return items
    
    def crawl(self, keyword, limit=30, max_pages=5, delay=None):
        """
        执行爬取
        
        Args:
            keyword: 搜索关键词
            limit: 最大结果数
            max_pages: 最大页数
            delay: 请求间隔（秒），None表示随机0.5-1.5秒
            
        Returns:
            list: 爬取结果列表
        """
        try:
            items = []
            seen = set()
            p_name = self.pagination.get("param")
            p_start = int(self.pagination.get("start", 0))
            p_step = int(self.pagination.get("step", 1))
            kw_param = self.params.get("keyword_param")
            base_params = {k: v for k, v in self.params.items() if k != "keyword_param"}
            
            # 计算需要爬取的页数（确保能获取足够数据）
            # 假设每页约10-20条，多爬几页以确保数据量
            estimated_per_page = 15
            min_pages_needed = (limit // estimated_per_page) + 2
            actual_max_pages = max(max_pages, min_pages_needed)
            
            empty_page_count = 0  # 连续空页计数
            
            for i in range(actual_max_pages):
                # 请求间隔（缩短间隔以加快采集）
                if i > 0:
                    wait_time = delay if delay else random.uniform(0.5, 1.5)
                    time.sleep(wait_time)
                
                # 构建参数
                params = dict(base_params)
                if kw_param:
                    params[kw_param] = keyword
                if p_name:
                    params[p_name] = p_start + i * p_step
                
                # 发送请求
                logger.info(f"PachongCrawler [{self.name}]: fetching page {i+1}/{actual_max_pages}")
                try:
                    resp = requests.get(
                        self.base_url, 
                        headers=self.headers, 
                        params=params, 
                        timeout=20,
                        allow_redirects=True
                    )
                except requests.exceptions.Timeout:
                    logger.warning(f"PachongCrawler [{self.name}]: timeout on page {i+1}")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"PachongCrawler [{self.name}]: request error: {e}")
                    continue
                
                logger.info(f"PachongCrawler [{self.name}]: status={resp.status_code}, len={len(resp.text)}")
                
                if resp.status_code != 200:
                    logger.warning(f"PachongCrawler [{self.name}]: bad status {resp.status_code}")
                    continue
                
                # 解析页面
                soup = BeautifulSoup(resp.text, "html.parser")
                page_items = self._parse(soup)
                
                logger.info(f"PachongCrawler [{self.name}]: parsed {len(page_items)} items from page {i+1}")
                
                # 如果当前页没有结果
                if not page_items:
                    empty_page_count += 1
                    # 连续3页为空才停止
                    if empty_page_count >= 3:
                        logger.info(f"PachongCrawler [{self.name}]: 3 consecutive empty pages, stopping")
                        break
                    continue
                else:
                    empty_page_count = 0
                
                # 去重并添加
                for it in page_items:
                    k = it.get("url") or it.get("title", "")
                    if k in seen:
                        continue
                    seen.add(k)
                    items.append(it)
                
                # 达到限制后停止
                if len(items) >= limit:
                    items = items[:limit]  # 精确截断
                    break
            
            logger.info(f"PachongCrawler [{self.name}]: total {len(items)} items collected")
            return items
            
        except Exception as e:
            logger.error(f"PachongCrawler [{self.name}] error: {e}")
            import traceback
            traceback.print_exc()
            return []


class BaiduNewsCrawler(PachongCrawler):
    """百度新闻专用爬虫"""
    
    def __init__(self):
        from .presets import get_preset
        config = get_preset("baidu_news") or {}
        super().__init__(config)


class XinhuaCrawler(PachongCrawler):
    """新华网专用爬虫"""
    
    def __init__(self):
        from .presets import get_preset
        config = get_preset("xinhua") or {}
        super().__init__(config)
