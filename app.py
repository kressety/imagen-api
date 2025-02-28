import json
import os
from io import BytesIO

from flask import Flask, request, jsonify, send_file

from providers.aliyun import AliyunFactory
from providers.cloudflare import CloudflareFactory
from providers.modelscope import ModelScopeFactory

app = Flask(__name__)

# 加载配置文件
CONFIG_PATH = "models_config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    MODELS_CONFIG = json.load(f)

# 假设API密钥存储在环境变量中（实际使用时需设置）
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "your_cloudflare_account_id")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "your_cloudflare_api_token")
MODELSCOPE_API_TOKEN = os.getenv("MODELSCOPE_API_TOKEN", "your_modelscope_api_token")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "your_dashscope_api_key")

# 提供者工厂映射
PROVIDER_FACTORIES = {
    "cloudflare": CloudflareFactory(CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN),
    "modelscope": ModelScopeFactory(MODELSCOPE_API_TOKEN),
    "aliyun": AliyunFactory(DASHSCOPE_API_KEY)
}


def validate_request(provider: str, model: str, task: str) -> tuple[bool, str]:
    """
    校验请求是否有效。

    Args:
        provider (str): 供应商名。
        model (str): 模型名。
        task (str): 任务类型。

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)。
    """
    # 检查供应商是否存在
    if provider not in MODELS_CONFIG:
        return False, f"Provider '{provider}' not found in configuration."

    provider_models = MODELS_CONFIG[provider]

    # 检查模型名是否有效
    if "*" in provider_models:  # 通配符支持（如ModelScope）
        if task not in provider_models["*"]:
            return False, f"Task '{task}' not supported by any model under provider '{provider}'."
    else:
        if model not in provider_models:
            return False, f"Model '{model}' not found under provider '{provider}'."
        if task not in provider_models[model]:
            return False, f"Task '{task}' not supported by model '{model}' under provider '{provider}'."

    return True, ""


@app.route("/generate", methods=["POST"])
def generate_image():
    """
    文生图和图文生图API端点。

    Request Body (multipart/form-data):
        - provider (str): 供应商名，例如"cloudflare"。
        - model (str): 模型名，例如"@cf/runwayml/stable-diffusion-v1-5-img2img"。
        - task (str): 任务类型，"text_to_image" 或 "image_to_image"。
        - prompt (str): 文本提示。
        - image (file, 可选): 输入图像文件（仅image_to_image需要）。

    Returns:
        - 成功：图像文件（image/png）。
        - 失败：JSON错误消息。
    """
    # 获取表单数据
    provider = request.form.get("provider")
    model = request.form.get("model")
    task = request.form.get("task")
    prompt = request.form.get("prompt")

    # 基本参数校验
    if not all([provider, model, task, prompt]):
        return jsonify({"error": "Missing required parameters: provider, model, task, prompt"}), 400

    if task not in ["text_to_image", "image_to_image"]:
        return jsonify({"error": "Invalid task type. Use 'text_to_image' or 'image_to_image'."}), 400

    # 校验配置
    is_valid, error_msg = validate_request(provider, model, task)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # 获取图像文件（仅图文生图需要）
    input_image = None
    if task == "image_to_image":
        if "image" not in request.files:
            return jsonify({"error": "Missing 'image' file for image-to-image task."}), 400
        image_file = request.files["image"]
        if image_file.filename == "":
            return jsonify({"error": "No selected file for 'image'."}), 400
        input_image = image_file.read()

    # 创建提供者实例
    if provider not in PROVIDER_FACTORIES:
        return jsonify({"error": f"Provider '{provider}' is not implemented."}), 500
    factory = PROVIDER_FACTORIES[provider]
    provider_instance = factory.create_provider(model)

    # 生成图像
    try:
        if task == "text_to_image":
            image_bytes = provider_instance.generate("text_to_image", prompt=prompt)
        else:  # image_to_image
            image_bytes = provider_instance.generate("image_to_image", prompt=prompt, input_image=input_image)

        # 返回图像文件
        return send_file(
            BytesIO(image_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name="generated_image.png"
        )
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500

@app.route("/models", methods=["GET"])
def list_models():
    """
    返回models_config.json的内容，列出所有支持的供应商、模型及其任务能力。

    Returns:
        JSON: models_config.json的内容。
    """
    try:
        # 直接返回加载的配置
        return jsonify(MODELS_CONFIG), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load models configuration: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
