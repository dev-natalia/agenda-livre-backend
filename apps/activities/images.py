"""Validação e tratamento das imagens enviadas para as atividades.

`process_image` confere o conteúdo do arquivo (não a extensão) e os limites de tamanho e de
dimensões, aplica a orientação, reduz o lado maior e regrava a imagem sem nenhum metadado.
"""

import io
import logging

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

MAX_BYTES = 5 * 1024 * 1024
MIN_SIZE = (400, 300)
MAX_SIZE = (6000, 6000)
OUTPUT_MAX_SIDE = 1600
JPEG_QUALITY = 85
ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

NOT_AN_IMAGE = "Envie uma imagem JPEG, PNG ou WebP."
UNREADABLE = "Não foi possível ler a imagem. Envie outro arquivo."
TOO_BIG_FILE = "A imagem deve ter no máximo 5 MB."
TOO_SMALL = "A imagem deve ter pelo menos 400×300 pixels."
TOO_LARGE = "A imagem deve ter no máximo 6000×6000 pixels."


def process_image(uploaded):
    """Valida e trata a imagem. Devolve `(ContentFile, extensão)` ou levanta `ValidationError`."""
    if uploaded.size > MAX_BYTES:
        raise ValidationError(TOO_BIG_FILE)
    image, image_format = _open(uploaded)
    _check_dimensions(image.size)
    try:
        image.load()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ValidationError(UNREADABLE) from None
    image = ImageOps.exif_transpose(image)
    image.thumbnail((OUTPUT_MAX_SIDE, OUTPUT_MAX_SIDE), Image.Resampling.LANCZOS)
    return ContentFile(_encode(image, image_format)), ALLOWED_FORMATS[image_format]


def _open(uploaded):
    try:
        image = Image.open(uploaded)
    except UnidentifiedImageError:
        raise ValidationError(NOT_AN_IMAGE) from None
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ValidationError(UNREADABLE) from None
    if image.format not in ALLOWED_FORMATS:
        raise ValidationError(NOT_AN_IMAGE)
    return image, image.format


def _check_dimensions(size):
    """Confere as dimensões pelo cabeçalho, antes de decodificar o arquivo inteiro."""
    width, height = size
    if width < MIN_SIZE[0] or height < MIN_SIZE[1]:
        raise ValidationError(TOO_SMALL)
    if width > MAX_SIZE[0] or height > MAX_SIZE[1]:
        raise ValidationError(TOO_LARGE)


def _encode(image, image_format):
    """Regrava a imagem do zero: nenhum metadado (EXIF, GPS, texto) é copiado."""
    buffer = io.BytesIO()
    if image_format == "JPEG":
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True)
    elif image_format == "PNG":
        image.save(buffer, "PNG", optimize=True)
    else:
        image.save(buffer, "WEBP", quality=JPEG_QUALITY)
    return buffer.getvalue()


def delete_stored_file(name):
    """Apaga o arquivo do armazenamento. Uma falha só é registrada, nunca interrompe a operação."""
    if not name:
        return
    try:
        default_storage.delete(name)
    except Exception as error:
        logger.error("Falha ao apagar a imagem %s (%s).", name, type(error).__name__)
