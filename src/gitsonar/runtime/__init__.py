"""Runtime package for GitSonar."""


def main():
    from .app import main as runtime_main

    return runtime_main()


__all__ = ["main"]
