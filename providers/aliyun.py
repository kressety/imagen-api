from http import HTTPStatus

import requests
from dashscope import ImageSynthesis

from providers.provider import ImageProvider


# Aliyun提供者类
class AliyunProvider(ImageProvider):
    def __init__(self, api_key: str, model_name: str):
        """
        初始化Aliyun提供者。

        Args:
            api_key (str): DashScope API密钥。
            model_name (str): 模型名称，例如"wanx_v1"。
        """
        self._api_key = api_key
        self._model_name = model_name

    def text_to_image(self, prompt: str, **kwargs) -> bytes:
        """
        使用Aliyun DashScope API从文本生成图像（同步调用，返回URL后下载）。

        Args:
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - n (int): 生成图像数量，默认1
                - style (str): 风格，例如"<watercolor>"
                - size (str): 图像尺寸，例如"1024*1024"

        Returns:
            bytes: 生成图像的字节内容。
        """
        rsp = ImageSynthesis.call(
            api_key=self._api_key,
            model=self._model_name,
            prompt=prompt,
            n=kwargs.get("n", 1),
            style=kwargs.get("style", "<auto>"),
            size=kwargs.get("size", "1024*1024")
        )

        if rsp.status_code == HTTPStatus.OK:
            # 只返回第一张图像的字节内容
            result = rsp.output.results[0]
            image_url = result.url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return image_response.content
        else:
            raise ValueError(
                f"Text-to-image failed, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}"
            )

    def image_to_image(self, input_image: bytes, prompt: str, **kwargs) -> bytes:
        """
        使用Aliyun DashScope API从图像和文本生成新图像（同步调用，返回URL后下载）。

        Args:
            input_image (bytes): 输入图像的字节内容。
            prompt (str): 文本提示。
            **kwargs: 可选参数，支持：
                - n (int): 生成图像数量，默认1
                - style (str): 风格，例如"<auto>"
                - size (str): 图像尺寸，例如"1024*1024"
                - ref_mode (str): 参考模式，默认"repaint"
                - ref_strength (float): 参考强度，默认1.0

        Returns:
            bytes: 生成图像的字节内容。

        Note:
            输入图像通过临时文件上传，假设DashScope支持本地路径方式。
        """
        import tempfile
        import os

        # 将输入图像保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(input_image)
            temp_file_path = temp_file.name

        try:
            rsp = ImageSynthesis.call(
                api_key=self._api_key,
                model=self._model_name,
                prompt=prompt,
                n=kwargs.get("n", 1),
                style=kwargs.get("style", "<auto>"),
                size=kwargs.get("size", "1024*1024"),
                ref_mode=kwargs.get("ref_mode", "repaint"),
                ref_strength=kwargs.get("ref_strength", 1.0),
                sketch_image_url=temp_file_path  # 使用本地文件路径
            )

            if rsp.status_code == HTTPStatus.OK:
                # 只返回第一张图像的字节内容
                result = rsp.output.results[0]
                image_url = result.url
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                return image_response.content
            else:
                raise ValueError(
                    f"Image-to-image failed, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}"
                )
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)


# Aliyun工厂类
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
