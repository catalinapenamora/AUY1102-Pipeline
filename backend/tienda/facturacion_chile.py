"""
Sistema de Facturación para Chile - Solución Realista
==================================================

OPCIONES IMPLEMENTADAS:
1. ✅ Comprobantes PDF (Gratis, inmediato)
2. 🔄 Preparado para LibreDTE ($40k/mes)
3. 🔄 Preparado para Nubox (cotizar)

PROCESO RECOMENDADO:
1. Empezar con PDFs para validar el negocio
2. Cuando tengas volumen, integrar LibreDTE o Nubox
3. Migración gradual sin romper nada
"""
import logging
from django.conf import settings
from datetime import datetime
import os
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.units import inch
logger = logging.getLogger(__name__)

# ===================================
# CONFIGURACIÓN
# ===================================

FACTURACION_CONFIG = {
    # Modo actual (cambiar cuando integres API real)
    'modo': 'pdf_simple',  # Opciones: 'pdf_simple', 'libredte', 'nubox'
    
    # Datos de tu empresa
    'rut_empresa': getattr(settings, 'RUT_EMPRESA', '76.123.456-7'),
    'nombre_empresa': getattr(settings, 'NOMBRE_EMPRESA', 'Bastian AutoParts'),
    'direccion_empresa': getattr(settings, 'DIRECCION_EMPRESA', 'Santiago, Chile'),
    'telefono_empresa': getattr(settings, 'TELEFONO_EMPRESA', '+56 9 1234 5678'),
    'email_empresa': getattr(settings, 'EMAIL_EMPRESA', 'contacto@autoparts.cl'),
    
    # APIs futuras (agregar cuando las contrates)
    'libredte_api_key': getattr(settings, 'LIBREDTE_API_KEY', ''),
    'libredte_rut': getattr(settings, 'LIBREDTE_RUT_EMPRESA', ''),
    'nubox_api_key': getattr(settings, 'NUBOX_API_KEY', ''),
}

# ===================================
# CLASE PRINCIPAL
# ===================================

