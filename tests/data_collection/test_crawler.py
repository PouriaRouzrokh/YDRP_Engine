import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ydrpolicy.data_collection.crawl import crawl_main
from ydrpolicy.data_collection.config import config


def test_crawler():
    config.PATHS.DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test_data"
    )
    config.PATHS.RAW_DATA_DIR = os.path.join(config.PATHS.DATA_DIR, "raw")
    config.PATHS.DOCUMENT_DIR = os.path.join(config.PATHS.RAW_DATA_DIR, "documents")
    config.PATHS.MARKDOWN_DIR = os.path.join(config.PATHS.RAW_DATA_DIR, "markdown_files")
    config.PATHS.PROCESSED_DATA_DIR = os.path.join(config.PATHS.DATA_DIR, "processed")
    config.PATHS.SCRAPED_POLICIES_DIR = os.path.join(config.PATHS.PROCESSED_DATA_DIR, "scraped_policies")
    config.LOGGING.CRAWLER_LOG_FILE = os.path.join(config.PATHS.DATA_DIR, "logs", "crawler.log")
    config.CRAWLER.MAX_DEPTH = 1

    crawl_main(config=config)


if __name__ == "__main__":
    test_crawler()
