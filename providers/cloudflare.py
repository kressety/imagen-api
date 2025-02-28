import base64

import requests

from providers.provider import ImageProvider


# Cloudflare提供者类
class CloudflareProvider(ImageProvider):
    def __init__(self, account_id: str, api_token: str, model_name: str):
        """
        初始化Cloudflare提供者。

        Args:
            account_id (str): Cloudflare账户ID。
            api_token (str): Cloudflare API令牌。
            model_name (str): 模型名称，例如@cf/runwayml/stable-diffusion-v1-5-img2img。
        """
        self._account_id = account_id
        self._api_token = api_token
        self._model_name = model_name
        self._base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}"

    def text_to_image(self, prompt: str, **kwargs) -> bytes:
        """
        使用Cloudflare API从文本生成图像（同步调用）。

        Args:
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - negative_prompt (str)
                - height (int): 256-2048
                - width (int): 256-2048
                - num_steps (int): 最大20
                - guidance (float): 默认7.5
                - seed (int)

        Returns:
            bytes: 生成的PNG图像字节内容。
        """
        headers = {"Authorization": f"Bearer {self._api_token}"}
        payload = {"prompt": prompt, **kwargs}

        response = requests.post(self._base_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.content

    def image_to_image(self, input_image: bytes, prompt: str, **kwargs) -> bytes:
        """
        使用Cloudflare API从图像和文本生成新图像（同步调用）。

        Args:
            input_image (bytes): 输入图像的字节内容。
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - negative_prompt (str)
                - height (int): 256-2048
                - width (int): 256-2048
                - num_steps (int): 最大20
                - strength (float): 0-1，默认1
                - guidance (float): 默认7.5
                - seed (int)

        Returns:
            bytes: 生成的PNG图像字节内容。
        """
        headers = {"Authorization": f"Bearer {self._api_token}"}
        # 将输入图像转换为base64编码
        image_b64 = base64.b64encode(input_image).decode("utf-8")
        payload = {
            "prompt": prompt,
            "image_b64": image_b64,
            **kwargs
        }

        response = requests.post(self._base_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.content


# Cloudflare工厂类
class CloudflareFactory:
    def __init__(self, account_id: str, api_token: str):
        """
        初始化Cloudflare工厂。

        Args:
            account_id (str): Cloudflare账户ID。
            api_token (str): Cloudflare API令牌。
        """
        self._account_id = account_id
        self._api_token = api_token

    def create_provider(self, model_name: str) -> CloudflareProvider:
        """
        根据模型名创建Cloudflare提供者实例。

        Args:
            model_name (str): 模型名称，例如"@cf/runwayml/stable-diffusion-v1-5-img2img"。

        Returns:
            CloudflareProvider: 提供者实例。
        """
        return CloudflareProvider(self._account_id, self._api_token, model_name)
