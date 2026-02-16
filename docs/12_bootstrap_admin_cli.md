# Bootstrap Admin CLI

Comando backend para crear el primer usuario administrador de forma segura.

## Para que sirve

- Evita crear admin desde endpoint publico.
- Solo permite crear admin si la tabla `users` esta vacia.
- Si ya existe cualquier usuario, bloquea la operacion.

## Comando

```bash
python -m app.scripts.bootstrap_admin --username rootadmin --password StrongAdmin123
```

## Flujo interno

1. Abre sesion de DB.
2. Comprueba si hay usuarios.
3. Si no hay, crea usuario con `is_superuser=True`.
4. Cierra sesion y devuelve codigo de salida (`0` ok, `1` error).

## Cuando usarlo

- Primera instalacion del entorno.
- Entornos nuevos (staging/dev local) donde no existe ningun usuario.


