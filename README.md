# 夜间阅读器

一个可以导入 PDF、TXT、EPUB、MOBI、DOC/DOCX 等文本文件并按章节浏览与导出的夜间配色网页程序。

## 功能特点
- 支持上传多种常见文本格式并在服务器端解析。
- 自动提取章节目录，支持章节预览、进度滑块滚动阅读。
- 一键复制或导出当前章节内容为 TXT 文件。
- 夜间阅读主题界面，支持响应式布局。

## 开发环境
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 运行
```bash
flask --app app run
```

访问 <http://localhost:5000> 体验网页。

> 注意：解析 DOC 格式依赖 `textract`，该库需要系统额外组件（如 `antiword`）。如遇安装或解析失败，可将文档转换为 DOCX 后再导入。
