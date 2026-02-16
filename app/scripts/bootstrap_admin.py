"""
Comando CLI para crear el primer usuario administrador.
"""
import argparse

from app.core.database import SessionLocal
from app.services.auth_service import AuthService


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de linea de comandos con argumentos obligatorios."""
    parser = argparse.ArgumentParser(
        description="Crea el primer usuario administrador cuando la base de datos no tiene usuarios.",
    )
    parser.add_argument("--username", required=True, help="Nombre del admin a crear")
    parser.add_argument("--password", required=True, help="Contrasena del admin")
    return parser


def run_bootstrap(username: str, password: str) -> int:
    """Ejecuta el bootstrap y devuelve un codigo de salida."""
    db = SessionLocal()
    try:
        created_admin = AuthService.bootstrap_first_admin(
            db=db,
            username=username,
            password=password,
        )
        print(
            f"Administrador creado correctamente: username={created_admin.username}, id={created_admin.id}"
        )
        return 0
    except ValueError as exc:
        print(f"Bootstrap fallido: {exc}")
        return 1
    finally:
        db.close()


def main() -> int:
    """Punto de entrada CLI para bootstrap del primer admin."""
    parser = build_parser()
    args = parser.parse_args()
    return run_bootstrap(username=args.username, password=args.password)


if __name__ == "__main__":
    raise SystemExit(main())
