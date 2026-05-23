import os
import re

vietnamese_chars = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]")

puml_files = []
for root, dirs, files in os.walk("docs"):
    for file in files:
        if file.endswith(".puml"):
            puml_files.append(os.path.join(root, file))

output_lines = []
for f in sorted(puml_files):
    viet_lines = []
    with open(f, "r", encoding="utf-8", errors="ignore") as file:
        for idx, line in enumerate(file):
            if vietnamese_chars.search(line):
                viet_lines.append((idx + 1, line.strip()))
    if viet_lines:
        output_lines.append(f"File: {f}")
        for ln, text in viet_lines:
            output_lines.append(f"  Line {ln}: {text}")
        output_lines.append("")

with open("vietnamese_lines.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(output_lines))

print(f"Scanned {len(puml_files)} files. Found Vietnamese in {len([x for x in output_lines if x.startswith('File:')])} files.")
