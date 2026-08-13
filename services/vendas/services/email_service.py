"""
Serviço de envio de email via SMTP.
Usado para enviar credenciais de conta criada durante checkout.
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import structlog

from config import settings

log = structlog.get_logger()


def _loja_login_url(empresa_slug: str | None) -> str:
    """URL de login da loja do tenant; sem slug, cai na raiz do site."""
    if empresa_slug:
        return f"{settings.FRONTEND_URL}/c/{empresa_slug}/login"
    return settings.FRONTEND_URL


def _build_welcome_email_html(email: str, senha_temporaria: str, empresa_nome: str, login_url: str) -> str:
    """Monta o HTML do email de boas-vindas com credenciais."""
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Conta Criada - {empresa_nome}</title>
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
                {empresa_nome.upper()}
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <p style="margin:0 0 8px;font-size:22px;font-weight:600;color:#e5e7eb;">
                🎉 Bem-vindo(a)!
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:#94a3b8;line-height:1.6;">
                Sua conta foi criada com sucesso! Agora você pode acompanhar seus pedidos e fazer novas compras.
              </p>

              <!-- Credenciais -->
              <table cellpadding="0" cellspacing="0" width="100%"
                     style="background:rgba(59,130,246,0.08);
                            border:1px solid rgba(59,130,246,0.2);
                            border-radius:8px;margin:0 0 24px;">
                <tr>
                  <td style="padding:20px;">
                    <p style="margin:0 0 12px;font-size:14px;color:#94a3b8;font-weight:600;">
                      Suas credenciais de acesso:
                    </p>
                    <p style="margin:0 0 8px;font-size:14px;color:#e5e7eb;">
                      <strong style="color:#3b82f6;">Email:</strong> {email}
                    </p>
                    <p style="margin:0;font-size:14px;color:#e5e7eb;">
                      <strong style="color:#3b82f6;">Senha temporária:</strong> {senha_temporaria}
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px;font-size:15px;color:#94a3b8;line-height:1.6;">
                Recomendamos que você altere sua senha no primeiro acesso para maior segurança.
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
                <tr>
                  <td align="center"
                      style="background:linear-gradient(135deg,#3b82f6 0%,#8b5cf6 100%);
                             border-radius:8px;">
                    <a href="{login_url}"
                       style="display:inline-block;padding:14px 36px;
                              font-size:15px;font-weight:600;color:#ffffff;
                              text-decoration:none;letter-spacing:0.3px;">
                      Acessar Minha Conta
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Warning -->
              <table cellpadding="0" cellspacing="0" width="100%"
                     style="background:rgba(245,158,11,0.08);
                            border:1px solid rgba(245,158,11,0.2);
                            border-radius:8px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <p style="margin:0;font-size:13px;color:#fbbf24;line-height:1.5;">
                      🔒 Mantenha suas credenciais seguras e não compartilhe com terceiros.
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


async def enviar_email_credenciais(
    to_email: str,
    senha_temporaria: str,
    empresa_nome: str = "Loja Online",
    empresa_slug: str | None = None
) -> bool:
    """
    Envia email com credenciais de acesso para conta recém-criada.

    Args:
        to_email: Email do destinatário
        senha_temporaria: Senha temporária gerada
        empresa_nome: Nome da empresa/loja
        empresa_slug: Slug da loja (monta o link /c/{slug}/login)

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    login_url = _loja_login_url(empresa_slug)
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.warning("email.smtp_not_configured", message="SMTP não configurado, email não será enviado")
        return False

    # Montar mensagem
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Conta Criada - {empresa_nome}"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    # Versão texto simples (fallback)
    text_body = (
        f"Bem-vindo(a)!\n\n"
        f"Sua conta foi criada com sucesso em {empresa_nome}.\n\n"
        f"Suas credenciais de acesso:\n"
        f"Email: {to_email}\n"
        f"Senha temporária: {senha_temporaria}\n\n"
        f"Recomendamos que você altere sua senha no primeiro acesso.\n\n"
        f"Acesse: {login_url}\n\n"
        f"Runas ERP"
    )

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_welcome_email_html(to_email, senha_temporaria, empresa_nome, login_url), "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        log.info("email.sent", to=to_email, type="welcome_credentials")
        return True

    except Exception as e:
        log.error("email.send_failed", to=to_email, error=str(e))
        return False
