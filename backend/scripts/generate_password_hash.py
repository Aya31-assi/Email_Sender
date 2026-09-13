from getpass import getpass

from pwdlib import PasswordHash


def main() -> None:
    password = getpass("Admin password: ")
    confirmation = getpass("Confirm password: ")
    if not password or password != confirmation:
        raise SystemExit("Passwords are empty or do not match.")
    print(PasswordHash.recommended().hash(password))


if __name__ == "__main__":
    main()
