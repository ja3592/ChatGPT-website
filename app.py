# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response
import requests
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)

# 从.env文件中加载api配置
load_dotenv()

# 获取环境变量
api_url = os.getenv('API_URL')
api_key = os.getenv('API_KEY')


@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    messages = request.form.get("prompts", None)
    apiKey = api_key
    model = "glm-4"
    if messages is None:
        return jsonify({"error": {"message": "请输入prompts！", "type": "invalid_request_error", "code": ""}})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    # json串转对象
    prompts = json.loads(messages)

    data = {
        "messages": prompts,
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.5,
        "top_p": 1,
        "stream": True,
    }

    try:
        resp = requests.post(
            url=api_url,
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 10)  # 连接超时时间为10秒，读取超时时间为10秒
        )
        print(f'resp:{resp}')
    except requests.exceptions.Timeout:
        return jsonify({"error": {"message": "请求超时，请稍后再试！", "type": "timeout_error", "code": ""}})

    def generate():
        errorStr = ""
        for chunk in resp.iter_lines():
            if chunk:
                streamStr = chunk.decode("utf-8").replace("data: ", "")
                try:
                    streamDict = json.loads(streamStr)  # 说明出现返回信息不是正常数据,是接口返回的具体错误信息
                    print(f'streamDict:{streamDict}')
                except:
                    errorStr += streamStr.strip()  # 错误流式数据累加
                    continue
                delData = streamDict.get("choices","None")[0]
                if delData.get("finish_reason",'haha') == 'stop' :
                    break
                else:
                    respStr = delData["delta"]["content"]
                    # print(respStr)
                    yield respStr

        # 如果出现错误，此时错误信息迭代器已处理完，app_context已经出栈，要返回错误信息，需要将app_context手动入栈
        if errorStr != "":
            with app.app_context():
                yield errorStr
    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(port=5000)
