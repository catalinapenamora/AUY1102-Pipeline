"""
Sistema de envío de emails híbrido para AutoParts
=================================================

Este módulo maneja el envío de emails de forma híbrida:
- Desarrollo: Muestra en consola + opción manual Gmail
- Producción: Envío automático Gmail
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class EmailManagerHibrido:
    """Gestor híbrido de emails con fallback"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ventas@autoparts.cl')
        self.gmail_user = 'ventas.autoparts.2025@gmail.com'
        self.gmail_password = 'bqwn zcgy wyft sejj'
    
    def enviar_comprobante_email(self, pedido, cliente_email, pdf_path, numero_comprobante):
        """
        Envía email híbrido: consola + opción Gmail manual
        """
        try:
            # Obtener datos del cliente
            nombre_cliente = self._obtener_nombre_cliente(cliente_email)
            
            context = {
                'nombre_cliente': nombre_cliente,
                'numero_comprobante': numero_comprobante,
                'order_id': pedido.order_id,
                'monto': pedido.monto,
                'fecha': pedido.created_at if hasattr(pedido, 'created_at') else 'Fecha no disponible',
                'cliente_email': cliente_email,
                'empresa_nombre': 'AutoParts',
                'empresa_url': 'https://autoparts.cl',
                'soporte_email': 'soporte@autoparts.cl'
            }
            
            # Generar contenido
            html_content = self._generar_template_email(context)
            subject = f"🧾 Tu comprobante de compra #{numero_comprobante} - AutoParts Chile"
            
            # 1. Enviar por Django (consola)
            resultado_consola = self._enviar_django(subject, html_content, cliente_email, pdf_path, numero_comprobante)
            
            # 2. Mostrar instrucciones para Gmail manual
            self._mostrar_instrucciones_gmail(cliente_email, subject, pdf_path)
            
            # 3. Intentar Gmail directo (opcional)
            resultado_gmail = self._intentar_gmail_directo(subject, html_content, cliente_email, pdf_path, numero_comprobante)
            
            return {
                'success': True,
                'message': f'Email procesado para {cliente_email}',
                'consola': resultado_consola,
                'gmail': resultado_gmail
            }
            
        except Exception as e:
            logger.error(f"Error en email híbrido: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _obtener_nombre_cliente(self, cliente_email):
        """Obtiene el nombre real del cliente"""
        try:
            from django.contrib.auth.models import User
            user_obj = User.objects.filter(email=cliente_email).first()
            if user_obj:
                if user_obj.first_name and user_obj.last_name:
                    return f"{user_obj.first_name} {user_obj.last_name}"
                elif user_obj.first_name:
                    return user_obj.first_name
                else:
                    return user_obj.username
        except Exception as e:
            logger.warning(f"No se pudo obtener nombre: {e}")
        return "Cliente"
    
    def _enviar_django(self, subject, html_content, cliente_email, pdf_path, numero_comprobante):
        """Enviar usando Django (aparece en consola)"""
        try:
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=self.from_email,
                to=[cliente_email],
            )
            email.content_subtype = "html"
            
            # Adjuntar PDF si existe
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    email.attach(
                        filename=f'comprobante_{numero_comprobante}.pdf',
                        content=pdf_file.read(),
                        mimetype='application/pdf'
                    )
            
            email.send()
            return True
        except Exception as e:
            logger.error(f"Error Django email: {e}")
            return False
    
    def _mostrar_instrucciones_gmail(self, cliente_email, subject, pdf_path):
        """Muestra instrucciones para envío manual"""
        print("\n" + "="*60)
        print("📧 INSTRUCCIONES PARA ENVÍO MANUAL POR GMAIL")
        print("="*60)
        print(f"Para: {cliente_email}")
        print(f"Asunto: {subject}")
        print(f"PDF: {pdf_path}")
        print("\n🔹 Opción 1: Usar Gmail web")
        print("1. Ve a gmail.com e inicia sesión con ventas.autoparts.2025@gmail.com")
        print("2. Crea un nuevo email")
        print(f"3. Destinatario: {cliente_email}")
        print(f"4. Asunto: {subject}")
        print("5. Adjunta el PDF desde la ruta mostrada arriba")
        print("\n🔹 Opción 2: Ejecutar script automático")
        print("python enviar_gmail_manual.py")
        print("="*60 + "\n")
    
    def _intentar_gmail_directo(self, subject, html_content, cliente_email, pdf_path, numero_comprobante):
        """Intenta enviar directamente por Gmail (puede fallar por SSL)"""
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.gmail_user
            msg['To'] = cliente_email
            
            # Agregar contenido HTML
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Adjuntar PDF
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_attach = MIMEApplication(pdf_file.read(), _subtype='pdf')
                    pdf_attach.add_header('Content-Disposition', 'attachment', 
                                        filename=f'comprobante_{numero_comprobante}.pdf')
                    msg.attach(pdf_attach)
            
            # Enviar
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ EMAIL GMAIL ENVIADO EXITOSAMENTE A {cliente_email}")
            return True
            
        except Exception as e:
            print(f"⚠️ Gmail directo falló (normal en Windows): {e}")
            return False
    
    def _generar_template_email(self, context):
        """Genera el contenido HTML del email"""
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprobante de Compra - AutoParts</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #2c5aa0;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .footer {{
            background-color: #e9ecef;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-radius: 0 0 8px 8px;
        }}
        .highlight {{
            background-color: #fff;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #2c5aa0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧾 Comprobante de Compra</h1>
        <h2>AutoParts Chile</h2>
    </div>
    
    <div class="content">
        <h3>¡Gracias por tu compra en AutoParts!</h3>
        
        <p>Hola <strong>{context['nombre_cliente']}</strong>,</p>
        
        <p>¡Tu pedido ha sido procesado exitosamente! 🎉</p>
        
        <div class="highlight">
            <strong>📋 Resumen de tu pedido:</strong><br>
            <strong>Número de Comprobante:</strong> {context['numero_comprobante']}<br>
            <strong>Código de Pedido:</strong> {context['order_id']}<br>
            <strong>💰 Total pagado:</strong> ${context['monto']:,}<br>
            <strong>📧 Email:</strong> {context['cliente_email']}
        </div>
        
        <p><strong>📎 Documento adjunto:</strong> comprobante_{context['numero_comprobante']}.pdf</p>
        
        <h4>🚚 Próximos pasos:</h4>
        <p>• Tu pedido será procesado en 24-48 horas<br>
        • Recibirás confirmación de despacho<br>
        • Podrás rastrear tu envío</p>
        
        <h4>💬 Contacto:</h4>
        <p>📧 {context['soporte_email']}<br>
        🕒 Lun-Vie 9:00-18:00</p>
        
        <p><strong>¡Gracias por confiar en AutoParts! 🚗</strong></p>
    </div>
    
    <div class="footer">
        <p>
            <strong>🚗 AutoParts Chile</strong><br>
            📍 Santiago, Chile | 🌐 www.autoparts.cl
        </p>
    </div>
</body>
</html>
        """

# Crear instancia global
email_manager_hibrido = EmailManagerHibrido()

def enviar_comprobante_automatico(pedido, pdf_path, numero_comprobante):
    """Función de conveniencia para usar en facturacion_simple.py"""
    return email_manager_hibrido.enviar_comprobante_email(
        pedido=pedido,
        cliente_email=pedido.email,
        pdf_path=pdf_path,
        numero_comprobante=numero_comprobante
    )
