import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaiduCrawler:
    def __init__(self):
        # 使用更稳定的百度新闻检索端点
        self.base_url = "https://news.baidu.com/ns"
        self.enable_deep = False
        # 更精简且通用的请求头
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "news.baidu.com",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }

    def _is_dirty(self, item):
        if not item.get('title') or not item.get('url'):
            return True
        return False

    def _parse(self, soup):
        results = []
        # 1. 优先解析标准新闻结果容器
        news_items = soup.select('.result, .result-op, .new-pmd, .c-container')

        # 2. 尝试通过标题定位父容器
        if not news_items:
            titles = soup.select('h3.c-title, h3.t, h3')
            if titles:
                news_items = [t.parent or t for t in titles]

        # 3. 在容器中提取信息
        for item in news_items:
            try:
                # 标题与链接
                title_elem = item.select_one('h3.c-title a, h3.t a, h3 a, .news-title_1YtI1 a')
                if not title_elem:
                    # 容器未找到标题时，继续下一项
                    continue
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                if not url or not title:
                    continue

                # 来源
                source_elem = item.select_one('span.c-author, .c-author, .c-color-gray, .news-source, .source-text_3o2Yd')
                source = source_elem.get_text(strip=True) if source_elem else "Baidu News"

                # 图片
                img_elem = item.select_one('img.c-img, .c-img img, img')
                cover = ""
                if img_elem:
                    cover = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-actualsrc') or ""

                # 摘要
                summary_elem = item.select_one('.c-abstract, .c-font-normal-three, .c-span18, .content-right_8Zs40, .summary, .news-desc')
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                obj = {"title": title, "summary": summary, "cover": cover, "url": url, "source": source}
                if not self._is_dirty(obj):
                    results.append(obj)
            except Exception as e:
                logger.error(f"Error parsing item: {e}")
                continue

        # 4. 回退：页面容器提取失败时，直接遍历所有 h3 标题链接
        if not results:
            for link in soup.select('h3 a'):
                try:
                    title = link.get_text(strip=True)
                    url = link.get('href')
                    if not title or not url:
                        continue
                    parent = link.find_parent(['div', 'article', 'li'])
                    source_elem = parent.select_one('span.c-author, .c-author, .c-color-gray, .news-source') if parent else None
                    source = source_elem.get_text(strip=True) if source_elem else "Baidu News"
                    img_elem = parent.select_one('img.c-img, .c-img img, img') if parent else None
                    cover = ""
                    if img_elem:
                        cover = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-actualsrc') or ""
                    summary_elem = parent.select_one('.c-abstract, .summary, .c-span18') if parent else None
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    obj = {"title": title, "summary": summary, "cover": cover, "url": url, "source": source}
                    if not self._is_dirty(obj):
                        results.append(obj)
                except Exception:
                    continue
        return results

    def crawl(self, keyword, limit=30, max_pages=5):
        try:
            all_results = []
            seen = set()
            per_page = 20
            for page_index in range(max_pages):
                pn = page_index * per_page
                params = {
                    "word": keyword,
                    "pn": pn,
                    "rn": per_page,
                    "ct": "1",
                    "tn": "news",
                    "from": "news",
                    "cl": "2"
                }
                response = requests.get(self.base_url, headers=self.headers, params=params, timeout=12)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                page_items = self._parse(soup)
                for it in page_items:
                    key = it.get("url") or (it.get("title", "") + it.get("source", ""))
                    if key in seen:
                        continue
                    seen.add(key)
                    all_results.append(it)
                    if len(all_results) >= limit:
                        break
                if len(all_results) >= limit:
                    break
            return all_results
        except Exception as e:
            logger.error(f"Baidu crawl error: {e}")
            return []

