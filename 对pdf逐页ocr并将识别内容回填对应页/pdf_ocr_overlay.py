import os
import sys
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import fitz  # PyMuPDF


# 检查输入的PDF路径
def check_pdf_path(pdf_path):
    # 去除单引号和双引号
    pdf_path = pdf_path.strip("'\"")

    # 验证文件是否存在
    if not os.path.exists(pdf_path):
        print(f"文件 {pdf_path} 不存在.")
        sys.exit(1)

    # 验证文件是否为PDF
    if not pdf_path.lower().endswith(".pdf"):
        print(f"文件 {pdf_path} 不是一个PDF文件.")
        sys.exit(1)

    return pdf_path


# 生成包含正常文本的单页PDF
def create_transparent_text_pdf(text, page_width, page_height, rotation):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # 设置字体、颜色和位置
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.red)

    text_height = page_height - 20

    # 根据页面旋转角度调整文本方向
    if rotation == 90:
        c.rotate(90)
        c.translate(0, -page_width)  # 翻转坐标系
        text_height = page_width - 20   # 调整文本起始
    elif rotation == 180:
        c.rotate(180)
        c.translate(-page_width, -page_height)
    elif rotation == 270:
        c.rotate(270)
        c.translate(-page_height, 0)
        text_height = page_width - 20   # 调整文本起始

    # 分段添加OCR文本
    text_lines = text.split('\n')

    for line in text_lines:
        if text_height < 40:  # 避免绘制到页面底部外
            break
        c.drawString(20, text_height, line)
        text_height -= 12  # 每行向下偏移

    c.save()

    # 返回PDF内容
    packet.seek(0)
    return packet


# 提取OCR文本并处理
def extract_ocr_text(images, page_num):
    # 执行OCR
    ocr_text = pytesseract.image_to_string(images[page_num])
    # 替换不存在的特殊字符“|”为大写“I”
    ocr_text = ocr_text.replace('|', 'I')
    print(f"OCR识别结果 - 第{page_num+1}页:\n{ocr_text}")
    print("=================================")
    return ocr_text


# 获取页面的大小和旋转信息
def get_page_rotation_and_size(page):
    page_width = float(page.mediabox.width)
    page_height = float(page.mediabox.height)
    rotation = page.get('/Rotate', 0)  # 获取页面旋转角度，默认为0
    return page_width, page_height, rotation


# 生成PDF输出路径
def generate_output_path(pdf_path, mode_desc, total_pages):
    pdf_dir = os.path.dirname(pdf_path)
    pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
    return os.path.join(pdf_dir, f"{pdf_name}_添加{mode_desc}_共{total_pages}页.pdf")


# 添加可以正常看到和打印的备注
def process_normal_mode(pdf_path, images):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    # 逐页处理PDF
    for i, page in enumerate(reader.pages):
        page_width, page_height, rotation = get_page_rotation_and_size(page)
        ocr_text = extract_ocr_text(images, i)

        # 创建包含OCR透明文本的PDF页面
        transparent_text_pdf = create_transparent_text_pdf(ocr_text, page_width, page_height, rotation)

        # 加载透明PDF并合并到当前页面
        transparent_pdf_page = PdfReader(transparent_text_pdf).pages[0]
        page.merge_page(transparent_pdf_page)

        # 添加合并后的页面到writer
        writer.add_page(page)

    output_pdf_path = generate_output_path(pdf_path, "正常备注", total_pages)
    with open(output_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"处理完成，生成文件: {output_pdf_path}")


# 添加不能被看到和打印的备注
def process_hidden_mode(pdf_path, images):
    pdf_document = fitz.open(pdf_path)
    total_pages = len(pdf_document)

    # 逐页处理PDF
    for i in range(total_pages):
        page = pdf_document.load_page(i)
        ocr_text = extract_ocr_text(images, i)

        # 在页面上添加不可见的OCR文本层
        text_lines = ocr_text.split('\n')
        for line_num, line in enumerate(text_lines):
            page.insert_text(
                (20, 40 + line_num * 6),  # 设置文本的起始坐标 (x, y)
                line,  # 要插入的文本
                fontsize=5,  # 字体大小
                color=(1, 1, 1),  # 配置成 color=(0, 0, 0, 0) 没有用
                overlay=True,  # 确保文本不会覆盖原有内容
                fill_opacity=0,  # 文本完全透明，不会显现或打印
                # 不要加render_mode，会使 Adobe Acrobat 报错 “无法处理页面，因为“页面捕捉”识别服务发生错误。(6)”
                # render_mode=3  # 透明度设置
            )

    output_pdf_path = generate_output_path(pdf_path, "隐藏备注", total_pages)
    pdf_document.save(output_pdf_path)
    pdf_document.close()

    print(f"处理完成，生成文件: {output_pdf_path}")


# 主程序入口，处理用户选择
if __name__ == "__main__":
    # 手动指定 Tesseract-OCR 的安装路径
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # 获取PDF路径
    print("功能：对pdf逐页ocr，作为隐藏信息回填对应页")
    pdf_path = input("请输入需要处理的PDF文件路径：")
    pdf_path = check_pdf_path(pdf_path)

    # 选择处理模式
    print("请选择处理模式：")
    print("1: 隐藏备注（不可见文本）")
    print("2: 正常备注（可见文本）")
    choice = input("请输入选择（1或2，直接回车为1）：")

    # 将PDF页面转换为图像
    images = convert_from_path(pdf_path)

    # 根据用户选择进行处理
    if choice in ["1", ""]:
        process_hidden_mode(pdf_path, images)
    elif choice == '2':
        process_normal_mode(pdf_path, images)
    else:
        print("无效的选择")
