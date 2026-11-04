"""Valida conteúdo de imagens/PDF e monta URLs autenticadas para fotos de chamados."""
import io
import warnings
from pathlib import PurePath
from PIL import Image,UnidentifiedImageError
from pypdf import PdfReader
from pypdf.generic import IndirectObject,DictionaryObject,ArrayObject
from exceptions import ValidacaoError

MAX_BYTES = 4 * 1024 * 1024
MAX_PIXELS = 16_000_000
MIMES = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","webp":"image/webp","pdf":"application/pdf"}
FORMATS = {"png":"PNG","jpg":"JPEG","jpeg":"JPEG","webp":"WEBP"}


def validate_upload(file,allow_pdf=False):
    extension = (file.filename or "").rsplit(".",1)[-1].lower()
    if extension not in MIMES or (extension=="pdf" and not allow_pdf):
        raise ValidacaoError("Tipo de arquivo não permitido.")
    if file.mimetype not in {MIMES[extension],"image/jpg" if extension in {"jpg","jpeg"} else MIMES[extension]}:
        raise ValidacaoError("O MIME não corresponde ao tipo de arquivo.")
    file.stream.seek(0)
    data = file.stream.read(MAX_BYTES+1)
    file.stream.seek(0)
    if not data or len(data)>MAX_BYTES:
        raise ValidacaoError("Arquivo vazio ou maior que 4 MB.")
    try:
        if extension=="pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError("Assinatura PDF inválida.")
            pdf = PdfReader(io.BytesIO(data),strict=True)
            if pdf.is_encrypted or len(pdf.pages)>30:
                raise ValueError("PDF protegido ou muito extenso.")
            visited=set()
            def inspect(value):
                if isinstance(value,IndirectObject):
                    marker=(value.idnum,value.generation)
                    if marker in visited:return
                    visited.add(marker)
                    if len(visited)>10000:raise ValueError("PDF complexo.")
                    value=value.get_object()
                if isinstance(value,DictionaryObject):
                    if any(key in value for key in ("/JS","/JavaScript","/OpenAction","/AA","/Launch","/EmbeddedFiles","/AcroForm","/RichMedia")):
                        raise ValueError("PDF contém recursos ativos.")
                    for child in value.values():inspect(child)
                elif isinstance(value,ArrayObject):
                    for child in value:inspect(child)
            inspect(pdf.trailer["/Root"])
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error",Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if image.format != FORMATS[extension] or image.width*image.height>MAX_PIXELS:
                        raise ValueError("Formato ou dimensões inválidas.")
                    image.verify()
                with Image.open(io.BytesIO(data)) as image:
                    image.load()
                    clean=io.BytesIO()
                    image.save(clean,format=FORMATS[extension]) # Não copiar EXIF/IPTC ou geolocalização.
                    if clean.tell()>MAX_BYTES:raise ValueError("Imagem muito grande.")
                    data=clean.getvalue()
    except Exception as error:
        if isinstance(error,ValidacaoError):raise
        raise ValidacaoError("Arquivo inválido, corrompido ou com conteúdo ativo não permitido.") from None
    file.stream=io.BytesIO(data)
    return extension


def photo_url(identifier,service_id,reference):
    if reference.startswith("private-cloudinary:"):
        return f"/api/servicos/{service_id}/fotos/{identifier}"
    return reference # Somente legado: não torna assets públicos antigos privados.
