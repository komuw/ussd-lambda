import os

import boto3
import structlog


def here(*args):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *args)


PROJECT_ROOT = here('')


def project_root_joiner(*args):
    return os.path.join(os.path.abspath(PROJECT_ROOT), *args)


DEBUG = os.environ.get('DEBUG', True)
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'A-random-and-secure-secret-key.\nKeep-this-very-SAFE!')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
)

STATIC_ROOT = project_root_joiner('', 'static/')
STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            project_root_joiner('', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug':
            DEBUG,
        },
    },
]

# dont specify a Database, we'll use dynamodb
# DATABASES = {}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s\n'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

UP_ENVIRONMENT = os.getenv("UP_ENVIRONMENT", None)
logger = structlog.get_logger(__name__).bind(UP_ENVIRONMENT=UP_ENVIRONMENT)
logger.info("setup_boto")

try:
    if UP_ENVIRONMENT:
        logger.info("boto_setup", method="access-keys")

        # this variables will be setup by CI,
        # during CI, we'll edit up.json and add this env vars
        DYNAMODB_SESSIONS_AWS_ACCESS_KEY_ID = os.getenv(
            "DYNAMODB_SESSIONS_AWS_ACCESS_KEY_ID")
        DYNAMODB_SESSIONS_AWS_SECRET_ACCESS_KEY = os.getenv(
            "DYNAMODB_SESSIONS_AWS_SECRET_ACCESS_KEY")
        DYNAMODB_SESSIONS_AWS_REGION_NAME = os.getenv(
            "DYNAMODB_SESSIONS_AWS_REGION_NAME", "eu-west-1")

        logger.info('write-out-boto-profile')
        lambda_root = os.environ.get('LAMBDA_TASK_ROOT', '/var/task')
        if not os.path.exists(lambda_root):
            os.makedirs(lambda_root)
        os.environ["AWS_ACCESS_KEY_ID"] = DYNAMODB_SESSIONS_AWS_ACCESS_KEY_ID
        os.environ["AWS_SECRET_ACCESS_KEY"] = DYNAMODB_SESSIONS_AWS_SECRET_ACCESS_KEY
        os.environ["AWS_DEFAULT_REGION"] = DYNAMODB_SESSIONS_AWS_REGION_NAME
        os.environ["AWS_PROFILE"] = "apex-up-profile"

        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = "{lambda_root}/credentials".format(lambda_root=lambda_root)
        os.environ['AWS_CONFIG_FILE'] = "{lambda_root}/config".format(lambda_root=lambda_root)
        logger.info("environ", environ=os.environ)

        f= open("{lambda_root}/credentials".format(lambda_root=lambda_root),"w+")
        prof = '[apex-up-profile]\naws_access_key_id={aws_access_key_id}\naws_secret_access_key={aws_secret_access_key}\nregion={region}'.format(
            aws_access_key_id=DYNAMODB_SESSIONS_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=DYNAMODB_SESSIONS_AWS_SECRET_ACCESS_KEY,
            region=DYNAMODB_SESSIONS_AWS_REGION_NAME
        )
        f.write(prof)
        f.close()

        f= open("{lambda_root}/config".format(lambda_root=lambda_root),"w+")
        prof = '[default]\noutput=json\nregion=eu-west-1'
        f.write(prof)
        f.close()

        f= open("{lambda_root}/credentials".format(lambda_root=lambda_root),"r")
        content = f.read()
        f.close()
        logger.info("content", content=content)


        DYNAMODB_SESSIONS_BOTO_SESSION = boto3.Session(
            aws_access_key_id=DYNAMODB_SESSIONS_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=DYNAMODB_SESSIONS_AWS_SECRET_ACCESS_KEY,
            region_name=DYNAMODB_SESSIONS_AWS_REGION_NAME)
    else:
        logger.info("boto_setup", method="profile")
        DYNAMODB_SESSIONS_BOTO_SESSION = boto3.Session(
            profile_name='apex-up-profile')
except Exception as e:
    logger.exception("boto_setup_error", error=str(e))
