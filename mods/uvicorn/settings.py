LOGGING_UVICORN = {
    'formatters': {
       'uvicorn.access': {
           '()': 'uvicorn.logging.AccessFormatter',
           'style': '{',
           'fmt': '[{asctime}] {levelname} {name} "{request_line}" {status_code}',
           'datefmt': '%d/%m/%Y:%H:%M:%S %z',  # 22/Mar/2025:10:05:09 +0100
       }
    },
    'handlers': {
        'uvicorn.access': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'uvicorn.access',
        },
    },
    'loggers': {
        # Override default uvicorn logging configuration
        'uvicorn': {
            'propagate': True,
        },
        'uvicorn.access': {
            'handlers': ['uvicorn.access'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
