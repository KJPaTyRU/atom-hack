import sys

from hmm.config import get_settings
import uvicorn


def run_uvicorn(run_args: dict):
    uvicorn.run("hmm.main:create_app", **run_args)


def main():
    run_uvicorn(get_settings().uvicorn_kwargs)


if __name__ == "__main__":
    sys.exit(main())
