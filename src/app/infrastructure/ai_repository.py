import requests

# TODO: MAKE ONLY IN CI-PIPELINE MAYBE :/
API_TOKEN = "sk-RGR8hA6f3zld0VxhG8KgZUXEvLCA9wvn"

BASE_URL = "https://api.proxyapi.ru/openai"
HEADER_TOKEN_LIMIT = 64
BODY_TOKEN_LIMIT = 128

TOKEN_LIMIT_MAX = 1024

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
})

def make_ai_request(prompt, token_limit=96, model="gpt-4o-mini"):
    if token_limit > TOKEN_LIMIT_MAX:
        token_limit = TOKEN_LIMIT_MAX

    request = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "max_tokens": token_limit
    }

    response = session.post(f"{BASE_URL}/v1/chat/completions", json=request)
    return response.json().get("choices", [dict()])[0].get("message", dict()).get("content")


def gen_title_by_description(description, token_limit=32):
    prompt = "Make a title from problems description below. ONLY USE ORIGINAL TEXT'S LANG. Give only result in answer.\n{0}"
    return make_ai_request(prompt.format(description), token_limit)


def enchant_text(description, token_limit=196):
    prompt = "Enchant this text. Make it more relevant and understandable, marks all problems. ONLY USE ORIGINAL TEXT'S LANG. Give only result in answer.\n{0}"
    return make_ai_request(prompt.format(description), token_limit)