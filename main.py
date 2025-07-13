import requests
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit
import bisect
import os
import re
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
import base64
import requests
import binascii

def fetch_and_save_content(url, output_file="raw.txt"):
    global proxies
    """
    请求指定的URL，并将响应内容原样保存到txt文件
    
    参数:
        url (str): 要请求的URL
        output_file (str): 输出文件名(默认为'raw.txt')
    
    返回:
        bool: 操作是否成功
    """
    try:
        headers = {
            "User-Agent": "curl/8.12.1",
            "Accept": "*/*",
            'Accept-Encoding': 'identity',
        }
        # 发送HTTP请求
        response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        print(f"请求链接: {url}")
        
        # 获取响应内容
        content = response.content
        
        # 尝试将内容转换为UTF-8字符串
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，使用错误占位符替换
            text_content = content.decode("utf-8", errors="replace")
            
        # 写入内容到文件
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(text_content)
            
        print(f"保存成功! 内容已保存到: {output_file}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"处理过程中出错: {e}")
        
    return False


def decode_and_save_base64(url, output_file="raw.txt"):
    global proxies
    """
    请求指定的URL，尝试Base64解码内容，并将解码结果保存到txt文件

    参数:
        url (str): 要请求的URL
        output_file (str): 输出文件名(默认为'decoded_output.txt')

    返回:
        bool: 操作是否成功
    """
    try:
        headers = {
            "User-Agent": "curl/8.12.1",
            "Accept": "*/*",
            'Accept-Encoding': 'identity',
        }
        # 发送HTTP请求
        response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        print(f"订阅链接: {url}")
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

        # 写入解码内容到文件
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(decoded_text)

        print(f"解码成功! 结果已保存到: {output_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"处理过程中出错: {e}")

    return False


def extract_domain_urls_if_contains_date(target_url, domain, ext):
    """
    提取包含当前日期的网页中属于指定域名的所有URL

    参数:
    target_url (str): 要分析的网页URL
    domain (str): 需要匹配的域名(可包含子域名)，如"example.com"或"sub.example.com"

    返回:
    list: 包含匹配域名的URL列表，若无匹配返回空列表
    """
    global proxies
    # 获取当前日期并生成多种格式
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

    try:
        # 发起HTTP请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }

        response = requests.get(
            target_url, proxies=proxies, headers=headers, timeout=10
        )
        response.raise_for_status()

        # 检查日期格式是否存在
        content = response.text
        found = any(date_str in content for date_str in date_formats)

        if not found:
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

        # 返回去重后的URL列表
        url_lst = list(all_urls)
        urls = []
        for i in url_lst:
            if ext in i.lower():
                urls.append(i)
        return urls

    except (requests.RequestException, ValueError) as e:
        print(f"处理URL时出错 {target_url}: {e}")
        return []


def get_nearest_urls_for_today(url):
    global proxies
    """获取所有包含当日日期的位置，并为每个位置找到最近的URL"""
    # 生成多种格式的当日日期
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:

        # 发送请求获取页面内容
        response = requests.get(url, headers=headers, timeout=10, proxies=proxies)
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
        for fmt in date_formats:
            escaped_fmt = re.escape(fmt)
            for match in re.finditer(escaped_fmt, page_text):
                date_positions.append(
                    {"date": fmt, "start": match.start(), "end": match.end()}
                )

        # 如果没有找到日期
        if not date_positions:
            print("在页面中未找到当日日期")
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
        print(f"请求出错: {e}")
        return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []


def crawler(target_url, domain, ext):

    result_links = get_nearest_urls_for_today(target_url)
    for link in result_links:
        #print(f"{link}")
        for i in extract_domain_urls_if_contains_date(link, domain, ext):
            decode_and_save_base64(i)

def convert_to_base64_and_save(input_file_path="raw.txt", output_file_path="v2.txt"):
    """
    读取文件、转换为Base64编码并保存结果
    
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

def remove_blank_lines():
    """
    移除文件中的空行和注释行
    读取raw.txt文件，过滤掉所有空行和以#开头的注释行后重新写入原文件
    """
    with open('raw.txt', 'r', encoding='utf-8') as file:
        # 过滤条件：1. 不是空行 2. 不是以#开头的注释行
        filtered_lines = [line for line in file if line.strip() != "" and not line.strip().startswith('#')]
    # 覆盖写入原文件
    with open('raw.txt', 'w', encoding='utf-8') as file:
        file.writelines(filtered_lines)
    
    print("已移除所有空行和注释行")

# 使用示例
if __name__ == "__main__":
    global proxies
    for file in ["raw.txt", "v2.txt"]:
        if os.path.exists(file):
            os.remove(file)
#     proxies = {
#     "http": "http://192.168.36.133:10809",
#     "https": "http://192.168.36.133:10809",
# }
    proxies=None
    source = [
        {
            "target_url": "https://www.mibei77.com/",
            "domain": "mm.mibei77.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://clashnodev2ray.github.io/",
            "domain": "a.nodeshare.xyz",
            "ext": ".txt",
        },
        {
            "target_url": "https://wanzhuanmi.com/",
            "domain": "wanzhuanmi.cczzuu.top",
            "ext": ".txt",
        },
        {
            "target_url": "https://www.freeclashnode.com/free-node/",
            "domain": "node.freeclashnode.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://betternode.org/freenode",
            "domain": "betternode.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://oneclash.cc/freenode",
            "domain": "oneclash.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://wenode.cc/freenode",
            "domain": "wenode.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://nodeclash.com/free-node/",
            "domain": "node.nodeclash.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://v2rayshare.org/free-node/",
            "domain": "node.v2rayshare.org",
            "ext": ".txt",
        },
        {
            "target_url": "https://v2rayshare.org/free-node/",
            "domain": "nodefree.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://www.stairnode.com/freenode",
            "domain": "stairnode.cczzuu.top",
            "ext": ".txt",
        },
        {
            "target_url": "https://naidounode.com/freenode",
            "domain": "naidounode.cczzuu.top",
            "ext": ".txt",
        },
        {
            "target_url": "https://v2raynode.net/archives/category/freenode",
            "domain": "v2raynode.cczzuu.top",
            "ext": ".txt",
        },
        {
            "target_url": "https://www.freev2raynode.com/free-node-subscription/",
            "domain": "node.freev2raynode.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://clashgithub.net/free-node/",
            "domain": "node.clashgithub.net",
            "ext": ".txt",
        },
        {
            "target_url": "https://clashfreenode.com/",
            "domain": "clashfreenode.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://mianfeiv2rayx.github.io/",    #失败
            "domain": "mianfeiv2rayx.github.io",
            "ext": ".txt",
        },
        {
            "target_url": "https://clash-meta.github.io/",        #失败
            "domain": "node.freeclashnode.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://nodev2ray.com/",                #失败
            "domain": "node.nodev2ray.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://nodefree.net/",                #失败
            "domain": "nodefree.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://v2rayshare.net/",            #失败
            "domain": "v2rayshare.githubrowcontent.com",
            "ext": ".txt",
        },
        {
            "target_url": "https://hiddifynextnode.github.io/",
            "domain": "hiddifynextnode.github.io",
            "ext": ".txt",
        }
    ]

    github_source=[
        "https://raw.githubusercontent.com/Barabama/FreeNodes/refs/heads/main/nodes/blues.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/clashmeta.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/ndnode.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/nodefree.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/nodev2ray.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/v2rayshare.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/wenode.txt",
        "https://github.com/Barabama/FreeNodes/raw/refs/heads/main/nodes/yudou66.txt",
        "https://github.com/hzcsure/hzcsure/raw/refs/heads/main/example.txt"
        
    ]

    github_source_base64=[
        "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
        "https://raw.githubusercontent.com/snakem982/proxypool/main/source/v2ray-2.txt"
    ]
    
    for i in source:
        crawler(i["target_url"], i["domain"], i["ext"])

    for i in github_source_base64:
        decode_and_save_base64(i)
    
    for i in github_source:
        fetch_and_save_content(i)
        
    remove_blank_lines()
    convert_to_base64_and_save()
