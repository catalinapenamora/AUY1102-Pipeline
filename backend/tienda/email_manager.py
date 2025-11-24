"""
Sistema de envío de emails para AutoParts
==========================================

Este módulo maneja el envío de emails con comprobantes PDF adjuntos.
"""

import os
import logging
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class EmailManager:
    """Gestor de emails para envío de comprobantes"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ventas@autoparts.cl')
    
    def enviar_comprobante_email(self, pedido, cliente_email, pdf_path, numero_comprobante):
        """
        Envía un email con el comprobante PDF adjunto
        
        Args:
            pedido: Objeto Pedido de Django
            cliente_email: Email del cliente
            pdf_path: Ruta al archivo PDF
            numero_comprobante: Número del comprobante
        
        Returns:
            dict: {'success': bool, 'message': str, 'error': str}
        """
        try:
            # Validar que el archivo PDF existe
            if not os.path.exists(pdf_path):
                logger.error(f"PDF no encontrado: {pdf_path}")
                return {
                    'success': False,
                    'error': 'Archivo PDF no encontrado'
                }
            
            # Datos para el template del email
            # Obtener nombre real del cliente
            nombre_cliente = "Cliente"  # Valor por defecto
            try:
                # Si tenemos un User asociado al email
                from django.contrib.auth.models import User
                user_obj = User.objects.filter(email=cliente_email).first()
                if user_obj:
                    if user_obj.first_name and user_obj.last_name:
                        nombre_cliente = f"{user_obj.first_name} {user_obj.last_name}"
                    elif user_obj.first_name:
                        nombre_cliente = user_obj.first_name
                    else:
                        nombre_cliente = user_obj.username
            except Exception as e:
                logger.warning(f"No se pudo obtener nombre del cliente: {e}")
            
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
            
            # Crear el contenido HTML del email
            html_content = self.generar_template_email(context)
            text_content = strip_tags(html_content)
            
            # Asunto del email
            subject = f"🧾 Tu comprobante de compra #{numero_comprobante} - AutoParts Chile"
            
            # Crear el email
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=self.from_email,
                to=[cliente_email],
                reply_to=['soporte@autoparts.cl']
            )
            email.content_subtype = "html"  # Para enviar HTML
            
            # Adjuntar el PDF
            with open(pdf_path, 'rb') as pdf_file:
                email.attach(
                    filename=f'comprobante_{numero_comprobante}.pdf',
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
            
            # Enviar el email
            email.send()
            
            logger.info(f"✅ Comprobante enviado por email a {cliente_email}")
            return {
                'success': True,
                'message': f'Comprobante enviado exitosamente a {cliente_email}'
            }
            
        except FileNotFoundError:
            logger.error(f"Archivo PDF no encontrado: {pdf_path}")
            return {
                'success': False,
                'error': 'Archivo PDF no encontrado'
            }
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return {
                'success': False,
                'error': f'Error enviando email: {str(e)}'
            }
    
    def generar_template_email(self, context):
        """Genera el contenido HTML del email"""
        html_template = f"""
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
        .button {{
            display: inline-block;
            background-color: #2c5aa0;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧾 Comprobante de Compra</h1>
        <h2>AutoParts</h2>
    </div>
    
    <div class="content">
        <h3>¡Gracias por tu compra en AutoParts!</h3>
        
        <p>Hola <strong>{context['nombre_cliente']}</strong>,</p>
        
        <p>¡Tu pedido ha sido procesado exitosamente! 🎉</p>
        
        <p>Hemos preparado tu comprobante de compra y lo encontrarás adjunto en formato PDF. Este documento incluye todos los detalles de tu pedido y puede ser usado para garantías y reclamos.</p>
        
        <div class="highlight">
            <strong>📋 Resumen de tu pedido:</strong><br>
            <strong>Número de Comprobante:</strong> {context['numero_comprobante']}<br>
            <strong>Código de Pedido:</strong> {context['order_id']}<br>
            <strong>💰 Total pagado:</strong> ${context['monto']:,}<br>
            <strong>📧 Email de contacto:</strong> {context['cliente_email']}
        </div>
        
        <p><strong>📎 Documento adjunto:</strong> comprobante_{context['numero_comprobante']}.pdf</p>
        
        <h4>🚚 ¿Qué sigue ahora?</h4>
        <p>• Tu pedido será procesado en las próximas 24-48 horas<br>
        • Recibirás un email de confirmación cuando tu pedido sea despachado<br>
        • Podrás rastrear tu envío usando el código que te enviaremos</p>
        
        <h4>💬 ¿Necesitas ayuda?</h4>
        <p>Nuestro equipo está listo para ayudarte:</p>
        <ul>
            <li>📧 Email: {context['soporte_email']}</li>
            <li>🕒 Horario de atención: Lunes a Viernes, 9:00 - 18:00 hrs</li>
            <li>📱 WhatsApp: +56 9 1234 5678 (próximamente)</li>
        </ul>
        
        <p><strong>¡Gracias por confiar en AutoParts para tus repuestos automotrices! 🚗</strong></p>
    </div>
    
    <div class="footer">
        <p>
            📧 Este es un email automático, por favor no responder directamente.<br>
            Para consultas, escribir a: {context['soporte_email']}<br><br>
            <strong>🚗 AutoParts Chile</strong> - Tu tienda de confianza para repuestos automotrices<br>
            📍 Santiago, Chile | 🌐 www.autoparts.cl<br>
            💬 Síguenos en redes sociales para ofertas exclusivas
        </p>
    </div>
</body>
</html>
        """
        return html_template
    
    def enviar_email_notificacion_admin(self, pedido, error_msg=None):
        """Envía notificación al admin cuando hay problemas con el envío"""
        try:
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@autoparts.cl')
            
            if error_msg:
                subject = f"Error enviando comprobante - Pedido {pedido.order_id}"
                message = f"""
Error enviando comprobante por email:

Pedido: {pedido.order_id}
Cliente: {pedido.email}
Monto: ${pedido.monto}
Error: {error_msg}

Por favor revisar y enviar manualmente.
                """
            else:
                subject = f"Comprobante enviado exitosamente - Pedido {pedido.order_id}"
                message = f"""
Comprobante enviado exitosamente:

Pedido: {pedido.order_id}
Cliente: {pedido.email}
Monto: ${pedido.monto}
                """
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=self.from_email,
                to=[admin_email]
            )
            email.send()
            
        except Exception as e:
            logger.error(f"Error enviando notificación a admin: {e}")
    
    def enviar_email_simple(self, destinatario, asunto, mensaje_html):
        """
        Envía un email simple sin adjuntos
        
        Args:
            destinatario: Email del destinatario
            asunto: Asunto del email
            mensaje_html: Contenido HTML del email
        
        Returns:
            bool: True si se envió correctamente, False si no
        """
        try:
            email = EmailMessage(
                subject=asunto,
                body=mensaje_html,
                from_email=self.from_email,
                to=[destinatario],
            )
            email.content_subtype = 'html'
            resultado = email.send()
            
            logger.info(f"Email simple enviado a {destinatario}")
            return resultado > 0
            
        except Exception as e:
            logger.error(f"Error enviando email simple: {e}")
            return False

# Instancia global para usar en otras partes del código
email_manager = EmailManager()

def enviar_comprobante_automatico(pedido, pdf_path, numero_comprobante):
    """
    Función de conveniencia para enviar comprobante automáticamente
    """
    resultado = email_manager.enviar_comprobante_email(
        pedido=pedido,
        cliente_email=pedido.email,
        pdf_path=pdf_path,
        numero_comprobante=numero_comprobante
    )
    
    # Notificar al admin del resultado
    if resultado['success']:
        email_manager.enviar_email_notificacion_admin(pedido)
    else:
        email_manager.enviar_email_notificacion_admin(pedido, resultado.get('error'))
    
    return resultado
