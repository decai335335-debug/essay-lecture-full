"""辅助脚本：分析申论讲义 MD 的结构，打印每个「讲」和题目的行号。

这个脚本只做分析和打印，不做拆分——拆分逻辑需要 Claude 根据材料-题目对应关系
（一对一 / 一对多共享 / 多对多独立）做判断，不能全自动完成。

用法：
    python split_lectures.py <源文件路径>
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def analyze(md_path: Path):
    text = md_path.read_text(encoding='utf-8')
    lines = text.split('\n')

    lectures = []  # (行号, 标题)
    questions = []  # (行号, 题目文本)
    subheaders = []  # (行号, 真题/试题 X)
    share_markers = []  # (行号, 同上材料的行)

    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if '## 第' in s and '讲' in s:
            lectures.append((i, s))
        if re.match(r'^###\s*(真题|试题)\s*\d*', s):
            subheaders.append((i, s))
        if s.startswith('**') and '根据' in s:
            questions.append((i, s))
        if re.search(r'同(试题|上)\s*\d*\s*材料', s):
            share_markers.append((i, s))

    print('=' * 60)
    print(f'源文件: {md_path}')
    print(f'总行数: {len(lines)}')
    print('=' * 60)

    print('\n【讲标题】')
    for ln, t in lectures:
        print(f'  行{ln}: {t}')

    print('\n【真题/试题块】')
    for ln, t in subheaders:
        print(f'  行{ln}: {t}')

    print('\n【题目】')
    for ln, t in questions:
        preview = t[:60] + '...' if len(t) > 60 else t
        print(f'  行{ln}: {preview}')

    print('\n【共享材料标记】')
    for ln, t in share_markers:
        print(f'  行{ln}: {t}')

    print('\n' + '=' * 60)
    print('下一步：Claude 应根据上述信息判断每个「讲」的对应关系类型。')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('用法: python split_lectures.py <源文件>')
        sys.exit(1)
    analyze(Path(sys.argv[1]))
