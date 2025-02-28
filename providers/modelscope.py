import json

import requests

from providers.provider import ImageProvider


# ModelScope提供者类
class ModelScopeProvider(ImageProvider):
    def __init__(self, api_token: str, model_name: str):
        """
        初始化ModelScope提供者。

        Args:
            api_token (str): ModelScope API令牌。
            model_name (str): 模型名称，例如"MAILAND/majicflus_v1"。
        """
        self._api_token = api_token
        self._model_name = model_name
        self._base_url = "https://api-inference.modelscope.cn/v1/images/generations"

    def text_to_image(self, prompt: str, **kwargs) -> bytes:
        """
        使用ModelScope API从文本生成图像（同步调用，返回URL后下载）。

        Args:
            prompt (str): 文本提示。
            **kwargs: 可选参数（假设支持，实际需参考API文档）。

        Returns:
            bytes: 生成图像的字节内容。
        """
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            **kwargs  # 可扩展支持其他参数，如width、height等（需API支持）
        }

        # 发送请求生成图像
        response = requests.post(
            self._base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers
        )
        response.raise_for_status()

        # 解析返回的图像URL并下载
        response_data = response.json()
        image_url = response_data["images"][0]["url"]
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        return image_response.content


# ModelScope工厂类
class ModelScopeFactory:
    def __init__(self, api_token: str):
        """
        初始化ModelScope工厂。

        Args:
            api_token (str): ModelScope API令牌。
        """
        self._api_token = api_token

    def create_provider(self, model_name: str) -> ModelScopeProvider:
        """
        根据模型名创建ModelScope提供者实例。

        Args:
            model_name (str): 模型名称，例如"MAILAND/majicflus_v1"。

        Returns:
            ModelScopeProvider: 提供者实例。
        """
        return ModelScopeProvider(self._api_token, model_name)
