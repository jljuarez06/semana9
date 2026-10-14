import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from PIL import Image, ImageOps, UnidentifiedImageError

from pila import Stack


BASE_DIR = Path(__file__).resolve().parent
PHOTO_DIR = BASE_DIR / "fotos"
PHOTO_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "clave-local-para-desarrollo",
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

DEFAULT_CAPACITY = 10
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def get_items():
    """Obtiene los elementos guardados en la sesión."""
    items = session.get("items", [])

    if not isinstance(items, list):
        session["items"] = []
        return []

    return items


def get_stack():
    """Reconstruye la pila a partir de la sesión."""
    capacity = session.get("capacity")

    if (
        isinstance(capacity, bool)
        or not isinstance(capacity, int)
        or not 1 <= capacity <= 20
    ):
        return None

    stack = Stack(capacity)

    for item in get_items():
        if not isinstance(item, dict):
            continue

        if item.get("type") == "text" and isinstance(
            item.get("value"), str
        ):
            stack.push(item)

        elif item.get("type") == "photo" and isinstance(
            item.get("filename"), str
        ):
            if Path(item["filename"]).name == item["filename"]:
                stack.push(item)

    return stack


def delete_photo(filename):
    """Elimina una fotografía del almacenamiento local."""
    if not isinstance(filename, str):
        return

    if Path(filename).name != filename:
        return

    path = PHOTO_DIR / filename

    if path.is_file():
        path.unlink()


def clear_stack():
    """Elimina los archivos y vacía los elementos de la sesión."""
    for item in get_items():
        if isinstance(item, dict) and item.get("type") == "photo":
            delete_photo(item.get("filename"))

    session["items"] = []


@app.errorhandler(413)
def file_too_large(error):
    flash("La imagen supera el límite de 8 MB.", "danger")
    return redirect(url_for("index"))


@app.get("/")
def index():
    stack = get_stack()
    items = stack.show() if stack else []

    return render_template(
        "index.html",
        stack=stack,
        items=items,
        default_capacity=DEFAULT_CAPACITY,
    )


@app.post("/configure")
def configure():
    try:
        raw_capacity = request.form.get("capacity", "").strip()

        if not raw_capacity.isdecimal():
            raise ValueError

        capacity = int(raw_capacity)

        if not 1 <= capacity <= 20:
            raise ValueError

    except ValueError:
        flash(
            "La capacidad debe ser un entero entre 1 y 20.",
            "danger",
        )
        return redirect(url_for("index"))

    clear_stack()
    session["capacity"] = capacity

    flash("Capacidad actualizada.", "success")
    return redirect(url_for("index"))


@app.post("/push-text")
def push_text():
    stack = get_stack()

    if stack is None:
        flash("Primero configura la capacidad de la pila.", "warning")
        return redirect(url_for("index"))

    if stack.is_full():
        flash("La pila está llena.", "warning")
        return redirect(url_for("index"))

    value = request.form.get("value", "").strip()

    if not value:
        flash("Escribe un valor antes de apilarlo.", "warning")
        return redirect(url_for("index"))

    if len(value) > 200:
        flash("El texto no puede superar los 200 caracteres.", "warning")
        return redirect(url_for("index"))

    items = get_items()
    items.append({"type": "text", "value": value})
    session["items"] = items

    flash("Elemento apilado correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/push-photo")
def push_photo():
    stack = get_stack()

    if stack is None:
        flash("Primero configura la capacidad de la pila.", "warning")
        return redirect(url_for("index"))

    if stack.is_full():
        flash("La pila está llena.", "warning")
        return redirect(url_for("index"))

    upload = request.files.get("image")

    if upload is None or not upload.filename:
        flash("Captura o selecciona una fotografía.", "warning")
        return redirect(url_for("index"))

    filename = f"{uuid.uuid4().hex}.jpg"
    destination = PHOTO_DIR / filename

    try:
        with Image.open(upload.stream) as image:
            if image.format not in ALLOWED_FORMATS:
                raise ValueError("Formato no permitido.")
            image.verify()

        upload.stream.seek(0)

        with Image.open(upload.stream) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            image.thumbnail((1920, 1920))
            image.save(
                destination,
                format="JPEG",
                quality=85,
                optimize=True,
            )

    except (UnidentifiedImageError, OSError, ValueError):
        delete_photo(filename)
        flash(
            "Imagen no válida. Utiliza JPEG, PNG o WEBP.",
            "danger",
        )
        return redirect(url_for("index"))

    items = get_items()
    items.append({"type": "photo", "filename": filename})
    session["items"] = items

    flash("Fotografía apilada correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/pop")
def pop():
    stack = get_stack()

    if stack is None or stack.is_empty():
        flash("La pila está vacía.", "warning")
        return redirect(url_for("index"))

    items = get_items()
    removed = items.pop()
    session["items"] = items

    if removed.get("type") == "photo":
        delete_photo(removed.get("filename"))

    flash("Elemento desapilado correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/clear")
def clear():
    if get_stack() is None:
        flash("Primero configura la pila.", "warning")
        return redirect(url_for("index"))

    clear_stack()
    flash("La pila se ha vaciado.", "success")
    return redirect(url_for("index"))


@app.get("/photos/<filename>")
def photo(filename):
    if Path(filename).name != filename:
        abort(404)

    registered = any(
        isinstance(item, dict)
        and item.get("type") == "photo"
        and item.get("filename") == filename
        for item in get_items()
    )

    if not registered:
        abort(404)

    response = send_from_directory(
        PHOTO_DIR,
        filename,
        mimetype="image/jpeg",
        as_attachment=False,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store"

    return response


if __name__ == "__main__":
    app.run(debug=True)