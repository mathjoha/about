import os
import subprocess

# Prevent infinite recursion when quarto render calls pre-render again
if os.environ.get("QUARTO_PRERENDER_RUNNING"):
    exit(0)

root_dir = os.path.abspath(os.path.dirname(__file__))

# Generate full CV (without max-items limit)
short_file = os.path.join(root_dir, "cv", "short.qmd")
with open(short_file, "r", encoding="utf8") as f:
    content = f.read()

content = content.replace("max-items: 3", "")

full_file = os.path.join(root_dir, "cv", "full.qmd")
with open(full_file, "w", encoding="utf8") as f:
    f.write(content)

# Generate PDF CV
generate_script = os.path.join(root_dir, "generate_cv_pdf.py")
subprocess.run(["python3", generate_script], cwd=root_dir, check=True)

cv_qmd = os.path.join(root_dir, "cv_for_pdf.qmd")
dst_pdf = os.path.join(root_dir, "CV_MJ.latest.pdf")
env = os.environ.copy()
env["QUARTO_PRERENDER_RUNNING"] = "1"
result = subprocess.run(
    ["quarto", "render", cv_qmd, "--to", "pdf", "--output", "CV_MJ.latest.pdf"],
    cwd=root_dir,
    env=env,
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"PDF generation failed:\n{result.stderr}")
else:
    print(f"Generated: {dst_pdf}")
