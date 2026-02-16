from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Token JWT de acceso")
    refresh_token: str = Field(..., description="Token JWT de refresco usado para rotacion")
    token_type: str = Field(default="bearer", description="Tipo de token")


class CurrentUserResponse(BaseModel):
    username: str = Field(..., description="Nombre de usuario autenticado")
    specialty: str = Field(..., description="Especialidad operativa del usuario")
    is_superuser: bool = Field(
        default=False,
        description="Indica si el usuario tiene permisos admin",
    )


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nuevo nombre de usuario",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contrasena en texto plano",
    )
    specialty: str = Field(default="general", min_length=2, max_length=80)


class RegisterResponse(BaseModel):
    id: int = Field(..., description="ID del usuario creado")
    username: str = Field(..., description="Nombre de usuario creado")
    specialty: str = Field(..., description="Especialidad operativa asignada")


class AdminUserResponse(BaseModel):
    id: int = Field(..., description="ID de usuario")
    username: str = Field(..., description="Nombre de usuario")
    specialty: str = Field(..., description="Especialidad operativa del usuario")
    is_active: bool = Field(..., description="Indica si la cuenta esta activa")
    is_superuser: bool = Field(..., description="Indica si la cuenta tiene permisos admin")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="Refresh token para rotar sesion")
