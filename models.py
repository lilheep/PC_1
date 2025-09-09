from peewee import CharField, IntegerField, AutoField, ForeignKeyField, DateField, DateTimeField, Model, TextField, DecimalField
from database import db_connection
from hashing_password import hash_password
import datetime
import hashlib
import json


class JSONField(TextField):
    def db_value(self, value):
        if value is not None:
           return json.dumps(value)
        return None
    def python_value(self, value):
        if value is not None:
            return json.loads(value)
        return None 

class BaseModel(Model):
    class Meta:
        database = db_connection
        
class Roles(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, unique=True, null=False)

class Users(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=False)
    email = CharField(max_length=255, null=False)
    password = CharField(max_length=255, null=False)
    phone = CharField(max_length=20, null=False)
    role_id = ForeignKeyField(Roles, on_delete='CASCADE', backref='user_role', on_update='CASCADE')
    address = TextField(null=True)

class PasswordChangeRequest(BaseModel):
    id = AutoField()
    user = ForeignKeyField(Users, backref='user_change', on_delete='CASCADE', null=False)
    code = CharField(max_length=10)
    created_at = DateTimeField(default=datetime.datetime.now())
    expires_at = DateTimeField()

class UserToken(BaseModel):
    id = AutoField()
    user_id = ForeignKeyField(Users, on_delete='CASCADE', null=False, backref='us_token', on_update='CASCADE')
    token = CharField(max_length=255, null=False)
    created_at = DateTimeField(default=datetime.datetime.now(), null=False)
    expires_at = DateTimeField(null=False)

class Manufactures(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=False, unique=True)

class ComponentsTypes(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=False)
    description = TextField(null=True)

class Components(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=False)
    type_id = ForeignKeyField(ComponentsTypes, on_delete='SET NULL', null=True, backref='type_comp', on_update='CASCADE')
    manufactures_id = ForeignKeyField(Manufactures, on_delete='SET NULL', null=True, backref='man_comp', on_update='CASCADE')
    price = DecimalField(max_digits=15, decimal_places=2, null=False)
    stock_quantity = IntegerField(null=True, default=0)
    specification = JSONField(null=True)

class Configurations(BaseModel):
    id = AutoField()
    user_id = ForeignKeyField(Users, on_delete='CASCADE', backref='user_config', on_update='CASCADE')
    name_config = CharField(max_length=255, null=True)
    description = TextField(null=True)
    created_at = DateField(default=datetime.datetime.now())

class ConfigurationsComponents(BaseModel):
    id = AutoField()
    configuration_id = ForeignKeyField(Configurations, on_delete='CASCADE', backref='config_components', on_update='CASCADE')
    components_id = ForeignKeyField(Components, on_delete='CASCADE', backref='component_config', on_update='CASCADE')
    quantity = IntegerField(null=False, default=1)

class OrdersStatus(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=False, unique=True)

class Orders(BaseModel):
    id = AutoField()
    user_id = ForeignKeyField(Users, on_delete='CASCADE', backref='order_user', on_update='CASCADE')
    order_date = DateTimeField(null=False, default=datetime.datetime.now())
    total_amout = DecimalField(max_digits=15, decimal_places=2, null=False)
    status_id = ForeignKeyField(OrdersStatus, on_delete='CASCADE', backref='order_status', on_update='CASCADE')

class OrderConfigurations(BaseModel):
    id = AutoField()
    order_id = ForeignKeyField(Orders, on_delete='CASCADE', backref='order_config', on_update='CASCADE')
    configuration_id = ForeignKeyField(Configurations, on_delete='CASCADE', backref='config_con', on_update='CASCADE')
    quantity = IntegerField(null=False, default=1)
    price_at_time = DecimalField(max_digits=15, decimal_places=2, null=False)

tables = [Roles,
          Users,
          PasswordChangeRequest,
          UserToken,
          Manufactures,
          ComponentsTypes,
          Components,
          Configurations,
          ConfigurationsComponents,
          OrdersStatus,
          Orders,
          OrderConfigurations]

def init_tables():
    try:
        db_connection.create_tables(tables, safe=True)
        print(f'Таблицы успешно созданы. Количество: {len(tables)}.')
    except Exception as e:
        print(f'Ошибка при создании таблиц: {e}.')
        
def create_roles():
    try:
        if Roles.select().count() > 1:
            print('Тестовые роли уже созданы.')
            return
        
        roles = [
            {
                "name": "Администратор"
            },
            {
                "name": "Пользователь"
            }
        ]
        
        for role in roles:
            Roles.create(**role)
        print('Роли успешно созданы.')
    except Exception as e:
        print(f'Ошибка при создании ролей: {e}')

