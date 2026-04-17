"""批量把目录下的 Markdown 转成 PDF，用 Playwright 渲染，支持中文。

用法：
    python md_to_pdf.py <输入目录> <输出目录>
"""
import sys
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
    font-family: "Microsoft YaHei", "SimHei", "PingFang SC", "Source Han Sans SC", sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #222;
  }}
  h1, h2, h3 {{ color: #1a1a1a; }}
  h1 {{ font-size: 15pt; border-bottom: 1.5px solid #333; padding-bottom: 4px; }}
  h2 {{ font-size: 12.5pt; margin-top: 1em; }}
  h3 {{ font-size: 11pt; }}
  p {{ text-indent: 2em; margin: 0.35em 0; }}
  hr {{ border: none; border-top: 1px dashed #888; margin: 1em 0; }}
  strong {{ color: #b00; }}
  .question {{ background: #fff8e1; padding: 8px 12px; border-left: 3px solid #f5a623; margin: 0.8em 0; }}
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


def _wrap_annotations(html: str) -> str:
    """把中文全角方括号【…】包成 <span class="annot">【…】</span>，用于标注版渲染。"""
    import re
    return re.sub(r'【([^】]+)】', r'<span class="annot">【\1】</span>', html)


def md_to_html(md_text: str) -> str:
    """极简 Markdown → HTML。只处理申论讲义需要的标签：标题、分隔符、粗体、段落。"""
    try:
        import markdown
        html = markdown.markdown(md_text, extensions=['extra'])
        return _wrap_annotations(html)
    except ImportError:
        # 最小 fallback
        html_lines = []
        for line in md_text.split('\n'):
            s = line.strip()
            if not s:
                html_lines.append('')
            elif s.startswith('### '):
                html_lines.append(f'<h3>{s[4:]}</h3>')
            elif s.startswith('## '):
                html_lines.append(f'<h2>{s[3:]}</h2>')
            elif s.startswith('# '):
                html_lines.append(f'<h1>{s[2:]}</h1>')
            elif s.startswith('---'):
                html_lines.append('<hr>')
            else:
                # 处理 **加粗**
                import re
                s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
                html_lines.append(f'<p>{s}</p>')
        return _wrap_annotations('\n'.join(html_lines))


async def render_one(html: str, pdf_path: Path):
    from playwright.async_api import async_playwright
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


async def main(in_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(in_dir.glob('*.md'))
    if not md_files:
        print(f'未在 {in_dir} 找到 .md 文件')
        return

    for md in md_files:
        text = md.read_text(encoding='utf-8')
        body = md_to_html(text)
        html = HTML_TEMPLATE.format(title=md.stem, body=body)
        pdf_path = out_dir / f'{md.stem}.pdf'
        print(f'渲染: {md.name} -> {pdf_path.name}')
        await render_one(html, pdf_path)
    print(f'完成：{len(md_files)} 个 PDF 已输出到 {out_dir}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('用法: python md_to_pdf.py <输入目录> <输出目录>')
        sys.exit(1)
    asyncio.run(main(Path(sys.argv[1]), Path(sys.argv[2])))
