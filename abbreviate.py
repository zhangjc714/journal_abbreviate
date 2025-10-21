import os
import re
import argparse

"""
修改.bib文件：将期刊全称或会议全称改为缩写
"""

parser = argparse.ArgumentParser(description="将.bib文件中的期刊和会议名替换为缩写")
parser.add_argument("--file", type=str, default='', help="指定需要修改的.bib文件绝对路径")
args = parser.parse_args()

path = os.path.dirname(args.file)  # 工作路径
name = os.path.splitext(os.path.basename(args.file))[0]  # 不带后缀的.bib文件名
input_file  = args.file  # 修改前的.bib文件
output_file = f"{path}/{name}_abrv.bib"  # 修改后的.bib文件

# -------------------------
# 1. 定义归一化函数（模糊匹配）
# -------------------------
def normalize(text):
    """
    将名称标准化：
    - 忽略大小写
    - 忽略多余空格
    - 将 \& 转换为 &
    - 忽略句点、逗号、分号等轻微标点差异
    """
    text = text.replace("\\&", "&")   # 将 BibTeX 风格的 \& 转换为 &
    text = re.sub(r"[\s\.,;:]+", " ", text)  # 合并空格和轻微标点
    return text.strip().lower()

# -------------------------
# 2. 读取期刊映射表
# -------------------------
journal_map = {}
map_file = f"{os.path.dirname(__file__)}/journal_list.txt"  # 读取[全名-缩写]配置文件
with open(map_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            parts = line.split("=")
            if len(parts) == 2:
                full_name = parts[0].strip()
                abrv_name = parts[1].strip()
                journal_map[normalize(full_name)] = abrv_name

# -------------------------
# 3. 读取 bib 文件
# -------------------------
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# -------------------------
# 4. 替换 journal 和 booktitle 字段
# -------------------------
total_entries = len(re.findall(r"@\w+\s*\{", content))  # 更精确统计条目数
journal_entries = len(re.findall(r"journal\s*=\s*\{", content, re.IGNORECASE))
booktitle_entries = len(re.findall(r"booktitle\s*=\s*\{", content, re.IGNORECASE))

modified_count = 0
unmodified_names = []  # 合并 journal 和 booktitle 未匹配项

def replace_field(match):
    """正则替换回调函数（适用于 journal 和 booktitle）"""
    global modified_count
    field_name = match.group(1)  # journal 或 booktitle
    full_name = match.group(2).strip()
    clean_name = full_name.strip("{} ").strip()
    key = normalize(clean_name)

    if key in journal_map:
        modified_count += 1
        return f"{field_name} = {{{journal_map[key]}}}"
    else:
        unmodified_names.append(clean_name)
        return match.group(0)  # 保留原样

# 匹配 journal 或 booktitle 字段
pattern = re.compile(r"(journal|booktitle)\s*=\s*\{([^}]*)\}", re.IGNORECASE)
new_content = pattern.sub(replace_field, content)

# -------------------------
# 5. 输出结果文件
# -------------------------
with open(output_file, "w", encoding="utf-8") as f:
    f.write(new_content)

# -------------------------
# 6. 输出统计信息
# -------------------------
unmodified_unique = sorted(set(unmodified_names))
unmodified_count = len(unmodified_unique)
total_target_fields = journal_entries + booktitle_entries

print("📘 BibTeX 期刊/会议名替换完成！")
print(f"  • 总条目数（所有类型）: {total_entries}")
print(f"  • 含 journal 和 booktitle 字段的条目数: {total_target_fields}")
print(f"  • 成功修改字段总数: {modified_count}")
print(f"  • 未修改字段数: {unmodified_count}")

if unmodified_count > 0:
    print("\n⚠️ 以下期刊/会议未匹配到缩写：")
    for j in unmodified_unique:
        print("   -", j)

print(f"\n✅ 已生成新文件: {output_file}")
