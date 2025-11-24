"""
Sistema de facturación electrónica para Chile
Soporte para LibreDTE (SII válido) y comprobantes PDF simples
"""
import requests
import logging
from django.conf import settings
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

# Configuración de LibreDTE (Chile - SII)
LIBREDTE_CONFIG = {
    'api_url': 'https://libredte.cl/api/',
    'api_token': getattr(settings, 'LIBREDTE_API_TOKEN', ''),
    'rut_empresa': getattr(settings, 'LIBREDTE_RUT_EMPRESA', ''),
    'test_mode': getattr(settings, 'LIBREDTE_TEST_MODE', True),
    'enabled': getattr(settings, 'LIBREDTE_ENABLED', False),  # Deshabilitado por defecto
}

class TributiAPI:
    """Cliente para la API de Tributi"""
    
    def __init__(self):
        self.api_key = TRIBUTI_CONFIG['api_key']
        self.base_url = TRIBUTI_CONFIG['api_url_test'] if TRIBUTI_CONFIG['test_mode'] else TRIBUTI_CONFIG['api_url']
        self.rut_empresa = TRIBUTI_CONFIG['rut_empresa']
        
        if not self.api_key:
            logger.warning("⚠️ API Key de Tributi no configurada")
    
    def _make_request(self, endpoint, method='GET', data=None):
        """Realizar petición a la API de Tributi"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en API Tributi: {e}")
            raise Exception(f"Error conectando con Tributi: {str(e)}")
    
    def crear_factura_electronica(self, pedido, productos, cliente_data):
        """
        Crear factura electrónica en Tributi
        """
        try:
            # Determinar tipo de documento
            # 33 = Factura Electrónica, 39 = Boleta Electrónica
            tipo_documento = 39  # Boleta por defecto para personas naturales
            
            # Si es empresa, usar factura
            if cliente_data.get('rut_empresa') or cliente_data.get('es_empresa'):
                tipo_documento = 33
            
            # Preparar items de la factura
            items = []
            for producto in productos:
                # Calcular valores con IVA incluido (Chile)
                precio_unitario = float(producto['precio'])
                cantidad = int(producto['cantidad'])
                subtotal_item = precio_unitario * cantidad
                
                # IVA 19% en Chile
                iva_item = round(subtotal_item * 0.19, 0)
                neto_item = subtotal_item - iva_item
                
                items.append({
                    "nombre": producto['producto'][:80],  # Máximo 80 caracteres
                    "descripcion": f"Autopartes - {producto['producto']}",
                    "cantidad": cantidad,
                    "precio_unitario": int(neto_item / cantidad),  # Precio neto unitario
                    "total_item": int(subtotal_item)
                })
            
            # Calcular totales
            total_bruto = float(pedido.monto)
            iva_total = round(total_bruto * 0.19, 0)
            neto_total = total_bruto - iva_total
            
            # Datos del documento
            documento_data = {
                "tipo_documento": tipo_documento,
                "numero_documento": None,  # Tributi asigna automáticamente
                "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "fecha_vencimiento": datetime.now().strftime("%Y-%m-%d"),
                
                # Emisor (tu empresa)
                "emisor": {
                    "rut": self.rut_empresa,
                    "razon_social": "Bastian AutoParts",
                    "direccion": "Tu dirección comercial",
                    "comuna": "Tu comuna",
                    "ciudad": "Tu ciudad"
                },
                
                # Receptor (cliente)
                "receptor": {
                    "rut": cliente_data.get('rut', '66666666-6'),  # RUT genérico si no hay
                    "razon_social": cliente_data.get('nombre', 'Cliente'),
                    "direccion": pedido.direccion or 'Sin dirección',
                    "comuna": pedido.comuna or 'Sin comuna',
                    "ciudad": pedido.region or 'Sin región',
                    "email": pedido.email
                },
                
                # Totales
                "neto": int(neto_total),
                "iva": int(iva_total),
                "total": int(total_bruto),
                
                # Items
                "items": items,
                
                # Referencias adicionales
                "referencia": f"Pedido #{pedido.order_id}",
                "observaciones": f"Compra realizada en Bastian AutoParts - Pedido: {pedido.order_id}"
            }
            
            logger.info(f"📄 Creando documento electrónico tipo {tipo_documento} para pedido {pedido.order_id}")
            
            # Enviar a Tributi
            response = self._make_request('documentos', 'POST', documento_data)
            
            logger.info(f"✅ Documento creado exitosamente: {response}")
            
            return {
                'success': True,
                'numero_documento': response.get('numero'),
                'folio': response.get('folio'),
                'pdf_url': response.get('pdf_url'),
                'xml_url': response.get('xml_url'),
                'estado_sii': response.get('estado_sii'),
                'tipo_documento': tipo_documento,
                'tributi_id': response.get('id')
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando factura en Tributi: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_estado_documento(self, tributi_id):
        """Consultar estado de un documento en el SII"""
        try:
            response = self._make_request(f'documentos/{tributi_id}')
            return {
                'success': True,
                'estado_sii': response.get('estado_sii'),
                'numero_documento': response.get('numero'),
                'pdf_url': response.get('pdf_url')
            }
        except Exception as e:
            logger.error(f"❌ Error consultando estado: {e}")
            return {'success': False, 'error': str(e)}

def generar_factura_automatica(pedido, productos, cliente_data=None):
    """
    Función principal para generar factura después del pago
    """
    try:
        # Datos del cliente por defecto
        if not cliente_data:
            cliente_data = {
                'nombre': 'Cliente AutoParts',
                'rut': '66666666-6',  # RUT genérico
                'email': pedido.email,
                'es_empresa': False
            }
        
        # Inicializar API de Tributi
        tributi = TributiAPI()
        
        # Crear documento electrónico
        resultado = tributi.crear_factura_electronica(pedido, productos, cliente_data)
        
        if resultado['success']:
            # Actualizar pedido con datos de facturación
            pedido.numero_factura = resultado.get('numero_documento')
            pedido.folio_factura = resultado.get('folio')
            pedido.pdf_factura_url = resultado.get('pdf_url')
            pedido.tributi_id = resultado.get('tributi_id')
            pedido.estado_factura = 'generada'
            pedido.save()
            
            logger.info(f"✅ Factura generada para pedido {pedido.order_id}: {resultado.get('numero_documento')}")
            
            return resultado
        else:
            logger.error(f"❌ Falló la generación de factura: {resultado.get('error')}")
            return resultado
            
    except Exception as e:
        logger.error(f"❌ Error en generar_factura_automatica: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def enviar_factura_por_email(pedido, pdf_url):
    """
    Enviar factura por email al cliente
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        asunto = f"Factura AutoParts - Pedido #{pedido.order_id}"
        mensaje = f"""
        Estimado/a cliente,
        
        Adjunto encontrará la factura de su compra en Bastian AutoParts.
        
        Detalles:
        - Pedido: #{pedido.order_id}
        - Monto: ${pedido.monto:,}
        - Fecha: {pedido.created_at.strftime('%d/%m/%Y')}
        
        Puede descargar su factura desde: {pdf_url}
        
        ¡Gracias por su compra!
        
        Equipo Bastian AutoParts
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [pedido.email],
            fail_silently=False,
        )
        
        logger.info(f"📧 Factura enviada por email a {pedido.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email: {e}")
        return False

# Función de fallback - Factura simple en PDF
def generar_factura_simple_pdf(pedido, productos):
    """
    Genera una factura simple en PDF usando ReportLab
    (Para casos donde Tributi no esté disponible)
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        import os
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("BASTIAN AUTOPARTS", title_style))
        story.append(Paragraph("COMPROBANTE DE COMPRA", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Información del pedido
        info_data = [
            ['Pedido #:', pedido.order_id],
            ['Fecha:', datetime.now().strftime('%d/%m/%Y')],
            ['Cliente:', pedido.email],
            ['Total:', f"${pedido.monto:,}"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Tabla de productos
        productos_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
        
        for producto in productos:
            productos_data.append([
                producto['producto'],
                str(producto['cantidad']),
                f"${producto['precio']:,}",
                f"${producto['subtotal']:,}"
            ])
        
        productos_table = Table(productos_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        productos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(productos_table)
        story.append(Spacer(1, 30))
        
        # Total
        story.append(Paragraph(f"<b>TOTAL: ${pedido.monto:,}</b>", styles['Heading2']))
        
        # Construir PDF
        doc.build(story)
        
        # Guardar archivo
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Guardar en media
        filename = f"factura_{pedido.order_id}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'facturas', filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        # URL del archivo
        pdf_url = f"{settings.MEDIA_URL}facturas/{filename}"
        
        return {
            'success': True,
            'pdf_url': pdf_url,
            'filepath': filepath,
            'tipo': 'comprobante_simple'
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando PDF simple: {e}")
        return {
            'success': False,
            'error': str(e)
        }
