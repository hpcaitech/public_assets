from crawler import CondaCrawler

if __name__ == '__main__':
    MIN_TORCH_VERSION = '1.8.0'
    MIN_CUDA_VERSION = '10.2'
    crawler = CondaCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    conda_wheel_list = crawler.crawl()
    print(conda_wheel_list)
