"""Armazenamento de arquivos: imagens das atividades no Amazon S3.

O banco guarda apenas o nome do objeto; o arquivo fica no bucket. Nenhuma função deste módulo
acessa a rede nem importa `boto3`: ele só descreve a configuração usada pelo `django-storages`.
"""


def build_storages(options):
    """Monta o dicionário `STORAGES` a partir das variáveis `AWS_*` já validadas."""
    bucket = options["AWS_STORAGE_BUCKET_NAME"]
    region = options["AWS_S3_REGION_NAME"]
    return {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": bucket,
                "region_name": region,
                # Endereço regional do próprio bucket (não é domínio próprio): evita o redirecio-
                # namento do endereço global e dá URLs iguais às do contrato da API.
                "custom_domain": f"{bucket}.s3.{region}.amazonaws.com",
                "access_key": options["AWS_ACCESS_KEY_ID"],
                "secret_key": options["AWS_SECRET_ACCESS_KEY"],
                # URLs públicas e permanentes: a leitura vem da política do bucket.
                "querystring_auth": False,
                "default_acl": None,
                # Os nomes são UUIDs gerados pelo modelo, então não há colisão a checar.
                "file_overwrite": True,
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
