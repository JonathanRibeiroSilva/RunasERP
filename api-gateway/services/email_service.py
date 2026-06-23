"""
Serviço de envio de email via SMTP (Gmail).
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import structlog

from config import settings

log = structlog.get_logger()


def _build_reset_email_html(reset_url: str, nome: str | None = None) -> str:
    """Monta o HTML do email de reset de senha."""
    saudacao = f"Olá, {nome}!" if nome else "Olá!"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Redefinir Senha - Runas ERP</title>
</head>
<body style="margin:0;padding:0;background:#0f1115;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1115;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#171a21;border:1px solid rgba(255,255,255,0.1);
                      border-radius:16px;overflow:hidden;max-width:560px;width:100%;">

          <!-- Header -->
          <tr>
            <td align="center"
                style="background:linear-gradient(135deg,#1e3a5f 0%,#1a1d24 100%);
                       padding:36px 40px 28px;">
              <p style="margin:0;font-size:28px;font-weight:700;letter-spacing:8px;
                        color:#3b82f6;">RUNAS</p>
              <p style="margin:8px 0 0;font-size:13px;color:#94a3b8;letter-spacing:2px;">
                SISTEMA DE GESTÃO COMERCIAL
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <p style="margin:0 0 8px;font-size:22px;font-weight:600;color:#e5e7eb;">
                Redefinição de Senha
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:#94a3b8;line-height:1.6;">
                {saudacao} Recebemos uma solicitação para redefinir a senha da sua conta no Runas ERP.
              </p>

              <p style="margin:0 0 24px;font-size:15px;color:#94a3b8;line-height:1.6;">
                Clique no botão abaixo para criar uma nova senha. O link é válido por <strong style="color:#e5e7eb;">1 hora</strong>.
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
                <tr>
                  <td align="center"
                      style="background:linear-gradient(135deg,#3b82f6 0%,#8b5cf6 100%);
                             border-radius:8px;">
                    <a href="{reset_url}"
                       style="display:inline-block;padding:14px 36px;
                              font-size:15px;font-weight:600;color:#ffffff;
                              text-decoration:none;letter-spacing:0.3px;">
                      Redefinir Minha Senha
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Link fallback -->
              <p style="margin:0 0 8px;font-size:13px;color:#64748b;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </p>
              <p style="margin:0 0 32px;font-size:12px;word-break:break-all;">
                <a href="{reset_url}" style="color:#3b82f6;text-decoration:none;">{reset_url}</a>
              </p>

              <!-- Warning -->
              <table cellpadding="0" cellspacing="0" width="100%"
                     style="background:rgba(245,158,11,0.08);
                            border:1px solid rgba(245,158,11,0.2);
                            border-radius:8px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <p style="margin:0;font-size:13px;color:#fbbf24;line-height:1.5;">
                      ⚠️ Se você não solicitou a redefinição de senha, ignore este email.
                      Sua senha permanece a mesma e nenhuma alteração foi feita.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px 32px;border-top:1px solid rgba(255,255,255,0.06);">
              <p style="margin:0;font-size:12px;color:#475569;text-align:center;line-height:1.6;">
                Este é um email automático, não responda.<br/>
                © 2025 Runas ERP · Todos os direitos reservados.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_reset_password_email(
    to_email: str,
    reset_token: str,
    nome: str | None = None
) -> bool:
    """
    Envia email de reset de senha via SMTP Gmail.

    Args:
        to_email: Email do destinatário
        reset_token: Token de reset gerado
        nome: Nome do usuário (opcional, para personalizar o email)

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.error("email.smtp_not_configured")
        return False

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # Montar mensagem
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Redefinição de Senha - Runas ERP"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    # Versão texto simples (fallback)
    text_body = (
        f"Olá{', ' + nome if nome else ''}!\n\n"
        f"Recebemos uma solicitação para redefinir sua senha no Runas ERP.\n\n"
        f"Acesse o link abaixo para criar uma nova senha (válido por 1 hora):\n"
        f"{reset_url}\n\n"
        f"Se você não solicitou isso, ignore este email.\n\n"
        f"Runas ERP"
    )

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_reset_email_html(reset_url, nome), "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        log.info("email.sent", to=to_email, type="reset_password")
        return True

    except Exception as e:
        log.error("email.send_failed", to=to_email, error=str(e))
        return False
