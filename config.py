from pydantic import BaseModel
from fastapi_mail import ConnectionConfig

class EmailConfig(BaseModel):
    MAIL_USERNAME: str = "dirantechie@gmail.com"
    MAIL_PASSWORD: str = "ywlp iqji wkkcihlg"
    MAIL_FROM: str = "dirantechie@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

conf = ConnectionConfig(
    MAIL_USERNAME=EmailConfig().MAIL_USERNAME,
    MAIL_PASSWORD=EmailConfig().MAIL_PASSWORD,
    MAIL_FROM=EmailConfig().MAIL_FROM,
    MAIL_PORT=EmailConfig().MAIL_PORT,
    MAIL_SERVER=EmailConfig().MAIL_SERVER,
    MAIL_STARTTLS=EmailConfig().MAIL_STARTTLS,
    MAIL_SSL_TLS=EmailConfig().MAIL_SSL_TLS
)
