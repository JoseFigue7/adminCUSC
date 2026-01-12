"""
Comando para poblar los catálogos SEP con datos básicos
"""
from django.core.management.base import BaseCommand
from students.models import (
    Pais, EntidadFederativa, Idioma, NecesidadEducativaEspecial,
    AntecedenteAcademico, NivelEducativo, ModalidadEducativa, Turno
)


class Command(BaseCommand):
    help = 'Pobla los catálogos SEP con datos básicos requeridos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Poblando catálogos SEP...'))
        
        # Países de Latinoamérica y Estados Unidos (México primero)
        paises_data = [
            # México (prioritario)
            {'codigo': 'MX', 'nombre': 'México'},
            
            # Estados Unidos (incluido por solicitud)
            {'codigo': 'US', 'nombre': 'Estados Unidos'},
            
            # América Central
            {'codigo': 'BZ', 'nombre': 'Belice'},
            {'codigo': 'CR', 'nombre': 'Costa Rica'},
            {'codigo': 'SV', 'nombre': 'El Salvador'},
            {'codigo': 'GT', 'nombre': 'Guatemala'},
            {'codigo': 'HN', 'nombre': 'Honduras'},
            {'codigo': 'NI', 'nombre': 'Nicaragua'},
            {'codigo': 'PA', 'nombre': 'Panamá'},
            
            # Caribe
            {'codigo': 'AG', 'nombre': 'Antigua y Barbuda'},
            {'codigo': 'BS', 'nombre': 'Bahamas'},
            {'codigo': 'BB', 'nombre': 'Barbados'},
            {'codigo': 'CU', 'nombre': 'Cuba'},
            {'codigo': 'DM', 'nombre': 'Dominica'},
            {'codigo': 'DO', 'nombre': 'República Dominicana'},
            {'codigo': 'GD', 'nombre': 'Granada'},
            {'codigo': 'HT', 'nombre': 'Haití'},
            {'codigo': 'JM', 'nombre': 'Jamaica'},
            {'codigo': 'KN', 'nombre': 'San Cristóbal y Nieves'},
            {'codigo': 'LC', 'nombre': 'Santa Lucía'},
            {'codigo': 'VC', 'nombre': 'San Vicente y las Granadinas'},
            {'codigo': 'TT', 'nombre': 'Trinidad y Tobago'},
            
            # América del Sur
            {'codigo': 'AR', 'nombre': 'Argentina'},
            {'codigo': 'BO', 'nombre': 'Bolivia'},
            {'codigo': 'BR', 'nombre': 'Brasil'},
            {'codigo': 'CL', 'nombre': 'Chile'},
            {'codigo': 'CO', 'nombre': 'Colombia'},
            {'codigo': 'EC', 'nombre': 'Ecuador'},
            {'codigo': 'GY', 'nombre': 'Guyana'},
            {'codigo': 'PY', 'nombre': 'Paraguay'},
            {'codigo': 'PE', 'nombre': 'Perú'},
            {'codigo': 'SR', 'nombre': 'Surinam'},
            {'codigo': 'UY', 'nombre': 'Uruguay'},
            {'codigo': 'VE', 'nombre': 'Venezuela'},
        ]
        
        # Crear países y obtener diccionario para relacionar con entidades
        paises_dict = {}
        for pais_data in paises_data:
            pais, created = Pais.objects.get_or_create(
                codigo=pais_data['codigo'],
                defaults={'nombre': pais_data['nombre']}
            )
            paises_dict[pais_data['codigo']] = pais
        
        self.stdout.write(self.style.SUCCESS(f'✓ Países creados: {len(paises_data)}'))
        
        # Entidades Federativas / Estados / Ciudades por país
        # México - Estados (32 estados)
        entidades_mexico = [
            {'codigo': 'AG', 'nombre': 'Aguascalientes'},
            {'codigo': 'BC', 'nombre': 'Baja California'},
            {'codigo': 'BS', 'nombre': 'Baja California Sur'},
            {'codigo': 'CM', 'nombre': 'Campeche'},
            {'codigo': 'CS', 'nombre': 'Chiapas'},
            {'codigo': 'CH', 'nombre': 'Chihuahua'},
            {'codigo': 'CO', 'nombre': 'Coahuila'},
            {'codigo': 'CL', 'nombre': 'Colima'},
            {'codigo': 'DF', 'nombre': 'Ciudad de México'},
            {'codigo': 'DG', 'nombre': 'Durango'},
            {'codigo': 'GT', 'nombre': 'Guanajuato'},
            {'codigo': 'GR', 'nombre': 'Guerrero'},
            {'codigo': 'HG', 'nombre': 'Hidalgo'},
            {'codigo': 'JA', 'nombre': 'Jalisco'},
            {'codigo': 'MX', 'nombre': 'Estado de México'},
            {'codigo': 'MI', 'nombre': 'Michoacán'},
            {'codigo': 'MO', 'nombre': 'Morelos'},
            {'codigo': 'NA', 'nombre': 'Nayarit'},
            {'codigo': 'NL', 'nombre': 'Nuevo León'},
            {'codigo': 'OA', 'nombre': 'Oaxaca'},
            {'codigo': 'PU', 'nombre': 'Puebla'},
            {'codigo': 'QT', 'nombre': 'Querétaro'},
            {'codigo': 'QR', 'nombre': 'Quintana Roo'},
            {'codigo': 'SL', 'nombre': 'San Luis Potosí'},
            {'codigo': 'SI', 'nombre': 'Sinaloa'},
            {'codigo': 'SO', 'nombre': 'Sonora'},
            {'codigo': 'TB', 'nombre': 'Tabasco'},
            {'codigo': 'TM', 'nombre': 'Tamaulipas'},
            {'codigo': 'TL', 'nombre': 'Tlaxcala'},
            {'codigo': 'VE', 'nombre': 'Veracruz'},
            {'codigo': 'YU', 'nombre': 'Yucatán'},
            {'codigo': 'ZA', 'nombre': 'Zacatecas'},
        ]
        
        # Estados Unidos - Estados principales (50 estados principales)
        entidades_usa = [
            {'codigo': 'AL', 'nombre': 'Alabama'}, {'codigo': 'AK', 'nombre': 'Alaska'}, {'codigo': 'AZ', 'nombre': 'Arizona'},
            {'codigo': 'AR', 'nombre': 'Arkansas'}, {'codigo': 'CA', 'nombre': 'California'}, {'codigo': 'CO', 'nombre': 'Colorado'},
            {'codigo': 'CT', 'nombre': 'Connecticut'}, {'codigo': 'DE', 'nombre': 'Delaware'}, {'codigo': 'FL', 'nombre': 'Florida'},
            {'codigo': 'GA', 'nombre': 'Georgia'}, {'codigo': 'HI', 'nombre': 'Hawaii'}, {'codigo': 'ID', 'nombre': 'Idaho'},
            {'codigo': 'IL', 'nombre': 'Illinois'}, {'codigo': 'IN', 'nombre': 'Indiana'}, {'codigo': 'IA', 'nombre': 'Iowa'},
            {'codigo': 'KS', 'nombre': 'Kansas'}, {'codigo': 'KY', 'nombre': 'Kentucky'}, {'codigo': 'LA', 'nombre': 'Louisiana'},
            {'codigo': 'ME', 'nombre': 'Maine'}, {'codigo': 'MD', 'nombre': 'Maryland'}, {'codigo': 'MA', 'nombre': 'Massachusetts'},
            {'codigo': 'MI', 'nombre': 'Michigan'}, {'codigo': 'MN', 'nombre': 'Minnesota'}, {'codigo': 'MS', 'nombre': 'Mississippi'},
            {'codigo': 'MO', 'nombre': 'Missouri'}, {'codigo': 'MT', 'nombre': 'Montana'}, {'codigo': 'NE', 'nombre': 'Nebraska'},
            {'codigo': 'NV', 'nombre': 'Nevada'}, {'codigo': 'NH', 'nombre': 'New Hampshire'}, {'codigo': 'NJ', 'nombre': 'New Jersey'},
            {'codigo': 'NM', 'nombre': 'New Mexico'}, {'codigo': 'NY', 'nombre': 'New York'}, {'codigo': 'NC', 'nombre': 'North Carolina'},
            {'codigo': 'ND', 'nombre': 'North Dakota'}, {'codigo': 'OH', 'nombre': 'Ohio'}, {'codigo': 'OK', 'nombre': 'Oklahoma'},
            {'codigo': 'OR', 'nombre': 'Oregon'}, {'codigo': 'PA', 'nombre': 'Pennsylvania'}, {'codigo': 'RI', 'nombre': 'Rhode Island'},
            {'codigo': 'SC', 'nombre': 'South Carolina'}, {'codigo': 'SD', 'nombre': 'South Dakota'}, {'codigo': 'TN', 'nombre': 'Tennessee'},
            {'codigo': 'TX', 'nombre': 'Texas'}, {'codigo': 'UT', 'nombre': 'Utah'}, {'codigo': 'VT', 'nombre': 'Vermont'},
            {'codigo': 'VA', 'nombre': 'Virginia'}, {'codigo': 'WA', 'nombre': 'Washington'}, {'codigo': 'WV', 'nombre': 'West Virginia'},
            {'codigo': 'WI', 'nombre': 'Wisconsin'}, {'codigo': 'WY', 'nombre': 'Wyoming'}, {'codigo': 'DC', 'nombre': 'District of Columbia'},
        ]
        
        # Guatemala - Departamentos principales
        entidades_guatemala = [
            {'codigo': 'GT-01', 'nombre': 'Alta Verapaz'}, {'codigo': 'GT-02', 'nombre': 'Baja Verapaz'}, {'codigo': 'GT-03', 'nombre': 'Chimaltenango'},
            {'codigo': 'GT-04', 'nombre': 'Chiquimula'}, {'codigo': 'GT-05', 'nombre': 'El Progreso'}, {'codigo': 'GT-06', 'nombre': 'Escuintla'},
            {'codigo': 'GT-07', 'nombre': 'Guatemala'}, {'codigo': 'GT-08', 'nombre': 'Huehuetenango'}, {'codigo': 'GT-09', 'nombre': 'Izabal'},
            {'codigo': 'GT-10', 'nombre': 'Jalapa'}, {'codigo': 'GT-11', 'nombre': 'Jutiapa'}, {'codigo': 'GT-12', 'nombre': 'Petén'},
            {'codigo': 'GT-13', 'nombre': 'Quetzaltenango'}, {'codigo': 'GT-14', 'nombre': 'Quiché'}, {'codigo': 'GT-15', 'nombre': 'Retalhuleu'},
            {'codigo': 'GT-16', 'nombre': 'Sacatepéquez'}, {'codigo': 'GT-17', 'nombre': 'San Marcos'}, {'codigo': 'GT-18', 'nombre': 'Santa Rosa'},
            {'codigo': 'GT-19', 'nombre': 'Sololá'}, {'codigo': 'GT-20', 'nombre': 'Suchitepéquez'}, {'codigo': 'GT-21', 'nombre': 'Totonicapán'},
            {'codigo': 'GT-22', 'nombre': 'Zacapa'},
        ]
        
        # Colombia - Departamentos principales
        entidades_colombia = [
            {'codigo': 'CO-01', 'nombre': 'Amazonas'}, {'codigo': 'CO-02', 'nombre': 'Antioquia'}, {'codigo': 'CO-03', 'nombre': 'Arauca'},
            {'codigo': 'CO-04', 'nombre': 'Atlántico'}, {'codigo': 'CO-05', 'nombre': 'Bolívar'}, {'codigo': 'CO-06', 'nombre': 'Boyacá'},
            {'codigo': 'CO-07', 'nombre': 'Caldas'}, {'codigo': 'CO-08', 'nombre': 'Caquetá'}, {'codigo': 'CO-09', 'nombre': 'Casanare'},
            {'codigo': 'CO-10', 'nombre': 'Cauca'}, {'codigo': 'CO-11', 'nombre': 'Cesar'}, {'codigo': 'CO-12', 'nombre': 'Chocó'},
            {'codigo': 'CO-13', 'nombre': 'Córdoba'}, {'codigo': 'CO-14', 'nombre': 'Cundinamarca'}, {'codigo': 'CO-15', 'nombre': 'Guainía'},
            {'codigo': 'CO-16', 'nombre': 'Guaviare'}, {'codigo': 'CO-17', 'nombre': 'Huila'}, {'codigo': 'CO-18', 'nombre': 'La Guajira'},
            {'codigo': 'CO-19', 'nombre': 'Magdalena'}, {'codigo': 'CO-20', 'nombre': 'Meta'}, {'codigo': 'CO-21', 'nombre': 'Nariño'},
            {'codigo': 'CO-22', 'nombre': 'Norte de Santander'}, {'codigo': 'CO-23', 'nombre': 'Putumayo'}, {'codigo': 'CO-24', 'nombre': 'Quindío'},
            {'codigo': 'CO-25', 'nombre': 'Risaralda'}, {'codigo': 'CO-26', 'nombre': 'San Andrés y Providencia'}, {'codigo': 'CO-27', 'nombre': 'Santander'},
            {'codigo': 'CO-28', 'nombre': 'Sucre'}, {'codigo': 'CO-29', 'nombre': 'Tolima'}, {'codigo': 'CO-30', 'nombre': 'Valle del Cauca'},
            {'codigo': 'CO-31', 'nombre': 'Vaupés'}, {'codigo': 'CO-32', 'nombre': 'Vichada'},
        ]
        
        # Argentina - Provincias principales
        entidades_argentina = [
            {'codigo': 'AR-01', 'nombre': 'Buenos Aires'}, {'codigo': 'AR-02', 'nombre': 'Catamarca'}, {'codigo': 'AR-03', 'nombre': 'Chaco'},
            {'codigo': 'AR-04', 'nombre': 'Chubut'}, {'codigo': 'AR-05', 'nombre': 'Córdoba'}, {'codigo': 'AR-06', 'nombre': 'Corrientes'},
            {'codigo': 'AR-07', 'nombre': 'Entre Ríos'}, {'codigo': 'AR-08', 'nombre': 'Formosa'}, {'codigo': 'AR-09', 'nombre': 'Jujuy'},
            {'codigo': 'AR-10', 'nombre': 'La Pampa'}, {'codigo': 'AR-11', 'nombre': 'La Rioja'}, {'codigo': 'AR-12', 'nombre': 'Mendoza'},
            {'codigo': 'AR-13', 'nombre': 'Misiones'}, {'codigo': 'AR-14', 'nombre': 'Neuquén'}, {'codigo': 'AR-15', 'nombre': 'Río Negro'},
            {'codigo': 'AR-16', 'nombre': 'Salta'}, {'codigo': 'AR-17', 'nombre': 'San Juan'}, {'codigo': 'AR-18', 'nombre': 'San Luis'},
            {'codigo': 'AR-19', 'nombre': 'Santa Cruz'}, {'codigo': 'AR-20', 'nombre': 'Santa Fe'}, {'codigo': 'AR-21', 'nombre': 'Santiago del Estero'},
            {'codigo': 'AR-22', 'nombre': 'Tierra del Fuego'}, {'codigo': 'AR-23', 'nombre': 'Tucumán'}, {'codigo': 'AR-24', 'nombre': 'Ciudad Autónoma de Buenos Aires'},
        ]
        
        # Brasil - Estados principales (27 estados)
        entidades_brasil = [
            {'codigo': 'BR-AC', 'nombre': 'Acre'}, {'codigo': 'BR-AL', 'nombre': 'Alagoas'}, {'codigo': 'BR-AP', 'nombre': 'Amapá'},
            {'codigo': 'BR-AM', 'nombre': 'Amazonas'}, {'codigo': 'BR-BA', 'nombre': 'Bahía'}, {'codigo': 'BR-CE', 'nombre': 'Ceará'},
            {'codigo': 'BR-DF', 'nombre': 'Distrito Federal'}, {'codigo': 'BR-ES', 'nombre': 'Espírito Santo'}, {'codigo': 'BR-GO', 'nombre': 'Goiás'},
            {'codigo': 'BR-MA', 'nombre': 'Maranhão'}, {'codigo': 'BR-MT', 'nombre': 'Mato Grosso'}, {'codigo': 'BR-MS', 'nombre': 'Mato Grosso do Sul'},
            {'codigo': 'BR-MG', 'nombre': 'Minas Gerais'}, {'codigo': 'BR-PA', 'nombre': 'Pará'}, {'codigo': 'BR-PB', 'nombre': 'Paraíba'},
            {'codigo': 'BR-PR', 'nombre': 'Paraná'}, {'codigo': 'BR-PE', 'nombre': 'Pernambuco'}, {'codigo': 'BR-PI', 'nombre': 'Piauí'},
            {'codigo': 'BR-RJ', 'nombre': 'Río de Janeiro'}, {'codigo': 'BR-RN', 'nombre': 'Río Grande do Norte'}, {'codigo': 'BR-RS', 'nombre': 'Río Grande do Sul'},
            {'codigo': 'BR-RO', 'nombre': 'Rondônia'}, {'codigo': 'BR-RR', 'nombre': 'Roraima'}, {'codigo': 'BR-SC', 'nombre': 'Santa Catarina'},
            {'codigo': 'BR-SP', 'nombre': 'São Paulo'}, {'codigo': 'BR-SE', 'nombre': 'Sergipe'}, {'codigo': 'BR-TO', 'nombre': 'Tocantins'},
        ]
        
        # Chile - Regiones principales
        entidades_chile = [
            {'codigo': 'CL-01', 'nombre': 'Arica y Parinacota'}, {'codigo': 'CL-02', 'nombre': 'Tarapacá'}, {'codigo': 'CL-03', 'nombre': 'Antofagasta'},
            {'codigo': 'CL-04', 'nombre': 'Atacama'}, {'codigo': 'CL-05', 'nombre': 'Coquimbo'}, {'codigo': 'CL-06', 'nombre': 'Valparaíso'},
            {'codigo': 'CL-07', 'nombre': 'Metropolitana de Santiago'}, {'codigo': 'CL-08', 'nombre': "O'Higgins"}, {'codigo': 'CL-09', 'nombre': 'Maule'},
            {'codigo': 'CL-10', 'nombre': 'Ñuble'}, {'codigo': 'CL-11', 'nombre': 'Biobío'}, {'codigo': 'CL-12', 'nombre': 'Araucanía'},
            {'codigo': 'CL-13', 'nombre': 'Los Ríos'}, {'codigo': 'CL-14', 'nombre': 'Los Lagos'}, {'codigo': 'CL-15', 'nombre': 'Aysén'},
            {'codigo': 'CL-16', 'nombre': 'Magallanes y la Antártica Chilena'},
        ]
        
        # Perú - Departamentos principales
        entidades_peru = [
            {'codigo': 'PE-01', 'nombre': 'Amazonas'}, {'codigo': 'PE-02', 'nombre': 'Áncash'}, {'codigo': 'PE-03', 'nombre': 'Apurímac'},
            {'codigo': 'PE-04', 'nombre': 'Arequipa'}, {'codigo': 'PE-05', 'nombre': 'Ayacucho'}, {'codigo': 'PE-06', 'nombre': 'Cajamarca'},
            {'codigo': 'PE-07', 'nombre': 'Callao'}, {'codigo': 'PE-08', 'nombre': 'Cusco'}, {'codigo': 'PE-09', 'nombre': 'Huancavelica'},
            {'codigo': 'PE-10', 'nombre': 'Huánuco'}, {'codigo': 'PE-11', 'nombre': 'Ica'}, {'codigo': 'PE-12', 'nombre': 'Junín'},
            {'codigo': 'PE-13', 'nombre': 'La Libertad'}, {'codigo': 'PE-14', 'nombre': 'Lambayeque'}, {'codigo': 'PE-15', 'nombre': 'Lima'},
            {'codigo': 'PE-16', 'nombre': 'Loreto'}, {'codigo': 'PE-17', 'nombre': 'Madre de Dios'}, {'codigo': 'PE-18', 'nombre': 'Moquegua'},
            {'codigo': 'PE-19', 'nombre': 'Pasco'}, {'codigo': 'PE-20', 'nombre': 'Piura'}, {'codigo': 'PE-21', 'nombre': 'Puno'},
            {'codigo': 'PE-22', 'nombre': 'San Martín'}, {'codigo': 'PE-23', 'nombre': 'Tacna'}, {'codigo': 'PE-24', 'nombre': 'Tumbes'},
            {'codigo': 'PE-25', 'nombre': 'Ucayali'},
        ]
        
        # Crear entidades por país
        entidades_por_pais = [
            ('MX', entidades_mexico),
            ('US', entidades_usa),
            ('GT', entidades_guatemala),
            ('CO', entidades_colombia),
            ('AR', entidades_argentina),
            ('BR', entidades_brasil),
            ('CL', entidades_chile),
            ('PE', entidades_peru),
        ]
        
        total_entidades = 0
        entidades_creadas = 0
        entidades_actualizadas = 0
        
        for codigo_pais, entidades_list in entidades_por_pais:
            if codigo_pais not in paises_dict:
                self.stdout.write(self.style.WARNING(f'⚠ País {codigo_pais} no encontrado en el diccionario'))
                continue
                
            pais = paises_dict[codigo_pais]
            self.stdout.write(f'  Procesando {pais.nombre} ({len(entidades_list)} entidades)...')
            
            for entidad_data in entidades_list:
                entidad, created = EntidadFederativa.objects.get_or_create(
                    pais=pais,
                    codigo=entidad_data['codigo'],
                    defaults={'nombre': entidad_data['nombre']}
                )
                
                # Si ya existía pero el nombre cambió, actualizarlo
                if not created and entidad.nombre != entidad_data['nombre']:
                    entidad.nombre = entidad_data['nombre']
                    entidad.is_active = True
                    entidad.save()
                    entidades_actualizadas += 1
                elif created:
                    entidades_creadas += 1
                
                total_entidades += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Entidades Federativas / Estados / Ciudades procesadas: {total_entidades} '
            f'(Creadas: {entidades_creadas}, Actualizadas: {entidades_actualizadas})'
        ))
        
        # Idiomas
        idiomas_data = [
            {'codigo': 'ES', 'nombre': 'Español'},
            {'codigo': 'EN', 'nombre': 'Inglés'},
            {'codigo': 'FR', 'nombre': 'Francés'},
            {'codigo': 'DE', 'nombre': 'Alemán'},
            {'codigo': 'IT', 'nombre': 'Italiano'},
            {'codigo': 'PT', 'nombre': 'Portugués'},
            {'codigo': 'ZH', 'nombre': 'Chino'},
            {'codigo': 'JA', 'nombre': 'Japonés'},
            {'codigo': 'AR', 'nombre': 'Árabe'},
            {'codigo': 'RU', 'nombre': 'Ruso'},
            {'codigo': 'MAYA', 'nombre': 'Maya'},
            {'codigo': 'NAHU', 'nombre': 'Náhuatl'},
            {'codigo': 'MIX', 'nombre': 'Mixteco'},
            {'codigo': 'ZAP', 'nombre': 'Zapoteco'},
            {'codigo': 'OTO', 'nombre': 'Otomí'},
            {'codigo': 'TOT', 'nombre': 'Totonaco'},
        ]
        
        for idioma_data in idiomas_data:
            Idioma.objects.get_or_create(
                codigo=idioma_data['codigo'],
                defaults={'nombre': idioma_data['nombre']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Idiomas creados: {len(idiomas_data)}'))
        
        # Necesidades Educativas Especiales
        necesidades_data = [
            {'codigo': 'AUD', 'nombre': 'Discapacidad Auditiva', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'VIS', 'nombre': 'Discapacidad Visual', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'MOT', 'nombre': 'Discapacidad Motriz', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'INT', 'nombre': 'Discapacidad Intelectual', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'PSI', 'nombre': 'Discapacidad Psicosocial', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'MUL', 'nombre': 'Discapacidad Múltiple', 'tipo': 'DISCAPACIDAD'},
            {'codigo': 'APT', 'nombre': 'Aptitudes Sobresalientes', 'tipo': 'APTITUD_SOBRESALIENTE'},
            {'codigo': 'TAL', 'nombre': 'Talento Específico', 'tipo': 'APTITUD_SOBRESALIENTE'},
        ]
        
        for necesidad_data in necesidades_data:
            NecesidadEducativaEspecial.objects.get_or_create(
                codigo=necesidad_data['codigo'],
                defaults={
                    'nombre': necesidad_data['nombre'],
                    'tipo': necesidad_data['tipo']
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Necesidades Educativas Especiales creadas: {len(necesidades_data)}'))
        
        # Antecedentes Académicos
        antecedentes_data = [
            {'codigo': 'SEC', 'nombre': 'Secundaria'},
            {'codigo': 'PRE', 'nombre': 'Preparatoria'},
            {'codigo': 'BACH', 'nombre': 'Bachillerato'},
            {'codigo': 'COLL', 'nombre': 'Carrera Técnica o Comercial'},
            {'codigo': 'UNI', 'nombre': 'Universidad (incompleta)'},
            {'codigo': 'NONE', 'nombre': 'Sin antecedente académico'},
        ]
        
        for antecedente_data in antecedentes_data:
            AntecedenteAcademico.objects.get_or_create(
                codigo=antecedente_data['codigo'],
                defaults={'nombre': antecedente_data['nombre']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Antecedentes Académicos creados: {len(antecedentes_data)}'))
        
        # Niveles Educativos
        niveles_data = [
            {'codigo': 'LIC', 'nombre': 'Licenciatura'},
            {'codigo': 'ING', 'nombre': 'Ingeniería'},
            {'codigo': 'TEC', 'nombre': 'Técnico Superior'},
            {'codigo': 'MAE', 'nombre': 'Maestría'},
            {'codigo': 'DOC', 'nombre': 'Doctorado'},
        ]
        
        for nivel_data in niveles_data:
            NivelEducativo.objects.get_or_create(
                codigo=nivel_data['codigo'],
                defaults={'nombre': nivel_data['nombre']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Niveles Educativos creados: {len(niveles_data)}'))
        
        # Modalidades Educativas
        modalidades_data = [
            {'codigo': 'ESC', 'nombre': 'Escolar'},
            {'codigo': 'NES', 'nombre': 'No Escolarizada'},
            {'codigo': 'MIX', 'nombre': 'Mixta'},
        ]
        
        for modalidad_data in modalidades_data:
            ModalidadEducativa.objects.get_or_create(
                codigo=modalidad_data['codigo'],
                defaults={'nombre': modalidad_data['nombre']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Modalidades Educativas creadas: {len(modalidades_data)}'))
        
        # Turnos
        turnos_data = [
            {'codigo': 'MAT', 'nombre': 'Matutino'},
            {'codigo': 'VES', 'nombre': 'Vespertino'},
            {'codigo': 'NOCT', 'nombre': 'Nocturno'},
            {'codigo': 'MIX', 'nombre': 'Mixto'},
            {'codigo': 'FIN', 'nombre': 'Fin de Semana'},
        ]
        
        for turno_data in turnos_data:
            Turno.objects.get_or_create(
                codigo=turno_data['codigo'],
                defaults={'nombre': turno_data['nombre']}
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Turnos creados: {len(turnos_data)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Catálogos SEP poblados exitosamente!'))

