from django.core.management.base import BaseCommand
from tienda.models import MarcaVehiculo, ModeloVehiculo

class Command(BaseCommand):
    help = 'Poblar la base de datos con marcas y modelos de vehículos de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Poblando base de datos con vehículos...'))

        # Marcas de vehículos populares en Chile
        marcas_data = [
            {'nombre': 'Toyota', 'pais_origen': 'Japón'},
            {'nombre': 'Chevrolet', 'pais_origen': 'Estados Unidos'},
            {'nombre': 'Hyundai', 'pais_origen': 'Corea del Sur'},
            {'nombre': 'Kia', 'pais_origen': 'Corea del Sur'},
            {'nombre': 'Nissan', 'pais_origen': 'Japón'},
            {'nombre': 'Ford', 'pais_origen': 'Estados Unidos'},
            {'nombre': 'Mazda', 'pais_origen': 'Japón'},
            {'nombre': 'Honda', 'pais_origen': 'Japón'},
            {'nombre': 'Suzuki', 'pais_origen': 'Japón'},
            {'nombre': 'Mitsubishi', 'pais_origen': 'Japón'},
            {'nombre': 'Peugeot', 'pais_origen': 'Francia'},
            {'nombre': 'Renault', 'pais_origen': 'Francia'},
            {'nombre': 'Volkswagen', 'pais_origen': 'Alemania'},
            {'nombre': 'Subaru', 'pais_origen': 'Japón'},
        ]

        # Crear marcas
        marcas_creadas = {}
        for marca_data in marcas_data:
            marca, created = MarcaVehiculo.objects.get_or_create(
                nombre=marca_data['nombre'],
                defaults={'pais_origen': marca_data['pais_origen']}
            )
            marcas_creadas[marca.nombre] = marca
            if created:
                self.stdout.write(f'✓ Marca creada: {marca.nombre}')
            else:
                self.stdout.write(f'• Marca existente: {marca.nombre}')

        # Modelos por marca
        modelos_data = {
            'Toyota': [
                {'nombre': 'Corolla', 'año_inicio': 2000, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'Yaris', 'año_inicio': 2005, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.3L', 'combustible': 'gasolina'},
                {'nombre': 'RAV4', 'año_inicio': 2010, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'Hilux', 'año_inicio': 2005, 'año_fin': None, 'tipo_vehiculo': 'pickup', 'cilindrada': '2.4L', 'combustible': 'diesel'},
                {'nombre': 'Prius', 'año_inicio': 2010, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.8L', 'combustible': 'hibrido'},
                {'nombre': 'Etios', 'año_inicio': 2012, 'año_fin': 2020, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.5L', 'combustible': 'gasolina'},
            ],
            'Chevrolet': [
                {'nombre': 'Aveo', 'año_inicio': 2005, 'año_fin': 2018, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.4L', 'combustible': 'gasolina'},
                {'nombre': 'Spark', 'año_inicio': 2010, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.0L', 'combustible': 'gasolina'},
                {'nombre': 'Captiva', 'año_inicio': 2008, 'año_fin': 2018, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'diesel'},
                {'nombre': 'Tracker', 'año_inicio': 2020, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '1.2L', 'combustible': 'gasolina'},
                {'nombre': 'Sail', 'año_inicio': 2014, 'año_fin': 2020, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.4L', 'combustible': 'gasolina'},
            ],
            'Hyundai': [
                {'nombre': 'Accent', 'año_inicio': 2000, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.4L', 'combustible': 'gasolina'},
                {'nombre': 'Grand i10', 'año_inicio': 2014, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.2L', 'combustible': 'gasolina'},
                {'nombre': 'Tucson', 'año_inicio': 2010, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'Elantra', 'año_inicio': 2012, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'Santa Fe', 'año_inicio': 2013, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.2L', 'combustible': 'diesel'},
            ],
            'Kia': [
                {'nombre': 'Rio', 'año_inicio': 2012, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.4L', 'combustible': 'gasolina'},
                {'nombre': 'Cerato', 'año_inicio': 2013, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'Sportage', 'año_inicio': 2016, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'Morning', 'año_inicio': 2011, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.0L', 'combustible': 'gasolina'},
                {'nombre': 'Sorento', 'año_inicio': 2015, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.2L', 'combustible': 'diesel'},
            ],
            'Nissan': [
                {'nombre': 'Versa', 'año_inicio': 2012, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'March', 'año_inicio': 2011, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'X-Trail', 'año_inicio': 2014, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.5L', 'combustible': 'gasolina'},
                {'nombre': 'Sentra', 'año_inicio': 2013, 'año_fin': None, 'tipo_vehiculo': 'sedan', 'cilindrada': '1.8L', 'combustible': 'gasolina'},
                {'nombre': 'Kicks', 'año_inicio': 2017, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
            ],
            'Ford': [
                {'nombre': 'Fiesta', 'año_inicio': 2011, 'año_fin': 2019, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'Focus', 'año_inicio': 2012, 'año_fin': 2019, 'tipo_vehiculo': 'hatchback', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'EcoSport', 'año_inicio': 2013, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '1.5L', 'combustible': 'gasolina'},
                {'nombre': 'Ranger', 'año_inicio': 2012, 'año_fin': None, 'tipo_vehiculo': 'pickup', 'cilindrada': '2.2L', 'combustible': 'diesel'},
                {'nombre': 'Edge', 'año_inicio': 2015, 'año_fin': 2020, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
            ],
            'Mazda': [
                {'nombre': 'Mazda2', 'año_inicio': 2011, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.5L', 'combustible': 'gasolina'},
                {'nombre': 'Mazda3', 'año_inicio': 2014, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'CX-5', 'año_inicio': 2013, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
                {'nombre': 'BT-50', 'año_inicio': 2012, 'año_fin': None, 'tipo_vehiculo': 'pickup', 'cilindrada': '2.2L', 'combustible': 'diesel'},
                {'nombre': 'CX-3', 'año_inicio': 2016, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '2.0L', 'combustible': 'gasolina'},
            ],
            'Suzuki': [
                {'nombre': 'Swift', 'año_inicio': 2005, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.2L', 'combustible': 'gasolina'},
                {'nombre': 'Alto', 'año_inicio': 2010, 'año_fin': None, 'tipo_vehiculo': 'hatchback', 'cilindrada': '0.8L', 'combustible': 'gasolina'},
                {'nombre': 'Vitara', 'año_inicio': 2016, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
                {'nombre': 'Jimny', 'año_inicio': 2019, 'año_fin': None, 'tipo_vehiculo': 'suv', 'cilindrada': '1.5L', 'combustible': 'gasolina'},
                {'nombre': 'SX4', 'año_inicio': 2007, 'año_fin': 2014, 'tipo_vehiculo': 'hatchback', 'cilindrada': '1.6L', 'combustible': 'gasolina'},
            ],
        }

        # Crear modelos
        total_modelos = 0
        for marca_nombre, modelos in modelos_data.items():
            if marca_nombre in marcas_creadas:
                marca = marcas_creadas[marca_nombre]
                for modelo_data in modelos:
                    modelo, created = ModeloVehiculo.objects.get_or_create(
                        marca_vehiculo=marca,
                        nombre=modelo_data['nombre'],
                        año_inicio=modelo_data['año_inicio'],
                        defaults={
                            'año_fin': modelo_data['año_fin'],
                            'tipo_vehiculo': modelo_data['tipo_vehiculo'],
                            'cilindrada': modelo_data['cilindrada'],
                            'combustible': modelo_data['combustible']
                        }
                    )
                    if created:
                        self.stdout.write(f'  ✓ Modelo creado: {marca.nombre} {modelo.nombre}')
                        total_modelos += 1
                    else:
                        self.stdout.write(f'  • Modelo existente: {marca.nombre} {modelo.nombre}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Población completada!\n'
                f'• Marcas: {len(marcas_creadas)}\n'
                f'• Modelos nuevos: {total_modelos}\n'
                f'• Total modelos en BD: {ModeloVehiculo.objects.count()}'
            )
        )
