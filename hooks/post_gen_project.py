import os
import subprocess
import random
import shutil
import string

TERMINATOR = "\x1b[0m"
SUCCESS = "\x1b[1;32m [SUCCESS]: "
WARNING = "\x1b[1;33m [WARNING]: "
HINT = "\x1b[3;33m"

try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    using_sysrandom = False

def generate_random_string(length, using_digits=True, using_ascii_letters=True, using_punctuation=False):
    if not using_sysrandom:
        return None
    chars = ''
    if using_digits:
        chars += string.digits
    if using_ascii_letters:
        chars += string.ascii_letters
    if using_punctuation:
        chars += string.punctuation.replace('"', "").replace("'", "").replace("\\", "")
    return ''.join(random.choice(chars) for _ in range(length))

def set_flag(filepath, marker, value=None, formatted=None, *args, **kwargs):
    if value is None:
        value = generate_random_string(*args, **kwargs)
        if not value:
            print(WARNING + f"Secure random generator unavailable. Please set {marker} manually." + TERMINATOR)
            value = marker
        if formatted:
            value = formatted.format(value)
    with open(filepath, "r+", encoding="utf-8") as f:
        content = f.read().replace(marker, value)
        f.seek(0)
        f.write(content)
        f.truncate()
    return value

def set_secrets():
    paths = [
        os.path.join(".envs", ".local", ".django"),
        os.path.join(".envs", ".production", ".django"),
        os.path.join(".envs", ".local", ".postgres"),
        os.path.join(".envs", ".production", ".postgres"),
    ]
    for path in paths:
        if os.path.exists(path):
            set_flag(path, "!!!SET DJANGO_SECRET_KEY!!!", length=64)
            set_flag(path, "!!!SET DJANGO_ADMIN_URL!!!", formatted="{}/", length=32)
            set_flag(path, "!!!SET POSTGRES_PASSWORD!!!", length=48)
            set_flag(path, "!!!SET CELERY_FLOWER_USER!!!", length=16)
            set_flag(path, "!!!SET CELERY_FLOWER_PASSWORD!!!", length=48)

def remove_docker_files():
    for path in ["docker-compose.yml", ".dockerignore", "docker-files"]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

def reformat_white_space():
    try:
        import autopep8
        target = os.path.abspath("./{{ cookiecutter.app_name }}")
        args = autopep8.parse_args([
            '--max-line-length=119',
            '--in-place',
            '--recursive',
            target  # ✅ <-- include target here as argument!
        ])
        autopep8.fix_multiple_files([target], args)
    except ImportError:
        print(WARNING + "autopep8 not found. Skipping formatting." + TERMINATOR)
    except Exception as e:
        print(WARNING + f"autopep8 failed: {e}" + TERMINATOR)

def main():
    set_secrets()
    shutil.move(".editorconfig.template", ".editorconfig")
    is_docker = "{{ cookiecutter.dockerize }}" != "n"

    print(HINT + "Next steps:" + TERMINATOR)

    if not is_docker:
        remove_docker_files()
        print(HINT + f"""
cd {{ cookiecutter.project_slug }}
poetry install
npm install
poetry run python manage.py initialize_shop_demo
poetry run python manage.py runserver
""" + TERMINATOR)
    else:
        set_flag("docker-files/databases.environ", "!!!SET POSTGRES_PASSWORD!!!", length=48)
        print(HINT + f"""
cd {{ cookiecutter.project_slug }}
docker-compose build
docker-compose up -d
""" + TERMINATOR)

    reformat_white_space()
    print(SUCCESS + "Project initialized using Poetry. 🚀" + TERMINATOR)

if __name__ == "__main__":
    main()
