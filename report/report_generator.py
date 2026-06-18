import os
import platform
import traceback

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

_FONT_PATHS = {
    "Windows": ["C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc"],
    "Darwin": [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}

CHINESE_FONT = "Helvetica"
_font_paths = [
    *_FONT_PATHS.get(platform.system(), []),
    os.path.join(os.path.dirname(__file__), "..", "fonts", "SimHei.ttf"),
]

for fp in _font_paths:
    if os.path.isfile(fp):
        try:
            pdfmetrics.registerFont(TTFont("CJKFont", fp))
            CHINESE_FONT = "CJKFont"
            break
        except Exception:
            continue

if CHINESE_FONT == "Helvetica":
    print("警告：未找到中文字体文件，PDF中文可能乱码")


def generate_pdf(data, filename="outputs/reports/interview_report.pdf"):
    """Generate a PDF report. Returns the absolute path to the created file.

    Raises RuntimeError if PDF generation fails.
    """
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)

    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()

        custom_style = ParagraphStyle(
            "ChineseStyle",
            parent=styles["Normal"],
            fontName=CHINESE_FONT,
            fontSize=10,
            leading=15,
            wordWrap="CJK" if CHINESE_FONT != "Helvetica" else "normal",
        )

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontName=CHINESE_FONT,
            fontSize=18,
            alignment=1,
            spaceAfter=20,
        )

        content = []
        content.append(Paragraph("AI 面试评估报告", title_style))
        content.append(Spacer(1, 12))

        for i, row in enumerate(data):
            text = (
                f"<b>问题 {i + 1}:</b> {row['question']}<br/>"
                f"<b>回答:</b> {row['answer']}<br/>"
                f"<b>AI 评分:</b><br/>{row['score']}<p/>"
            )
            content.append(Paragraph(text, custom_style))
            content.append(Spacer(1, 10))
            content.append(Paragraph("-" * 80, custom_style))

        doc.build(content)

    except Exception as exc:
        raise RuntimeError(
            f"PDF generation failed: {exc}\n{traceback.format_exc()}"
        ) from exc

    # Verify the file was actually written
    if not os.path.isfile(filename):
        # List directory to help debug
        try:
            files = os.listdir(dirname)
        except Exception:
            files = ["<cannot list>"]
        raise RuntimeError(
            f"PDF file not found after build: {filename}\n"
            f"Directory contents ({dirname}): {files}"
        )

    print(f"报告已生成至: {filename}")
    return filename
