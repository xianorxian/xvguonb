import os
import time
import cv2
import numpy as np


# 支持的图片格式
SUPPORTED_IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def is_supported_image(file_path):
    """
    判断图片格式是否支持
    """
    return file_path.lower().endswith(SUPPORTED_IMAGE_TYPES)


def read_image(file_path):
    """
    读取本地图片，兼容中文路径
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError("图片文件不存在，请检查路径是否正确")

    if not is_supported_image(file_path):
        raise ValueError("图片格式不支持，请选择 jpg、jpeg、png、bmp 或 webp 图片")

    # 兼容中文路径读取
    image_data = np.fromfile(file_path, dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("图片读取失败，可能是图片损坏或格式异常")

    return image


def resize_image(image, max_width=1600):
    """
    如果图片宽度超过 max_width，则按比例缩小
    """

    height, width = image.shape[:2]

    if width <= max_width:
        return image

    scale = max_width / width
    new_width = max_width
    new_height = int(height * scale)

    resized_image = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    return resized_image


def save_image(file_path, image):
    """
    保存图片，兼容中文路径
    """

    ext = os.path.splitext(file_path)[1]

    if ext == "":
        ext = ".png"
        file_path += ext

    success, encoded_image = cv2.imencode(ext, image)

    if not success:
        raise ValueError("图片保存失败")

    encoded_image.tofile(file_path)


def get_image_info(file_path):
    """
    获取图片基本信息
    """

    image = read_image(file_path)

    height, width = image.shape[:2]

    if len(image.shape) == 3:
        channels = image.shape[2]
    else:
        channels = 1

    return {
        "path": file_path,
        "width": width,
        "height": height,
        "channels": channels
    }


def is_clean_screenshot(gray, image=None):
    """
    判断图片是否更像“截图 / 网页 / 软件界面 / 地图 / 游戏界面”。

    返回 True：
        采用轻度预处理，尽量保留原图信息。

    返回 False：
        采用文档增强预处理，适合拍照纸张、手写笔记、试卷。
    """

    # 白色区域比例
    white_ratio = np.mean(gray > 235)

    # 黑色区域比例
    dark_ratio = np.mean(gray < 50)

    # 灰度标准差，反映整体明暗变化
    gray_std = np.std(gray)

    # 边缘密度
    edges = cv2.Canny(gray, 80, 160)
    edge_ratio = np.mean(edges > 0)

    # 如果是彩色图，计算平均饱和度
    saturation_mean = 0

    if image is not None and len(image.shape) == 3:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation_mean = np.mean(hsv[:, :, 1])

    # 情况 1：大量白底，通常是网页、截图、文档截图
    if white_ratio > 0.45 and dark_ratio < 0.25:
        return True

    # 情况 2：图片本身很干净，明暗变化不剧烈
    if white_ratio > 0.35 and gray_std < 70:
        return True

    # 情况 3：彩色截图、地图、游戏界面一般饱和度较高
    if saturation_mean > 35 and gray_std > 45:
        return True

    # 情况 4：黑底或深色界面截图
    if dark_ratio > 0.35 and gray_std > 50:
        return True

    # 情况 5：边缘很多的复杂界面，不适合强行文档增强
    if edge_ratio > 0.18 and gray_std > 55:
        return True

    return False


def import_and_preprocess_image(input_path, output_folder="processed_images", max_width=1600):
    """
    图片导入与预处理总函数

    功能：
    1. 检查图片路径是否存在
    2. 检查图片格式是否支持
    3. 自动新建保存文件夹
    4. 读取图片，兼容中文路径
    5. 调整图片大小
    6. 自动判断图片类型
    7. 截图/网页/地图/游戏界面：轻度处理
    8. 拍照文档/手写笔记/试卷：文档增强处理
    9. 保存处理后的图片
    10. 返回处理后的图片路径

    参数：
        input_path: 原始图片路径
        output_folder: 处理后图片保存文件夹，默认 processed_images
        max_width: 图片最大宽度，默认 1600

    返回：
        processed_image_path: 处理后的图片路径
    """

    # 1. 自动新建保存文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 2. 读取图片
    image = read_image(input_path)

    # 3. 获取图片基本信息
    height, width = image.shape[:2]

    if len(image.shape) == 3:
        channels = image.shape[2]
    else:
        channels = 1

    print("图片读取成功")
    print(f"原始图片路径：{input_path}")
    print(f"图片宽度：{width}")
    print(f"图片高度：{height}")
    print(f"图片通道数：{channels}")

    # 4. 调整图片大小
    image = resize_image(image, max_width=max_width)

    new_height, new_width = image.shape[:2]

    if new_width != width:
        print(f"图片已缩放为：{new_width} × {new_height}")
    else:
        print("图片尺寸未超过限制，不需要缩放")

    # 5. 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 6. 判断图片类型
    clean_screenshot = is_clean_screenshot(gray, image)

    if clean_screenshot:
        print("检测结果：图片较干净，采用轻度预处理")

        # =====================================================
        # 模式一：轻度处理
        # 适合：网页截图、软件界面、地图、游戏界面、手机截图
        # =====================================================

        # 轻微去噪
        denoised = cv2.bilateralFilter(gray, 3, 30, 30)

        # 轻微锐化
        blur = cv2.GaussianBlur(denoised, (3, 3), 0)

        sharpened = cv2.addWeighted(
            denoised,
            1.15,
            blur,
            -0.15,
            0
        )

        # 轻微提亮背景
        final_image = cv2.convertScaleAbs(
            sharpened,
            alpha=1.03,
            beta=3
        )

    else:
        print("检测结果：图片背景较复杂，采用文档增强预处理")

        # =====================================================
        # 模式二：文档增强处理
        # 适合：拍照纸张、手写笔记、试卷、背景有阴影的图片
        # =====================================================

        # 轻微去噪，保留文字边缘
        denoised = cv2.bilateralFilter(gray, 5, 45, 45)

        # 背景光照校正
        # 用大范围模糊估计背景，减少纸张阴影和底纹
        background = cv2.GaussianBlur(denoised, (41, 41), 0)

        corrected = cv2.divide(
            denoised,
            background,
            scale=255
        )

        # 局部对比度增强
        # clipLimit 不宜太大，否则容易把背景噪点放大
        clahe = cv2.createCLAHE(
            clipLimit=1.2,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(corrected)

        # 轻微锐化，让文字边缘更清楚
        blur = cv2.GaussianBlur(enhanced, (3, 3), 0)

        sharpened = cv2.addWeighted(
            enhanced,
            1.25,
            blur,
            -0.25,
            0
        )

        # 只加深真正偏暗的文字区域
        final_image = sharpened.copy()

        # 灰度值越小越黑
        # 小于 165 的区域一般是文字或线条
        text_mask = final_image < 165

        final_image[text_mask] = np.clip(
            final_image[text_mask] * 0.75,
            0,
            255
        ).astype(np.uint8)

        # 轻微提亮背景，防止底纹过重
        final_image = cv2.convertScaleAbs(
            final_image,
            alpha=1.02,
            beta=4
        )

    # 7. 生成处理后图片文件名
    file_name = f"preprocessed_{int(time.time())}.png"

    # 8. 拼接保存路径
    processed_image_path = os.path.join(output_folder, file_name)

    # 9. 保存图片
    save_image(processed_image_path, final_image)

    # 10. 转成绝对路径，方便 OCR 模块调用
    processed_image_path = os.path.abspath(processed_image_path)

    print("图片预处理完成")
    print(f"处理后的图片已保存到：{processed_image_path}")

    return processed_image_path


def preprocess_image(input_path, output_dir="processed_images"):
    """
    兼容旧代码的函数名。

    如果之前别的文件调用的是 preprocess_image，
    这里会自动转到 import_and_preprocess_image。
    """

    return import_and_preprocess_image(
        input_path=input_path,
        output_folder=output_dir
    )


if __name__ == "__main__":
    """
    单独运行 processed.py 时，用来测试图片预处理效果。
    """

    test_path = input("请输入图片路径：").strip()

    try:
        result_path = import_and_preprocess_image(test_path)

        print("最终处理结果路径：")
        print(result_path)

    except Exception as e:
        print("图片处理失败：")
        print(e)
