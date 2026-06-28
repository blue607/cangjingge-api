from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ========== 复制粘贴你已验证通过的爬虫函数 ==========
def extract_text_from_content(content):
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
        if 'data' in content:
            return extract_text_from_content(content['data'])
        elif 'text' in content:
            return extract_text_from_content(content['text'])
        elif 'content' in content:
            return extract_text_from_content(content['content'])
        else:
            parts = []
            for v in content.values():
                text = extract_text_from_content(v)
                if text:
                    parts.append(text)
            return '\n'.join(parts)
    else:
        return str(content)

def search_and_get_answer(keyword):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Referer": "https://cangjggame.com/",
        "Origin": "https://cangjggame.com",
        "Accept": "application/json, text/plain, */*",
    }
    
    history_url = "https://game-forum.shannonai.com/api/search/history"
    params = {"keyword": keyword, "gameId": 652}
    
    try:
        resp = session.get(history_url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        article_id = data.get('articleId')
        if not article_id:
            return None
    except Exception as e:
        logging.error(f"搜索失败: {e}")
        return None
    
    detail_url = f"https://game-forum.shannonai.com/api/history/detail?id={article_id}"
    try:
        detail_resp = session.get(detail_url, headers=headers, timeout=10)
        detail_resp.raise_for_status()
        return detail_resp.json()
    except Exception as e:
        logging.error(f"详情失败: {e}")
        return None

def format_answer(data):
    if not data:
        return "未找到相关内容"
    title = data.get('title', '无标题')
    content = data.get('content', '')
    full_content = extract_text_from_content(content)
    if not full_content or len(full_content.strip()) < 10:
        intro = data.get('introduction', '')
        if intro:
            full_content = intro
    return f"【{title}】\n\n{full_content}"
# ==================================================

@app.route('/search', methods=['GET'])
def search_api():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({"error": "请提供关键词参数 q"}), 400
    
    data = search_and_get_answer(keyword)
    if data:
        return jsonify({
            "success": True,
            "title": data.get('title', ''),
            "answer": format_answer(data)
        })
    else:
        return jsonify({"success": False, "error": "未找到相关内容"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)