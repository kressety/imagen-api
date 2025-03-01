import os
import tempfile
from http import HTTPStatus

import requests
from dashscope import ImageSynthesis

from providers.provider import ImageProvider


class AliyunProvider(ImageProvider):
    def __init__(self, api_key: str, model_name: str):
        """
        初始化Aliyun提供者。

        Args:
            api_key (str): DashScope API密钥。
            model_name (str): 模型名称，例如"wanx_v1" 或 "stable-diffusion-xl"。
        """
        self._api_key = api_key
        self._model_name = model_name

    def _is_stable_diffusion_model(self):
        """
        检查模型是否为Stable Diffusion系列。

        Returns:
            bool: True 如果模型名以"stable-diffusion"开头。
        """
        return self._model_name.startswith("stable-diffusion")

    def text_to_image(self, prompt: str, **kwargs) -> bytes:
        """
        使用Aliyun DashScope API从文本生成图像（同步调用，返回URL后下载）。

        Args:
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - n (int): 生成图像数量，默认1
                - style (str): 风格，例如"<watercolor>"（非SD模型）
                - size (str): 图像尺寸，例如"1024*1024"
                - negative_prompt (str): 负提示词（SD模型支持）

        Returns:
            bytes: 生成图像的字节内容。
        """
        # 根据模型类型调整参数
        base_params = {
            "api_key": self._api_key,
            "model": self._model_name,
            "prompt": prompt,
            "n": kwargs.get("n", 1),
            "size": kwargs.get("size", "1024*1024")
        }

        if self._is_stable_diffusion_model():
            # Stable Diffusion 模型特有参数
            params = {
                **base_params,
                "negative_prompt": kwargs.get("negative_prompt", "")
            }
        else:
            # 非Stable Diffusion 模型（如wanx_v1）
            params = {
                **base_params,
                "style": kwargs.get("style", "<auto>")
            }

        rsp = ImageSynthesis.call(**params)

        if rsp.status_code != HTTPStatus.OK:
            raise ValueError(
                f"Text-to-image failed, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}"
            )

        # 检查返回结果，确保有results字段
        if not hasattr(rsp.output, "results") or not rsp.output.results:
            raise ValueError(f"Unexpected response format for model '{self._model_name}': no 'results' found.")

        # 获取第一张图像
        result = rsp.output.results[0]
        image_url = result.url
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        return image_response.content

    def image_to_image(self, input_image: bytes, prompt: str, **kwargs) -> bytes:
        """
        使用Aliyun DashScope API从图像和文本生成新图像（同步调用，返回URL后下载）。

        Args:
            input_image (bytes): 输入图像的字节内容。
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - n (int): 生成图像数量，默认1
                - style (str): 风格，例如"<auto>"（非SD模型）
                - size (str): 图像尺寸，例如"1024*1024"
                - ref_mode (str): 参考模式，默认"repaint"（非SD模型）
                - ref_strength (float): 参考强度，默认1.0（非SD模型）
                - negative_prompt (str): 负提示词（SD模型支持）

        Returns:
            bytes: 生成图像的字节内容。
        """
        # 将输入图像保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(input_image)
            temp_file_path = temp_file.name

        try:
            # 根据模型类型调整参数
            base_params = {
                "api_key": self._api_key,
                "model": self._model_name,
                "prompt": prompt,
                "n": kwargs.get("n", 1),
                "size": kwargs.get("size", "1024*1024"),
                "sketch_image_url": temp_file_path
            }

            if self._is_stable_diffusion_model():
                # Stable Diffusion 模型特有参数
                params = {
                    **base_params,
                    "negative_prompt": kwargs.get("negative_prompt", "")
                }
            else:
                # 非Stable Diffusion 模型（如wanx_v1）
                params = {
                    **base_params,
                    "style": kwargs.get("style", "<auto>"),
                    "ref_mode": kwargs.get("ref_mode", "repaint"),
                    "ref_strength": kwargs.get("ref_strength", 1.0)
                }

            rsp = ImageSynthesis.call(**params)

            if rsp.status_code != HTTPStatus.OK:
                raise ValueError(
                    f"Image-to-image failed, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}"
                )

            # 检查返回结果，确保有results字段
            if not hasattr(rsp.output, "results") or not rsp.output.results:
                raise ValueError(f"Unexpected response format for model '{self._model_name}': no 'results' found.")

            # 获取第一张图像
            result = rsp.output.results[0]
            image_url = result.url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return image_response.content
        finally:
            os.unlink(temp_file_path)


class AliyunFactory:
    def __init__(self, api_key: str):
        """
        初始化Aliyun工厂。

        Args:
            api_key (str): DashScope API密钥。
        """
        self._api_key = api_key

    def create_provider(self, model_name: str) -> AliyunProvider:
        """
        根据模型名创建Aliyun提供者实例。

        Args:
            model_name (str): 模型名称，例如"wanx_v1"。

        Returns:
            AliyunProvider: 提供者实例。
        """
        return AliyunProvider(self._api_key, model_name)
