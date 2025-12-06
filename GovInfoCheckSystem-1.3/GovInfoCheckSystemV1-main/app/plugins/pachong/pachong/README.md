# Pachong 爬虫插件

多站点新闻采集插件，支持 27+ 预设站点。

## 功能特性

- **多站点支持**: 27个预设站点，覆盖搜索引擎、政府网站、央媒、门户、财经、科技、地方媒体
- **并行采集**: 支持多站点同时采集，提高效率
- **自定义配置**: 支持用户自定义站点配置
- **进度回调**: 支持异步采集和进度查询

## 目录结构

```
plugins/pachong/
├── __init__.py      # 插件入口
├── crawler.py       # 爬虫核心类
├── plugin.py        # 插件主类
├── presets.py       # 预设站点配置
├── routes.py        # API 路由
└── README.md        # 说明文档
```

## 预设站点

### 搜索引擎 (4个)
- 百度新闻、搜狗新闻、必应新闻、中国搜索

### 政府网站 (3个)
- 中国政府网、商务部、发改委

### 央媒 (6个)
- 新华网、央视网、中国新闻网、光明网、中国经济网、人民网

### 门户网站 (6个)
- 新浪新闻、网易新闻、腾讯新闻、今日头条、凤凰网、环球网

### 财经媒体 (4个)
- 东方财富、和讯网、第一财经、财新网

### 科技媒体 (3个)
- 36氪、IT之家、cnBeta

### 地方媒体 (4个)
- 新京报、澎湃新闻、界面新闻、参考消息

## 使用方式

### Python 代码调用

```python
from app.plugins.pachong import PachongPlugin

# 创建插件实例
plugin = PachongPlugin()

# 获取可用站点
sources = plugin.get_available_sources()

# 执行爬取
results = plugin.crawl(
    keyword="关键词",
    sources=["baidu_news", "xinhua"],
    limit=30,
    max_pages=3
)

# 使用自定义配置
config = {
    "name": "自定义站点",
    "base_url": "https://example.com/search",
    "params": {"keyword_param": "q"},
    "selectors": {
        "container": ".item",
        "title": "h3 a",
        "link": "h3 a"
    }
}
results = plugin.crawl_with_config("关键词", config)
```

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/pachong/` | GET | 插件首页 |
| `/pachong/api/info` | GET | 获取插件信息 |
| `/pachong/api/sources` | GET | 获取所有可用站点 |
| `/pachong/api/source/<key>` | GET | 获取站点详情 |
| `/pachong/api/crawl` | POST | 同步爬取 |
| `/pachong/api/crawl/async` | POST | 异步爬取 |
| `/pachong/api/crawl/status` | GET | 查询异步任务状态 |
| `/pachong/api/test` | POST | 测试爬虫配置 |

### 爬取请求示例

```json
POST /pachong/api/crawl
{
    "keyword": "人工智能",
    "sources": ["baidu_news", "xinhua", "36kr"],
    "limit": 20,
    "max_pages": 2
}
```

## 配置说明

每个站点配置包含以下字段：

```json
{
    "name": "站点名称",
    "base_url": "搜索接口URL",
    "headers": {
        "User-Agent": "浏览器标识",
        "Cookie": "登录凭证（如需要）",
        "Referer": "来源页面"
    },
    "params": {
        "keyword_param": "关键词参数名",
        "其他固定参数": "值"
    },
    "pagination": {
        "param": "分页参数名",
        "start": 0,
        "step": 10
    },
    "selectors": {
        "container": "新闻条目容器选择器",
        "title": "标题选择器",
        "link": "链接选择器",
        "source": "来源选择器",
        "image": "图片选择器"
    }
}
```

## 版本

- v1.0.0 - 初始版本，支持27个预设站点
