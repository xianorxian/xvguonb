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

    # 兼容中文路径读取图片
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


def analyze_image_type(image):
    """
    自动分析图片类型。

    返回：
        dark_ui:
            深色游戏界面、深色软件界面、黑底截图

        clean_screen:
            普通网页截图、手机截图、地图、软件界面

        document:
            拍照试卷、纸质文档、手写笔记
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    white_ratio = np.mean(gray > 235)
    dark_ratio = np.mean(gray < 50)
    gray_mean = np.mean(gray)
    gray_std = np.std(gray)

    edges = cv2.Canny(gray, 80, 160)
    edge_ratio = np.mean(edges > 0)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation_mean = np.mean(hsv[:, :, 1])

    print("图片特征分析：")
    print(f"白色区域比例：{white_ratio:.3f}")
    print(f"黑色区域比例：{dark_ratio:.3f}")
    print(f"平均亮度：{gray_mean:.2f}")
    print(f"亮度标准差：{gray_std:.2f}")
    print(f"边缘比例：{edge_ratio:.3f}")
    print(f"平均饱和度：{saturation_mean:.2f}")

    # 深色游戏界面 / 黑底 UI
    if dark_ratio > 0.45:
        return "dark_ui"

    if gray_mean < 85 and dark_ratio > 0.30:
        return "dark_ui"

    # 彩色界面、地图、游戏、软件 UI
    if saturation_mean > 35 and gray_std > 40:
        return "clean_screen"

    # 大面积白底截图，例如网页、GitHub、搜索页面
    if white_ratio > 0.45 and dark_ratio < 0.30:
        return "clean_screen"

    # 边缘特别多的复杂界面，不适合文档增强
    if edge_ratio > 0.16 and gray_std > 55:
        return "clean_screen"

    # 其他情况默认按文档处理
    return "document"


def preprocess_dark_ui(image):
    """
    深色游戏界面 / 深色 UI 的预处理。

    这类图片不能强行洗白，否则会变成黑白漫画效果。
    这里输出灰度增强图，保证保存的是处理后的图片。
    """

    # 转灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 轻微去噪
    denoised = cv2.bilateralFilter(gray, 3, 25, 25)

    # 轻微锐化
    blur = cv2.GaussianBlur(denoised, (3, 3), 0)

    sharpened = cv2.addWeighted(
        denoised,
        1.25,
        blur,
        -0.25,
        0
    )

    # 轻微增强对比度
    final_image = cv2.convertScaleAbs(
        sharpened,
        alpha=1.10,
        beta=0
    )

    return final_image


def preprocess_clean_screen(image):
    """
    普通截图 / 网页 / 地图 / 软件界面的预处理。

    这类图片本来比较清楚，所以只做灰度化、轻微去噪、轻微锐化。
    """

    # 转灰度，保证结果明显是处理后的图片
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 轻微去噪
    denoised = cv2.bilateralFilter(gray, 3, 25, 25)

    # 轻微锐化
    blur = cv2.GaussianBlur(denoised, (3, 3), 0)

    sharpened = cv2.addWeighted(
        denoised,
        1.20,
        blur,
        -0.20,
        0
    )

    # 轻微提亮
    final_image = cv2.convertScaleAbs(
        sharpened,
        alpha=1.08,
        beta=3
    )

    return final_image


def preprocess_document(image):
    """
    拍照文档 / 试卷 / 手写笔记的预处理。

    目标：
    1. 减弱纸张阴影
    2. 保留文字
    3. 不要过度洗白
    4. 适当加深文字
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 轻微去噪，保护文字边缘
    denoised = cv2.bilateralFilter(gray, 5, 35, 35)

    # 背景估计
    background = cv2.GaussianBlur(denoised, (61, 61), 0)

    # 背景校正
    corrected = cv2.divide(
        denoised,
        background,
        scale=245
    )

    # 和原灰度图混合，避免处理过度
    corrected = cv2.addWeighted(
        corrected,
        0.65,
        gray,
        0.35,
        0
    )

    # 局部对比度增强
    clahe = cv2.createCLAHE(
        clipLimit=1.0,
        tileGridSize=(12, 12)
    )

    enhanced = clahe.apply(corrected)

    # 温和锐化
    blur = cv2.GaussianBlur(enhanced, (3, 3), 0)

    sharpened = cv2.addWeighted(
        enhanced,
        1.12,
        blur,
        -0.12,
        0
    )

    final_image = sharpened.copy()

    # 只加深较暗文字区域
    text_mask = final_image < 145

    final_image[text_mask] = np.clip(
        final_image[text_mask] * 0.82,
        0,
        255
    ).astype(np.uint8)

    # 轻微提亮背景
    final_image = cv2.convertScaleAbs(
        final_image,
        alpha=1.00,
        beta=2
    )

    return final_image


def import_and_preprocess_image(input_path, output_folder="processed_images", max_width=1600):
    """
    图片导入与预处理总函数。

    功能：
    1. 检查图片路径是否存在
    2. 检查图片格式是否支持
    3. 自动新建保存文件夹
    4. 读取图片，兼容中文路径
    5. 调整图片大小
    6. 自动判断图片类型
    7. 根据图片类型选择不同预处理方案
    8. 保存处理后的图片
    9. 返回处理后的图片路径
    """

    # 1. 创建保存文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 2. 读取图片
    image = read_image(input_path)

    # 3. 获取原图信息
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

    # 4. 缩放图片
    image = resize_image(image, max_width=max_width)

    new_height, new_width = image.shape[:2]

    if new_width != width:
        print(f"图片已缩放为：{new_width} × {new_height}")
    else:
        print("图片尺寸未超过限制，不需要缩放")

    # 5. 自动判断图片类型
    image_type = analyze_image_type(image)

    print(f"检测结果：{image_type}")

    # 6. 根据类型选择不同预处理方案
    if image_type == "dark_ui":
        print("采用方案：深色界面灰度轻增强")
        final_image = preprocess_dark_ui(image)

    elif image_type == "clean_screen":
        print("采用方案：截图灰度轻增强")
        final_image = preprocess_clean_screen(image)

    else:
        print("采用方案：文档温和增强")
        final_image = preprocess_document(image)

    # 7. 生成文件名
    timestamp = int(time.time() * 1000)

    file_name = f"preprocessed_{image_type}_{timestamp}.png"

    processed_image_path = os.path.join(output_folder, file_name)

    print("即将保存的处理后图片信息：")
    print(f"处理后图片尺寸：{final_image.shape}")
    print(f"处理后图片类型：{final_image.dtype}")

    # 8. 保存处理后的图片
    save_image(processed_image_path, final_image)

    # 9. 转成绝对路径，方便其他模块调用
    processed_image_path = os.path.abspath(processed_image_path)

    print("图片预处理完成")
    print(f"处理后的图片已保存到：{processed_image_path}")

    return processed_image_path


def preprocess_image(input_path, output_dir="processed_images"):
    """
    兼容旧代码。

    如果之前别的文件调用的是 preprocess_image，
    这里会自动调用 import_and_preprocess_image。
    """

    return import_and_preprocess_image(
        input_path=input_path,
        output_folder=output_dir
    )


if __name__ == "__main__":
    """
    单独运行 processed.py 时，用于测试。
    """

    test_path = input("请输入图片路径：").strip()

    try:
        result_path = import_and_preprocess_image(test_path)

        print("最终处理结果路径：")
        print(result_path)

    except Exception as e:
        print("图片处理失败：")
        print(e)
