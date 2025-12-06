from app.plugins.pachong.pachong.crawler import PachongCrawler
import sys

def test_crawler():
    print("Testing PachongCrawler...")
    crawler = PachongCrawler()
    
    # Test with a common keyword and source
    keyword = "人工智能"
    sources = ["baidu_news"] # Assuming this is a valid key from presets
    
    print(f"Crawling keyword: {keyword} from {sources}...")
    
    try:
        results = crawler.crawl(
            keyword=keyword,
            sources=sources,
            limit=5,
            max_pages=1,
            parallel=False
        )
        
        print(f"Crawl finished. Found {len(results)} items.")
        for item in results:
            print(f"- {item.get('title')} ({item.get('source_name')})")
            
    except Exception as e:
        print(f"Crawl failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crawler()
