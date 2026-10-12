import sys

import pytest

from config.storage import build_storages

OPTIONS = {
    "AWS_ACCESS_KEY_ID": "chave-de-teste",
    "AWS_SECRET_ACCESS_KEY": "segredo-de-teste",
    "AWS_STORAGE_BUCKET_NAME": "bucket-de-teste",
    "AWS_S3_REGION_NAME": "sa-east-1",
}


@pytest.fixture
def storages():
    return build_storages(OPTIONS)


def test_default_storage_is_s3(storages):
    assert storages["default"]["BACKEND"] == "storages.backends.s3.S3Storage"


def test_default_storage_takes_bucket_region_and_credentials(storages):
    config = storages["default"]["OPTIONS"]

    assert config["bucket_name"] == "bucket-de-teste"
    assert config["region_name"] == "sa-east-1"
    assert config["access_key"] == "chave-de-teste"
    assert config["secret_key"] == "segredo-de-teste"


def test_urls_are_public_and_permanent(storages):
    config = storages["default"]["OPTIONS"]

    assert config["querystring_auth"] is False


def test_urls_use_the_regional_endpoint_of_the_bucket(storages):
    config = storages["default"]["OPTIONS"]

    assert config["custom_domain"] == "bucket-de-teste.s3.sa-east-1.amazonaws.com"


def test_names_are_random_so_files_are_not_checked_before_writing(storages):
    assert storages["default"]["OPTIONS"]["file_overwrite"] is True


def test_no_acl_is_sent_per_object(storages):
    assert storages["default"]["OPTIONS"]["default_acl"] is None


def test_staticfiles_backend_is_kept(storages):
    assert storages["staticfiles"] == {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    }


def test_building_the_settings_does_not_import_boto3():
    sys.modules.pop("boto3", None)

    build_storages(OPTIONS)

    assert "boto3" not in sys.modules
