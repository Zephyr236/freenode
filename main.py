#!/usr/bin/env python3
"""
代理节点收集和验证系统

此脚本从各种来源收集VPN/代理配置，包括网站、GitHub仓库和Telegram频道，
使用速度测试验证它们，并提供包含工作节点的组织化输出文件。

作者: Node Collector
许可证: MIT
"""

import requests
import re
import base64
import binascii
import subprocess
import csv
import time
import tempfile
import shutil
import threading
import concurrent.futures
import os
import logging
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlparse
from bs4 import BeautifulSoup
import bisect


# =============================================================================
# 配置和常量
# =============================================================================

class Config:
    """代理收集系统的配置常量"""
    
    # 文件路径
    RAW_OUTPUT_FILE = "raw.txt"              # 原始输出文件
    VALID_OUTPUT_FILE = "valid.txt"          # 有效节点输出文件
    BASE64_OUTPUT_FILE = "v2.txt"           # Base64编码输出文件
    SPEED_TEST_RESULTS_FILE = "results.csv" # 速度测试结果文件
    SPEED_TEST_TOOL_ZIP = "Xray-knife-linux-64.zip"    # 速度测试工具压缩包
    SPEED_TEST_TOOL_BINARY = "./xray-knife"            # 速度测试工具二进制文件
    LOG_FILE = "proxy_collection.log"       # 日志文件
    
    # 网络设置
    REQUEST_TIMEOUT = 30                     # 请求超时时间
    TELEGRAM_REQUEST_TIMEOUT = 60            # Telegram请求超时时间
    DECODE_REQUEST_TIMEOUT = 10              # 解码请求超时时间
    MAX_CONCURRENT_WORKERS = 10              # 最大并发工作线程数
    SPEED_TEST_THREADS = 500                 # 速度测试线程数
    
    # 支持的代理协议
    SUPPORTED_PROTOCOLS = [
        'vmess://', 'ss://', 'ssr://', 'trojan://', 
        'hy2://', 'vless://'
    ]
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    CURL_HEADERS = {
        "User-Agent": "curl/8.12.1",
        "Accept": "*/*",
        'Accept-Encoding': 'identity',
    }


class SourceConfig:
    """不同代理源的配置"""
    
    # 网站爬虫源 - 需要基于日期解析的网站
    WEBSITE_CRAWLER_SOURCES = [
        {
            "target_url": "https://www.mibei77.com/",
            "domain": "mm.mibei77.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://clashnodev2ray.github.io/",
            "domain": "a.nodeshare.xyz",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://wanzhuanmi.com/",
            "domain": "wanzhuanmi.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://www.freeclashnode.com/free-node/",
            "domain": "node.freeclashnode.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://betternode.org/freenode",
            "domain": "betternode.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://oneclash.cc/freenode",
            "domain": "oneclash.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://wenode.cc/freenode",
            "domain": "wenode.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://nodeclash.com/free-node/",
            "domain": "node.nodeclash.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://v2rayshare.org/free-node/",
            "domain": "node.v2rayshare.org",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://v2rayshare.org/free-node/",
            "domain": "nodefree.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://www.stairnode.com/freenode",
            "domain": "stairnode.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://naidounode.com/freenode",
            "domain": "naidounode.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://v2raynode.net/archives/category/freenode",
            "domain": "v2raynode.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://www.freev2raynode.com/free-node-subscription/",
            "domain": "node.freev2raynode.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://clashgithub.net/free-node/",
            "domain": "node.clashgithub.net",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://clashfreenode.com/",
            "domain": "clashfreenode.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://mianfeiv2rayx.github.io/",    # 失败
            "domain": "mianfeiv2rayx.github.io",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://clash-meta.github.io/",        # 失败
            "domain": "node.freeclashnode.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://nodev2ray.com/",                # 失败
            "domain": "node.nodev2ray.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://nodefree.net/",                # 失败
            "domain": "nodefree.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://v2rayshare.net/",            # 失败
            "domain": "v2rayshare.githubrowcontent.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://hiddifynextnode.github.io/",
            "domain": "hiddifynextnode.github.io",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://www.crazygeeky.com/category/151/",
            "domain": "crazygeeky.com",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://wanzhuanmi.com/freenode",
            "domain": "wanzhuanmi.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://www.stairnode.com/freenode",
            "domain": "stairnode.cczzuu.top",
            "file_extension": ".txt",
        },
        {
            "target_url": "https://free.datiya.com/",
            "domain": "free.datiya.com",
            "file_extension": ".txt",
        }
    ]

    # GitHub明文内容源
    GITHUB_PLAIN_TEXT_SOURCES = [
        "https://raw.githubusercontent.com/Barabama/FreeNodes/refs/heads/main/nodes/blues.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/clashmeta.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/ndnode.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/nodefree.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/nodev2ray.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/v2rayshare.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/wenode.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/yudou66.txt",
        "https://github.com/hzcsure/hzcsure/raw/refs/heads/main/example.txt",
        "https://raw.githubusercontent.com/HakurouKen/free-node/main/public",
        "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
        "https://raw.githubusercontent.com/vxiaov/free_proxies/refs/heads/main/links.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/hysteria.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/hysteria2.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/ss.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/ssr.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/trojan.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/vless.txt",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/vmess.txt",
        "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.txt"
    ]

    # GitHub Base64编码内容源
    GITHUB_BASE64_SOURCES = [
        "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
        "https://raw.githubusercontent.com/snakem982/proxypool/main/source/v2ray-2.txt",
        "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
        "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
        "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
        "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
        "https://github.001315.xyz/https://gist.githubusercontent.com/shaoyouvip/9dc3d23482fdc4a19e407a7e944782b8/raw/base64.txt",
        "https://dlconf.clashapps.cc/conf/c641d872-b44b-2b3e-b21e-6cd4997dd084.conf",
        "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/refs/heads/master/Eternity.txt",
        "https://raw.githubusercontent.com/peasoft/NoMoreWalls/refs/heads/master/list.txt",
        "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
        "https://raw.githubusercontent.com/hello-world-1989/cn-news/main/end-gfw-together",
        "https://raw.githubusercontent.com/ggborr/FREEE-VPN/refs/heads/main/6V2ray",
        "https://raw.githubusercontent.com/hello-world-1989/v2-sub/refs/heads/main/end-gfw-together",
        "https://iwxf.netlify.app/",
        "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/v2ray",
        "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/a11",
        "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/refs/heads/main/sub/base64.txt",
        "https://links.bocchi2b.top/clash",
        "https://sub.xeton.dev/sub?target=v2ray&url=https%3A%2F%2Fraw.githubusercontent.com%2Fanaer%2FSub%2Fmain%2Fclash.yaml",
        "https://x-access-token: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@raw.githubusercontent.com/Zephyr236/freenode/refs/heads/main/v2.txt",
        "https://raw.githubusercontent.com/Flikify/Free-Node/refs/heads/main/v2ray.txt"
    ]

    # Telegram订阅处理频道
    TELEGRAM_SUBSCRIPTION_CHANNELS = [
        "https://t.me/s/wxdy666",
        "https://t.me/s/fq521",
        "https://t.me/s/jiedian_share",
        "https://t.me/s/ednovasfree",
        "https://t.me/s/fqzw9",
        "https://t.me/s/SSRSUB",
        "https://t.me/s/freevpnatm",
        "https://t.me/s/sdffnkl",
        "https://t.me/s/ccbaohe",
        "https://t.me/s/juzibaipiao",
        "https://t.me/s/dns68",
        "https://t.me/s/hkaa0",
        "https://t.me/s/SubscriptionShare",
        "https://t.me/s/dingyue_center",
        "https://t.me/s/freeVPNjd",
        "https://t.me/s/mfbp1"
    ]

    # Telegram直接代理链接提取频道
    TELEGRAM_DIRECT_CHANNELS = [
        "https://t.me/s/zerobaipiao",
        "https://t.me/s/wxdy666",
        "https://t.me/s/ShareCentrePro",
        "https://t.me/s/JiedianSsr",
        "https://t.me/s/jiedianF",
        "https://t.me/s/mftizi",
        "https://t.me/s/freevpnatm",
        "https://t.me/s/vpn_3000",
        "https://t.me/s/ZDYZ2",
        "https://t.me/s/v2rayfree",
        "https://t.me/s/v2ray_t",
        "https://t.me/s/dingyue_center",
        "https://github.com/Alvin9999/new-pac/wiki/v2ray%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7",
        "https://github.com/Alvin9999/new-pac/wiki/ss%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7"
    ]


