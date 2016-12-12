import toml

with open("conf.toml") as conffile:
    config = toml.loads(conffile.read())

DATABASES = {
    'default': {
        'ENGINE': config['db']['databases']['engine'],
        'NAME': config['db']['databases']['name'],
        'USER': config['db']['databases']['user'],
        'PASSWORD': config['db']['databases']['password'],
        'HOST': config['db']['databases']['host'],
        'PORT': config['db']['databases']['port'],
    }
}

INSTALLED_APPS = (
    'data',
)

DEFAULT_CURRENCY = "USD"

SECRET_KEY = config['db']['secret_key']

FIXTURE_DIRS = ["fixtures"]