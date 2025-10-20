import subprocess
import sys


def install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"'{package}' installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while installing '{package}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    install('pycryptodome')
    install('javalang')
    install('anthropic')