def create_users():
    try:
        if Users.select().count() > 4:
            print("Тестовые пользователи уже созданы")
            return
        
        users = [
            {
                "name": "Румянцев Никита Русланович",
                "email": "nikita.ded0000@gmail.com",
                "password": hash_password('1234567ty'),
                "phone": "89532347865",
                "role_id": 1,
                "adress": "Кострома"
                
            },
            {
                 "name": "Архипов Анндрей Валерьевич",
                "email": "andrey.ded0000@gmail.com",
                "password": hash_password('127869jhg'),
                "phone": "89535671234",
                "role_id": 2,
                "adress": "Кострома"
            },
            {
                 "name": "Комаров Кирилл Александрович",
                "email": "kirill.ded0000@gmail.com",
                "password": hash_password('111kirillof'),
                "phone": "89456666567",
                "role_id": 2,
                "adress": "Кострома"
            },
            {
                "name": "Машков Виталий Сергеевич",
                "email": "mashok.ded0000@gmail.com",
                "password": hash_password('111vityaf'),
                "phone": "89932345678",
                "role_id": 2,
                "adress": "Ковров"
            },
            {
                "name": "Комов Егор Павлович",
                "email": "igor.ded0000@gmail.com",
                "password": hash_password('111kehaaagfdhf'),
                "phone": "89532405628",
                "role_id": 2,
                "adress": "Кострома"
            } 
        ]
        for user in users:
            Users.create(**user)
        print("Роли успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании пользователей: {e}")

def create_manufactures():
    try:
        if Manufactures.select().count() > 4:
            print("Тестовые производители уже созданы.")
            return
        manufactures = [
            {
                "name": "NVIDIA"
            },
            {
                "name": "ASUS"
            },
            {
                "name": "SAMSUNG"
            },
            {
                "name": "HYPERX"
            },
             {
                "name": "MSI"
            }   
        ]
        for m in manufactures:
            Manufactures.create(**m)   
        print("Производители успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании производителей: {e}")
def create_componentstypes():
    try:
        if ComponentsTypes.select().count()>4:
            print("Тестовые комплектующиеуже созданы.")
            return
        componentstypes = [
            {
                "name": "Процессор",
                "description": "Центральный процессор (CPU) - основное вычислительное устройство, определяющее производительность системы."
            },
            {
                "name": "Материнская плата",
                "description": "Материнская плата - основа компьютера, объединяющая все компоненты и определяющая их совместимость."
            },
            {
                "name": "Блок питания",
                "description": "Блок питания (PSU) - обеспечивает стабильное электропитание всех компонентов системы."
            },
            {
                "name": "Корпус",
                "description": "Корпус системного блока - защищает компоненты от внешних воздействий и определяет форм-фактор сборки."
            },
            {
                "name": "Видеокарта",
                "description": "Видеокарта (GPU) - обрабатывает графику и обеспечивает вывод изображения на монитор."
            },
            {
                "name": "Охлаждение процессора",
                "description": "Система охлаждения CPU - поддерживает оптимальную температуру процессора для стабильной работы."
            },
            {
                "name": "Оперативная память",
                "description": "Оперативная память (RAM) - временное хранилище данных для быстрого доступа процессора."
            },
            {
                "name": "Накопители",
                "description": "Накопители (SSD/HDD) - устройства для постоянного хранения операционной системы и данных."
            },
            {
                "name": "Звуковая карта",
                "description": "Звуковая карта - обрабатывает аудиосигналы и обеспечивает высококачественный вывод звука."
            },
            {
                "name": "Дополнительные детали",
                "description": "Дополнительные компоненты - кабели, переходники и аксессуары для расширения функционала."
            },
            {
                "name": "Периферия",
                "description": "Периферийные устройства - внешние компоненты (мониторы, клавиатуры, мыши и др.)."
            }
        ]
        for comp in componentstypes:
            ComponentsTypes.create(**comp)   
        print("Комплектующие успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании комплектующих: {e}")

