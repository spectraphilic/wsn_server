STATIC_COMPRESS_FILE_EXTS = ['js', 'css', 'svg']
STATIC_COMPRESS_METHODS = ['br']
STATIC_COMPRESS_KEEP_ORIGINAL = True
STATIC_COMPRESS_MIN_SIZE_KB = 1

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "static_compress.CompressedStaticFilesStorage",
    },
}