class XinhuaCrawler:
    def __init__(self):
        self.base_url = "http://sc.news.cn/scyw.htm"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        }

    def _is_dirty(self, item):
        c = 0
        if not item.get("url"):
            c += 1
        if not item.get("cover"):
            c += 1
        src = item.get("source", "")
        if not src:
            c += 1
        title = item.get("title", "")
        if not title:
            c += 1
        if not item.get("summary"):
            c += 1
        return c >= 3

    def _enrich(self, item):
        try:
            url = item.get("url")
            if not url:
                return item
            resp = requests.get(url, headers=self.headers, timeout=8)
            soup = BeautifulSoup(resp.text, 'html.parser')
            if not item.get("cover"):
                img = soup.find('meta', attrs={"property": "og:image"}) or soup.find('meta', attrs={"name": "twitter:image"})
                if img and img.get('content'):
                    item["cover"] = img.get('content')
                else:
                    link_img = soup.find('link', rel="image_src")
                    if link_img and link_img.get('href'):
                        item["cover"] = link_img.get('href')
                    else:
                        any_img = soup.find('img')
                        if any_img:
                            src = any_img.get('src') or any_img.get('data-src') or any_img.get('data-actualsrc')
                            if src:
                                item["cover"] = urllib.parse.urljoin(url, src)
        except Exception:
            pass
        return item

    def _parse(self, soup):
        results = []
        seen = set()
        for a in soup.select('a[href]'):
            href = a.get('href') or ''
            if not href:
                continue
            if 'news.cn' not in href:
                continue
            if href.startswith('javascript'):
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 6:
                continue
            if href in seen:
                continue
            seen.add(href)
            img = a.find('img') or (a.find_parent('li').find('img') if a.find_parent('li') else None)
            cover = ""
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-actualsrc') or ""
                if src:
                    cover = urllib.parse.urljoin(self.base_url, src)
            item_obj = {
                "title": title,
                "summary": "",
                "cover": cover,
                "url": urllib.parse.urljoin(self.base_url, href),
                "source": "新华网"
            }
            if not self._is_dirty(item_obj):
                results.append(item_obj)
        return results

    def crawl(self, keyword, limit=30, max_pages=1):
        try:
            all_results = []
            import requests
            resp = requests.get(self.base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            page_items = self._parse(soup)
            seen = set()
            enrich_budget = 15
            for it in page_items:
                key = it.get("url") or it.get("title", "")
                if key in seen:
                    continue
                seen.add(key)
                if (not it.get("cover")) and enrich_budget > 0:
                    it = self._enrich(it)
                    enrich_budget -= 1
                all_results.append(it)
                if len(all_results) >= limit:
                    break
            return all_results
        except Exception:
            return []

class ChinaSoCrawler:
    def __init__(self):
        self.base_url = "http://www.chinaso.com/newssearch/all/allResults"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "www.chinaso.com",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        }

    def _is_dirty(self, item):
        c = 0
        if not item.get("url"):
            c += 1
        src = item.get("source", "")
        if not src:
            c += 1
        title = item.get("title", "")
        if not title:
            c += 1
        if not item.get("summary"):
            c += 1
        return c >= 3

    def _parse(self, soup):
        results = []
        seen = set()
        for a in soup.select('a[href]'):
            href = a.get('href') or ''
            if not href:
                continue
            if href.startswith('javascript'):
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 6:
                continue
            parent = a.find_parent(['li','div'])
            img = None
            if parent:
                img = parent.find('img')
            cover = ""
            if img:
                cover = img.get('src') or img.get('data-src') or img.get('data-actualsrc') or ""
            try:
                import urllib.parse as up
                full_url = up.urljoin(self.base_url, href)
            except Exception:
                full_url = href
            try:
                from urllib.parse import urlparse
                host = urlparse(full_url).netloc or ""
            except Exception:
                host = ""
            item_obj = {
                "title": title,
                "summary": "",
                "cover": cover,
                "url": full_url,
                "source": host or "中国搜索"
            }
            key = item_obj["url"]
            if key in seen:
                continue
            seen.add(key)
            if not self._is_dirty(item_obj):
                results.append(item_obj)
            if len(results) >= 60:
                break
        return results

    def crawl(self, keyword, limit=30, max_pages=3):
        try:
            import requests
            from bs4 import BeautifulSoup
            items = []
            seen = set()
            for page_index in range(max_pages):
                pn = page_index + 1
                params = {"pn": pn, "force": 0, "q": keyword}
                resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                page_items = self._parse(soup)
                for it in page_items:
                    key = it.get("url") or (it.get("title", "") + it.get("source", ""))
                    if key in seen:
                        continue
                    seen.add(key)
                    if keyword:
                        try:
                            if keyword not in it.get("title", ""):
                                continue
                        except Exception:
                            pass
                    items.append(it)
                    if len(items) >= limit:
                        break
                if len(items) >= limit:
                    break
            return items
        except Exception:
            return []

class DynamicCrawler:
    def __init__(self, config):
        self.base_url = config.get("base_url")
        self.headers = config.get("headers") or {}
        self.params = config.get("params") or {}
        self.pagination = config.get("pagination") or {}
        self.selectors = config.get("selectors") or {}

    def _is_dirty(self, item):
        c = 0
        if not item.get("url"):
            c += 1
        src = item.get("source", "")
        if not src:
            c += 1
        title = item.get("title", "")
        if not title:
            c += 1
        if not item.get("summary"):
            c += 1
        return c >= 3

    def _parse(self, soup):
        items = []
        cont_sel = self.selectors.get("container")
        title_sel = self.selectors.get("title")
        link_sel = self.selectors.get("link")
        source_sel = self.selectors.get("source")
        img_sel = self.selectors.get("image")
        containers = soup.select(cont_sel) if cont_sel else []
        seen = set()
        for item in containers:
            t = item.select_one(title_sel) if title_sel else None
            title = t.get_text(strip=True) if t else ""
            a = item.select_one(link_sel) if link_sel else None
            href = a.get("href") if a and a.has_attr("href") else ""
            s = item.select_one(source_sel) if source_sel else None
            source = s.get_text(strip=True) if s else ""
            cover = ""
            img = item.select_one(img_sel) if img_sel else None
            if img:
                cover = img.get("src") or img.get("data-src") or img.get("data-actualsrc") or ""
            u = href
            obj = {"title": title, "summary": "", "cover": cover, "url": u, "source": source}
            k = obj["url"] or (obj["title"] + obj["source"])
            if k in seen:
                continue
            seen.add(k)
            if not self._is_dirty(obj):
                items.append(obj)
        return items

    def crawl(self, keyword, limit=30, max_pages=5):
        try:
            import requests
            from bs4 import BeautifulSoup
            items = []
            seen = set()
            p_name = self.pagination.get("param")
            p_start = int(self.pagination.get("start", 0))
            p_step = int(self.pagination.get("step", 1))
            kw_param = self.params.get("keyword_param")
            base_params = {k: v for k, v in self.params.items() if k != "keyword_param"}
            for i in range(max_pages):
                params = dict(base_params)
                if kw_param:
                    params[kw_param] = keyword
                if p_name:
                    params[p_name] = p_start + i * p_step
                resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                page_items = self._parse(soup)
                for it in page_items:
                    k = it.get("url") or (it.get("title", "") + it.get("source", ""))
                    if k in seen:
                        continue
                    seen.add(k)
                    items.append(it)
                    if len(items) >= limit:
                        break
                if len(items) >= limit:
                    break
            return items
        except Exception:
            return []

