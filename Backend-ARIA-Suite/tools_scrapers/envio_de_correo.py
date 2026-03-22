import smtplib
from email.message import EmailMessage
import mimetypes
import os


def enviar_correo(
    gmail_user: str,
    gmail_app_password: str,
    nombre_remitente: str,
    destinatario_nombre: str,
    destinatario_correo: str,
    mensaje: str,
    ruta_adjunto: str = None,
) -> dict:
    """
    Envía un correo electrónico usando las credenciales proporcionadas por el usuario
    desde el frontend. Retorna un dict con 'success' (bool) y 'message' (str).
    """
    try:
        email = EmailMessage()
        email["From"] = f'"{nombre_remitente}" <{gmail_user}>'
        email["To"] = destinatario_correo
        email["Subject"] = f"Mensaje de {nombre_remitente}"

        cuerpo_completo = f"{mensaje}\n\nSaludos cordiales,\n{nombre_remitente}"
        email.set_content(cuerpo_completo)

        adjunto_incluido = False
        if ruta_adjunto and os.path.exists(ruta_adjunto):
            ctype, _ = mimetypes.guess_type(ruta_adjunto)
            if ctype is None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(ruta_adjunto, "rb") as fp:
                email.add_attachment(
                    fp.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=os.path.basename(ruta_adjunto),
                )
            adjunto_incluido = True
            print(f"--- Adjuntando archivo: {ruta_adjunto} ---")
        elif ruta_adjunto:
            print(f"--- Advertencia: No se encontró el archivo en la ruta: {ruta_adjunto} ---")

        with smtplib.SMTP_SSL("smtp.gmail.com") as smtp:
            smtp.login(gmail_user, gmail_app_password)
            smtp.send_message(email)

        if ruta_adjunto and not adjunto_incluido:
            return {
                "success": True,
                "message": f"Correo enviado a {destinatario_correo}, pero NO se pudo adjuntar el archivo (no encontrado).",
            }
        elif adjunto_incluido:
            return {
                "success": True,
                "message": f"Correo enviado exitosamente a {destinatario_correo} con adjunto.",
            }
        else:
            return {
                "success": True,
                "message": f"Correo enviado exitosamente a {destinatario_correo}.",
            }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Credenciales incorrectas. Verifica tu Gmail y la contraseña de aplicación.",
        }
    except Exception as e:
        return {"success": False, "message": f"Error al enviar el correo: {e}"}
