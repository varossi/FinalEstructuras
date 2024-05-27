class Config:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'



class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DB = 'flask_login' 
    MYSQL_UNIX_SOCKET = '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock'


config = {
    'development': DevelopmentConfig
}