# =============================================================================
# 日志配置
# =============================================================================

def setup_logging():
    """配置日志系统"""
    # 创建日志格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志系统
logger = setup_logging()


class LogHelper:
    """日志辅助工具类，提供格式化和统计功能"""
    
    @staticmethod
    def print_section_header(title):
        """打印章节标题"""
        separator = "=" * 60
        logger.info(separator)
        logger.info(f"  {title}")
        logger.info(separator)
    
    @staticmethod
    def print_subsection_header(title):
        """打印子章节标题"""
        separator = "-" * 40
        logger.info(separator)
        logger.info(f"  {title}")
        logger.info(separator)
    
    @staticmethod
    def print_progress(current, total, prefix="进度"):
        """打印进度信息"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        logger.info(f"{prefix}: [{bar}] {current}/{total} ({percentage:.1f}%)")
    
    @staticmethod
    def print_statistics(stats_dict):
        """打印统计信息"""
        logger.info("统计信息:")
        for key, value in stats_dict.items():
            logger.info(f"  {key}: {value}")
    
    @staticmethod
    def print_success(message):
        """打印成功信息"""
        logger.info(f"✓ {message}")
    
    @staticmethod
    def print_warning(message):
        """打印警告信息"""
        logger.warning(f"⚠ {message}")
    
    @staticmethod
    def print_error(message):
        """打印错误信息"""
        logger.error(f"✗ {message}")
    
    @staticmethod
    def print_time_elapsed(start_time, end_time, operation="操作"):
        """打印耗时信息"""
        elapsed = end_time - start_time
        if elapsed < 60:
            logger.info(f"⏱ {operation}耗时: {elapsed:.2f}秒")
        else:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            logger.info(f"⏱ {operation}耗时: {minutes}分{seconds:.2f}秒")


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total, description="处理中"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.success_count = 0
        self.error_count = 0
    
    def update(self, increment=1, success=True):
        """更新进度"""
        self.current += increment
        if success:
            self.success_count += increment
        else:
            self.error_count += increment
        
        # 每10%或最后一个显示进度
        if self.current % max(1, self.total // 10) == 0 or self.current == self.total:
            self._display_progress()
    
    def _display_progress(self):
        """显示进度"""
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        bar_length = 25
        filled_length = int(bar_length * self.current // self.total) if self.total > 0 else 0
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        
        logger.info(
            f"{self.description}: [{bar}] "
            f"{self.current}/{self.total} ({percentage:.1f}%) "
            f"| 成功: {self.success_count} | 失败: {self.error_count} | "
            f"速度: {rate:.1f}/秒"
        )
    
    def finish(self):
        """完成进度追踪"""
        total_time = time.time() - self.start_time
        success_rate = (self.success_count / self.total) * 100 if self.total > 0 else 0
        
        LogHelper.print_success(
            f"{self.description}完成! 成功率: {success_rate:.1f}% "
            f"(成功: {self.success_count}, 失败: {self.error_count}) "
            f"耗时: {total_time:.2f}秒"
        )


# =============================================================================
# 工具类和函数
# =============================================================================

class FileManager:
    """处理文件操作和管理"""
    
    # 文件操作的线程锁
    _file_lock = threading.Lock()
    
    @staticmethod
    def remove_duplicates_from_file(filename, encoding='utf-8'):
        """
        从文件中删除重复的行，并覆盖原文件
        
        参数:
            filename (str): 需要去重的文件路径
            encoding (str): 文件编码，默认为'utf-8'
        
        返回:
            int: 去重后的行数，出错则返回-1
        """
        temp_filename = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w+', encoding=encoding, delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # 读取原文件并写入去重后的内容到临时文件
                seen_lines = set()
                unique_count = 0
                
                with open(filename, 'r', encoding=encoding) as file:
                    for line in file:
                        if line not in seen_lines:
                            seen_lines.add(line)
                            temp_file.write(line)
                            unique_count += 1
            
            # 用临时文件替换原文件
            shutil.move(temp_filename, filename)
            logger.info(f"成功去重，保留了 {unique_count} 行唯一内容。")
            return unique_count
        except Exception as e:
            logger.error(f"处理文件时出错: {e}")
            # 如果临时文件存在，删除它
            if temp_filename and os.path.exists(temp_filename):
                os.remove(temp_filename)
            return -1

    @staticmethod
    def remove_blank_lines(filename=Config.RAW_OUTPUT_FILE):
        """
        移除文件中的空行和注释行
        
        参数:
            filename (str): 要清理的文件路径
        """
        with open(filename, 'r', encoding='utf-8') as file:
            # 过滤条件：1. 不是空行 2. 不是以#开头的注释行
            filtered_lines = [
                line for line in file 
                if line.strip() != "" and not line.strip().startswith('#')
            ]
        
        # 覆盖写入原文件
        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(filtered_lines)
        
        logger.info("已移除所有空行和注释行")

    @staticmethod
    def convert_to_base64_and_save(input_file_path=Config.VALID_OUTPUT_FILE, 
                                 output_file_path=Config.BASE64_OUTPUT_FILE):
        """
        读取文件内容，转换为Base64编码并保存结果
        
        参数:
            input_file_path (str): 要读取的原始文件路径
            output_file_path (str): 保存Base64编码结果的文件路径
        
        返回:
            str: 成功信息或错误信息
        """
        try:
            # 读取原始文件内容（二进制模式）
            with open(input_file_path, 'rb') as file:
                file_content = file.read()
            
            # 将二进制内容转换为Base64编码（返回bytes类型）
            base64_bytes = base64.b64encode(file_content)
            
            # 将Base64 bytes转换为UTF-8字符串
            base64_string = base64_bytes.decode('utf-8')
            
            # 将Base64字符串保存到新文件
            with open(output_file_path, 'w') as output_file:
                output_file.write(base64_string)
            
            return f"成功将文件转换为Base64并保存到: {output_file_path}"
        
        except FileNotFoundError:
            return "错误：输入文件不存在"
        except PermissionError:
            return "错误：没有文件读写权限"
        except Exception as e:
            return f"未知错误: {str(e)}"

    @staticmethod
    def clean_temporary_files():
        """删除处理过程中生成的临时文件"""
        files_to_clean = [
            Config.RAW_OUTPUT_FILE, 
            Config.BASE64_OUTPUT_FILE,
            Config.VALID_OUTPUT_FILE,
            Config.SPEED_TEST_RESULTS_FILE
        ]
        
        for file_path in files_to_clean:
            if os.path.exists(file_path):
                os.remove(file_path)


class DateFormatter:
    """处理网页抓取的日期格式化"""
    
    @staticmethod
    def get_current_date_formats():
        """
        生成当前日期的多种格式
        
        返回:
            list: 各种格式的日期字符串列表
        """
        today = datetime.now()
        date_formats = [
            f"{today.month}月{today.day}日",  # 6月3日
            f"{today.year}年{today.month}月{today.day}日",  # 2024年6月3日
            f"{today.month}月{today.day}号",  # 6月3号
            f"{today.year}-{today.month:02d}-{today.day:02d}",  # 2024-06-03
            f"{today.year}年{today.month:02d}月{today.day:02d}日",  # 2024年06月03日
            f"{today.year}.{today.month:02d}.{today.day:02d}",  # 2024.06.03
            f"{today.month:02d}月{today.day:02d}日",  # 06月03日
            f"{today.month:02d}月{today.day}日",  # 06月3日
            f"{today.month}月{today.day:02d}日",  # 6月03日
        ]
        return date_formats


# =============================================================================
# 核心处理器类
# =============================================================================

class ProxyExtractor:
    """处理从各种来源提取代理链接"""
    
    def __init__(self, proxy_settings=None):
        """
        初始化代理提取器
        
        参数:
            proxy_settings (dict): 请求的代理配置
        """
        self.proxy_settings = proxy_settings
        self.file_lock = FileManager._file_lock

    def extract_and_save_proxy_links(self, url, filename=Config.RAW_OUTPUT_FILE):
        """
        从指定URL提取代理链接并直接追加保存到文件
        
        参数:
            url (str): 要请求的网页URL
            filename (str): 保存的文件名，默认为raw.txt
            
        返回:
            int: 提取并保存的链接数量
        """
        try:
            # 发送HTTP请求
            response = requests.get(
                url, 
                headers=Config.DEFAULT_HEADERS, 
                timeout=Config.REQUEST_TIMEOUT,
                proxies=self.proxy_settings
            )
            response.raise_for_status()
            html_content = response.text
            
            # 提取所有协议链接
            all_proxy_links = set()
            
            # 方法1: 按行提取
            for line in html_content.split('\n'):
                line = line.strip()
                for protocol in Config.SUPPORTED_PROTOCOLS:
                    if line.startswith(protocol):
                        all_proxy_links.add(line)
            
            # 方法2: 使用正则表达式提取
            for protocol in Config.SUPPORTED_PROTOCOLS:
                pattern = f'(?<![a-zA-Z]){re.escape(protocol)}[^\s<>"\']*'
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if match.startswith(protocol):
                        all_proxy_links.add(match)
            
            # 使用文件锁安全地将链接追加到文件
            if all_proxy_links:
                with self.file_lock:
                    with open(filename, 'a', encoding='utf-8') as f:
                        for link in all_proxy_links:
                            f.write(f"{link}\n")
                
                logger.info(f"从 {url} 提取并保存了 {len(all_proxy_links)} 个代理链接")
            else:
                logger.warning(f"从 {url} 未找到代理链接")
            
            return len(all_proxy_links)
            
        except Exception as e:
            logger.error(f"提取链接时出错: {e}")
            return 0

    def extract_urls_by_regex(self, html_content):
        """
        使用正则表达式从HTML内容中提取所有可能的URL
        
        参数:
            html_content: 网页HTML内容
            
        返回:
            list: 提取的URL列表
        """
        # URL正则表达式模式 - 匹配大多数URL格式
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%/.]+)*(?:\?[^"\s<>]*)?'
        
        # 使用正则表达式查找所有匹配
        urls = re.findall(url_pattern, html_content)
        
        # 过滤掉包含t.me和telegram的链接
        filtered_urls = []
        for url in urls:
            if "https://t.me/" not in url and "http://t.me/" not in url and "telegram" not in url:
                filtered_urls.append(url)
        
        return filtered_urls


class ContentFetcher:
    """处理从URL获取和处理内容"""
    
    def __init__(self, proxy_settings=None):
        """
        初始化内容获取器
        
        参数:
            proxy_settings (dict): 请求的代理配置
        """
        self.proxy_settings = proxy_settings

    def fetch_and_save_content(self, url, output_file=Config.RAW_OUTPUT_FILE):
        """
        请求指定的URL，并将响应内容原样保存到txt文件
        
        参数:
            url (str): 要请求的URL
            output_file (str): 输出文件名(默认为'raw.txt')
        
        返回:
            bool: 操作是否成功
        """
        try:
            # 发送HTTP请求
            response = requests.get(
                url, 
                proxies=self.proxy_settings, 
                headers=Config.CURL_HEADERS, 
                timeout=Config.DECODE_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"请求链接: {url}")
            
            # 获取响应内容
            content = response.content
            
            # 尝试将内容转换为UTF-8字符串
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，使用错误占位符替换
                text_content = content.decode("utf-8", errors="replace")
                
            # 使用文件锁安全地写入内容到文件
            with FileManager._file_lock:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(text_content)
                
            logger.info(f"保存成功! 内容已保存到: {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            LogHelper.print_error(f"请求失败 ({url}): {e}")
        except Exception as e:
            LogHelper.print_error(f"处理失败 ({url}): {e}")
            
        return False

    def decode_and_save_base64(self, url, output_file=Config.RAW_OUTPUT_FILE):
        """
        请求指定的URL，尝试Base64解码内容，并将解码结果保存到txt文件

        参数:
            url (str): 要请求的URL
            output_file (str): 输出文件名(默认为'raw.txt')

        返回:
            bool: 操作是否成功
        """
        try:
            # 发送HTTP请求
            response = requests.get(
                url, 
                proxies=self.proxy_settings, 
                headers=Config.CURL_HEADERS, 
                timeout=Config.DECODE_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"订阅链接: {url}")
            
            # 获取响应内容（二进制格式）
            content = response.content

            # 尝试Base64解码
            try:
                decoded_content = base64.b64decode(content)
            except binascii.Error:
                # 如果标准解码失败，尝试URL安全变体
                decoded_content = base64.urlsafe_b64decode(content)

            # 尝试将解码内容转换为UTF-8字符串
            try:
                decoded_text = decoded_content.decode("utf-8")
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，使用错误占位符替换
                decoded_text = decoded_content.decode("utf-8", errors="replace")

            # 使用文件锁安全地写入解码内容到文件
            with FileManager._file_lock:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(decoded_text)

            logger.info(f"解码成功! 结果已保存到: {output_file}")
            return True

        except requests.exceptions.RequestException as e:
            LogHelper.print_error(f"请求失败 ({url}): {e}")
        except Exception as e:
            LogHelper.print_error(f"处理失败 ({url}): {e}")

        return False


class TelegramProcessor:
    """处理Telegram频道"""
    
    def __init__(self, proxy_settings=None):
        """
        初始化Telegram处理器
        
        参数:
            proxy_settings (dict): 请求的代理配置
        """
        self.proxy_settings = proxy_settings
        self.file_lock = FileManager._file_lock
        self.proxy_extractor = ProxyExtractor(proxy_settings)

    def process_telegram_channel(self, channel_url, output_file=Config.RAW_OUTPUT_FILE, 
                                max_workers=Config.MAX_CONCURRENT_WORKERS):
        """
        处理Telegram公开频道，使用BeautifulSoup和正则表达式两种方式提取链接，
        并尝试Base64解码保存订阅内容
        
        参数:
            channel_url: Telegram公开频道URL (例如: https://t.me/s/channelname)
            output_file: 保存解码内容的文件名，默认为raw.txt
            max_workers: 线程池的最大线程数，默认为10
            
        返回:
            tuple: (成功解码的链接数, 提取的总链接数)
        """
        
        # 确保频道URL使用公开访问格式
        if "/s/" not in channel_url:
            channel_url = channel_url.replace("https://t.me/", "https://t.me/s/")
        
        logger.info(f"正在处理Telegram频道: {channel_url}")
        
        try:
            response = requests.get(
                channel_url, 
                headers=Config.DEFAULT_HEADERS, 
                timeout=Config.TELEGRAM_REQUEST_TIMEOUT,
                proxies=self.proxy_settings
            )
            response.raise_for_status()
            html_content = response.text
            
            # 方法1: 使用BeautifulSoup从<a>标签提取URLs
            soup = BeautifulSoup(html_content, 'html.parser')
            beautifulsoup_links = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href').strip()
                # 过滤无效链接
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                    continue
                # 转换为绝对URL
                absolute_url = urljoin(channel_url, href)
                
                # 过滤掉包含t.me和telegram的链接
                if ("https://t.me/" not in absolute_url and 
                    "http://t.me/" not in absolute_url and 
                    "telegram" not in absolute_url):
                    beautifulsoup_links.append(absolute_url)
            
            # 方法2: 使用正则表达式提取URLs
            regex_links = self.proxy_extractor.extract_urls_by_regex(html_content)
            
            # 合并两种方式提取的链接并去重
            all_subscription_links = []
            for link in list(set(beautifulsoup_links + regex_links)):
                if ("https://t.me/" not in link and 
                    "http://t.me/" not in link and 
                    "telegram" not in link):
                    all_subscription_links.append(link)
            
            # 分别记录两种方式的结果
            logger.info(f"BeautifulSoup方式提取: {len(beautifulsoup_links)} 个链接")
            logger.info(f"正则表达式方式提取: {len(regex_links)} 个链接")
            logger.info(f"合并去重后总计: {len(all_subscription_links)} 个可能的订阅链接")
            
            # 使用线程池并发处理链接
            success_count = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 创建任务列表，每个任务处理一个链接
                future_to_url = {
                    executor.submit(self._telegram_decode_and_save_base64, url, output_file): url 
                    for url in all_subscription_links
                }
                
                # 收集处理结果
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                    except Exception as exc:
                        logger.error(f'{url} 处理时出现异常: {exc}')
            
            logger.info(f"频道处理完成: {len(all_subscription_links)} 个链接, {success_count} 个成功解码并保存")
            return success_count, len(all_subscription_links)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求频道出错: {e}")
            return 0, 0
        except Exception as e:
            logger.error(f"处理频道过程中出错: {e}")
            return 0, 0

    def _telegram_decode_and_save_base64(self, url, output_file):
        """
        请求指定的URL，尝试Base64解码内容，检查是否包含"://"，
        并将符合条件的解码结果保存到txt文件
        使用锁确保文件写入同步
        """
        try:
            # 发送HTTP请求
            response = requests.get(
                url, 
                headers=Config.CURL_HEADERS, 
                timeout=Config.DECODE_REQUEST_TIMEOUT,
                proxies=self.proxy_settings
            )
            response.raise_for_status()
            
            logger.debug(f"尝试订阅链接: {url}")
            content = response.content
            
            # 尝试Base64解码
            try:
                decoded_content = base64.b64decode(content)
            except binascii.Error:
                # 如果标准解码失败，尝试URL安全变体
                try:
                    decoded_content = base64.urlsafe_b64decode(content)
                except binascii.Error:
                    logger.warning(f"Base64解码失败: {url}")
                    return False
            
            # 尝试将解码内容转换为UTF-8字符串
            try:
                decoded_text = decoded_content.decode("utf-8")
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，使用错误占位符替换
                decoded_text = decoded_content.decode("utf-8", errors="replace")
            
            # 检查解码结果是否包含"://"
            if "://" not in decoded_text:
                logger.debug(f"解码内容不包含有效协议标识(://)，跳过: {url}")
                return False
            
            # 使用锁进行线程同步，确保文件写入安全
            with self.file_lock:
                # 写入解码内容到文件
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(decoded_text + "\n")  # 添加换行符分隔不同订阅内容
            
            logger.info(f"✓ 解码成功! 已保存到: {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败: {e}")
        except Exception as e:
            logger.error(f"处理过程中出错: {e}")
        
        return False


class WebCrawler:
    """处理基于日期的代理源网页爬虫"""
    
    def __init__(self, proxy_settings=None):
        """
        初始化网页爬虫
        
        参数:
            proxy_settings (dict): 请求的代理配置
        """
        self.proxy_settings = proxy_settings
        self.content_fetcher = ContentFetcher(proxy_settings)

    def extract_domain_urls_if_contains_date(self, target_url, domain, file_extension):
        """
        提取包含当前日期的网页中属于指定域名的所有URL

        参数:
        target_url (str): 要分析的网页URL
        domain (str): 需要匹配的域名(可包含子域名)，如"example.com"或"sub.example.com"
        file_extension (str): 要过滤的文件扩展名

        返回:
        list: 包含匹配域名的URL列表，若无匹配返回空列表
        """
        # 获取当前日期并生成多种格式
        date_formats = DateFormatter.get_current_date_formats()

        try:
            # 发起HTTP请求
            response = requests.get(
                target_url, 
                proxies=self.proxy_settings, 
                headers=Config.DEFAULT_HEADERS, 
                timeout=Config.DECODE_REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # 检查日期格式是否存在
            content = response.text
            date_found = any(date_str in content for date_str in date_formats)

            if not date_found:
                return []  # 未找到日期字符串

            # 使用正则表达式提取所有URL
            url_pattern = re.compile(
                r'https?://[^\s"\'<>()]+|[^\s"\'<>()]+\.(?:com|cn|net|org|edu|gov|us|uk|jp|de|fr|ru|info|biz|co|io)[^\s"\'<>()]*|/[^\s"\'<>()]+',
                re.IGNORECASE,
            )

            all_urls = set()  # 使用集合自动去重
            for match in url_pattern.findall(content):
                # 清理URL（删除末尾可能存在的无效字符）
                clean_url = re.sub(r"[^\w/.?=&%:]+$", "", match.strip())
                if clean_url:
                    # 转换为绝对URL
                    absolute_url = urljoin(target_url, clean_url)
                    parsed_url = urlparse(absolute_url)

                    # 简化域名匹配逻辑
                    if parsed_url.netloc and (
                        domain.lower() in parsed_url.netloc.lower()
                        or urlparse(target_url).netloc.lower() in parsed_url.netloc.lower()
                    ):
                        all_urls.add(absolute_url)

            # 返回去重后的URL列表，过滤指定扩展名
            url_list = list(all_urls)
            filtered_urls = []
            for url in url_list:
                if file_extension in url.lower():
                    filtered_urls.append(url)
            return filtered_urls

        except (requests.RequestException, ValueError) as e:
            logger.error(f"处理URL时出错 {target_url}: {e}")
            return []

    def get_nearest_urls_for_today(self, url):
        """获取所有包含当日日期的位置，并为每个位置找到最近的URL"""
        # 生成多种格式的当日日期
        date_formats = DateFormatter.get_current_date_formats()

        try:
            # 发送请求获取页面内容
            response = requests.get(
                url, 
                headers=Config.DEFAULT_HEADERS, 
                timeout=Config.DECODE_REQUEST_TIMEOUT, 
                proxies=self.proxy_settings
            )
            response.raise_for_status()
            page_text = response.text

            # 获取基础URL用于处理相对路径
            base_url = response.url

            # 步骤1: 提取页面上所有URL及其位置
            url_pattern = re.compile(r'href\s*=\s*["\']?([^\s>"\'?#]+)', re.IGNORECASE)
            url_matches = []
            for match in url_pattern.finditer(page_text):
                href = match.group(1).strip()
                # 过滤空链接和特殊协议
                if href and not href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    url_matches.append(
                        {"url": href, "start": match.start(1), "end": match.end(1)}
                    )

            # 按URL开始位置排序
            url_matches.sort(key=lambda x: x["start"])

            # 创建URL开始位置列表用于二分查找
            url_positions = [url["start"] for url in url_matches]

            # 步骤2: 查找所有当日日期的位置
            date_positions = []
            for date_format in date_formats:
                escaped_format = re.escape(date_format)
                for match in re.finditer(escaped_format, page_text):
                    date_positions.append(
                        {"date": date_format, "start": match.start(), "end": match.end()}
                    )

            # 如果没有找到日期
            if not date_positions:
                logger.debug("在页面中未找到当日日期")
                return []

            # 步骤3: 为每个日期位置找到最近的URL
            nearest_urls = set()
            base_domain = "{0.scheme}://{0.netloc}".format(urlsplit(base_url))

            for date_info in date_positions:
                date_start = date_info["start"]
                date_end = date_info["end"]

                # 查找在日期位置前的最近URL
                before_index = bisect.bisect_left(url_positions, date_start) - 1
                if before_index >= 0:
                    url_info = url_matches[before_index]
                    url_str = url_info["url"]

                    # 转换为绝对URL
                    if url_str.startswith("/"):
                        url_str = f"{base_domain}{url_str}"
                    elif not url_str.startswith(("http://", "https://")):
                        url_str = urljoin(base_url, url_str)

                    nearest_urls.add(url_str)

                # 查找在日期位置后的最近URL
                after_index = bisect.bisect_left(url_positions, date_end)
                if after_index < len(url_matches):
                    url_info = url_matches[after_index]
                    url_str = url_info["url"]

                    # 转换为绝对URL
                    if url_str.startswith("/"):
                        url_str = f"{base_domain}{url_str}"
                    elif not url_str.startswith(("http://", "https://")):
                        url_str = urljoin(base_url, url_str)

                    nearest_urls.add(url_str)

            return list(nearest_urls)

        except requests.exceptions.RequestException as e:
            logger.error(f"请求出错: {e}")
            return []
        except Exception as e:
            logger.error(f"发生错误: {e}")
            return []

    def crawl_website_source(self, source_config):
        """
        使用提供的配置爬取网站源
        
        参数:
            source_config (dict): 包含target_url、domain和file_extension的配置
        """
        target_url = source_config["target_url"]
        domain = source_config["domain"]
        file_extension = source_config["file_extension"]
        
        result_links = self.get_nearest_urls_for_today(target_url)
        for link in result_links:
            extracted_urls = self.extract_domain_urls_if_contains_date(link, domain, file_extension)
            for url in extracted_urls:
                self.content_fetcher.decode_and_save_base64(url)


class SpeedTester:
    """处理节点速度测试和验证"""
    
    @staticmethod
    def test_nodes_and_extract_valid_ones():
        """
        下载xray-knife工具，执行节点测速，并提取有效节点保存到valid.txt
        """
        
        logger.info("开始下载xray-knife工具...")
        try:
            # 下载xray-knife工具
            subprocess.run(
                ["wget", "https://github.com/lilendian0x00/xray-knife/releases/download/v6.2.6/Xray-knife-linux-64.zip"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 解压工具
            subprocess.run(
                ["unzip", "-o", Config.SPEED_TEST_TOOL_ZIP], 
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 赋予执行权限
            subprocess.run(
                ["chmod", "+x", Config.SPEED_TEST_TOOL_BINARY], 
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info("开始测速节点，请稍等...")
            # 执行测速
            subprocess.run(
                [Config.SPEED_TEST_TOOL_BINARY, "http", "-f", Config.RAW_OUTPUT_FILE, 
                 "--speedtest", "--sort", "--type", "csv", "-o", Config.SPEED_TEST_RESULTS_FILE, 
                 "-t", str(Config.SPEED_TEST_THREADS)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 读取CSV文件并提取有效节点
            valid_nodes = []
            nodes_data = []
            
            with open(Config.SPEED_TEST_RESULTS_FILE, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # 检查download值是否大于0
                    try:
                        download_value = float(row.get('download', '0'))
                        if download_value > 0:
                            nodes_data.append({
                                'link': row['link'],
                                'download': download_value
                            })
                    except (ValueError, TypeError):
                        continue
            
            # 按照download值从大到小排序
            nodes_data.sort(key=lambda x: x['download'], reverse=True)
            
            # 提取排序后的链接
            valid_nodes = [node['link'] for node in nodes_data]
            
            # 保存有效节点到valid.txt（已按download值从大到小排序）
            with open(Config.VALID_OUTPUT_FILE, "w", encoding="utf-8") as f:
                for node in valid_nodes:
                    f.write(f"{node}\n")
            
            logger.info(f"已从测速结果中提取 {len(valid_nodes)} 个有效节点保存到 {Config.VALID_OUTPUT_FILE}（已按下载速度从高到低排序）")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"执行命令失败: {e}")
        except Exception as e:
            logger.error(f"处理过程中出错: {e}")


# =============================================================================
# 主应用程序类
# =============================================================================

class ProxyCollectionSystem:
    """协调整个代理收集过程的主应用程序类"""
    
    def __init__(self, proxy_settings=None):
        """
        初始化代理收集系统
        
        参数:
            proxy_settings (dict): 请求的代理配置
        """
        self.proxy_settings = proxy_settings
        
        # 初始化处理器
        self.web_crawler = WebCrawler(proxy_settings)
        self.content_fetcher = ContentFetcher(proxy_settings)
        self.telegram_processor = TelegramProcessor(proxy_settings)
        self.proxy_extractor = ProxyExtractor(proxy_settings)
        
        logger.info("代理收集系统初始化完成")

    def collect_from_website_crawlers(self):
        """从网站爬虫源收集代理 - 使用多线程提升效率"""
        logger.info("=== 开始从网站爬虫源收集代理 ===")
        
        def process_website_source(source_config):
            """处理单个网站源的包装函数"""
            try:
                self.web_crawler.crawl_website_source(source_config)
                return f"成功处理: {source_config['target_url']}"
            except Exception as e:
                error_msg = f"处理网站源 {source_config['target_url']} 时出错: {e}"
                logger.error(error_msg)
                return error_msg
        
        # 使用线程池并发处理网站源
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_WORKERS) as executor:
            # 提交所有任务
            future_to_source = {
                executor.submit(process_website_source, source_config): source_config 
                for source_config in SourceConfig.WEBSITE_CRAWLER_SOURCES
            }
            
            # 收集结果
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_source):
                source_config = future_to_source[future]
                try:
                    result = future.result()
                    completed_count += 1
                    logger.debug(f"网站源处理完成 ({completed_count}/{len(SourceConfig.WEBSITE_CRAWLER_SOURCES)}): {source_config['target_url']}")
                except Exception as exc:
                    logger.error(f"网站源 {source_config['target_url']} 处理时出现异常: {exc}")
        
        logger.info(f"网站爬虫源收集完成，共处理 {len(SourceConfig.WEBSITE_CRAWLER_SOURCES)} 个源")

    def collect_from_github_base64_sources(self):
        """从GitHub Base64源收集代理 - 使用多线程提升效率"""
        logger.info("=== 开始从GitHub Base64源收集代理 ===")
        
        def process_github_base64_source(url):
            """处理单个GitHub Base64源的包装函数"""
            try:
                result = self.content_fetcher.decode_and_save_base64(url)
                return f"成功处理: {url}" if result else f"处理失败: {url}"
            except Exception as e:
                error_msg = f"处理GitHub Base64源 {url} 时出错: {e}"
                logger.error(error_msg)
                return error_msg
        
        # 使用线程池并发处理GitHub Base64源
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_WORKERS) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(process_github_base64_source, url): url 
                for url in SourceConfig.GITHUB_BASE64_SOURCES
            }
            
            # 收集结果
            completed_count = 0
            success_count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    completed_count += 1
                    if "成功处理" in result:
                        success_count += 1
                    logger.debug(f"GitHub Base64源处理完成 ({completed_count}/{len(SourceConfig.GITHUB_BASE64_SOURCES)}): {url}")
                except Exception as exc:
                    logger.error(f"GitHub Base64源 {url} 处理时出现异常: {exc}")
        
        logger.info(f"GitHub Base64源收集完成，共处理 {len(SourceConfig.GITHUB_BASE64_SOURCES)} 个源，成功 {success_count} 个")
    
    def collect_from_github_plain_text_sources(self):
        """从GitHub明文源收集代理 - 使用多线程提升效率"""
        logger.info("=== 开始从GitHub明文源收集代理 ===")
        
        def process_github_plain_text_source(url):
            """处理单个GitHub明文源的包装函数"""
            try:
                result = self.content_fetcher.fetch_and_save_content(url)
                return f"成功处理: {url}" if result else f"处理失败: {url}"
            except Exception as e:
                error_msg = f"处理GitHub明文源 {url} 时出错: {e}"
                logger.error(error_msg)
                return error_msg
        
        # 使用线程池并发处理GitHub明文源
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_WORKERS) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(process_github_plain_text_source, url): url 
                for url in SourceConfig.GITHUB_PLAIN_TEXT_SOURCES
            }
            
            # 收集结果
            completed_count = 0
            success_count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    completed_count += 1
                    if "成功处理" in result:
                        success_count += 1
                    logger.debug(f"GitHub明文源处理完成 ({completed_count}/{len(SourceConfig.GITHUB_PLAIN_TEXT_SOURCES)}): {url}")
                except Exception as exc:
                    logger.error(f"GitHub明文源 {url} 处理时出现异常: {exc}")
        
        logger.info(f"GitHub明文源收集完成，共处理 {len(SourceConfig.GITHUB_PLAIN_TEXT_SOURCES)} 个源，成功 {success_count} 个")

    def collect_from_telegram_subscription_channels(self):
        """从Telegram订阅频道收集代理 - 保持原有的多线程机制"""
        logger.info("=== 开始从Telegram订阅频道收集代理 ===")
        
        def process_telegram_subscription_channel(channel_url):
            """处理单个Telegram订阅频道的包装函数"""
            try:
                success_count, total_count = self.telegram_processor.process_telegram_channel(channel_url)
                return f"成功处理: {channel_url}, 成功解码 {success_count}/{total_count} 个链接"
            except Exception as e:
                error_msg = f"处理Telegram订阅频道 {channel_url} 时出错: {e}"
                logger.error(error_msg)
                return error_msg
        
        # 使用线程池并发处理Telegram订阅频道
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_WORKERS) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(process_telegram_subscription_channel, channel_url): channel_url 
                for channel_url in SourceConfig.TELEGRAM_SUBSCRIPTION_CHANNELS
            }
            
            # 收集结果
            completed_count = 0
            total_success = 0
            total_processed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                channel_url = future_to_url[future]
                try:
                    result = future.result()
                    completed_count += 1
                    # 从结果中提取成功和总数
                    if "成功解码" in result:
                        try:
                            parts = result.split("成功解码 ")[1].split("/")
                            success = int(parts[0])
                            total = int(parts[1].split(" 个链接")[0])
                            total_success += success
                            total_processed += total
                        except:
                            pass
                    logger.debug(f"Telegram订阅频道处理完成 ({completed_count}/{len(SourceConfig.TELEGRAM_SUBSCRIPTION_CHANNELS)}): {channel_url}")
                except Exception as exc:
                    logger.error(f"Telegram订阅频道 {channel_url} 处理时出现异常: {exc}")
        
        logger.info(f"Telegram订阅频道收集完成，共处理 {len(SourceConfig.TELEGRAM_SUBSCRIPTION_CHANNELS)} 个频道，成功解码 {total_success}/{total_processed} 个链接")

    def collect_from_telegram_direct_channels(self):
        """从Telegram直接频道收集代理 - 使用多线程提升效率"""
        logger.info("=== 开始从Telegram直接频道收集代理 ===")
        
        def process_telegram_direct_channel(channel_url):
            """处理单个Telegram直接频道的包装函数"""
            try:
                link_count = self.proxy_extractor.extract_and_save_proxy_links(channel_url)
                return f"成功处理: {channel_url}, 提取 {link_count} 个链接"
            except Exception as e:
                error_msg = f"处理Telegram直接频道 {channel_url} 时出错: {e}"
                logger.error(error_msg)
                return error_msg
        
        # 使用线程池并发处理Telegram直接频道
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_CONCURRENT_WORKERS) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(process_telegram_direct_channel, channel_url): channel_url 
                for channel_url in SourceConfig.TELEGRAM_DIRECT_CHANNELS
            }
            
            # 收集结果
            completed_count = 0
            total_links = 0
            for future in concurrent.futures.as_completed(future_to_url):
                channel_url = future_to_url[future]
                try:
                    result = future.result()
                    completed_count += 1
                    # 从结果中提取链接数量
                    if "提取" in result and "个链接" in result:
                        try:
                            link_count = int(result.split("提取 ")[1].split(" 个链接")[0])
                            total_links += link_count
                        except:
                            pass
                    logger.debug(f"Telegram直接频道处理完成 ({completed_count}/{len(SourceConfig.TELEGRAM_DIRECT_CHANNELS)}): {channel_url}")
                except Exception as exc:
                    logger.error(f"Telegram直接频道 {channel_url} 处理时出现异常: {exc}")
        
        logger.info(f"Telegram直接频道收集完成，共处理 {len(SourceConfig.TELEGRAM_DIRECT_CHANNELS)} 个频道，提取 {total_links} 个链接")
    
    def process_collected_data(self):
        """处理收集到的代理数据"""
        logger.info("=== 开始处理收集的数据 ===")
        
        # 移除空行和注释
        FileManager.remove_blank_lines()
        
        # 移除重复项
        FileManager.remove_duplicates_from_file(Config.RAW_OUTPUT_FILE)
        
        # 测试节点并提取有效节点
        SpeedTester.test_nodes_and_extract_valid_ones()
        
        # 转换为Base64
        result = FileManager.convert_to_base64_and_save()
        logger.info(result)

    def run_full_collection(self):
        """执行完整的代理收集流程 - 优化了多线程性能"""
        logger.info("开始执行完整的代理收集流程...")
        start_time = time.time()
        
        # 清理任何现有文件
        FileManager.clean_temporary_files()
        
        # 从所有源收集（每个方法内部已经实现了多线程）
        collection_start = time.time()
        
        self.collect_from_website_crawlers()
        website_time = time.time() - collection_start
        logger.info(f"网站爬虫源收集耗时: {website_time:.2f}秒")
        
        github_base64_start = time.time()
        self.collect_from_github_base64_sources()
        github_base64_time = time.time() - github_base64_start
        logger.info(f"GitHub Base64源收集耗时: {github_base64_time:.2f}秒")
        
        github_plain_start = time.time()
        self.collect_from_github_plain_text_sources()
        github_plain_time = time.time() - github_plain_start
        logger.info(f"GitHub明文源收集耗时: {github_plain_time:.2f}秒")
        
        telegram_sub_start = time.time()
        self.collect_from_telegram_subscription_channels()
        telegram_sub_time = time.time() - telegram_sub_start
        logger.info(f"Telegram订阅频道收集耗时: {telegram_sub_time:.2f}秒")
        
        telegram_direct_start = time.time()
        self.collect_from_telegram_direct_channels()
        telegram_direct_time = time.time() - telegram_direct_start
        logger.info(f"Telegram直接频道收集耗时: {telegram_direct_time:.2f}秒")
        
        collection_time = time.time() - collection_start
        logger.info(f"所有源收集总耗时: {collection_time:.2f}秒")
        
        # 处理收集的数据
        process_start = time.time()
        self.process_collected_data()
        process_time = time.time() - process_start
        logger.info(f"数据处理耗时: {process_time:.2f}秒")
        
        total_time = time.time() - start_time
        logger.info(f"=== 代理收集流程完成，总耗时: {total_time:.2f}秒 ===")


# =============================================================================
# 主执行部分
# =============================================================================

def main():
    """主执行函数"""
    # 配置代理设置（设为None表示不使用代理）
    proxy_settings = None
    # 代理配置示例:
    # proxy_settings = {
    #   "http": "socks5://192.168.79.1:10909",
    #   "https": "socks5://192.168.79.1:10909",
    # }
    
    # 初始化并运行代理收集系统
    collection_system = ProxyCollectionSystem(proxy_settings)
    collection_system.run_full_collection()


if __name__ == "__main__":
    main()

