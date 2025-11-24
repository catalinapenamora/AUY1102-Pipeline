"""
Sistema de Facturación Simple - Sin APIs Externas
================================================

Este módulo genera comprobantes PDF básicos sin necesidad de APIs externas.
Perfecto para desarrollo y testing.
"""

import os
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("ReportLab no está instalado. PDFs no estarán disponibles.")
    REPORTLAB_AVAILABLE = False

class ComprobanteSimple:
    """Generador de comprobantes PDF simple"""
    
    def __init__(self):
        self.empresa_data = {
            'nombre': 'Autoparts',
            'rut': '77.777.777-7',
            'direccion': 'Santiago, Chile',
            'telefono': '+56 9 1234 5678',
            'email': 'ventas@autoparts.cl',
            'giro': 'Venta de partes y accesorios para vehículos'
        }

    def generar_comprobante(self, pedido, productos, cliente_data, perfil_usuario=None):
        """Generar comprobante PDF simple"""
        
        if not REPORTLAB_AVAILABLE:
            return {
                'success': False,
                'error': 'ReportLab no está disponible. Instala con: pip install reportlab'
            }
        
        try:
            # Crear nombre del archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comprobante_{pedido.order_id}_{timestamp}.pdf"
            filepath = os.path.join('facturas', filename)
            
            # Crear directorio si no existe
            full_path = os.path.join(settings.MEDIA_ROOT, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Crear PDF
            doc = SimpleDocTemplate(full_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("COMPROBANTE DE COMPRA", title_style))
            story.append(Spacer(1, 20))
            
            # Datos de la empresa
            empresa_text = f"""
            <b>{self.empresa_data['nombre']}</b><br/>
            RUT: {self.empresa_data['rut']}<br/>
            {self.empresa_data['direccion']}<br/>
            Tel: {self.empresa_data['telefono']}<br/>
            Email: {self.empresa_data['email']}
            """
            story.append(Paragraph(empresa_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Información del comprobante
            numero_comp = f"COMP-{timestamp}"
            fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            info_text = f"""
            <b>Número de Comprobante:</b> {numero_comp}<br/>
            <b>Fecha de Emisión:</b> {fecha_actual}<br/>
            <b>Order ID:</b> {pedido.order_id}<br/>
            <b>Email Cliente:</b> {cliente_data.get('email', 'No especificado')}
            """
            story.append(Paragraph(info_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Datos del cliente
            # Obtener datos del perfil de usuario o usar datos proporcionados
            if perfil_usuario:
                nombre_cliente = perfil_usuario.user.username
                rut_cliente = perfil_usuario.rut if perfil_usuario.rut else 'Sin RUT'
                email_cliente = perfil_usuario.user.email
            else:
                nombre_cliente = cliente_data.get('nombre', 'Cliente sin nombre')
                rut_cliente = cliente_data.get('rut', 'Sin RUT')
                email_cliente = cliente_data.get('email', 'Sin email')
            
            cliente_text = f"""
            <b>DATOS DEL CLIENTE:</b><br/>
            Nombre: {nombre_cliente}<br/>
            RUT: {rut_cliente}<br/>
            Email: {email_cliente}
            """
            
            # Agregar dirección si existe
            if hasattr(pedido, 'direccion') and pedido.direccion:
                cliente_text += f"<br/>Dirección: {pedido.direccion}"
            if hasattr(pedido, 'comuna') and pedido.comuna:
                cliente_text += f"<br/>Comuna: {pedido.comuna}"
            if hasattr(pedido, 'region') and pedido.region:
                cliente_text += f"<br/>Región: {pedido.region}"
                
            story.append(Paragraph(cliente_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Tabla de productos
            data = [['Producto', 'Cant.', 'Precio Unit.', 'Subtotal']]
            
            total_sin_iva = 0
            for prod in productos:
                nombre = prod.get('producto', 'Sin nombre')
                cantidad = prod.get('cantidad', 0)
                precio = prod.get('precio', 0)
                subtotal = prod.get('subtotal', precio * cantidad)
                
                data.append([
                    nombre[:30],
                    str(cantidad),
                    f"${precio:,.0f}".replace(",", "."),
                    f"${subtotal:,.0f}".replace(",", ".")
                ])
                total_sin_iva += subtotal
            
            # Calcular IVA y total
            neto = round(total_sin_iva / 1.19)
            iva  = total_sin_iva - neto
            costo_envio = getattr(pedido, 'costo_envio', 0)
            total_final = total_sin_iva + costo_envio

            # 2) Añade filas de Neto, IVA, Envío (si corresponde) y Total
            data.append(['', '', 'Subtotal (neto):', f"${neto:,.0f}".replace(",", ".")])
            data.append(['', '', 'IVA (19%):',      f"${iva:,.0f}".replace(",", ".")])
            if costo_envio > 0:
                data.append(['', '', 'Envío:', f"${costo_envio:,.0f}".replace(",", ".")])
            data.append(['', '', 'Total:', f"${total_final:,.0f}".replace(",", ".")])
            # Crear tabla
            table = Table(data, colWidths=[4*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Cuerpo
                ('BACKGROUND', (0, 1), (-1, -4), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -4), 9),
                
                # Totales
                ('BACKGROUND', (0, -3), (-1, -1), colors.beige),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -3), (-1, -1), 10),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Información adicional del pedido
            if hasattr(pedido, 'envio_domicilio') and pedido.envio_domicilio:
                envio_text = "<b>INFORMACIÓN DE ENVÍO:</b><br/>Envío a domicilio solicitado"
                if hasattr(pedido, 'ot_codigo') and pedido.ot_codigo:
                    envio_text += f"<br/>Código de seguimiento: {pedido.ot_codigo}"
                story.append(Paragraph(envio_text, styles['Normal']))
                story.append(Spacer(1, 15))
            elif hasattr(pedido, 'retiro_en_tienda') and pedido.retiro_en_tienda:
                story.append(Paragraph("<b>MODALIDAD:</b> Retiro en tienda", styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Nota legal
            nota_text = """
            <b>IMPORTANTE:</b><br/>
            Este es un comprobante de compra para efectos internos.<br/>
            Para solicitar factura electrónica válida, contactar con soporte.<br/>
            <br/>
            <b>Gracias por su compra!</b>
            """
            story.append(Paragraph(nota_text, styles['Normal']))
            
            # Generar el PDF
            doc.build(story)
            
            # URL del archivo
            pdf_url = f"{settings.MEDIA_URL}{filepath}"
            
            logger.info(f"Comprobante generado: {pdf_url}")
            
            return {
                'success': True,
                'numero_documento': numero_comp,
                'pdf_url': pdf_url,
                'pdf_path': filepath
            }
            
        except Exception as e:
            logger.error(f"Error generando comprobante: {e}")
            return {
                'success': False,
                'error': f"Error al generar PDF: {str(e)}"
            }

# Funciones de conveniencia
def generar_factura_automatica(pedido, productos, cliente_data, perfil_usuario=None, enviar_email=True):
    """Función principal para generar comprobante automáticamente"""
    comprobante = ComprobanteSimple()
    resultado = comprobante.generar_comprobante(pedido, productos, cliente_data, perfil_usuario)
    
    # Si se generó exitosamente y se solicita envío por email
    if resultado.get('success') and enviar_email:
        try:
            from .email_manager_hibrido import enviar_comprobante_automatico
            import os
            
            # Construir ruta completa al PDF
            pdf_path = os.path.join(settings.MEDIA_ROOT, resultado.get('pdf_path', ''))
            numero_comprobante = resultado.get('numero_documento', 'Sin número')
            
            # Enviar email
            resultado_email = enviar_comprobante_automatico(
                pedido=pedido,
                pdf_path=pdf_path,
                numero_comprobante=numero_comprobante
            )
            
            # Agregar información del email al resultado
            resultado['email_enviado'] = resultado_email.get('success', False)
            resultado['email_mensaje'] = resultado_email.get('message', resultado_email.get('error', ''))
            
            if resultado_email.get('success'):
                logger.info(f"✅ Comprobante y email enviados para pedido {pedido.order_id}")
            else:
                logger.warning(f"⚠️ Comprobante generado pero email falló para pedido {pedido.order_id}: {resultado_email.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando email para pedido {pedido.order_id}: {e}")
            resultado['email_enviado'] = False
            resultado['email_mensaje'] = f"Error enviando email: {str(e)}"
    
    return resultado

def enviar_factura_por_email(pedido, pdf_url):
    """Enviar comprobante por email usando el nuevo sistema"""
    try:
        from .email_manager_hibrido import enviar_comprobante_automatico
        import os
        
        # Construir ruta del archivo desde URL
        if pdf_url.startswith(settings.MEDIA_URL):
            pdf_path = pdf_url.replace(settings.MEDIA_URL, settings.MEDIA_ROOT + '/')
        else:
            pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_url)
        
        # Extraer número de comprobante del nombre del archivo
        numero_comprobante = f"COMP-{pedido.order_id}"
        
        resultado = enviar_comprobante_automatico(
            pedido=pedido,
            pdf_path=pdf_path,
            numero_comprobante=numero_comprobante
        )
        
        return resultado.get('success', False)
        
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False
