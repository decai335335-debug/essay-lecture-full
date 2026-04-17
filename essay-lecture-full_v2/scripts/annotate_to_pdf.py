"""把标注版 MD（含 **加粗** 和 【括号注解】）渲染为带灰底楷体样式的中文 PDF。

用法：
    python annotate_to_pdf.py <输入目录或文件> <输出PDF目录>
"""
import sys
import re
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{
    font-family: "Microsoft YaHei", "SimHei", "PingFang SC", sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #222;
  }}
  h1 {{ font-size: 15pt; border-bottom: 1.5px solid #333; padding-bottom: 4px; }}
  h2 {{ font-size: 12.5pt; margin-top: 1em; }}
  h3 {{ font-size: 11pt; }}
  p {{ text-indent: 2em; margin: 0.4em 0; }}
  hr {{ border: none; border-top: 1px dashed #888; margin: 1em 0; }}
  strong {{ color: #b00; font-weight: bold; }}
  .annot {{
    font-family: "KaiTi", "楷体", "STKaiti", monospace;
    font-size: 9pt;
    background: #f2f2f2;
    color: #666;
    padding: 1px 4px;
    border-radius: 3px;
    margin: 0 2px;
    font-weight: normal;
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def wrap_annotations(html: str) -> str:
    """【…】 → <span class="annot">【…】</span>"""
    return re.sub(r'【([^】]+)】', r'<span class="annot">【\1】</span>', html)


def md_to_html(md_text: str) -> str:
    try:
        import markdown
        html = markdown.markdown(md_text, extensions=['extra'])
    except ImportError:
        lines = []
        for line in md_text.split('\n'):
            s = line.strip()
            if not s:
                lines.append('')
            elif s.startswith('### '):
                lines.append(f'<h3>{s[4:]}</h3>')
            elif s.startswith('## '):
                lines.append(f'<h2>{s[3:]}</h2>')
            elif s.startswith('# '):
                lines.append(f'<h1>{s[2:]}</h1>')
            elif s.startswith('---'):
                lines.append('<hr>')
            else:
                s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
                lines.append(f'<p>{s}</p>')
        html = '\n'.join(lines)
    return wrap_annotations(html)


async def render_one(md_path: Path, pdf_path: Path):
    from playwright.async_api import async_playwright
    body = md_to_html(md_path.read_text(encoding='utf-8'))
    html = HTML_TEMPLATE.format(title=md_path.stem, body=body)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until='load')
        await page.pdf(
            path=str(pdf_path),
            format='A4',
            margin={'top': '20mm', 'bottom': '20mm', 'left': '18mm', 'right': '18mm'},
            print_background=True,
        )
        await browser.close()


async def main(src: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    md_files = [src] if src.is_file() else sorted(src.glob('*.md'))
    if not md_files:
        print(f'未在 {src} 找到 .md 文件')
        return
    for md in md_files:
        pdf = out_dir / f'{md.stem}.pdf'
        print(f'渲染: {md.name} -> {pdf.name}')
        await render_one(md, pdf)
    print(f'完成：{len(md_files)} 个 PDF 已输出到 {out_dir}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('用法: python annotate_to_pdf.py <输入目录或文件> <输出PDF目录>')
        sys.exit(1)
    asyncio.run(main(Path(sys.argv[1]), Path(sys.argv[2])))