def create_components():
    try:
        if Components.select().count() > 9:
            print("Тестовые компоненты уже созданы.")
            return
        
        components = [
            {
                "name": "Intel Core i7-12700K",
                "type_id": 1, 
                "manufactures_id": 5, 
                "price": 29999.99,
                "stock_quantity": 15,
                "specification": {
                    "сокет": "LGA 1700",
                    "ядро": "Alder Lake",
                    "количество ядер": 12,
                    "тактовая частота": "3.6 GHz",
                    "кэш": "25 MB"
                }
            },
            {
                "name": "ASUS ROG Strix Z690-E",
                "type_id": 2, 
                "manufactures_id": 2,
                "price": 24999.99,
                "stock_quantity": 8,
                "specification": {
                    "сокет": "LGA 1700",
                    "чипсет": "Intel Z690",
                    "формат": "ATX",
                    "слоты PCI-E": "3",
                    "слоты RAM": "4"
                }
            },
            {
                "name": "NVIDIA GeForce RTX 4070",
                "type_id": 5, 
                "manufactures_id": 1, 
                "price": 59999.99,
                "stock_quantity": 5,
                "specification": {
                    "чипсет": "GeForce RTX 4070",
                    "видеопамять": "12 GB GDDR6X",
                    "ширина шины": "192-bit",
                    "такты": "1920 MHz"
                }
            },
            {
                "name": "Samsung 980 PRO 1TB",
                "type_id": 8,
                "manufactures_id": 3,
                "price": 12999.99,
                "stock_quantity": 20,
                "specification": {
                    "тип": "SSD M.2",
                    "емкость": "1 TB",
                    "скорость чтения": "7000 MB/s",
                    "скорость записи": "5000 MB/s"
                }
            },
            {
                "name": "HyperX Fury 32GB",
                "type_id": 7,
                "manufactures_id": 4,
                "price": 8999.99,
                "stock_quantity": 12,
                "specification": {
                    "тип": "DDR4",
                    "объем": "32 GB",
                    "частота": "3200 MHz",
                    "тайминги": "CL16"
                }
            },
            {
                "name": "Be Quiet! Dark Rock Pro 4",
                "type_id": 6,
                "manufactures_id": 5,
                "price": 7999.99,
                "stock_quantity": 7,
                "specification": {
                    "тип": "Воздушное",
                    "рассеиваемая мощность": "250 W",
                    "шум": "24.3 dB",
                    "совместимость": "LGA 1700, AM4"
                }
            },
            {
                "name": "Seasonic Focus GX-750",
                "type_id": 3,
                "manufactures_id": 2,
                "price": 10999.99,
                "stock_quantity": 10,
                "specification": {
                    "мощность": "750 W",
                    "сертификат": "80+ Gold",
                    "модульность": "Полная",
                    "разъемы PCI-E": "4"
                }
            },
            {
                "name": "NZXT H510",
                "type_id": 4,
                "manufactures_id": 5, 
                "price": 6999.99,
                "stock_quantity": 6,
                "specification": {
                    "формат": "Mid-Tower",
                    "материал": "Сталь, стекло",
                    "размеры": "210 x 460 x 428 mm",
                    "мест для вентиляторов": "4"
                }
            },
            {
                "name": "Creative Sound Blaster Z",
                "type_id": 9, 
                "manufactures_id": 2,  
                "price": 8999.99,
                "stock_quantity": 3,
                "specification": {
                    "тип": "Внутренняя",
                    "каналы": "5.1",
                    "частота дискретизации": "192 kHz",
                    "соотношение сигнал/шум": "116 dB"
                }
            },
            {
                "name": "Corsair K95 RGB",
                "type_id": 11,  
                "manufactures_id": 4,  
                "price": 14999.99,
                "stock_quantity": 9,
                "specification": {
                    "тип": "Механическая",
                    "переключатели": "Cherry MX Speed",
                    "подсветка": "RGB",
                    "макроклавиши": "6"
                }
            }
        ]
        
        for component in components:
            Components.create(**component)
        print("Компоненты успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании компонентов: {e}")
def create_configurations():
    try:
        if Configurations.select().count() > 2:
            print("Тестовые конфигурации уже созданы.")
            return
        
        configurations = [
            {
                "user_id": 1,  
                "name_config": "Игровой ПК высшего класса",
                "description": "Мощная игровая система для AAA-игр в 4K разрешении"
            },
            {
                "user_id": 2,  
                "name_config": "Бюджетный офисный компьютер",
                "description": "Экономичная система для работы с документами и интернетом"
            },
            {
                "user_id": 3,  
                "name_config": "Студенческая сборка",
                "description": "Сбалансированный ПК для учебы и развлечений"
            },
            {
                "user_id": 1,  
                "name_config": "Сервер для стриминга",
                "description": "Производительная система для трансляции игрового процесса"
            },
            {
                "user_id": 4,  
                "name_config": "Домашний медиацентр",
                "description": "Тихий ПК для просмотра фильмов и прослушивания музыки"
            }
        ]
        
        for config in configurations:
            Configurations.create(**config)
        print("Конфигурации успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании конфигураций: {e}")
        
