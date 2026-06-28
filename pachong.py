import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_content(content):
    """
    递归提取 content 中的所有文本，支持嵌套的列表/字典
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            text = extract_text_from_content(item)
            if text:
                parts.append(text)
        return '\n'.join(parts)
    elif isinstance(content, dict):
        # 优先查找常见的文本字段
        if 'data' in content:
            return extract_text_from_content(content['data'])
        elif 'text' in content:
            return extract_text_from_content(content['text'])
        elif 'content' in content:
            return extract_text_from_content(content['content'])
        else:
            # 如果都没找到，递归提取所有值
            parts = []
            for v in content.values():
                text = extract_text_from_content(v)
                if text:
                    parts.append(text)
            return '\n'.join(parts)
    else:
        return str(content)

def search_and_get_answer(keyword):
    """
    根据关键词搜索，返回问答详情（JSON格式）
    """
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Referer": "https://cangjggame.com/",
        "Origin": "https://cangjggame.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    
    # 1. 调用 search/history 接口获取 articleId
    history_url = "https://game-forum.shannonai.com/api/search/history"
    params = {
        "keyword": keyword,
        "gameId": 652
    }
    
    try:
        logging.info(f"请求 search/history 接口: {history_url}?keyword={keyword}&gameId=652")
        resp = session.get(history_url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logging.info(f"search/history 接口返回: {data}")
        
        article_id = data.get('articleId')
        if not article_id:
            logging.error("search/history 接口未返回 articleId")
            return None
        
        logging.info(f"获取到 articleId: {article_id}")
    except Exception as e:
        logging.error(f"调用 search/history 接口失败: {e}")
        return None
    
    # 2. 调用 detail 接口获取完整内容
    detail_url = f"https://game-forum.shannonai.com/api/history/detail?id={article_id}"
    
    try:
        logging.info(f"请求 detail 接口: {detail_url}")
        detail_resp = session.get(detail_url, headers=headers, timeout=10)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()
        logging.info("成功获取详情数据")
        return detail_data
    except Exception as e:
        logging.error(f"调用 detail 接口失败: {e}")
        return None

def format_answer(data):
    """
    将API返回的数据格式化为可读的问答内容
    """
    if not data:
        return "未找到相关内容"
    
    title = data.get('title', '无标题')
    content = data.get('content', '')
    
    # 使用递归提取函数获取完整文本
    full_content = extract_text_from_content(content)
    
    # 如果 content 为空，尝试使用 introduction
    if not full_content or len(full_content.strip()) < 10:
        intro = data.get('introduction', '')
        if intro:
            full_content = intro
    
    return f"【{title}】\n\n{full_content}"

if __name__ == "__main__":
    keyword = input("请输入要搜索的关键词: ").strip()
    if not keyword:
        print("关键词不能为空")
    else:
        data = search_and_get_answer(keyword)
        if data:
            print("\n" + "="*60)
            print(format_answer(data))
            print("="*60)
        else:
            print("\n未能获取到答案。可能原因：")
            print("1. 网站没有找到相关文章")
            print("2. search/history 接口返回数据为空")
            print("3. 网络连接问题")
            print("请尝试其他关键词。")