# Simple test if run directly
if __name__ == "__main__":
    crawler = BaiduCrawler()
    data = crawler.crawl("西昌")
    for item in data:
        print(item)

class RuleCrawler:
    def __init__(self, rule):
        self.rule = rule
        self.headers = {}
        if rule.headers:
            import json
            try:
                self.headers = json.loads(rule.headers)
            except:
                pass
        # Ensure basic headers if missing
        if not self.headers.get('User-Agent'):
            self.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

    def _generate_xpath(self, element):
        """Generate a simple, robust XPath for an element."""
        if element is None:
            return None
        # Try ID
        if element.get('id'):
            return f"//*[@id='{element.get('id')}']"
        # Try Class (first class)
        if element.get('class'):
            cls = element.get('class').split()[0]
            return f"//{element.tag}[contains(@class, '{cls}')]"
        # Tag fallback for specific tags
        if element.tag in ['h1', 'article']:
            return f"//{element.tag}"
        # Fallback to lxml path
        try:
            return element.getroottree().getpath(element)
        except:
            return None

    def fetch_detail(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.encoding = resp.apparent_encoding # Handle encoding automatically
            
            from lxml import etree
            html = etree.HTML(resp.text)
            
            title = ""
            content = ""
            
            # 1. Try configured Title XPath
            if self.rule.title_xpath:
                # Support multiple XPaths separated by |
                # lxml xpath supports | operator naturally, but we might need to be careful
                ts = html.xpath(self.rule.title_xpath)
                if ts:
                    # Handle various xpath return types (element or string)
                    if isinstance(ts[0], str):
                        title = ts[0].strip()
                    elif hasattr(ts[0], 'text'):
                        # Try to get all text inside the title element, not just direct text
                        # This helps when title has spans or other tags inside
                        title = "".join(ts[0].xpath('.//text()')).strip()
                        
            # 2. Try configured Content XPath
            if self.rule.content_xpath:
                cs = html.xpath(self.rule.content_xpath)
                if cs:
                    # Usually content is a container, get all text
                    if hasattr(cs[0], 'xpath'):
                        # Get all text nodes under this element
                        texts = cs[0].xpath('.//text()')
                        content = "\n".join([t.strip() for t in texts if t.strip()])
                    elif isinstance(cs[0], str):
                        content = cs[0].strip()

            # 3. Automatic Rule Update Detection
            new_title_xpath = None
            new_content_xpath = None
            
            # If configured title failed (empty) but rule exists
            if self.rule.title_xpath and not title:
                # Heuristic: Look for h1 or class/id containing "title"
                candidates = html.xpath('//h1 | //*[contains(@class, "title")] | //*[@id="title"]')
                for c in candidates:
                    t_text = ""
                    if hasattr(c, 'text') and c.text:
                        t_text = c.text.strip()
                    if t_text and len(t_text) > 5: # Valid title usually > 5 chars
                        title = t_text
                        new_title_xpath = self._generate_xpath(c)
                        break
            
            # If configured content failed (empty) but rule exists
            if self.rule.content_xpath and not content:
                # Heuristic: Look for article, content containers
                candidates = html.xpath('//article | //*[contains(@class, "content")] | //*[contains(@class, "article")] | //*[@id="content"] | //*[@id="article"]')
                best_candidate = None
                max_len = 0
                for c in candidates:
                    texts = c.xpath('.//text()')
                    full_text = "\n".join([t.strip() for t in texts if t.strip()])
                    if len(full_text) > max_len:
                        max_len = len(full_text)
                        best_candidate = c
                
                if best_candidate is not None and max_len > 50: # Content usually > 50 chars
                    texts = best_candidate.xpath('.//text()')
                    content = "\n".join([t.strip() for t in texts if t.strip()])
                    new_content_xpath = self._generate_xpath(best_candidate)
                        
            return {
                "title": title,
                "content": content,
                "new_title_xpath": new_title_xpath,
                "new_content_xpath": new_content_xpath
            }
        except Exception as e:
            logger.error(f"Rule crawl error for {url}: {e}")
            return None