def create_configurations_components():
    try:
        if ConfigurationsComponents.select().count() > 5:
            print("Тестовые связи конфигураций с компонентами уже созданы.")
            return
        
        configurations_components = [
            {
                "configuration_id": 1,
                "components_id": 1,  
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 2,  
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 3, 
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 4,
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 5,  
                "quantity": 2  
            },
            {
                "configuration_id": 1,
                "components_id": 6,
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 7, 
                "quantity": 1
            },
            {
                "configuration_id": 1,
                "components_id": 8,  
                "quantity": 1
            },

            {
                "configuration_id": 2,
                "components_id": 1, 
                "quantity": 1
            },
            {
                "configuration_id": 2,
                "components_id": 2,
                "quantity": 1
            },
            {
                "configuration_id": 2,
                "components_id": 5, 
                "quantity": 1  
            },
            {
                "configuration_id": 2,
                "components_id": 4, 
                "quantity": 1
            },

            {
                "configuration_id": 3,
                "components_id": 1,
                "quantity": 1
            },
            {
                "configuration_id": 3,
                "components_id": 2,
                "quantity": 1
            },
            {
                "configuration_id": 3,
                "components_id": 3,
                "quantity": 1
            },
            {
                "configuration_id": 3,
                "components_id": 5,  
                "quantity": 1
            }
        ]
        
        for config_comp in configurations_components:
            ConfigurationsComponents.create(**config_comp)
        print("Связи конфигураций с компонентами успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании связей конфигураций с компонентами: {e}")
def create_orders_status():
    try:
        if OrdersStatus.select().count() > 2:
            print("Тестовые статусы заказов уже созданы.")
            return
        
        statuses = [
            {
                "name": "В обработке"
            },
            {
                "name": "Оплачен"
            },
            {
                "name": "Собирается"
            },
            {
                "name": "Отправлен"
            },
            {
                "name": "Доставлен"
            },
            {
                "name": "Отменен"
            }
        ]
        
        for status in statuses:
            OrdersStatus.create(**status)
        print("Статусы заказов успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании статусов заказов: {e}")

def create_orders():
    try:
        if Orders.select().count() > 2:
            print("Тестовые заказы уже созданы.")
            return
        
        orders = [
            {
                "user_id": 1,  
                "total_amout": 159999.95,  
                "status_id": 2  
            },
            {
                "user_id": 2,  
                "total_amout": 54999.97, 
                "status_id": 1  
            },
            {
                "user_id": 3,  
                "total_amout": 89999.98,  
                "status_id": 3  
            },
            {
                "user_id": 1,  
                "total_amout": 129999.99,  
                "status_id": 4  
            },
            {
                "user_id": 4,  
                "total_amout": 69999.99, 
                "status_id": 5  
            }
        ]
        
        for order in orders:
            Orders.create(**order)
        print("Заказы успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании заказов: {e}")

def create_order_configurations():
    try:
        if OrderConfigurations.select().count() > 2:
            print("Тестовые связи заказов с конфигурациями уже созданы.")
            return
        
        order_configurations = [
            
            {
                "order_id": 1,
                "configuration_id": 1,  
                "quantity": 1,
                "price_at_time": 159999.95
            },
            
            {
                "order_id": 2,
                "configuration_id": 2,  
                "quantity": 1,
                "price_at_time": 54999.97
            },
           
            {
                "order_id": 3,
                "configuration_id": 3,  
                "quantity": 1,
                "price_at_time": 89999.98
            },
           
            {
                "order_id": 4,
                "configuration_id": 4,  
                "quantity": 1,
                "price_at_time": 129999.99
            },
            
            {
                "order_id": 5,
                "configuration_id": 5,  
                "quantity": 1,
                "price_at_time": 69999.99
            }
        ]
        
        for order_config in order_configurations:
            OrderConfigurations.create(**order_config)
        print("Связи заказов с конфигурациями успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании связей заказов с конфигурациями: {e}")
        
init_tables()
create_roles()
create_users()
create_manufactures()
create_componentstypes()   
create_components()
create_configurations()    
create_configurations_components()
create_orders_status()
create_orders()
create_order_configurations()
