"""
爬虫预设配置
包含各主流新闻站点的选择器、Headers、Cookie等配置
支持：政府网站、主流媒体、搜索引擎、地方新闻等
"""

CRAWLER_PRESETS = {
    # ==================== 搜索引擎类 ====================
    "baidu_news": {
        "name": "百度新闻",
        "base_url": "https://www.baidu.com/s",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        },
        "params": {
            "keyword_param": "word",
            "tn": "news",
            "cl": "2",
            "rn": "50",
            "ie": "utf-8"
        },
        "pagination": {
            "param": "pn",
            "start": 0,
            "step": 50
        },
        "selectors": {
            "container": ".result-op, .c-container, .new-pmd, .result, [class*='result']",
            "title": "h3 a, .c-title a, [class*='title'] a, a[href*='news']",
            "link": "h3 a, .c-title a, [class*='title'] a, a[href*='news']",
            "source": ".c-color-gray, .news-source, .c-source, [class*='source'], .c-span-last",
            "image": "img[src*='http'], img[data-src]"
        }
    },
    
    "sogou_news": {
        "name": "搜狗新闻",
        "base_url": "https://news.sogou.com/news",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        },
        "params": {
            "keyword_param": "query",
            "mode": "1",
            "sort": "0",
            "pagesize": "20"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-list li, .vrwrap, .news-item, [class*='news']",
            "title": "h3 a, .news-title a, .txt-box a, a[href*='sogou']",
            "link": "h3 a, .news-title a, .txt-box a, a[href*='sogou']",
            "source": ".news-from, .news-time-source, .news-info, [class*='source']",
            "image": "img[src*='http'], img[data-src]"
        }
    },
    
    # 今日头条 - 已删除（需要JS渲染）
    
    "sina_news": {
        "name": "新浪新闻",
        "base_url": "https://search.sina.com.cn/news",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        },
        "params": {
            "keyword_param": "q",
            "c": "news",
            "from": "channel",
            "ie": "utf-8",
            "num": "20"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".box-result, .result, .r-info, [class*='result']",
            "title": "h2 a, .title a, a[href*='sina.com']",
            "link": "h2 a, .title a, a[href*='sina.com']",
            "source": ".fgray_time, .source, .from, [class*='time']",
            "image": "img[src*='http'], img[data-src]"
        }
    },
    
    # 网易新闻 - 已删除（需要JS渲染）
    # 腾讯新闻 - 已删除（需要JS渲染）
    
    "people_cn": {
        "name": "人民网",
        "base_url": "http://search.people.cn/s/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "keyword",
            "st": "0",
            "_": ""
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".search_list li, .news-list li",
            "title": "a.title, h3 a",
            "link": "a.title, h3 a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "xinhua": {
        "name": "新华网",
        "base_url": "https://so.news.cn/getNews",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://so.news.cn/"
        },
        "params": {
            "keyword_param": "keyword",
            "curPage": "1",
            "sortField": "0",
            "searchFields": "1"
        },
        "pagination": {
            "param": "curPage",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-item, .result-item",
            "title": ".title a, h3 a",
            "link": ".title a, h3 a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "chinaso": {
        "name": "中国搜索",
        "base_url": "https://www.chinaso.com/newssearch/all/allResults",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "q"
        },
        "pagination": {
            "param": "pn",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-list-item, .result-item",
            "title": ".news-title a, h3 a",
            "link": ".news-title a, h3 a",
            "source": ".news-source, .source",
            "image": "img"
        }
    },
    
    "bing_news": {
        "name": "必应新闻",
        "base_url": "https://cn.bing.com/news/search",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "q",
            "FORM": "HDRSC6"
        },
        "pagination": {
            "param": "first",
            "start": 1,
            "step": 10
        },
        "selectors": {
            "container": ".news-card, .newsitem",
            "title": "a.title, .title",
            "link": "a.title, a",
            "source": ".source, .source span",
            "image": "img"
        }
    },
    
    # ==================== 政府网站类 ====================
    "gov_cn": {
        "name": "中国政府网",
        "base_url": "http://sousuo.gov.cn/s.htm",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "http://www.gov.cn/"
        },
        "params": {
            "keyword_param": "q",
            "t": "govall",
            "timetype": "timeqb"
        },
        "pagination": {
            "param": "p",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result, .res-list li",
            "title": "h3 a, .res-title a",
            "link": "h3 a, .res-title a",
            "source": ".res-sub, .source",
            "image": "img"
        }
    },
    
    "mofcom": {
        "name": "商务部",
        "base_url": "http://search.mofcom.gov.cn/search",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "q",
            "siteCode": "mofcom"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news_list li, .result-item",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".time, .date",
            "image": "img"
        }
    },
    
    # 发改委 - 已删除（非搜索页面，结构不匹配）
    
    # ==================== 央媒类 ====================
    "cctv": {
        "name": "央视网",
        "base_url": "https://search.cctv.com/search.php",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://www.cctv.com/"
        },
        "params": {
            "keyword_param": "qtext",
            "type": "web",
            "sort": "relevance"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".tuwenjg li, .result-item, .news_li, [class*='item']",
            "title": "h3 a, .bre a, a[href*='cctv.com']",
            "link": "h3 a, .bre a, a[href*='cctv.com']",
            "source": ".tim, .source, .time, [class*='time']",
            "image": "img[src*='http'], img[data-src]"
        }
    },
    
    "chinanews": {
        "name": "中国新闻网",
        "base_url": "https://sou.chinanews.com.cn/search.do",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.chinanews.com.cn/"
        },
        "params": {
            "keyword_param": "q",
            "ps": "10",
            "type": "0"
        },
        "pagination": {
            "param": "pager.offset",
            "start": 0,
            "step": 10
        },
        "selectors": {
            "container": ".news_list li, .result-item",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "gmw": {
        "name": "光明网",
        "base_url": "https://search.gmw.cn/search.htm",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result-list li, .news-item",
            "title": "h3 a, .title a",
            "link": "h3 a, .title a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "ce_cn": {
        "name": "中国经济网",
        "base_url": "http://search.ce.cn/search.jsp",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "searchword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result-list li, .news-list li",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".time, .source",
            "image": "img"
        }
    },
    
    # ==================== 财经类 ====================
    "eastmoney": {
        "name": "东方财富",
        "base_url": "https://so.eastmoney.com/news/s",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.eastmoney.com/"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "pageindex",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-item, .result-item",
            "title": ".news-title a, h3 a",
            "link": ".news-title a, h3 a",
            "source": ".news-source, .source",
            "image": "img"
        }
    },
    
    # 和讯网 - 已删除（搜索接口变更）
    # 第一财经 - 已删除（需要JS渲染）
    
    # ==================== 科技类 ====================
    "36kr": {
        "name": "36氪",
        "base_url": "https://36kr.com/search/articles",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://36kr.com/"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".article-item, .search-item",
            "title": ".article-item-title, h3 a",
            "link": "a.article-item-title, h3 a",
            "source": ".kr-flow-bar-author, .source",
            "image": "img"
        }
    },
    
    # IT之家 - 已删除（需要JS渲染）
    # cnBeta - 已删除（需要JS渲染）
    
    # ==================== 地方媒体类 ====================
    "bjnews": {
        "name": "新京报",
        "base_url": "http://www.bjnews.com.cn/search",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-list li, .result-item",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".time, .source",
            "image": "img"
        }
    },
    
    "thepaper": {
        "name": "澎湃新闻",
        "base_url": "https://www.thepaper.cn/searchResult.jsp",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.thepaper.cn/"
        },
        "params": {
            "keyword_param": "word"
        },
        "pagination": {
            "param": "pageNo",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news_li, .result-item",
            "title": "h2 a, .title a",
            "link": "h2 a, .title a",
            "source": ".pdtt_trbs, .source",
            "image": "img"
        }
    },
    
    "jiemian": {
        "name": "界面新闻",
        "base_url": "https://www.jiemian.com/search.html",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".news-view, .result-item",
            "title": "h3 a, .title a",
            "link": "h3 a, .title a",
            "source": ".article-info, .source",
            "image": "img"
        }
    },
    
    "caixin": {
        "name": "财新网",
        "base_url": "https://search.caixin.com/search/search.jsp",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "keyword"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".searchxt, .result-item",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".time, .source",
            "image": "img"
        }
    },
    
    # ==================== 综合门户类 ====================
    "ifeng": {
        "name": "凤凰网",
        "base_url": "https://so.ifeng.com/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.ifeng.com/"
        },
        "params": {
            "keyword_param": "q",
            "c": "1"
        },
        "pagination": {
            "param": "p",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result, .news-item",
            "title": "h2 a, .title a",
            "link": "h2 a, .title a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "huanqiu": {
        "name": "环球网",
        "base_url": "https://so.huanqiu.com/search",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.huanqiu.com/"
        },
        "params": {
            "keyword_param": "q"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result-item, .news-item",
            "title": "h3 a, .title a",
            "link": "h3 a, .title a",
            "source": ".source, .time",
            "image": "img"
        }
    },
    
    "cankaoxiaoxi": {
        "name": "参考消息",
        "base_url": "http://www.cankaoxiaoxi.com/search.shtml",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        },
        "params": {
            "keyword_param": "wd"
        },
        "pagination": {
            "param": "page",
            "start": 1,
            "step": 1
        },
        "selectors": {
            "container": ".result-item, .news-list li",
            "title": "a, h3 a",
            "link": "a, h3 a",
            "source": ".time, .source",
            "image": "img"
        }
    }
}

