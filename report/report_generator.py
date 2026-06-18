import os
import platform
import traceback

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# Font paths keyed by platform.  CJK-capable fonts are listed first;
# fallback Western fonts last — only the former get wordWrap="CJK".
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

# ── Font discovery ──────────────────────────────────────────────
CHINESE_FONT = "Helvetica"
_CJK_CAPABLE = False  # only set True when a real CJK font is found

_font_paths = [
    *_FONT_PATHS.get(platform.system(), []),
    os.path.join(os.path.dirname(__file__), "..", "fonts", "SimHei.ttf"),
]

for fp in _font_paths:
    if os.path.isfile(fp):
        try:
            pdfmetrics.registerFont(TTFont("CJKFont", fp))
            CHINESE_FONT = "CJKFont"
            # Treat the font as CJK-capable unless it is DejaVu (Western fallback)
            _CJK_CAPABLE = "dejavu" not in fp.lower()
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

    # Only enable CJK word-wrap when we have a genuine CJK font;
    # using it with a Western font (e.g. DejaVu Sans) crashes reportlab.
    _word_wrap = "CJK" if _CJK_CAPABLE else "normal"

    try:
        styles = getSampleStyleSheet()

        custom_style = ParagraphStyle(
            "ChineseStyle",
            parent=styles["Normal"],
            fontName=CHINESE_FONT,
            fontSize=10,
            leading=15,
            wordWrap=_word_wrap,
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

        # Use explicit binary file handle — on Linux reportlab may
        # silently skip writing when only given a filename string.
        with open(filename, "wb") as fh:
            doc = SimpleDocTemplate(fh, pagesize=A4)
            doc.build(content)

    except Exception as exc:
        raise RuntimeError(f"PDF generation failed: {exc}\n{traceback.format_exc()}") from exc

    # Verify the file was actually written
    if not os.path.isfile(filename):
        try:
            files = os.listdir(dirname)
        except Exception:
            files = ["<cannot list>"]
        raise RuntimeError(f"PDF file not found after build: {filename}\nDirectory contents ({dirname}): {files}")

    print(f"报告已生成至: {filename}")
    return filename
