import requests
import re
import datetime
import base64
import threading
import html as ht
from concurrent.futures import ThreadPoolExecutor

now = datetime.datetime.now()
lock = threading.Lock()
PROTOCOL = ["ss://", "trojan://", "vless://",
            "vmess://", "hysteria2://", "hysteria://", "ssr://"]
SUBSCRIBE = []
URLS = [
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/v2ray-2.txt",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
    "https://gist.githubusercontent.com/shaoyouvip/9dc3d23482fdc4a19e407a7e944782b8/raw/base64.txt",
    "https://dlconf.clashapps.cc/conf/c641d872-b44b-2b3e-b21e-6cd4997dd084.conf",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/refs/heads/master/Eternity.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/refs/heads/master/list.txt",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt",
    "https://raw.githubusercontent.com/hello-world-1989/cn-news/main/end-gfw-together",
    "https://raw.githubusercontent.com/ggborr/FREEE-VPN/refs/heads/main/1V2RAY",
    "https://raw.githubusercontent.com/hello-world-1989/v2-sub/refs/heads/main/end-gfw-together",
    "https://iwxf.netlify.app/",
    "https://raw.githubusercontent.com/ssrsub/ssr/refs/heads/master/v2ray",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/a11",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/refs/heads/main/sub/base64.txt",
    "https://links.bocchi2b.top/clash",
    "https://raw.githubusercontent.com/Flikify/Free-Node/refs/heads/main/v2ray.txt",
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
WEBSITE_CRAWLER_SOURCES = [
    {
        "url": "https://www.mibei77.com/",
        "domain": "mm.mibei77.com"
    },
    {
        "url": "https://clashnodev2ray.github.io",
        "domain": "sfdr.zaixianyouxi.dpdns.org"
    },
    {
        "url": "https://wanzhuanmi.com/",
        "domain": "wanzhuanmi.cczzuu.top"
    },
    {
        "url": "https://www.freeclashnode.com",
        "domain": "node.freeclashnode.com",
    },
    {
        "url": "https://oneclash.cc/freenode",
        "domain": "oneclash.githubrowcontent.com"
    },
    {
        "url": "https://nodeclash.com",
        "domain": "node.nodeclash.com",
    },
    {
        "url": "https://v2rayshare.org",
        "domain": "node.v2rayshare.org",
    },
    {
        "url": "https://www.stairnode.com",
        "domain": "stairnode.cczzuu.top",
    },
    {
        "url": "https://naidounode.com/freenode",
        "domain": "naidounode.cczzuu.top",
    },
    {
        "url": "https://v2raynode.net/archives/category/freenode",
        "domain": "v2raynode.cczzuu.top"
    },
    {
        "url": "https://www.freev2raynode.com",
        "domain": "node.freev2raynode.com",
    },
    {
        "url": "https://clashgithub.net",
        "domain": "node.clashgithub.net",
    },
    {
        "url": "https://clashfreenode.com/",
        "domain": "clashfreenode.com",
    },
    {
        "url": "https://v2rayshare.net/",
        "domain": "v2rayshare.githubrowcontent.com",
    },
    {
        "url": "https://free.datiya.com",
        "domain": "free.datiya.com",
    }
]

TELEGRAM_SUBSCRIPTION_CHANNELS = [
    "https://t.me/s/wxdy666",
    "https://t.me/s/fq521",
    "https://t.me/s/jiedian_share",
    "https://t.me/s/fqzw9",
    "https://t.me/s/SSRSUB",
    "https://t.me/s/ccbaohe",
    "https://t.me/s/juzibaipiao",
    "https://t.me/s/dns68",
    "https://t.me/s/hkaa0",
    "https://t.me/s/SubscriptionShare",
    "https://t.me/s/dingyue_center",
    "https://t.me/s/freeVPNjd",
    "https://t.me/s/mfbp1"
]

DIRECT_SOURCE = [
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
    "https://github.com/free-nodes/v2rayfree",
    "https://t.me/s/wxdy666",
    "https://t.me/s/fq521",
    "https://t.me/s/jiedian_share",
    "https://t.me/s/fqzw9",
    "https://t.me/s/SSRSUB",
    "https://t.me/s/ccbaohe",
    "https://t.me/s/juzibaipiao",
    "https://t.me/s/dns68",
    "https://t.me/s/hkaa0",
    "https://t.me/s/SubscriptionShare",
    "https://t.me/s/dingyue_center",
    "https://t.me/s/freeVPNjd",
    "https://t.me/s/mfbp1"
]

date_format = [now.strftime("%Y年%m月%d日"), now.strftime(
    "%m.%d"), now.strftime("%m月%d日"), f"{now.month}月{now.day}日"]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}


def base64_decode(text):
    if any(i in text for i in PROTOCOL):
        return text
    else:
        missing_padding = len(text) % 4
        if missing_padding != 0:
            text += '=' * (4 - missing_padding)
        decoded_data = base64.b64decode(text)
        return decoded_data.decode('utf-8')


def p_extract(html):
    pattern = r'<p*>.*?</p>'
    matches = re.findall(pattern, html, re.DOTALL)

    pattern = r'<code>.*?</code>'
    matches1 = re.findall(pattern, html, re.DOTALL)
    return matches+matches1