# 站点分类信息（可用站点：百度新闻、搜狗新闻、央视网、新浪新闻）
PRESET_CATEGORIES = {
    "search": {
        "name": "搜索引擎",
        "items": ["baidu_news", "sogou_news"]
    },
    "central_media": {
        "name": "央媒",
        "items": ["cctv"]
    },
    "portal": {
        "name": "门户网站",
        "items": ["sina_news"]
    }
}

def get_preset(key):
    """获取预设配置"""
    return CRAWLER_PRESETS.get(key)

def get_all_presets():
    """获取所有预设"""
    return CRAWLER_PRESETS

def get_preset_list():
    """获取预设列表（用于前端选择，按分类组织）"""
    result = []
    for cat_key, cat_info in PRESET_CATEGORIES.items():
        for item_key in cat_info["items"]:
            if item_key in CRAWLER_PRESETS:
                result.append({
                    "key": item_key,
                    "name": CRAWLER_PRESETS[item_key]["name"],
                    "category": cat_info["name"]
                })
    # 添加未分类的
    categorized = set()
    for cat_info in PRESET_CATEGORIES.values():
        categorized.update(cat_info["items"])
    for k, v in CRAWLER_PRESETS.items():
        if k not in categorized:
            result.append({"key": k, "name": v["name"], "category": "其他"})
    return result

def get_categories():
    """获取分类信息"""
    return PRESET_CATEGORIES

def get_preset_count():
    """获取预设数量"""
    return len(CRAWLER_PRESETS)
