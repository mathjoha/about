import os

root_dir = os.path.abspath(os.path.dirname(__file__))

short_file = os.path.join(root_dir, "cv", "short.qmd")
with open(short_file, "r", encoding="utf8") as f:
    content = f.read()

contet = content.replace("max-items: 3", "")

full_file = os.path.join(root_dir, "cv", "full.qmd")
with open(full_file, "w", encoding="utf8") as f:
    # f.write('# Copied from "short.qmd"\n\n')
    f.write(content)
