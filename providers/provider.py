import time
from abc import ABC
from typing import Callable


class ImageProvider(ABC):
    """
    文生图和图文生图的提供者抽象类，支持同步和异步API。
    子类需实现具体提供者的API调用逻辑。
    """

    def generate(self, task: str, **params) -> bytes:
        """
        统一生成图像的接口，支持文生图和图文生图。

        Args:
            task (str): 任务类型，"text_to_image" 或 "image_to_image"。
            **params: 动态参数，包括：
                - prompt (str): 文本提示。
                - input_image (bytes, 可选): 输入图像的字节内容。
                - 其他提供者特定参数。

        Returns:
            bytes: 生成图像的字节内容。

        Raises:
            ValueError: 如果任务类型无效或缺少必要参数。
            NotImplementedError: 如果子类未实现对应方法。
        """
        if task == "text_to_image":
            prompt = params.pop("prompt", None)
            if not prompt:
                raise ValueError("Text-to-image task requires a 'prompt' parameter.")
            return self.text_to_image(prompt, **params)
        elif task == "image_to_image":
            prompt = params.pop("prompt", None)
            input_image = params.pop("input_image", None)
            if not prompt or not input_image:
                raise ValueError("Image-to-image task requires both 'prompt' and 'input_image' parameters.")
            return self.image_to_image(input_image, prompt, **params)
        else:
            raise ValueError(f"Unsupported task type: {task}. Use 'text_to_image' or 'image_to_image'.")

    def text_to_image(self, prompt: str, **kwargs) -> bytes:
        """
        从文本生成图像，默认抛出未实现错误。

        Args:
            prompt (str): 文本提示。
            **kwargs: 提供者特定参数。

        Returns:
            bytes: 生成图像的字节内容。

        Raises:
            NotImplementedError: 如果提供者不支持该功能。
        """
        raise NotImplementedError("This provider does not support text-to-image generation.")

    def image_to_image(self, input_image: bytes, prompt: str, **kwargs) -> bytes:
        """
        从图像和文本生成新图像，默认抛出未实现错误。

        Args:
            input_image (bytes): 输入图像的字节内容。
            prompt (str): 文本提示。
            **kwargs: 提供者特定参数。

        Returns:
            bytes: 生成图像的字节内容。

        Raises:
            NotImplementedError: 如果提供者不支持该功能。
        """
        raise NotImplementedError("This provider does not support image-to-image generation.")

    @staticmethod
    def _poll_for_result(status_func: Callable[[str], str],
                        result_func: Callable[[str], bytes],
                        task_id: str,
                        timeout: float = 60,
                        poll_interval: float = 5) -> bytes:
        """
        异步任务轮询辅助方法，检查任务状态并返回结果。

        Args:
            status_func (Callable[[str], str]): 获取任务状态的函数，接受task_id返回状态。
            result_func (Callable[[str], bytes]): 获取任务结果的函数，接受task_id返回图像内容。
            task_id (str): 任务ID。
            timeout (float): 最大等待时间（秒），默认60秒。
            poll_interval (float): 轮询间隔（秒），默认5秒。

        Returns:
            bytes: 生成图像的字节内容。

        Raises:
            TimeoutError: 如果任务超时。
            ValueError: 如果任务失败。
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = status_func(task_id)
            if status == "complete":
                return result_func(task_id)
            elif status == "failed":
                raise ValueError(f"Task {task_id} failed.")
            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds.")
