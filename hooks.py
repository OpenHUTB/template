from datetime import datetime
import shutil
import os
import re


# 列表项：缩进不超过 3 个空格的无序列表（-、*、+）或有序列表（数字加 .），且标记后紧跟内容
LIST_ITEM_RE = re.compile(r'^ {0,3}(?:[*+-]|(?P<number>\d+)\.)[ \t]+\S')
# 围栏代码块的开始或结束标记（``` 或 ~~~）
FENCE_RE = re.compile(r'^\s*(?P<fence>`{3,}|~{3,})')


# 动态获取页脚版权页面的年份
def on_config(config, **kwargs):
    year = str(datetime.now().year)
    config.copyright = config.copyright.format(year=year)


# 列表无需前置空行即可正确渲染（参考：https://github.com/OpenHUTB/mujoco_plugin/pull/76）
def on_page_markdown(markdown, **kwargs):
    """在紧跟段落的列表前补一个空行，使 mkdocs 的渲染效果与 GitHub 一致。

    Python-Markdown 要求列表前必须有空行，否则列表项会被并入上一段落显示在同一行；
    而 GitHub（CommonMark）允许列表直接打断段落。这里按 CommonMark 的规则处理：
    无序列表和从 1 开始的有序列表可以打断段落。围栏代码块中的内容保持不变。
    """
    lines = markdown.split('\n')
    result = []
    fence = None  # 当前所在围栏代码块的开始标记
    in_list = False  # 是否处于列表块中（从列表项开始直到下一个空行）
    previous = ''

    for line in lines:
        fence_match = FENCE_RE.match(line)
        if fence is not None:
            # 结束标记需与开始标记字符相同、长度不小于开始标记，且后面没有其他内容
            if (fence_match
                    and fence_match.group('fence')[0] == fence[0]
                    and len(fence_match.group('fence')) >= len(fence)
                    and not line[fence_match.end():].strip()):
                fence = None
        elif fence_match:
            fence = fence_match.group('fence')
        elif not line.strip():
            in_list = False
        else:
            item_match = LIST_ITEM_RE.match(line)
            if item_match:
                number = item_match.group('number')
                if (not in_list
                        and _is_paragraph_line(previous)
                        and (number is None or int(number) == 1)):
                    result.append('')
                in_list = True

        result.append(line)
        previous = line

    return '\n'.join(result)


def _is_paragraph_line(line):
    """判断一行是否为普通段落文本（排除空行、缩进内容、HTML、表格和引用）。"""
    return bool(line.strip()) and not line.startswith((' ', '\t', '<', '|', '>'))


# 在 MkDocs 构建开始前，将根目录下的 requirements.txt 拷贝到 docs 目录下，
# 确保文档站点能够引用到它（仅用于示例，实际使用时请根据需要修改 copied_file）。
# （名称必须为 on_pre_build）
def on_pre_build(**kwargs):
    copied_file = 'requirements.txt'
    # 源文件：项目根目录下的文件
    src_file = os.path.join(os.path.dirname(__file__), copied_file)
    # 目标文件：文档目录（相对于 docs_dir）
    dest_file = os.path.join(os.path.dirname(__file__), 'docs', copied_file)
    
    # 执行拷贝
    if os.path.exists(src_file):
        shutil.copy2(src_file, dest_file)
        print(f"Successfully copied {copied_file} to docs/{copied_file}")

 # 构建完成后，输出文档构建统计信息
def on_post_build(config, **kwargs):
    import os
    docs_path = config["docs_dir"]
    md_count = 0
    # 遍历统计所有md文档数量
    for root, dirs, files in os.walk(docs_path):
        for f in files:
            if f.endswith(".md"):
                md_count += 1
    print(f"✅ 文档网站构建完成！")
    print(f"📄 检测到Markdown文档总数：{md_count}") 