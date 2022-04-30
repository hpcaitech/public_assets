import os.path as osp

from sqlalchemy import over
from crawler import PipCrawler, WheelRecordCollection


MIN_TORCH_VERSION = '1.8.0'
MIN_CUDA_VERSION = '10.2'

def write_record_collection_to_file(record_collection: WheelRecordCollection, root='./torch_wheels', overwrite=False):
    filename = f'{root}/{record_collection.torch_ver}-cuda{record_collection.cuda_ver}.txt'

    if osp.exists(filename) and not overwrite:
        return

    with open(filename, 'w') as f:
        for record in record_collection.records:
            f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\n')

def main():
    pip_crawler = PipCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    pip_wheel_list = pip_crawler.crawl()

    for record_collection in pip_wheel_list:
        write_record_collection_to_file(record_collection)


    

if __name__ == '__main__':
    main()