class SistemaFacturacion:
    """Sistema de facturación híbrido para Chile"""
    
    def __init__(self):
        self.config = FACTURACION_CONFIG
        self.modo = self.config['modo']
    
    def generar_documento(self, pedido, productos, cliente_data=None):
        """
        Genera un documento de compra (comprobante o factura)
        """
        try:
            if self.modo == 'pdf_simple':
                return self._generar_comprobante_pdf(pedido, productos, cliente_data)
            elif self.modo == 'libredte':
                return self._generar_factura_libredte(pedido, productos, cliente_data)
            elif self.modo == 'nubox':
                return self._generar_factura_nubox(pedido, productos, cliente_data)
            else:
                raise ValueError(f"Modo {self.modo} no soportado")
                
        except Exception as e:
            logger.error(f"Error generando documento: {e}")
            # Fallback a PDF simple en caso de error
            return self._generar_comprobante_pdf(pedido, productos, cliente_data)
    
    def _generar_comprobante_pdf(self, pedido, productos, cliente_data):
        """
        Genera comprobante PDF simple (GRATIS)
        """

        # 2) Obtén costo de envío si lo tienes en el objeto `pedido`
        costo_envio = getattr(pedido, 'costo_envio', 0)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from io import BytesIO
            
            # Crear buffer para el PDF
            buffer = BytesIO()
            
            # Crear documento
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # ===== ENCABEZADO =====
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=20,
                alignment=1,  # Center
                textColor=colors.darkblue
            )
            
            story.append(Paragraph(self.config['nombre_empresa'].upper(), title_style))
            
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=14,
                spaceAfter=30,
                alignment=1,
                textColor=colors.grey
            )
            story.append(Paragraph("COMPROBANTE DE COMPRA", subtitle_style))
            story.append(Paragraph(f"RUT: {self.config['rut_empresa']}", subtitle_style))
            story.append(Spacer(1, 20))
            
            # ===== INFORMACIÓN DEL PEDIDO =====
            info_data = [
                ['Número de Comprobante:', f"CP-{pedido.order_id}"],
                ['Fecha de Emisión:', datetime.now().strftime('%d/%m/%Y %H:%M')],
                ['Cliente:', cliente_data.get('email', pedido.email) if cliente_data else pedido.email],
                ['Orden de Compra:', pedido.order_id],
                ['Tipo de Entrega:', 'Retiro en tienda' if pedido.retiro_en_tienda else 'Envío a domicilio'],
            ]
            
            if pedido.envio_domicilio and pedido.direccion:
                info_data.append(['Dirección de Envío:', f"{pedido.direccion}, {pedido.comuna}"])
            
            info_table = Table(info_data, colWidths=[2.5*inch, 3.5*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
          # ===== TABLA DE PRODUCTOS =====
            productos_data = [['Código', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
            total_general = 0

            for i, producto in enumerate(productos, 1):
                subtotal = producto.get('subtotal', producto['precio'] * producto['cantidad'])
                total_general += subtotal
                productos_data.append([
                    f"PROD-{i:03d}",
                    producto['producto'][:35],
                    str(producto['cantidad']),
                    f"${producto['precio']:,.0f}",
                    f"${subtotal:,.0f}"
                ])

            productos_table = Table(productos_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
            productos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(productos_table)
            story.append(Spacer(1, 20))


            # ==== TABLA DE TOTALES ====
            # 1) Cálculo de neto e IVA
            neto        = round(total_general / 1.19)
            iva         = total_general - neto
            costo_envio = getattr(pedido, 'costo_envio', 0)

            # 2) Matriz de filas para la tabla
            totales_data = [
                [
                Paragraph('<b>Subtotal:</b>', styles['Normal']),
                Paragraph(f'<b>${neto:,.0f}</b>', styles['Normal'])
                ],
                [
                Paragraph('<b>IVA (19%):</b>', styles['Normal']),
                Paragraph(f'<b>${iva:,.0f}</b>', styles['Normal'])
                ]
            ]
            if costo_envio:
                totales_data.append([
                Paragraph('<b>Envío:</b>', styles['Normal']),
                Paragraph(f'<b>${costo_envio:,.0f}</b>', styles['Normal'])
                ])

            gran_total = total_general + costo_envio
            totales_data.append([
            Paragraph('<b>Total:</b>', styles['Normal']),
            Paragraph(f'<b>${gran_total:,.0f}</b>', styles['Normal'])
            ])

            # 3) Construye y añade la tabla
            tabla_totales = Table(totales_data, colWidths=[4*inch, 2*inch], hAlign='RIGHT')
            tabla_totales.setStyle(TableStyle([
            ('ALIGN',(1,0),(1,-1),'RIGHT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ]))
            story.append(tabla_totales)
            story.append(Spacer(1, 30))


            
            # ===== PIE DE PÁGINA =====
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                alignment=1,  # Center
                textColor=colors.grey
            )
            
            story.append(Paragraph("─" * 80, footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>{self.config['nombre_empresa']}</b>", footer_style))
            story.append(Paragraph(f"RUT: {self.config['rut_empresa']}", footer_style))
            story.append(Paragraph(f"Dirección: {self.config['direccion_empresa']}", footer_style))
            story.append(Paragraph(f"Teléfono: {self.config['telefono_empresa']}", footer_style))
            story.append(Paragraph(f"Email: {self.config['email_empresa']}", footer_style))
            story.append(Spacer(1, 20))
            
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=1,
                textColor=colors.red
            )
            story.append(Paragraph(
                "<i>ESTE ES UN COMPROBANTE INTERNO - NO ES UN DOCUMENTO TRIBUTARIO VÁLIDO</i>",
                disclaimer_style
            ))
            story.append(Paragraph(
                "<i>Para facturas válidas SII, contacte a nuestro equipo comercial</i>",
                disclaimer_style
            ))
            
            # Construir PDF
            doc.build(story)
            
            # Guardar archivo
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Crear directorio si no existe
            filename = f"comprobante_{pedido.order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, 'comprobantes', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            # URL del archivo
            pdf_url = f"{settings.MEDIA_URL}comprobantes/{filename}"
            
            logger.info(f"✅ Comprobante PDF generado: {filename}")
            
            return {
                'success': True,
                'tipo': 'comprobante_pdf',
                'numero_documento': f"CP-{pedido.order_id}",
                'pdf_url': pdf_url,
                'filepath': filepath,
                'mensaje': 'Comprobante PDF generado exitosamente'
            }
            
        except ImportError:
            logger.error("❌ ReportLab no instalado. Instalar con: pip install reportlab")
            return {
                'success': False,
                'error': 'ReportLab no está instalado'
            }
        except Exception as e:
            logger.error(f"❌ Error generando PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generar_factura_libredte(self, pedido, productos, cliente_data):
        """
        Genera factura usando LibreDTE API ($40k/mes)
        TODO: Implementar cuando contrates LibreDTE
        """
        logger.info("🔄 LibreDTE no implementado aún. Usando PDF simple.")
        return self._generar_comprobante_pdf(pedido, productos, cliente_data)
    
    def _generar_factura_nubox(self, pedido, productos, cliente_data):
        """
        Genera factura usando Nubox API (cotizar precio)
        TODO: Implementar cuando contrates Nubox
        """
        logger.info("🔄 Nubox no implementado aún. Usando PDF simple.")
        return self._generar_comprobante_pdf(pedido, productos, cliente_data)

# ===================================
# FUNCIONES PÚBLICAS
# ===================================

def generar_factura_automatica(pedido, productos, cliente_data=None):
    """
    Función principal para generar factura/comprobante después del pago
    """
    try:
        sistema = SistemaFacturacion()
        resultado = sistema.generar_documento(pedido, productos, cliente_data)
        
        if resultado['success']:
            # Actualizar pedido con datos del documento
            from .models import Factura
            
            # Crear o actualizar registro de factura
            factura_data = {
                'tipo_documento': 999,  # Código interno para comprobante
                'numero_factura': resultado.get('numero_documento'),
                'rut_cliente': cliente_data.get('rut', '66666666-6') if cliente_data else '66666666-6',
                'nombre_cliente': cliente_data.get('nombre', pedido.email) if cliente_data else pedido.email,
                'email_cliente': pedido.email,
                'direccion_cliente': pedido.direccion or 'Sin dirección',
                'neto': int(float(pedido.monto) / 1.19),  # Aproximado
                'iva': int(float(pedido.monto) - (float(pedido.monto) / 1.19)),
                'total': int(pedido.monto),
                'estado': 'generada',
                'pdf_url': resultado.get('pdf_url'),
            }
            
            factura, created = Factura.objects.get_or_create(
                pedido=pedido,
                defaults=factura_data
            )
            
            if not created:
                # Actualizar factura existente
                for key, value in factura_data.items():
                    setattr(factura, key, value)
                factura.save()
            
            logger.info(f"✅ Documento generado para pedido {pedido.order_id}")
            
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en generar_factura_automatica: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def enviar_factura_por_email(pedido, pdf_url):
    """
    Enviar comprobante por email al cliente
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        asunto = f"Comprobante AutoParts - Pedido #{pedido.order_id}"
        mensaje = f"""
        Estimado/a cliente,
        
        Adjunto encontrará el comprobante de su compra en Bastian AutoParts.
        
        Detalles de la compra:
        - Pedido: #{pedido.order_id}
        - Monto: ${pedido.monto:,} CLP
        - Fecha: {pedido.fecha.strftime('%d/%m/%Y %H:%M') if hasattr(pedido, 'fecha') else 'N/A'}
        
        Puede descargar su comprobante desde: {pdf_url}
        
        IMPORTANTE: Este es un comprobante interno, no un documento tributario válido.
        Si necesita factura válida SII, contáctenos.
        
        ¡Gracias por su compra!
        
        Equipo Bastian AutoParts
        Teléfono: {FACTURACION_CONFIG['telefono_empresa']}
        Email: {FACTURACION_CONFIG['email_empresa']}
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [pedido.email],
            fail_silently=False,
        )
        
        logger.info(f"📧 Comprobante enviado por email a {pedido.email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email: {e}")
        return False

# ===================================
# PLAN DE MIGRACIÓN A API REAL
# ===================================

"""
CUANDO QUIERAS MIGRAR A LIBREDTE O NUBOX:

1. Contratar el servicio (LibreDTE $40k/mes o Nubox a cotizar)

2. Cambiar configuración en settings.py:
   LIBREDTE_API_KEY = 'tu_api_key'
   LIBREDTE_RUT_EMPRESA = '76123456-7'
   
3. Cambiar modo en facturacion.py:
   'modo': 'libredte'  # o 'nubox'

4. Implementar las funciones _generar_factura_libredte() o _generar_factura_nubox()

5. Los comprobantes anteriores siguen funcionando
   Los nuevos documentos serán válidos SII

6. Migración gradual sin romper nada existente
"""
