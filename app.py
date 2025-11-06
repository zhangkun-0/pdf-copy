import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from parser.document_parser import Chapter, DocumentParser, DocumentParserError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".epub", ".mobi", ".doc", ".docx"}
parser = DocumentParser()


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "未选择文件"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "文件名无效"}), 400

    if not allowed_file(filename):
        return jsonify({"error": "不支持的文件类型"}), 400

    suffix = Path(filename).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        chapters = parser.parse(tmp_path)
    except DocumentParserError as exc:
        os.unlink(tmp_path)
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - fallback error
        os.unlink(tmp_path)
        return jsonify({"error": "解析文件时发生未知错误"}), 500

    os.unlink(tmp_path)

    return jsonify({"chapters": [chapter.__dict__ for chapter in chapters]})


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