def find_urls(string):
    pattern = r'http.*?txt'
    matches = re.findall(pattern, string, re.DOTALL)
    return matches


def subscribe_extract(matches, domain):
    count = 0
    for i in matches:
        if domain in i:
            url = find_urls(i)
            if url:
                URLS.append(url[0])
                # print(url[0])
                count = count+1
    return count


def url_extract(html):
    pattern = r'<a[^r][^>]*>.*?</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    return matches


def today_url(matches):
    for i in matches:
        if any(date in i for date in date_format):
            pattern = r'href=[\'"].*?[\'"]'
            href = re.findall(pattern, i, re.DOTALL)
            if len(href) == 0:
                pattern = r'href=.*? '
                href = re.findall(pattern, i, re.DOTALL)
                return href[0][5:-1]
            return href[0][6:-1]


def web_crawler(i):
    response = requests.get(url=i['url'], headers=headers)
    response.encoding = response.apparent_encoding
    matches = url_extract(response.text)
    # print(response.text)
    # print(matches)
    url = today_url(matches)
    if not url.startswith("http"):
        url = i['url']+url
    # print(url)
    response = requests.get(url=url, headers=headers)
    matches = p_extract(response.text)
    # print(matches)
    count = subscribe_extract(matches, i['domain'])
    print(i['domain'], count)


def tg_base64_decode(url, count):
    # print(url)
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            return None
        response.encoding = response.apparent_encoding
        text = response.text
    except Exception as e:
        # print("error:", e)
        return None
    if "<" in text or "{" in text or "proxies:" in text:
        # print("html",text[:20])
        return None

    if any(i in text for i in PROTOCOL):
        # print("raw",text[:20])
        count[0] = count[0]+1
        URLS.append(url)
        return text
    else:
        missing_padding = len(text) % 4
        if missing_padding != 0:
            text += '=' * (4 - missing_padding)
        decoded_data = base64.b64decode(text)
        # print("decode",text[:20])
        count[0] = count[0]+1
        URLS.append(url)
        return decoded_data.decode('utf-8')


def all_url(matches):
    count = [0]
    with ThreadPoolExecutor(max_workers=20) as executor:
        for i in matches:
            if "http" not in i:
                continue
            if "</a>" in i:
                pattern = r'href=[\'"].*?[\'"]'
                href = re.findall(pattern, i, re.DOTALL)
                if "t.me" not in href[0][6:-1] and "telegram" not in href[0][6:-1]:
                    executor.submit(tg_base64_decode, href[0][6:-1], count)
                    # tg_base64_decode(href[0][6:-1],count)

                    # print(href[0][6:-1], text[:20])

            else:
                # tg_base64_decode(i[6:-7],count)
                executor.submit(tg_base64_decode, i[6:-7], count)
                pass

    return count[0]


def tg_url_extract(html):
    pattern = r'<a[^r][^>]*>.*?</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    pattern = r'<code>.*?</code>'
    matches1 = re.findall(pattern, html, re.DOTALL)
    return matches+matches1


def tg_crawler(i):
    response = requests.get(url=i, headers=headers)
    response.encoding = response.apparent_encoding
    matches = tg_url_extract(response.text)
    count = all_url(matches)
    print(i, count)


def find_subscribe(url):
    count = 0
    response = requests.get(url=url, headers=headers)
    response.encoding = response.apparent_encoding
    html = response.text
    matches_all = []
    for i in PROTOCOL:
        pattern = f'{i}.*?[ \\n<]'
        matches = re.findall(pattern, html, re.DOTALL)
        matches_all = matches_all+matches
    for i in matches_all:
        if len(i) > 20:
            # print(i.strip().replace("<",""))
            subscribe = ht.unescape(i.strip().replace("<", ""))
            SUBSCRIBE.append(subscribe)
            count = count+1
    print(url, count)


def save(url, file):
    response = requests.get(url=url, headers=headers)
    response.encoding = response.apparent_encoding
    subscribe = base64_decode(response.text)
    with lock:
        print(url, subscribe[:20])
        file.write(subscribe+"\n")


if __name__ == '__main__':
    # print(date_format)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in WEBSITE_CRAWLER_SOURCES:
            # web_crawler(i)
            executor.submit(web_crawler, i)

    # with ThreadPoolExecutor(max_workers=10) as executor:
        for i in TELEGRAM_SUBSCRIPTION_CHANNELS:
            # tg_crawler(i)
            executor.submit(tg_crawler, i)
    # for i in DIRECT_SOURCE:
    #     find_subscribe(i)
        for i in DIRECT_SOURCE:
            executor.submit(find_subscribe, i)

    with open("subscribe", "a", encoding="utf-8") as file:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i in URLS:
                executor.submit(save, i, file)
                # response = requests.get(url=i, headers=headers)
                # response.encoding = response.apparent_encoding
                # subscribe=base64_decode(response.text)
                # print(i,subscribe[:20])
                # file.write(subscribe+"\n")

        for i in SUBSCRIBE:
            file.write(i+"\n")

    seen = set()
    with open("subscribe", "r", encoding="utf-8") as input, open("v2", "a", encoding="utf-8") as output:
        for i in input:
            line = i.strip()
            if any(line.startswith(p) for p in PROTOCOL):

                if line and line not in seen:
                    seen.add(line)
                    output.write(line+"\n")
    print(f"去重后共{len(seen)}")
