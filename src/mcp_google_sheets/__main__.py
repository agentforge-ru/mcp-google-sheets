"""Entry point. Reads GOOGLE_APPLICATION_CREDENTIALS env var for service account JSON path."""
import os
import sys
from .server import build_server


def main() -> None:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print(
            "ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.\n"
            "Point it to your service account JSON key file. See README for setup.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(creds_path):
        print(f"ERROR: Credentials file not found: {creds_path}", file=sys.stderr)
        sys.exit(1)

    server = build_server(credentials_path=creds_path)

    try:
        server.run()
    except KeyboardInterrupt:
        print("Shutting down.", file=sys.stderr)


if __name__ == "__main__":
    main()
