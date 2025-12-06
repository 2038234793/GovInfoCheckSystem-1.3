
import sys
import os
import json
from app import create_app, db
from app.models import CrawlSource
from app.plugins.pachong.pachong.presets import CRAWLER_PRESETS

def migrate_crawlers():
    app = create_app()
    with app.app_context():
        print("Starting crawler migration...")
        count = 0
        for key, config in CRAWLER_PRESETS.items():
            # Check if exists (by name or some unique identifier)
            # Since we don't have a key column, we'll check by name
            name = config.get('name')
            if not name:
                continue
                
            existing = CrawlSource.query.filter_by(name=name).first()
            if existing:
                print(f"Skipping {name} (already exists)")
                continue
                
            print(f"Migrating {name}...")
            
            source = CrawlSource(
                name=name,
                base_url=config.get('base_url', ''),
                headers=json.dumps(config.get('headers', {}), ensure_ascii=False),
                params=json.dumps(config.get('params', {}), ensure_ascii=False),
                pagination=json.dumps(config.get('pagination', {}), ensure_ascii=False),
                selectors=json.dumps(config.get('selectors', {}), ensure_ascii=False),
                is_active=True
            )
            db.session.add(source)
            count += 1
            
        db.session.commit()
        print(f"Migration completed. Added {count} crawlers.")

if __name__ == '__main__':
    # Add project root to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    migrate_crawlers()
