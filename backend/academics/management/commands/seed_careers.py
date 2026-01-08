from django.core.management.base import BaseCommand
from academics.models import Career, Cuatrimestre, Course


class Command(BaseCommand):
    help = 'Seed database with careers and pensums'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de carreras y pensums...')
        
        # Definir carreras y pensums
        careers_data = [
            {
                'code': 101,
                'name': 'Licenciatura en Pedagogía',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestre',
                        'courses': [
                            {'code': 'PED101', 'name': 'Historia de la educación', 'credits': 4},
                            {'code': 'PED102', 'name': 'Sociología de la educación', 'credits': 4},
                            {'code': 'PED103', 'name': 'Teoría Pedagógica', 'credits': 4},
                            {'code': 'PED104', 'name': 'Teorías Pedagógicas contemporaneas', 'credits': 4},
                            {'code': 'PED105', 'name': 'Estrategias y métodos para el aprendizaje en línea', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'PED201', 'name': 'Historia de la educación en México', 'credits': 4},
                            {'code': 'PED202', 'name': 'Didáctica General', 'credits': 4},
                            {'code': 'PED203', 'name': 'Teorías pedagógicas contemporáneas', 'credits': 4},
                            {'code': 'PED204', 'name': 'Psicologia educativa', 'credits': 4},
                            {'code': 'PED205', 'name': 'Antropología filosófica', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'PED301', 'name': 'Sistema educativo nacional', 'credits': 4},
                            {'code': 'PED302', 'name': 'Didáctica de la enseñanza', 'credits': 4},
                            {'code': 'PED303', 'name': 'Filosofía de la educación', 'credits': 4},
                            {'code': 'PED304', 'name': 'Psicología de la infancia', 'credits': 4},
                            {'code': 'PED305', 'name': 'Barreras de aprendizaje', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'PED401', 'name': 'Marco Legal de la educación en México', 'credits': 4},
                            {'code': 'PED402', 'name': 'Psicología Social', 'credits': 4},
                            {'code': 'PED403', 'name': 'Problemas educativo en América Latina', 'credits': 4},
                            {'code': 'PED404', 'name': 'Psicología de la adolescencia', 'credits': 4},
                            {'code': 'PED405', 'name': 'Globalización y perspectiva de la educación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'PED501', 'name': 'Organismos educativos internacionales', 'credits': 4},
                            {'code': 'PED502', 'name': 'Desarrollo de técnicas de enseñanza', 'credits': 4},
                            {'code': 'PED503', 'name': 'Pedagogía comparada', 'credits': 4},
                            {'code': 'PED504', 'name': 'Psicología del adulto', 'credits': 4},
                            {'code': 'PED505', 'name': 'Taller de psicotecnia pedagógica', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Semestre',
                        'courses': [
                            {'code': 'PED601', 'name': 'Planeación educativa', 'credits': 4},
                            {'code': 'PED602', 'name': 'Política educativa', 'credits': 4},
                            {'code': 'PED603', 'name': 'Educación de adultos', 'credits': 4},
                            {'code': 'PED604', 'name': 'Orientación educativa', 'credits': 4},
                            {'code': 'PED605', 'name': 'Metodología de educación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Semestre',
                        'courses': [
                            {'code': 'PED701', 'name': 'Diseño y evaluación curricular', 'credits': 4},
                            {'code': 'PED702', 'name': 'Organización educativa', 'credits': 4},
                            {'code': 'PED703', 'name': 'Modelos de docencia', 'credits': 4},
                            {'code': 'PED704', 'name': 'Atención de necesidades educativas especiales', 'credits': 4},
                            {'code': 'PED705', 'name': 'Taller de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Semestre',
                        'courses': [
                            {'code': 'PED801', 'name': 'Alta dirección en centros educativos', 'credits': 4},
                            {'code': 'PED802', 'name': 'Desarrollo de proyectos educativos', 'credits': 4},
                            {'code': 'PED803', 'name': 'Seminarios de planeación prospectiva', 'credits': 4},
                            {'code': 'PED804', 'name': 'Seminarios de evaluación educativa', 'credits': 4},
                            {'code': 'PED805', 'name': 'Proyectos de innovación y emprendimiento', 'credits': 4},
                        ]
                    },
                ]
            },
            {
                'code': 102,
                'name': 'LICENCIATURA EN CRIMINOLOGÍA Y CRIMINALÍSTICA',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestres',
                        'courses': [
                            {'code': 'CRI101', 'name': 'Fundamentos generales del derecho', 'credits': 4},
                            {'code': 'CRI102', 'name': 'Introducción a la criminología y criminalística', 'credits': 4},
                            {'code': 'CRI103', 'name': 'Antropología y sociología forense', 'credits': 4},
                            {'code': 'CRI104', 'name': 'Bases de la conducta', 'credits': 4},
                            {'code': 'CRI105', 'name': 'Estrategias y métodos para el aprendizaje en línea', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'CRI201', 'name': 'Derechos humanos y garantías constitucionales', 'credits': 4},
                            {'code': 'CRI202', 'name': 'Criminalística', 'credits': 4},
                            {'code': 'CRI203', 'name': 'Criminología', 'credits': 4},
                            {'code': 'CRI204', 'name': 'Seguridad pública', 'credits': 4},
                            {'code': 'CRI205', 'name': 'Competencias tecnológicas laborales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'CRI301', 'name': 'Teoría general del delito', 'credits': 4},
                            {'code': 'CRI302', 'name': 'Criminalística de campo', 'credits': 4},
                            {'code': 'CRI303', 'name': 'Física forense', 'credits': 4},
                            {'code': 'CRI304', 'name': 'Química forense', 'credits': 4},
                            {'code': 'CRI305', 'name': 'Funciones corporales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'CRI401', 'name': 'Derecho penal', 'credits': 4},
                            {'code': 'CRI402', 'name': 'Dactiloscopia forense', 'credits': 4},
                            {'code': 'CRI403', 'name': 'Balística forense', 'credits': 4},
                            {'code': 'CRI404', 'name': 'Personalidad del criminal', 'credits': 4},
                            {'code': 'CRI405', 'name': 'Estructura y procesos vitales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'CRI501', 'name': 'Delitos en particular', 'credits': 4},
                            {'code': 'CRI502', 'name': 'Hechos de tránsito', 'credits': 4},
                            {'code': 'CRI503', 'name': 'Fotografía forense', 'credits': 4},
                            {'code': 'CRI504', 'name': 'Lesiones e identificación de personas', 'credits': 4},
                            {'code': 'CRI505', 'name': 'Criminología clínica', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Cuatrimestre',
                        'courses': [
                            {'code': 'CRI601', 'name': 'Delincuencia organizada y delincuencia serial', 'credits': 4},
                            {'code': 'CRI602', 'name': 'Incendios y explosiones', 'credits': 4},
                            {'code': 'CRI603', 'name': 'Poligrafía', 'credits': 4},
                            {'code': 'CRI604', 'name': 'Victimología', 'credits': 4},
                            {'code': 'CRI605', 'name': 'Metodología de la investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Cuatrimestre',
                        'courses': [
                            {'code': 'CRI701', 'name': 'Derecho procesal penal', 'credits': 4},
                            {'code': 'CRI702', 'name': 'Grafoscopía y documentos copia', 'credits': 4},
                            {'code': 'CRI703', 'name': 'Delitos informáticos', 'credits': 4},
                            {'code': 'CRI704', 'name': 'Análisis forense de las conductas antisociales', 'credits': 4},
                            {'code': 'CRI705', 'name': 'Taller de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Cuatrimestre',
                        'courses': [
                            {'code': 'CRI801', 'name': 'Sistema acusatorio', 'credits': 4},
                            {'code': 'CRI802', 'name': 'Observación práctica y criminalística', 'credits': 4},
                            {'code': 'CRI803', 'name': 'Sistema de identificación forense', 'credits': 4},
                            {'code': 'CRI804', 'name': 'Química, hematología y toxicología forense I', 'credits': 4},
                            {'code': 'CRI805', 'name': 'Seminarios de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 9,
                        'name': 'Nonveno Cuatrimestre',
                        'courses': [
                            {'code': 'CRI901', 'name': 'Delincuencia y responsabilidad juvenil', 'credits': 4},
                            {'code': 'CRI902', 'name': 'Coordinación e inteligencia pericial', 'credits': 4},
                            {'code': 'CRI903', 'name': 'Política criminal y prevención del delito', 'credits': 4},
                            {'code': 'CRI904', 'name': 'Química, hematología y toxicología forense II', 'credits': 4},
                            {'code': 'CRI905', 'name': 'Proyectos de innovación y emprendimiento', 'credits': 4},
                        ]
                    },
                ]
            },
            {
                'code': 103,
                'name': 'LICENCIATURA EN ADMINISTRACIÓN DE EMPRESAS Y NEGOCIOS',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestres',
                        'courses': [
                            {'code': 'ADM101', 'name': 'Introducción a la administración', 'credits': 4},
                            {'code': 'ADM102', 'name': 'Introducción a la mercadotecnia', 'credits': 4},
                            {'code': 'ADM103', 'name': 'Introducción a la contabilidad', 'credits': 4},
                            {'code': 'ADM104', 'name': 'Introducción al derecho', 'credits': 4},
                            {'code': 'ADM105', 'name': 'Estrategias y métodos para el aprendizaje en línea', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'ADM201', 'name': 'Mercadotecnia de productos', 'credits': 4},
                            {'code': 'ADM202', 'name': 'Contabilidad de costos', 'credits': 4},
                            {'code': 'ADM203', 'name': 'Derecho laboral', 'credits': 4},
                            {'code': 'ADM204', 'name': 'Macroeconomía', 'credits': 4},
                            {'code': 'ADM205', 'name': 'Competencias tecnológicas laborales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'ADM301', 'name': 'Mercadotecnia de servicios', 'credits': 4},
                            {'code': 'ADM302', 'name': 'Presupuestos', 'credits': 4},
                            {'code': 'ADM303', 'name': 'Derecho de la seguridad social', 'credits': 4},
                            {'code': 'ADM304', 'name': 'Macroeconomía', 'credits': 4},
                            {'code': 'ADM305', 'name': 'Información financiera', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'ADM401', 'name': 'Imagen corporativa', 'credits': 4},
                            {'code': 'ADM402', 'name': 'Matemáticas financieras', 'credits': 4},
                            {'code': 'ADM403', 'name': 'Derecho mercantil', 'credits': 4},
                            {'code': 'ADM404', 'name': 'Diseño organizacional', 'credits': 4},
                            {'code': 'ADM405', 'name': 'Negociación empresarial', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'ADM501', 'name': 'Gerencia de ventas', 'credits': 4},
                            {'code': 'ADM502', 'name': 'Administración financiera I', 'credits': 4},
                            {'code': 'ADM503', 'name': 'Sociedades mercantiles', 'credits': 4},
                            {'code': 'ADM504', 'name': 'Desarrollo organizacional', 'credits': 4},
                            {'code': 'ADM505', 'name': 'Administración política', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Cuatrimestre',
                        'courses': [
                            {'code': 'ADM601', 'name': 'Logística y distribución', 'credits': 4},
                            {'code': 'ADM602', 'name': 'Administración financiera II', 'credits': 4},
                            {'code': 'ADM603', 'name': 'Derecho administrativo y fiscal', 'credits': 4},
                            {'code': 'ADM604', 'name': 'Administración estratégica en los negocios', 'credits': 4},
                            {'code': 'ADM605', 'name': 'Taller de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Cuatrimestre',
                        'courses': [
                            {'code': 'ADM701', 'name': 'Comercio electrónico', 'credits': 4},
                            {'code': 'ADM702', 'name': 'Análisis de estados financieros', 'credits': 4},
                            {'code': 'ADM703', 'name': 'Derecho procesal administrativo y fiscal', 'credits': 4},
                            {'code': 'ADM704', 'name': 'Administración estratégica en los negocios', 'credits': 4},
                            {'code': 'ADM705', 'name': 'Taller de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Cuatrimestre',
                        'courses': [
                            {'code': 'ADM801', 'name': 'Generación de nuevos productos', 'credits': 4},
                            {'code': 'ADM802', 'name': 'Proyectos de inversión', 'credits': 4},
                            {'code': 'ADM803', 'name': 'Habilidades directivas', 'credits': 4},
                            {'code': 'ADM804', 'name': 'Empresas pequeñas y medianas', 'credits': 4},
                            {'code': 'ADM805', 'name': 'Seminarios de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 9,
                        'name': 'Noveno Semestre',
                        'courses': [
                            {'code': 'ADM901', 'name': 'Innovación tecnológica', 'credits': 4},
                            {'code': 'ADM902', 'name': 'Gerencia de la calidad empresarial', 'credits': 4},
                            {'code': 'ADM903', 'name': 'Dirección de empresas', 'credits': 4},
                            {'code': 'ADM904', 'name': 'Contratación y creación de franquicias', 'credits': 4},
                            {'code': 'ADM905', 'name': 'Proyectos de innovación y emprendimiento', 'credits': 4},
                        ]
                    },
                ]
            },
            {
                'code': 104,
                'name': 'LICENCIATURA EN DERECHO',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestres',
                        'courses': [
                            {'code': 'DER101', 'name': 'Acto jurídico y personas', 'credits': 4},
                            {'code': 'DER102', 'name': 'Historia del derecho mexicano', 'credits': 4},
                            {'code': 'DER103', 'name': 'Fundamentos generales del derecho', 'credits': 4},
                            {'code': 'DER104', 'name': 'Teoría general del estado', 'credits': 4},
                            {'code': 'DER105', 'name': 'Estrategias y métodos para el aprendizaje en línea', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'DER201', 'name': 'Bienes y derechos reales', 'credits': 4},
                            {'code': 'DER202', 'name': 'Derecho administrativo', 'credits': 4},
                            {'code': 'DER203', 'name': 'Teoría general del proceso', 'credits': 4},
                            {'code': 'DER204', 'name': 'Filosofía del derecho', 'credits': 4},
                            {'code': 'DER205', 'name': 'Derechos humanos y sus garantías', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'DER301', 'name': 'Obligaciones', 'credits': 4},
                            {'code': 'DER302', 'name': 'Derecho procesal administrativo', 'credits': 4},
                            {'code': 'DER303', 'name': 'Lógica y argumentación jurídica', 'credits': 4},
                            {'code': 'DER304', 'name': 'Teoría de la penal y del delito', 'credits': 4},
                            {'code': 'DER305', 'name': 'Títulos y operaciones de crédito', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'DER401', 'name': 'Contratos civiles', 'credits': 4},
                            {'code': 'DER402', 'name': 'Derecho fiscal', 'credits': 4},
                            {'code': 'DER403', 'name': 'Derecho agrario', 'credits': 4},
                            {'code': 'DER404', 'name': 'Delitos en particular', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'DER501', 'name': 'Derecho familiar', 'credits': 4},
                            {'code': 'DER502', 'name': 'Derecho procesal fiscal', 'credits': 4},
                            {'code': 'DER503', 'name': 'Derecho procesal agrario', 'credits': 4},
                            {'code': 'DER504', 'name': 'Derecho procesal penal', 'credits': 4},
                            {'code': 'DER505', 'name': 'Sociedades mercantiles', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Cuatrimestre',
                        'courses': [
                            {'code': 'DER601', 'name': 'Derecho sucesorio', 'credits': 4},
                            {'code': 'DER602', 'name': 'Derecho constitucional', 'credits': 4},
                            {'code': 'DER603', 'name': 'Derecho individual de trabajo', 'credits': 4},
                            {'code': 'DER604', 'name': 'Justicia alternativa', 'credits': 4},
                            {'code': 'DER605', 'name': 'Seguros y fianzas', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Cuatrimestre',
                        'courses': [
                            {'code': 'DER701', 'name': 'Derecho procesal civil', 'credits': 4},
                            {'code': 'DER702', 'name': 'Derecho procesal constitucional', 'credits': 4},
                            {'code': 'DER703', 'name': 'Derecho colectivo de trabajo', 'credits': 4},
                            {'code': 'DER704', 'name': 'Práctica de juicio oral penal', 'credits': 4},
                            {'code': 'DER705', 'name': 'Derecho procesal mercantil', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Cuatrimestre',
                        'courses': [
                            {'code': 'DER801', 'name': 'Juicios especiales', 'credits': 4},
                            {'code': 'DER802', 'name': 'Derecho de amparo', 'credits': 4},
                            {'code': 'DER803', 'name': 'Derecho de la seguridad social', 'credits': 4},
                            {'code': 'DER804', 'name': 'Derecho internacional público', 'credits': 4},
                            {'code': 'DER805', 'name': 'Investigación jurídica I', 'credits': 4},
                        ]
                    },
                    {
                        'number': 9,
                        'name': 'Noveno Cuatrimestre',
                        'courses': [
                            {'code': 'DER901', 'name': 'Derecho notarial y registral', 'credits': 4},
                            {'code': 'DER902', 'name': 'Prácticas de amparo', 'credits': 4},
                            {'code': 'DER903', 'name': 'Sistemas corporativos comparados', 'credits': 4},
                            {'code': 'DER904', 'name': 'Derecho internacional privado', 'credits': 4},
                        ]
                    },
                ]
            },
            {
                'code': 105,
                'name': 'LICENCIATURA EN MERCADOTECNIA DIGITAL Y PUBLICIDAD',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestres',
                        'courses': [
                            {'code': 'MER101', 'name': 'Introducción a la comunicación y mercadotecnia digital', 'credits': 4},
                            {'code': 'MER102', 'name': 'Desarrollo del pensamiento crítico', 'credits': 4},
                            {'code': 'MER103', 'name': 'Cultura y sociedad', 'credits': 4},
                            {'code': 'MER104', 'name': 'Régimen legal de la mercadotecnia', 'credits': 4},
                            {'code': 'MER105', 'name': 'Estrategias y métodos para el aprendizaje en línea', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'MER201', 'name': 'Teorías de la comunicación', 'credits': 4},
                            {'code': 'MER202', 'name': 'Lenguaje audiovisual', 'credits': 4},
                            {'code': 'MER203', 'name': 'Derecho en los medios de comunicación', 'credits': 4},
                            {'code': 'MER204', 'name': 'Administración y planeación estratégica', 'credits': 4},
                            {'code': 'MER205', 'name': 'Competencias tecnológicas laborales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'MER301', 'name': 'Semiotica de la comunicación', 'credits': 4},
                            {'code': 'MER302', 'name': 'Comunicación en medios digitales', 'credits': 4},
                            {'code': 'MER303', 'name': 'Comunicación organizacional', 'credits': 4},
                            {'code': 'MER304', 'name': 'Mercadotecnia tradicional', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'MER401', 'name': 'Comunicación en crisis', 'credits': 4},
                            {'code': 'MER402', 'name': 'Comunicación visual y diseño gráfico', 'credits': 4},
                            {'code': 'MER403', 'name': 'Investigación de mercados', 'credits': 4},
                            {'code': 'MER404', 'name': 'Comportamiento del consumidor', 'credits': 4},
                            {'code': 'MER405', 'name': 'Mercadotecnia de servicios', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'MER501', 'name': 'Estrategias de comunicación integrada', 'credits': 4},
                            {'code': 'MER502', 'name': 'Liderazgo y comunicación', 'credits': 4},
                            {'code': 'MER503', 'name': 'Finanzas mercadológicas', 'credits': 4},
                            {'code': 'MER504', 'name': 'Responsabilidad social corporativa', 'credits': 4},
                            {'code': 'MER505', 'name': 'Medios y plataformas digitales', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Cuatrimestre',
                        'courses': [
                            {'code': 'MER601', 'name': 'Metodología de la investigación', 'credits': 4},
                            {'code': 'MER602', 'name': 'Teoría de las redes sociales', 'credits': 4},
                            {'code': 'MER603', 'name': 'Publicidad digital', 'credits': 4},
                            {'code': 'MER604', 'name': 'Mercadotecnia digital', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Cuatrimestre',
                        'courses': [
                            {'code': 'MER701', 'name': 'Taller de investigación', 'credits': 4},
                            {'code': 'MER702', 'name': 'Gestión de redes sociales', 'credits': 4},
                            {'code': 'MER703', 'name': 'Diseño y creación de contenidos escritos', 'credits': 4},
                            {'code': 'MER704', 'name': 'Comercio electrónico', 'credits': 4},
                            {'code': 'MER705', 'name': 'Relaciones públicas', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Cuatrimestre',
                        'courses': [
                            {'code': 'MER801', 'name': 'Seminario de investigación', 'credits': 4},
                            {'code': 'MER802', 'name': 'Planificación estratégica de mercadotecnia', 'credits': 4},
                            {'code': 'MER803', 'name': 'Diseño y creación de contenidos digitales', 'credits': 4},
                            {'code': 'MER804', 'name': 'Fundamentos del posicionamiento web', 'credits': 4},
                            {'code': 'MER805', 'name': 'Herramientas de social media', 'credits': 4},
                        ]
                    },
                    {
                        'number': 9,
                        'name': 'Nonveno Cuatrimestre',
                        'courses': [
                            {'code': 'MER901', 'name': 'Proyectos de innovación y emprendimiento', 'credits': 4},
                            {'code': 'MER902', 'name': 'Proyectos de mercadotecnia digital', 'credits': 4},
                            {'code': 'MER903', 'name': 'Campaña publicitaria', 'credits': 4},
                            {'code': 'MER904', 'name': 'Diseño para dispositivos móviles', 'credits': 4},
                            {'code': 'MER905', 'name': 'Gestión de marca', 'credits': 4},
                        ]
                    },
                ]
            },
            {
                'code': 106,
                'name': 'LICENCIATURA EN CONTADURÍA PÚBLICA Y FINANZAS',
                'cuatrimestres': [
                    {
                        'number': 1,
                        'name': 'Primer Cuatrimestre',
                        'courses': [
                            {'code': 'CON101', 'name': 'Introducción a los principios contables', 'credits': 4},
                            {'code': 'CON102', 'name': 'Bases macroeconómicas', 'credits': 4},
                            {'code': 'CON103', 'name': 'Matemáticas financieras', 'credits': 4},
                            {'code': 'CON104', 'name': 'Fundamentos administrativos y jurídicos', 'credits': 4},
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Segundo Cuatrimestre',
                        'courses': [
                            {'code': 'CON201', 'name': 'Profundización en contabilidad intermedia', 'credits': 4},
                            {'code': 'CON202', 'name': 'Modelos de negocios', 'credits': 4},
                            {'code': 'CON203', 'name': 'Procesos administrativos', 'credits': 4},
                            {'code': 'CON204', 'name': 'Normativas mercantiles', 'credits': 4},
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Tercer Cuatrimestre',
                        'courses': [
                            {'code': 'CON301', 'name': 'Contabilidad avanzada', 'credits': 4},
                            {'code': 'CON302', 'name': 'Contexto socioeconómico de México', 'credits': 4},
                            {'code': 'CON303', 'name': 'Introducción a la auditoría', 'credits': 4},
                            {'code': 'CON304', 'name': 'Derecho de sociedades mercantiles', 'credits': 4},
                        ]
                    },
                    {
                        'number': 4,
                        'name': 'Cuarto Cuatrimestre',
                        'courses': [
                            {'code': 'CON401', 'name': 'Gestión de costos', 'credits': 4},
                            {'code': 'CON402', 'name': 'Finanzas empresariales', 'credits': 4},
                            {'code': 'CON403', 'name': 'Auditoría intermedia', 'credits': 4},
                            {'code': 'CON404', 'name': 'Administración de capital humano', 'credits': 4},
                            {'code': 'CON405', 'name': 'Derecho fiscal', 'credits': 4},
                        ]
                    },
                    {
                        'number': 5,
                        'name': 'Quinto Cuatrimestre',
                        'courses': [
                            {'code': 'CON501', 'name': 'Impuestos indirectos y estatales', 'credits': 4},
                            {'code': 'CON502', 'name': 'Finanzas avanzadas', 'credits': 4},
                            {'code': 'CON503', 'name': 'Auditoría avanzada', 'credits': 4},
                            {'code': 'CON504', 'name': 'Desarrollo del personal', 'credits': 4},
                            {'code': 'CON505', 'name': 'Derecho administrativo', 'credits': 4},
                        ]
                    },
                    {
                        'number': 6,
                        'name': 'Sexto Cuatrimestre',
                        'courses': [
                            {'code': 'CON601', 'name': 'Contabilidad del sector público', 'credits': 4},
                            {'code': 'CON602', 'name': 'Impuestos del comercio exterior', 'credits': 4},
                            {'code': 'CON603', 'name': 'Prácticas de auditoría', 'credits': 4},
                            {'code': 'CON604', 'name': 'Metodología de investigación', 'credits': 4},
                        ]
                    },
                    {
                        'number': 7,
                        'name': 'Septimo Cuatrimestre',
                        'courses': [
                            {'code': 'CON701', 'name': 'Contabilidad hotelera y bancaria', 'credits': 4},
                            {'code': 'CON702', 'name': 'Personas físicas', 'credits': 4},
                            {'code': 'CON703', 'name': 'Análisis de estados financieros', 'credits': 4},
                            {'code': 'CON704', 'name': 'Administración estratégica', 'credits': 4},
                        ]
                    },
                    {
                        'number': 8,
                        'name': 'Octavo Cuatrimestre',
                        'courses': [
                            {'code': 'CON801', 'name': 'Contabilidad de sociedades mercantiles', 'credits': 4},
                            {'code': 'CON802', 'name': 'Personas morales', 'credits': 4},
                            {'code': 'CON803', 'name': 'Seguridad social', 'credits': 4},
                            {'code': 'CON804', 'name': 'Derecho corporativo', 'credits': 4},
                        ]
                    },
                    {
                        'number': 9,
                        'name': 'Noveno Cuatrimestre',
                        'courses': [
                            {'code': 'CON901', 'name': 'Práctica contable y fiscal', 'credits': 4},
                            {'code': 'CON902', 'name': 'Seguridad social avanzada', 'credits': 4},
                            {'code': 'CON903', 'name': 'Administración de calidad', 'credits': 4},
                            {'code': 'CON904', 'name': 'Proyectos de innovación empresarial', 'credits': 4},
                        ]
                    },
                ]
            },
        ]
        
        # Crear carreras y pensums
        for career_data in careers_data:
            career, created = Career.objects.get_or_create(
                code=career_data['code'],
                defaults={
                    'name': career_data['name'],
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creada carrera: {career.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Carrera ya existe: {career.name}'))
            
            # Calcular total de créditos
            total_credits = 0
            for cuatrimestre_data in career_data['cuatrimestres']:
                for course_data in cuatrimestre_data['courses']:
                    total_credits += course_data['credits']
            
            career.total_credits = total_credits
            career.save()
            
            # Crear cuatrimestres y cursos
            for cuatrimestre_data in career_data['cuatrimestres']:
                cuatrimestre, _ = Cuatrimestre.objects.get_or_create(
                    career=career,
                    number=cuatrimestre_data['number'],
                    defaults={'name': cuatrimestre_data['name']}
                )
                
                for course_data in cuatrimestre_data['courses']:
                    Course.objects.get_or_create(
                        career=career,
                        code=course_data['code'],
                        defaults={
                            'cuatrimestre': cuatrimestre,
                            'name': course_data['name'],
                            'credits': course_data['credits'],
                            'is_required': True,
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('Seed completado exitosamente!'))

