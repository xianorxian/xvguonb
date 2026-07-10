import os
import time
from rapidocr_onnxruntime import RapidOCR

# 初始化（轻量，秒开）
print("正在加载 OCR 模型...")
engine = RapidOCR()
print("模型加载完成！")


def parse_result(raw_result):
    """
    从 RapidOCR 返回中提取文字和置信度
    raw_result: [(坐标框, 文字, 置信度), ...]
    """
    parsed = []
    if not raw_result:
        return parsed

    for item in raw_result:
        text = item[1]
        confidence = item[2]

        # ===== 修复1：处理 confidence 可能是列表的情况 =====
        if isinstance(confidence, (list, tuple)):
            confidence = confidence[0] if confidence else 0.0
        # ==================================================

        parsed.append({
            "text": text,
            "confidence": round(float(confidence), 4)
        })

    return parsed


def recognize(image_path):
    """
    核心接口：识别单张图片
    传入: image_path (字符串)
    返回: {"success": bool, "message": str, "data": list}
    """
    if not os.path.exists(image_path):
        return {"success": False, "message": "文件不存在", "data": [], "elapsed": 0}

    try:
        result, elapse = engine(image_path)
        data = parse_result(result)

        # ===== 修复2：处理耗时可能是列表的情况 =====
        if isinstance(elapse, (list, tuple)):
            elapsed_value = sum(float(x) for x in elapse)
        else:
            elapsed_value = float(elapse)
        # ============================================

        return {
            "success": True,
            "message": f"识别成功，共 {len(data)} 行",
            "data": data,
            "elapsed": elapsed_value
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"识别失败: {str(e)}",
            "data": [],
            "elapsed": 0
        }


def run_ocr(image_path):

    print(f"正在识别: {image_path}")
    print("-" * 40)

    output = recognize(image_path)

    print("返回结果:")
    print(output)
    print("-" * 40)

    return output


# 测试代码：现在只需要一行
if __name__ == "__main__":
    run_ocr("../assets/t2.jpg")
