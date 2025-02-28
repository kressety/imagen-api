import json
import os
from io import BytesIO
import azure.functions as func
from providers.aliyun import AliyunFactory
from providers.cloudflare import CloudflareFactory
from providers.modelscope import ModelScopeFactory

# 加载配置文件
CONFIG_PATH = "models_config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    MODELS_CONFIG = json.load(f)

# 从环境变量获取API密钥
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

# /generate 端点
def generate_image(req: func.HttpRequest) -> func.HttpResponse:
    """
    文生图和图文生图API端点。
    """
    try:
        # 获取 multipart/form-data 数据
        provider = req.form.get("provider")
        model = req.form.get("model")
        task = req.form.get("task")
        prompt = req.form.get("prompt")

        # 基本参数校验
        if not all([provider, model, task, prompt]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters: provider, model, task, prompt"}),
                status_code=400,
                mimetype="application/json"
            )

        if task not in ["text_to_image", "image_to_image"]:
            return func.HttpResponse(
                json.dumps({"error": "Invalid task type. Use 'text_to_image' or 'image_to_image'."}),
                status_code=400,
                mimetype="application/json"
            )

        # 校验配置
        is_valid, error_msg = validate_request(provider, model, task)
        if not is_valid:
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=400,
                mimetype="application/json"
            )

        # 获取图像文件（仅图文生图需要）
        input_image = None
        if task == "image_to_image":
            if "image" not in req.files:
                return func.HttpResponse(
                    json.dumps({"error": "Missing 'image' file for image-to-image task."}),
                    status_code=400,
                    mimetype="application/json"
                )
            image_file = req.files["image"]
            if not image_file or image_file.filename == "":
                return func.HttpResponse(
                    json.dumps({"error": "No selected file for 'image'."}),
                    status_code=400,
                    mimetype="application/json"
                )
            input_image = image_file.read()

        # 创建提供者实例
        if provider not in PROVIDER_FACTORIES:
            return func.HttpResponse(
                json.dumps({"error": f"Provider '{provider}' is not implemented."}),
                status_code=500,
                mimetype="application/json"
            )
        factory = PROVIDER_FACTORIES[provider]
        provider_instance = factory.create_provider(model)

        # 生成图像
        if task == "text_to_image":
            image_bytes = provider_instance.generate("text_to_image", prompt=prompt)
        else:
            image_bytes = provider_instance.generate("image_to_image", prompt=prompt, input_image=input_image)

        # 返回图像文件
        return func.HttpResponse(
            image_bytes,
            status_code=200,
            mimetype="image/png",
            headers={"Content-Disposition": "attachment; filename=generated_image.png"}
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Image generation failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

# /models 端点
def list_models(req: func.HttpRequest) -> func.HttpResponse:
    """
    返回models_config.json的内容，列出所有支持的供应商、模型及其任务能力。
    """
    try:
        return func.HttpResponse(
            json.dumps(MODELS_CONFIG),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Failed to load models configuration: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

# Azure Functions 应用的入口
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 注册HTTP触发器
app.register_functions([
    func.HttpTrigger(
        name="generate",
        route="generate",
        methods=["POST"],
        function=generate_image
    ),
    func.HttpTrigger(
        name="models",
        route="models",
        methods=["GET"],
        function=list_models
    )
])