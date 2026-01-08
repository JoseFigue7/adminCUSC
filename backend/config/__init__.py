# Solo configurar PyMySQL si se está usando MySQL
import os
import warnings
from decouple import config

# Suppress pkg_resources deprecation warnings from drf_yasg
warnings.filterwarnings('ignore', message='pkg_resources is deprecated', category=UserWarning)

USE_SQLITE = config('USE_SQLITE', default='True', cast=bool)

if not USE_SQLITE:
    import pymysql
    # Configurar PyMySQL para que Django lo use como mysqlclient
    pymysql.install_as_MySQLdb()

