import io
import os
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.activities.images import MAX_BYTES, process_image

NOT_AN_IMAGE = "Envie uma imagem JPEG, PNG ou WebP."
UNREADABLE = "Não foi possível ler a imagem. Envie outro arquivo."
TOO_BIG_FILE = "A imagem deve ter no máximo 5 MB."
TOO_SMALL = "A imagem deve ter pelo menos 400×300 pixels."
TOO_LARGE = "A imagem deve ter no máximo 6000×6000 pixels."


def _bytes(size=(800, 600), fmt="JPEG", mode="RGB", color=(200, 30, 30), **save):
    buffer = io.BytesIO()
    Image.new(mode, size, color).save(buffer, fmt, **save)
    return buffer.getvalue()


def _upload(content, name="foto.jpg"):
    return SimpleUploadedFile(name, content)


def _open(content_file):
    content_file.seek(0)
    return Image.open(io.BytesIO(content_file.read()))


def _error(content, name="foto.jpg"):
    with pytest.raises(ValidationError) as error:
        process_image(_upload(content, name))
    return error.value.messages


@pytest.mark.parametrize(
    "fmt,extension,name",
    [("JPEG", "jpg", "a.jpg"), ("PNG", "png", "a.png"), ("WEBP", "webp", "a.webp")],
)
def test_valid_images_keep_their_format(fmt, extension, name):
    result, found = process_image(_upload(_bytes(fmt=fmt), name))

    assert found == extension
    assert _open(result).format == fmt


def test_extension_comes_from_the_content_not_from_the_name():
    result, extension = process_image(_upload(_bytes(fmt="PNG"), "foto.jpg"))

    assert extension == "png"
    assert _open(result).format == "PNG"


def test_text_file_with_image_extension_is_rejected():
    assert _error(b"isto nao e uma imagem", "foto.jpg") == [NOT_AN_IMAGE]


def test_executable_with_image_extension_is_rejected():
    assert _error(b"MZ\x90\x00" + os.urandom(2048), "foto.png") == [NOT_AN_IMAGE]


@pytest.mark.parametrize("fmt", ["GIF", "BMP"])
def test_other_image_formats_are_rejected(fmt):
    assert _error(_bytes(fmt=fmt, mode="RGB" if fmt == "BMP" else "P", color=0)) == [NOT_AN_IMAGE]


def test_empty_file_is_rejected():
    assert _error(b"") == [NOT_AN_IMAGE]


def test_truncated_image_is_unreadable():
    noise = Image.frombytes("RGB", (800, 600), os.urandom(800 * 600 * 3))
    buffer = io.BytesIO()
    noise.save(buffer, "JPEG", quality=90)
    content = buffer.getvalue()

    assert _error(content[: len(content) // 2]) == [UNREADABLE]


def test_decompression_bomb_is_unreadable():
    with patch("apps.activities.images.Image.open", side_effect=Image.DecompressionBombError):
        with pytest.raises(ValidationError) as error:
            process_image(_upload(_bytes()))

    assert error.value.messages == [UNREADABLE]


def test_file_of_exactly_5_mb_is_accepted():
    content = _bytes()
    padded = content + b"\0" * (MAX_BYTES - len(content))
    assert len(padded) == MAX_BYTES

    result, extension = process_image(_upload(padded))

    assert extension == "jpg"
    assert _open(result).size == (800, 600)


def test_file_one_byte_over_5_mb_is_rejected_without_opening_it():
    content = _bytes()
    padded = content + b"\0" * (MAX_BYTES + 1 - len(content))

    with patch("apps.activities.images.Image.open") as opened:
        with pytest.raises(ValidationError) as error:
            process_image(_upload(padded))

    assert error.value.messages == [TOO_BIG_FILE]
    opened.assert_not_called()


@pytest.mark.parametrize("size", [(400, 300), (401, 301)])
def test_minimum_dimensions_are_accepted(size):
    result, _ = process_image(_upload(_bytes(size=size)))

    assert _open(result).size == size


@pytest.mark.parametrize("size", [(399, 300), (400, 299), (100, 100)])
def test_images_below_the_minimum_are_rejected(size):
    assert _error(_bytes(size=size)) == [TOO_SMALL]


def test_maximum_dimensions_are_accepted_and_reduced():
    content = _bytes(size=(6000, 6000), mode="L", color=120)

    result, _ = process_image(_upload(content))

    assert _open(result).size == (1600, 1600)


@pytest.mark.parametrize("size", [(6001, 6000), (6000, 6001)])
def test_images_above_the_maximum_are_rejected_before_decoding(size):
    content = _bytes(size=size, fmt="PNG", mode="1", color=0)

    with patch.object(Image.Image, "load", side_effect=AssertionError("decodificou")):
        assert _error(content, "foto.png") == [TOO_LARGE]


def test_large_image_is_reduced_to_1600_on_the_longest_side():
    result, _ = process_image(_upload(_bytes(size=(3200, 2000))))

    assert _open(result).size == (1600, 1000)


def test_portrait_image_is_reduced_keeping_proportion():
    result, _ = process_image(_upload(_bytes(size=(1800, 3600))))

    assert _open(result).size == (800, 1600)


def test_smaller_image_is_not_enlarged():
    result, _ = process_image(_upload(_bytes(size=(1000, 700))))

    assert _open(result).size == (1000, 700)


def test_image_of_exactly_1600_is_unchanged_in_size():
    result, _ = process_image(_upload(_bytes(size=(1600, 900))))

    assert _open(result).size == (1600, 900)


def test_exif_is_removed_and_orientation_is_applied():
    exif = Image.Exif()
    exif[0x0112] = 6  # girar 90° ao exibir
    exif[0x010F] = "Câmera de teste"
    content = _bytes(size=(1000, 600), exif=exif.tobytes())
    assert len(Image.open(io.BytesIO(content)).getexif()) > 0

    result, _ = process_image(_upload(content))

    saved = _open(result)
    assert len(saved.getexif()) == 0
    assert saved.size == (600, 1000)


def test_gps_location_is_removed():
    exif = Image.Exif()
    exif.get_ifd(0x8825)[1] = "S"  # GPSLatitudeRef
    content = _bytes(exif=exif.tobytes())

    result, _ = process_image(_upload(content))

    assert 0x8825 not in _open(result).getexif()


def test_png_text_chunks_are_removed():
    from PIL.PngImagePlugin import PngInfo

    info = PngInfo()
    info.add_text("Autor", "Fulana")
    content = _bytes(fmt="PNG", pnginfo=info)

    result, _ = process_image(_upload(content, "a.png"))

    assert _open(result).info.get("Autor") is None


def test_png_transparency_is_preserved():
    content = _bytes(size=(500, 400), fmt="PNG", mode="RGBA", color=(255, 0, 0, 128))

    result, extension = process_image(_upload(content, "a.png"))

    saved = _open(result)
    assert extension == "png"
    assert saved.mode == "RGBA"
    assert saved.getpixel((10, 10))[3] == 128


def test_cmyk_jpeg_is_converted_so_it_can_be_saved():
    content = _bytes(mode="CMYK", color=(0, 0, 0, 0))

    result, extension = process_image(_upload(content))

    assert extension == "jpg"
    assert _open(result).mode == "RGB"


def test_result_is_a_file_ready_to_be_saved():
    result, _ = process_image(_upload(_bytes()))

    assert result.size > 0
    assert result.read(2) in (b"\xff\xd8", b"")
