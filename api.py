from fastapi import FastAPI, HTTPException, Header
from typing import Optional, List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from hashing_password import hash_password, verify_password
import re
import uuid
import datetime
from models import Roles, Users, PasswordChangeRequest, UserToken, Manufactures, ComponentsTypes, Components, \
    Configurations, ConfigurationsComponents, OrdersStatus, Orders, OrderConfigurations
from database import db_connection
from pydantic import BaseModel
from email_utils import generation_confirmation_code, send_email
from decimal import Decimal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

EMAIL_REGEX = r'^[A-Za-zА-Яа-яЁё0-9._%+-]+@[A-Za-zА-Яа-яЁё-]+\.[A-Za-zА-Яа-яЁё-]{2,10}$'
PHONE_REGEX = r'^[0-9+()\-#]{10,15}$'

def get_user_by_token(token: str, required_role: Optional[str] = None) -> Users:
    try:
        user_token = (UserToken.select().join(Users).where(
            (UserToken.token==token) &
            (UserToken.expires_at > datetime.datetime.now()) 
        ).first())
        
        if not user_token:
            raise HTTPException(401, 'Недействительный или просроченный токен.')
               
        user = user_token.user_id
        user_role = Roles.get_by_id(user.role_id)
        if required_role:
            if user_role.name != 'Администратор':
                if user_role.name != required_role:
                    raise HTTPException(403, 'Недостаточно прав для выполнения этого действия.')
        
        user_token.expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        user_token.save()
        
        return user
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при проверке токена: {e}')
    
def get_component_type_by_name(type_name: str):
    """Получение имени типа компонента"""
    if not type_name:
        return None
    component_type = ComponentsTypes.select().where(ComponentsTypes.name==type_name).first()
    if not component_type:
        raise HTTPException(404, f'Тип компонента {type_name} не найден.')
    return component_type

def get_manufacture_by_name(manufacture_name: str):
    """Получение названия производителя"""
    if not manufacture_name:
        return None
    manufacture = Manufactures.select().where(Manufactures.name==manufacture_name).first()
    if not manufacture:
        raise HTTPException(404, f'Производитель {manufacture_name} не найден.')
    return manufacture

class AuthRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str

class SetRoleRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    new_role: str

class ComponentsTypesCreate(BaseModel):
    name: str
    description: str | None = None

class ComponentsTypesEdit(BaseModel):
    new_name: str | None = None
    description: str | None = None

class ComponentCreate(BaseModel):
    name: str
    type_name: Optional[str] = None
    manufacture_name: Optional[str] = None
    price: float
    stock_quantity: int
    specification: List[Dict[str, Any]] = None

class ComponentsEdit(BaseModel):
    new_name: Optional[str] = None
    type_name: Optional[str] = None
    manufacture_name: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    specification: List[Dict[str, Any]] = None
    
class ConfigurationCreate(BaseModel):
    name_config: Optional[str] = None
    description: Optional[str] = None

class ConfigurationEdit(BaseModel):
    name_config: Optional[str] = None
    description: Optional[str] = None

class ConfigComponentCreate(BaseModel):
    component_name: str
    quantity: int = 1

class ConfigComponentEdit(BaseModel):
    quantity: int

class OrderCreate(BaseModel):
    configuration_id: int
    quantity: int = 1

class OrderStatusUpdate(BaseModel):
    status_id: int

class OrderConfigCreate(BaseModel):
    configuration_id: int
    quantity: int = 1

class OrderConfigUpdate(BaseModel):
    quantity: int

class UserSearch(BaseModel):
    email: str | None = None
    phone: str | None = None
    
@app.post('/users/register/', tags=['Users'])
async def create_user(email: str, password: str, full_name: str, number_phone: str, address: str):
    """"Регистрация нового пользователя"""
    if not re.fullmatch(EMAIL_REGEX, email) or not re.fullmatch(PHONE_REGEX, number_phone):
        raise HTTPException(400, 'Неверный формат данных email/номера телефона')
    try:
        existing_user = Users.select().where((Users.email==email) | (Users.phone==number_phone)).first()
        if existing_user:
            raise HTTPException(403, 'Пользователь с таким email/номером телефона уже существует.')

        hashed_password = hash_password(password=password)
        with db_connection.atomic():
            user_role = Roles.get(Roles.name=='Пользователь')
            Users.create(
                name=full_name,
                email=email,
                password=hashed_password,
                phone=number_phone,
                role_id=user_role.id,
                address=address
            )
        return {'message': 'Вы успешно зарегистрировались!'}
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Произошла ошибка при регистрации: {e}')
    
@app.post('/users/auth/', tags=['Users'])
async def auth_user(data: AuthRequest):
    """Аутентификация пользователя"""
    email = data.email
    phone = data.phone
    password = data.password
    
    if not email and not phone:
        raise HTTPException(400, 'Введите email, либо номер телефона!')
    if email is not None:
        if not isinstance(email, str) or not re.fullmatch(EMAIL_REGEX, email):
            raise HTTPException(400, 'Неверный формат данных email.')
    if phone is not None:
        if not isinstance(phone, str) or not re.fullmatch(PHONE_REGEX, phone):
            raise HTTPException(400, 'Неверный формат данных номера телефона.')
    try:
        query = None
        if email:
            query = Users.select().where(Users.email==email)
        elif phone:
            query = Users.select().where(Users.phone==phone)
        existing_user = query.first() if query else None
        if not existing_user:
            raise HTTPException(404, 'Пользователя с таким email/номером телефона не  существует.')
        
        if not verify_password(password, existing_user.password):
            raise HTTPException(401, 'Вы ввели неправильный пароль! Попробуйте еще раз.')
        
        token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        UserToken.create(
            user_id=existing_user.id,
            token=token,
            expires_at=expires_at
        )
        
        return {'message': 'Успешная авторизация!',
                'token': token,
                'expires_at': expires_at.isoformat()}
        
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Произошла ошибка при авторизации: {e}')

@app.post('/users/change_password/', tags=['Users'])
async def request_change_password(email: str):
    """Запрос на смену пароля"""
    user = Users.select().where(Users.email==email).first()
    if not user:
        raise HTTPException(404, 'Пользователь с указанным email не найден.')
    code = generation_confirmation_code(length=6)
    expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
    PasswordChangeRequest.create(
        user=user.id,
        code=code,
        expires_at=expires
    )
    
    send_email(
        to_email=email,
        subject='Код подтверждения смены пароля.',
        body=f'Здравствуйте! \n Ваш код подтверждения смены пароля: {code.upper()}. \n Никому не сообщайте данный код. \n Если это были не Вы, проигнорируйте данное сообщение.'
    )
    
    return {'message': 'Код подтверждения успешно отправлен на указанную почту.'}

@app.post('/users/confirm_change_password/', tags=['Users'])
async def confirm_change_password(email: str, code: str, new_password: str):
    """Подтверждение и установка нового пароля"""
    user = Users.select().where(Users.email==email).first()
    if not user:
        raise HTTPException(404, 'Пользователь с указанным email не найден.')
    
    request = PasswordChangeRequest.select().where(
        (PasswordChangeRequest.user==user.id) &
        (PasswordChangeRequest.code==code.lower())
    ).order_by(PasswordChangeRequest.created_at.desc()).first()
    
    if not request:
        raise HTTPException(404, 'Неверный код подтверждения.')
    
    if datetime.datetime.now() > request.expires_at:
        raise HTTPException(400, 'Срок кода подтверждения истек.')
    
    update_rows = Users.update({
        Users.password: hash_password(new_password)
    }).where(Users.id==request.user.id).execute()
    
    if update_rows==0:
        raise HTTPException(500, 'Не удалось обновить пароль.')
    
    request.delete_instance()
    
    return {'message': 'Пароль успешно обновлен.'}

@app.get('/users/me/', tags=['Users'])
async def get_profile(token: str = Header(...)):
    """Получение своей информации пользователем"""
    try:
        user = get_user_by_token(token)
        if not user:
            raise HTTPException(401, 'Не удалось найти пользователя.')
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role_id.name,
            'address': user.address
        }
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Непредвиденая ошибка: {e}')

@app.get('/users/get_all/', tags=['Users'])
async def get_all_users(token: str = Header(...)):
    """Получение всех пользователей администратором"""
    current_user = get_user_by_token(token, 'Администратор')
    
    if not current_user:
        raise HTTPException(401, 'Не удалось найти пользователя.')
    
    users = Users.select()
    
    return [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role_id.name,
            'address': user.address
        } for user in users]

@app.delete('/users/delete_profile/', tags=['Users'])
async def delete_profile(token: str = Header(...)):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(401, 'Не удалось найти пользователя.')
    user.delete_instance()
    return {'message': 'Пользователь успешно удален.'}

@app.put('/users/edit_address/', tags=['Users'])
async def edit_user_address(new_address: str, token: str = Header(...)):
    """Изменение адреса пользователем"""
    current_user = get_user_by_token(token, 'Пользователь')
    try:
        if not current_user:
            raise HTTPException(401, 'Недействительный токен.')
        
        user = Users.select().where(Users.id==current_user.id).first()
        if not user:
            raise HTTPException(404, 'Пользователь не найден.')

        user.address = new_address
        user.save()
        
        return {'message': 'Адрес успешно изменен.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Не удалось изменить адрес для пользователя: {e}')
    
@app.post('/users/set_role/', tags=['Users'])
async def set_role_user(data: SetRoleRequest, token: str = Header(...)):
    """Изменение роли пользователей администратором"""
    current_user = get_user_by_token(token, 'Администратор')
    try:
        if not data.email and not data.phone:
            raise HTTPException(400, 'Введите email или номер телефона пользователя.')
        
        if data.email:
            user = Users.select().where(Users.email==data.email).first()
        elif data.phone:
            user = Users.select().where(Users.phone==data.phone).first()
        
        if not user:
            raise HTTPException(404, 'Пользователь не найден.')
        new_role = Roles.get_or_none(Roles.name==data.new_role)
        if not new_role:
            raise HTTPException(400, 'Неверно указано значение новой роли. Допустимые значения: "Пользователь", "Администратор".')
        
        user.role_id = new_role.id
        user.save()
        
        return {
            'message': 'Роль успешно изменена.',
            'email': user.email,
            'phone': user.phone,
            'new_role': new_role.name
        }
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении роли пользователя: {e}')

@app.post("/users/get_user_by_email_or_phone/", tags=['Users'])
async def get_user_by_login(data: UserSearch, token: str = Header(...)):
    """Для поиска админом конкретного пользователя"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
            raise HTTPException(401, 'Недействительный токен.')
    
    try:
        if not data.email and not data.phone:
            raise HTTPException(400, 'Введите email или номер телефона пользователя.')
        
        if data.email:
            user = Users.select().where(Users.email==data.email).first()
        elif data.phone:
            user = Users.select().where(Users.phone==data.phone).first()
        
        if not user:
            raise HTTPException(404, 'Пользователь не найден.')
        
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role_id.name,
            'address': user.address   
        }
        
    except HTTPException as http_exc:
        raise http_exc    
        
    except Exception as e:
        raise HTTPException(500, f'Не удалось подключиться к серверу: {e}')
    

@app.post('/manufactures/add_manufacture/', tags=['Manufactures'])
async def create_manufactrue(name: str, token: str = Header(...)):
    """Создание производетеля"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        Manufactures.create(name=name)
        return {'message': 'Производитель успешно создан.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании производителя: {e}') 

@app.put('/manufactures/edit_manufactures/', tags=['Manufactures'])
async def edit_manufactures(manufacture_id: int, new_name: str, token: str = Header(...)):
    """Изменение названия производителя"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    manufacture = Manufactures.select().where(Manufactures.id==manufacture_id).first()
    if not manufacture:
        raise HTTPException(404, 'Производителя с указанным ID не существует.')
    
    try:
        manufacture.name = new_name
        manufacture.save()
        return {'message': 'Название производителя успешно изменено.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении названия производителя: {e}') 

@app.get('/manufactures/get_manufactures_by_id/', tags=['Manufactures'])
async def get_manufacture_by_id(manufacture_id: int, token: str = Header(...)):
    """Получение данных о конкретном производителе"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    try:
        manufacture = Manufactures.select().where(Manufactures.id==manufacture_id).first()
        if not manufacture:
            raise HTTPException(404, 'Производителя с указанным ID не существует.')      
        
        return {
            'id': manufacture.id,
            'name': manufacture.name
        }
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении данных о производителе: {e}')

@app.get('/manufactures/get_manufactures/', tags=['Manufactures'])
async def get_all_manufactures(token: str = Header(...)):
    """Получении данных о всех производителях"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    try:
        manufactures = Manufactures.select()

        return [{
            'id': manufacture.id,
            'name': manufacture.name
        } for manufacture in manufactures]
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении данных о производителях: {e}')

@app.delete('/manufactures/del_manufacture_by_id/', tags=['Manufactures'])
async def delete_manufacture(manufacture_id: int, token: str = Header(...)):
    """Удаление выбранного производителя"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        manufacture = Manufactures.select().where(Manufactures.id==manufacture_id).first()
        if not manufacture:
            raise HTTPException(404, 'Производитель с указанным ID не существует.')
        manufacture.delete_instance() 
        return {'message': f'Прозводитель {manufacture.name} успешно удален.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении производителя: {e}')
        
@app.get('/components_types/get_all/', tags=['Components Types'])
async def get_all_cp(token: str = Header(...)):
    """Получение данных о всех типах компонентов"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        component_types = ComponentsTypes.select()
        return [{
            'name': component_type.name,
            'description': component_type.description
        } for component_type in component_types]
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении типов компонентов: {e}')

@app.get('/components_types/get_by_id/', tags=['Components Types'])
async def get_cp_by_id(cp_id: int, token: str = Header(...)):
    """Получение данных о выбранном типе компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        component_types = ComponentsTypes.select().where(ComponentsTypes.id==cp_id).first()
        if not component_types:
            raise HTTPException(404, 'Тип компонента с указанным ID не найден.')

        return {
            'id': component_types.id,
            'name': component_types.name,
            'description': component_types.description
        }
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении типа компонента: {e}')

@app.post('/components_types/create_cp/', tags=['Components Types'])
async def create_cp(data: ComponentsTypesCreate, token: str = Header(...)):
    """Создание типа компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    name = data.name
    description = data.description
    
    try:
        component_types = ComponentsTypes.select().where(ComponentsTypes.name==name).first()
        if component_types:
            raise HTTPException(403, 'Тип компонента с таким названием уже существует.')
        
        ComponentsTypes.create(
            name=name,
            description=description
        )
        
        return {'message': 'Тип компонента успешно создан.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании типа компонента: {e}')

@app.put('/components_types/edit_cp_by_id/', tags=['Components Types'])
async def edit_cp(cp_id: int, data: ComponentsTypesEdit, token: str = Header(...)):
    """Изменение данных о типе компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    new_name = data.new_name
    description = data.description
    component_type = ComponentsTypes.select().where(ComponentsTypes.id==cp_id).first()
    if not component_type:
        raise HTTPException(404, 'Тип компонента с указанным ID не найден.')
    try:
        component_type.name = new_name
        component_type.description = description
        component_type.save()
        return {'message': 'Данные о типе компонента успешно изменены.'}
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении типа компонента: {e}')
    
@app.delete('/components_types/delete_cp_by_id/', tags=['Components Types'])
async def delete_cp(cp_id: int, token: str = Header(...)):
    """Удаление типа компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        component_type = ComponentsTypes.select().where(ComponentsTypes.id==cp_id).first()
        if not component_type:
            raise HTTPException(404, 'Тип компонента с указанным ID не найден.')
        
        component_type.delete_instance()
        return {'message': f'Тип компонента {component_type.name} успешно удален.'}
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении типа компонента: {e}')    
    
@app.get('/components/get_all/', tags=['Components'])
async def get_all_components(token: str = Header(...)):
    """Получение данных о всех компонентах"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        components = Components.select()
        
        return [{
            'id': c.id,
            'name': c.name,
            'type_name': c.type_id.name if c.type_id else None,
            'manufacture_name': c.manufactures_id.name if c.manufactures_id else None,
            'price': float(c.price),
            'stock_quantity': c.stock_quantity,
            'specification': c.specification
        } for c in components]
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении компонентов: {e}')

@app.get('/components/get_by_id/', tags=['Components'])
async def get_component_by_id(component_id: int, token: str = Header(...)):
    """Получение данных о выбранном компоненте"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        component = Components.select().where(Components.id==component_id).first()
        if not component:
            raise HTTPException(404, 'Компонент с указанным ID не найден.')

        return {
            'name': component.name,
            'type_name': component.type_id.name if component.type_id else None,
            'manufacture_name': component.manufactures_id.name if component.manufactures_id else None,
            'price': float(component.price),
            'stock_quantity': component.stock_quantity,
            'specification': component.specification
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении компонента: {e}')

@app.post('/components/create/', tags=['Components'])
async def create_component(data: ComponentCreate, token: str = Header(...)):
    """Создание компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        existing_component = Components.select().where(Components.name==data.name).first()
        if existing_component:
            raise HTTPException(403, f'Компонент {existing_component.name} уже существует.')
        
        component_type = get_component_type_by_name(data.type_name) if data.type_name else None
        manufacture = get_manufacture_by_name(data.manufacture_name) if data.manufacture_name else None
        
        Components.create(
            name=data.name,
            type_id=component_type.id if component_type else None,
            manufactures_id=manufacture.id if manufacture else None,
            price=data.price,
            stock_quantity=data.stock_quantity,
            specification=data.specification
        )
        
        return {'message': 'Компонент успешно создан.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании компонента: {e}')

@app.put('/components/edit_by_id/', tags=['Components'])
async def edit_component(component_id: int, data: ComponentsEdit, token: str = Header(...)):
    """Изменение данных о компоненте"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        component = Components.select().where(Components.id==component_id).first()
        if not component:
            raise HTTPException(404, 'Компонент с указанным ID не существует.')
        
        if data.new_name and data.new_name != component.name:
            existing_component = Components.select().where(Components.name==data.new_name).first()
            if existing_component:
                raise HTTPException(403, f'Компонент {existing_component.name} уже существует.')
        
        component_type = None
        if data.type_name is not None:
            component_type = get_component_type_by_name(data.type_name) if data.type_name else None
        
        manufacture = None
        if data.manufacture_name is not None:
            manufacture = get_manufacture_by_name(data.manufacture_name) if data.manufacture_name else None
        
        if data.new_name is not None:
            component.name = data.new_name
        if data.type_name is not None:
            component.type_id = component_type.id if component_type else None
        if data.manufacture_name is not None:
            component.manufactures_id = manufacture.id if manufacture else None
        if data.price is not None:
            component.price = data.price
        if data.stock_quantity is not None:
            component.stock_quantity = data.stock_quantity
        if data.specification is not None:
            component.specification = data.specification
        
        component.save()
        
        return {'message': 'Данные о компоненте успешно изменены.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении компонента: {e}')

@app.delete('/components/delete_by_id/', tags=['Components'])
async def delete_component(component_id: int, token: str = Header(...)):
    """Удаление компонента"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        component = Components.select().where(Components.id==component_id).first()
        if not component:
            raise HTTPException(404, 'Компонент с указанным ID не найден.')
        
        component_name = component.name
        component.delete_instance()
        
        return {'message': f'Компонент {component_name} успешно удален.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении компонента: {e}')

@app.get('/configurations/get_all/', tags=['Configurations'])
async def get_all_configurations(token: str = Header(...)):
    """Получение всех конфигураций текущего пользователя"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configurations = Configurations.select().where(Configurations.user_id==current_user.id)
        return [{
            'id': config.id,
            'name_config': config.name_config,
            'description': config.description,
            'created_at': config.created_at.isoformat() if config.created_at else None
        } for config in configurations]
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении конфигураций: {e}')
    
@app.get('/configurations/get_by_id/', tags=['Configurations'])
async def get_configuration_by_id(config_id: int, token: str = Header(...)):
    """Получение конкретной конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        configuration = Configurations.select().where(
            (Configurations.id==config_id) & 
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация с указанным ID не найдена или у Вас нет доступа к ней.')

        return {
            'id': configuration.id,
            'name_config': configuration.name_config,
            'description': configuration.description,
            'created_at': configuration.created_at.isoformat() if configuration.created_at else None
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении конфигурации: {e}')

@app.post('/configurations/create/', tags=['Configurations'])
async def create_configuration(data: ConfigurationCreate, token: str = Header(...)):
    """Создание новой конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        if data.name_config:
            existing_config = Configurations.select().where(
                (Configurations.user_id==current_user.id) &
                (Configurations.name_config==data.name_config)
            ).first()
            if existing_config:
                raise HTTPException(403, f'Конфигурация {existing_config.name_config} уже существует.')
        
        Configurations.create(
            user_id=current_user.id,
            name_config=data.name_config,
            description=data.description
        )
        
        return {'message': 'Конфигурация успешно создана.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании конфигурации: {e}')

@app.put('/configurations/edit_by_id/', tags=['Configurations'])
async def edit_configuration(config_id: int, data: ConfigurationEdit, token: str = Header(...)):
    """Изменение конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        configuration = Configurations.select().where(
            (Configurations.id==config_id) &
            (Configurations.user_id==current_user.id)
        ).first()
       
        if not configuration:
            raise HTTPException(404, 'Конфигурация с указанным ID не найдена, или у Вас нет прав на ее изменение.')
       
        if data.name_config and data.name_config != configuration.name_config:
            existing_config = Configurations.select().where(
                (Configurations.name_config==data.name_config) &
                (Configurations.user_id==current_user.id)).first()
            if existing_config:
                raise HTTPException(403, f'Конфигурация {existing_config.name_config} уже существует.')
        
        if data.name_config is not None:
            configuration.name_config = data.name_config
        
        if data.description is not None:
            configuration.description = data.description
        
        configuration.save()
        
        return {'message': 'Конфигурация успешно изменена.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении конфигурации: {e}')

@app.delete('/configurations/delete_by_id/', tags=['Configurations'])
async def delete_configuration(config_id: int, token: str = Header(...)):
    """Удаление конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(
            (Configurations.user_id==current_user.id) &
            (Configurations.id==config_id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация с указанным ID не найдена, или у Вас нет прав на ее удаление.')
        
        config_name = configuration.name_config
        configuration.delete_instance()
        return {'message': f'Конфигурация {config_name} успешно удалена.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении конфигурации: {e}')

@app.get('/configurations/admin/get_all/', tags=['Configurations'])
async def admin_get_all_configurations(token: str = Header(...)):
    """Получение всех конфигураций (только для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configurations = Configurations.select()
        return [{
            'id': config.id,
            'user_id': config.user_id.id,
            'user_name': config.user_id.email,
            'name_config': config.name_config,
            'description': config.description,
            'created_at': config.created_at.isoformat() if config.created_at else None
        } for config in configurations]
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении конфигураций: {e}')

@app.delete('/configurations/admin/delete_by_id/', tags=['Configurations'])
async def admin_delete_configuration(config_id: int, token: str = Header(...)):
    """Удаление любой конфигурации (только для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(Configurations.id==config_id).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация с указанным ID не найдена.')
        
        config_name = configuration.name_config or f"Конфигурация #{configuration.id}"
        user_name = configuration.user_id.email
        
        configuration.delete_instance()
        
        return {
            'message': f'Конфигурация {config_name} пользователя {user_name} успешно удалена.',
            'deleted_config_id': config_id,
            'user_login': user_name
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении конфигурации: {e}')

@app.get('/configurations/admin/get_by_id/', tags=['Configurations'])
async def admin_get_configuration_by_id(config_id: int, token: str = Header(...)):
    """Получение любой конфигурации по ID (только для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')

    try:
        configuration = Configurations.select().where(Configurations.id==config_id).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация с указанным ID не найдена.')

        return {
            'id': configuration.id,
            'user_id': configuration.user_id.id,
            'user_login': configuration.user_id.email,
            'name_config': configuration.name_config,
            'description': configuration.description,
            'created_at': configuration.created_at.isoformat() if configuration.created_at else None
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении конфигурации: {e}')

@app.get('/configurations/{config_id}/components/', tags=['Configurations Components'])
async def get_configuration_components(config_id: int, token: str = Header(...)):
    """Получение всех компонентов конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(
            (Configurations.id==config_id) & 
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация не найдена или у вас нет к ней доступа.')
        
        config_components = ConfigurationsComponents.select().where(
            ConfigurationsComponents.configuration_id==config_id
        )
        
        return [{
            'id': cc.id,
            'component_id': cc.components_id.id,
            'component_name': cc.components_id.name,
            'type_name': cc.components_id.type_id.name if cc.components_id.type_id else None,
            'manufacture_name': cc.components_id.manufactures_id.name if cc.components_id.manufactures_id else None,
            'price': float(cc.components_id.price),
            'quantity': cc.quantity,
            'total_price': float(cc.components_id.price * cc.quantity)
        } for cc in config_components]
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении компонентов конфигурации: {e}')      

@app.post('/configurations/{config_id}/components/', tags=['Configurations Components'])
async def add_component_to_configuration(
    config_id: int, 
    data: ConfigComponentCreate, 
    token: str = Header(...)
):
    """Добавление компонента в конфигурацию"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(
            (Configurations.id==config_id) & 
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация не найдена или у вас нет к ней доступа.')

        component = Components.select().where(Components.name==data.component_name).first()
        if not component:
            raise HTTPException(404, f'Компонент "{data.component_name}" не найден.')

        existing_component = ConfigurationsComponents.select().where(
            (ConfigurationsComponents.configuration_id==config_id) &
            (ConfigurationsComponents.components_id==component.id)
        ).first()
        
        if existing_component:
            raise HTTPException(400, 'Этот компонент уже есть в конфигурации.')

        ConfigurationsComponents.create(
            configuration_id=config_id,
            components_id=component.id,
            quantity=data.quantity
        )
        
        return {'message': f'Компонент "{data.component_name}" успешно добавлен в конфигурацию.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при добавлении компонента: {e}')

@app.put('/configurations/{config_id}/components/{component_id}/', tags=['Configurations Components'])
async def update_configuration_component(
    config_id: int, 
    component_id: int, 
    data: ConfigComponentEdit, 
    token: str = Header(...)
):
    """Изменение количества компонентов в конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    try:
        config = Configurations.select().where(
            (Configurations.id==config_id) &
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not config:
            raise HTTPException(404, 'Конфигурация не найдена, или у вас нет доступа к ней.')
        
        config_component = ConfigurationsComponents.select().where(
            (ConfigurationsComponents.configuration_id==config_id) &
            (ConfigurationsComponents.id==component_id)
        ).first()
        if not config_component:
            raise HTTPException(404, 'Компонент не найден в данной конфигурации.')
        
        config_component.quantity = data.quantity
        config_component.save()
        
        return {'message': 'Количество компонента успешно изменено.'}
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Не удалось изменить количество компонента в конфигурации: {e}')

@app.delete('/configurations/{config_id}/components/{component_id}/', tags=['Configurations Components'])
async def delete_component_in_configuration(
    config_id: int,
    component_id: int,
    token: str = Header(...)
    ):
    """Удаление компонента из конфигурации"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(
            (Configurations.id==config_id) &
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация не найдена, или у вас нет доступа к ней.')
        
        config_component = ConfigurationsComponents.select().where(
            (ConfigurationsComponents.configuration_id==config_id) &
            (ConfigurationsComponents.id==component_id)
        ).first()
        if not config_component:
            raise HTTPException(404, 'Компонент не найден в данной конфигурации.')
        
        component_name = config_component.components_id.name
        config_component.delete_instance()
        
        return {'message': f'Компонент {component_name} успешно удален.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Не удалось удалить компонент из конфигурации: {e}')

@app.get('/configurations/admin/{config_id}/components/', tags=['Configurations Components'])
async def admin_get_configuration_components(config_id: int, token: str = Header(...)):
    """Получение компонентов любой конфигурации (для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        config = Configurations.select().where(Configurations.id==config_id).first()
        if not config:
            raise HTTPException(404, 'Не удалось найти конфигурацию.')
        configuration_components = ConfigurationsComponents.select().where(ConfigurationsComponents.configuration_id==config_id)
        
        return [
            {
                'id': cc.id,
                'component_id': cc.components_id.id,
                'component_name': cc.components_id.name,
                'type_name': cc.components_id.type_id.name if cc.components_id.type_id else None,
                'manufacture_name': cc.components_id.manufactures_id.name if cc.components_id.manufactures_id else None,
                'price': float(cc.components_id.price),
                'quantity': cc.quantity,
                'total_price': float(cc.components_id.price * cc.quantity)
            } for cc in configuration_components]
        
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении компонентов конфигурации: {e}') 

@app.delete('/configurations/admin/{config_id}/components/{component_id}/', tags=['Configurations Components'])
async def admin_remove_component_from_configuration(
    config_id: int, 
    component_id: int, 
    token: str = Header(...)
):
    """Удаление компонента из любой конфигурации (для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        config_component = ConfigurationsComponents.select().where(
            (ConfigurationsComponents.id==component_id) &
            (ConfigurationsComponents.configuration_id==config_id)
        ).first()
        
        if not config_component:
            raise HTTPException(404, 'Связь компонента с конфигурацией не найдена.')
        
        component_name = config_component.components_id.name
        user_login = config_component.configuration_id.user_id.email
        
        config_component.delete_instance()
        
        return {
            'message': f'Компонент "{component_name}" успешно удален из конфигурации пользователя {user_login}.',
            'deleted_component_id': component_id,
            'user_login': user_login
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении компонента: {e}')

@app.get('/order_status/get_all/', tags=['Orders Statuses'])
async def get_all_statuses(token: str = Header(...)):
    """Получение всех статусов заказа"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        statuses = OrdersStatus.select()
        return [{
            'id': status.id,
            'name': status.name
        } for status in statuses]
        
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении статусов заказов: {e}')

@app.post('/order_status/create_status/', tags=['Orders Statuses'])
async def create_order_status(name: str, token: str = Header(...)):
    """Создание нового статуса заказа (только для администратора)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        existing_status = OrdersStatus.select().where(OrdersStatus.name==name).first()
        if existing_status:
            raise HTTPException(400, 'Статус с таким названием уже существует.')
        OrdersStatus.create(name=name)
        return {'message': 'Статус заказа успешно создан.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании статуса заказа: {e}')       

@app.put('/status_order/edit_status', tags=['Orders Statuses'])
async def edit_order_status(id: int, new_name: str, token: str = Header(...)):
    """Изменение статуса заказа"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        status = OrdersStatus.select().where(OrdersStatus.id==id).first()
        if not status:
            raise HTTPException(404, 'Статус заказа с указанным ID не найден.')
        existing_status = OrdersStatus.select().where(OrdersStatus.name==new_name).first()
        if existing_status:
            raise HTTPException(403, f'Статус с заказа {existing_status.name} уже существует.')
        status.name = new_name
        status.save()
        return {'message': 'Статус заказа успешно изменен.'}
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении статуса заказа: {e}') 

@app.delete('/status_order/delete_status', tags=['Orders Statuses'])
async def delete_order_status(id: int, token: str = Header(...)):
    """Удаление статуса заказа"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.') 
    try:
        status = OrdersStatus.select().where(OrdersStatus.id==id).first()
        if not status:
            raise HTTPException(404, 'Статус заказа с указанным ID не найден.')
        
        status.delete_instance()
        return {'message': 'Статус заказа успешно удален.'}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении статуса заказа: {e}') 

@app.get('/orders/get_user_orders/', tags=['Orders'])
async def get_user_orders(token: str = Header(...)):
    """Получение заказов текущего пользователя"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        orders = Orders.select().where(Orders.user_id==current_user.id)
        
        result = []
        for order in orders:
            order_configs = OrderConfigurations.select().where(
                OrderConfigurations.order_id==order.id
            )
            
            configs_list = []
            for oc in order_configs:
                configs_list.append({
                    'configuration_id': oc.configuration_id.id,
                    'configuration_name': oc.configuration_id.name_config,
                    'quantity': oc.quantity,
                    'price_at_time': float(oc.price_at_time)
                })
            
            result.append({
                'id': order.id,
                'order_date': order.order_date.isoformat(),
                'total_amount': float(order.total_amout),
                'status_id': order.status_id.id,
                'status_name': order.status_id.name,
                'configurations': configs_list
            })
        
        return result
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении заказов: {e}')

@app.put('/orders/user/update_order_status/', tags=['Orders'])
async def user_update_order_status(order_id: int, new_status: str, token: str = Header(...)):
    """Изменение статуса заказа пользователем (только для оплаты)"""
    current_user = get_user_by_token(token, 'Пользователь')
    
    try:
        order = Orders.select().where(
            (Orders.id == order_id) & 
            (Orders.user_id == current_user.id)
        ).first()
        
        if not order:
            raise HTTPException(404, 'Заказ не найден или у вас нет к нему доступа.')

        if new_status != 'Оплачен':
            raise HTTPException(403, 'Вы можете изменить статус только на "Оплачен"')
        
        status = OrdersStatus.get_or_none(OrdersStatus.name == new_status)
        if not status:
            raise HTTPException(404, 'Статус не найден.')
        
        order.status_id = status.id
        order.save()
        
        return {
            'message': f'Статус заказа #{order_id} изменен на "{new_status}".',
            'order_id': order_id,
            'new_status': new_status
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении статуса заказа: {e}')

@app.get('/orders/get_order_by_id/', tags=['Orders'])
async def get_order_detail(order_id: int, token: str = Header(...)):
    """Получение деталей заказа"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(
            (Orders.id==order_id) & 
            (Orders.user_id==current_user.id)
        ).first()
        
        if not order:
            raise HTTPException(404, 'Заказ не найден или у вас нет к нему доступа.')

        order_configs = OrderConfigurations.select().where(
            OrderConfigurations.order_id==order.id
        )
        
        configs_list = []
        for oc in order_configs:
            configs_list.append({
                'configuration_id': oc.configuration_id.id,
                'configuration_name': oc.configuration_id.name_config,
                'quantity': oc.quantity,
                'price_at_time': float(oc.price_at_time),
                'total': float(oc.price_at_time * oc.quantity)
            })
        
        return {
            'id': order.id,
            'order_date': order.order_date.isoformat(),
            'total_amount': float(order.total_amout),
            'status_id': order.status_id.id,
            'status_name': order.status_id.name,
            'configurations': configs_list
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении заказа: {e}')

@app.post('/orders/create_order/', tags=['Orders'])
async def create_order(data: OrderCreate, token: str = Header(...)):
    """Создание нового заказа"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        configuration = Configurations.select().where(
            (Configurations.id==data.configuration_id) &
            (Configurations.user_id==current_user.id)
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация не найдена или у вас нет к ней доступа.')

        config_components = ConfigurationsComponents.select().where(
            ConfigurationsComponents.configuration_id==data.configuration_id
        )
        
        if not config_components:
            raise HTTPException(400, 'Конфигурация пустая. Добавьте компоненты перед созданием заказа.')
        
        total_amount = Decimal('0')
        for cc in config_components:
            total_amount += cc.components_id.price * cc.quantity
        
        total_amount *= data.quantity

        status = OrdersStatus.get_or_none(OrdersStatus.name=='В обработке')
        if not status:
            status = OrdersStatus.select().first()
            if not status:
                raise HTTPException(500, 'Не найден статус заказа.')

        order = Orders.create(
            user_id=current_user.id,
            total_amout=total_amount,
            status_id=status.id
        )

        OrderConfigurations.create(
            order_id=order.id,
            configuration_id=data.configuration_id,
            quantity=data.quantity,
            price_at_time=total_amount / data.quantity
        )
        
        return {
            'message': 'Заказ успешно создан.',
            'order_id': order.id,
            'total_amount': float(total_amount)
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при создании заказа: {e}')

@app.delete('/orders/cancel_order/', tags=['Orders'])
async def cancel_order(order_id: int, token: str = Header(...)):
    """Отмена заказа пользователем"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(
            (Orders.id==order_id) & 
            (Orders.user_id==current_user.id)
        ).first()
        
        if not order:
            raise HTTPException(404, 'Заказ не найден или у вас нет к нему доступа.')

        order_name = order.id
        order.delete_instance()
        
        return {'message': f'Заказ {order_name} успешно отменен.'}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при отмене заказа: {e}')

@app.get('/orders/admin/get_all', tags=['Orders'])
async def admin_get_all_orders(token: str = Header(...)):
    """Получение всех заказов (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        orders = Orders.select()
        
        result = []
        for order in orders:
            order_configs = OrderConfigurations.select().where(
                OrderConfigurations.order_id==order.id
            )
            
            configs_list = []
            for oc in order_configs:
                configs_list.append({
                    'configuration_id': oc.configuration_id.id,
                    'configuration_name': oc.configuration_id.name_config,
                    'quantity': oc.quantity,
                    'price_at_time': float(oc.price_at_time)
                })
            
            result.append({
                'id': order.id,
                'user_id': order.user_id.id,
                'user_login': order.user_id.email,
                'order_date': order.order_date.isoformat(),
                'total_amount': float(order.total_amout),
                'status_id': order.status_id.id,
                'status_name': order.status_id.name,
                'configurations': configs_list
            })
        
        return result
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении заказов: {e}')

@app.put('/orders/admin/edit_order_status/', tags=['Orders'])
async def admin_update_order_status(order_id: int, data: OrderStatusUpdate, token: str = Header(...)):
    """Изменение статуса заказа (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(Orders.id==order_id).first()
        if not order:
            raise HTTPException(404, 'Заказ не найден.')
        
        status = OrdersStatus.get_or_none(OrdersStatus.id==data.status_id)
        if not status:
            raise HTTPException(404, 'Статус с указанным ID не найден.')
        
        order.status_id = data.status_id
        order.save()
        
        return {
            'message': f'Статус заказа #{order_id} изменен на "{status.name}".',
            'order_id': order_id,
            'new_status': status.name
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении статуса заказа: {e}')

@app.delete('/orders/admin/delete_order/', tags=['Orders'])
async def admin_delete_order(order_id: int, token: str = Header(...)):
    """Удаление заказа администратором"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(Orders.id==order_id).first()
        
        if not order:
            raise HTTPException(404, 'Заказ не найден.')

        user_login = order.user_id.email
        order_name = order.id

        order.delete_instance()
        
        return {
            'message': f'Заказ {order_name} пользователя {user_login} успешно удален.',
            'deleted_order_id': order_id,
            'user_login': user_login
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении заказа: {e}')

@app.get('/order_configurations/get_user_order_config/', tags=['Order Configurations'])
async def get_order_configurations(order_id: int, token: str = Header(...)):
    """Получение конфигураций заказа"""
    current_user = get_user_by_token(token, 'Пользователь')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(
            (Orders.id==order_id) & 
            (Orders.user_id==current_user.id)
        ).first()
        
        if not order:
            raise HTTPException(404, 'Заказ не найден или у вас нет к нему доступа.')
        
        order_configs = OrderConfigurations.select().where(
            OrderConfigurations.order_id==order_id
        )
        
        result = []
        for oc in order_configs:
            result.append({
                'id': oc.id,
                'configuration_id': oc.configuration_id.id,
                'configuration_name': oc.configuration_id.name_config,
                'quantity': oc.quantity,
                'price_at_time': float(oc.price_at_time),
                'total': float(oc.price_at_time * oc.quantity)
            })
        
        return result
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении конфигураций заказа: {e}')
    
@app.post('/order_configurations/admin/create_config_in_order/', tags=['Order Configurations'])
async def add_configuration_to_order(
    order_id: int, 
    data: OrderConfigCreate, 
    token: str = Header(...)
):
    """Добавление конфигурации в заказ (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order = Orders.select().where(Orders.id == order_id).first()
        if not order:
            raise HTTPException(404, 'Заказ не найден.')

        configuration = Configurations.select().where(
            Configurations.id == data.configuration_id
        ).first()
        
        if not configuration:
            raise HTTPException(404, 'Конфигурация не найдена.')

        existing_config = OrderConfigurations.select().where(
            (OrderConfigurations.order_id == order_id) &
            (OrderConfigurations.configuration_id == data.configuration_id)
        ).first()
        
        if existing_config:
            raise HTTPException(400, 'Эта конфигурация уже есть в заказе.')

        config_components = ConfigurationsComponents.select().where(
            ConfigurationsComponents.configuration_id == data.configuration_id
        )
        
        if not config_components:
            raise HTTPException(400, 'Конфигурация пустая.')
        
        config_price = Decimal('0')
        for cc in config_components:
            config_price += cc.components_id.price * cc.quantity
   
        order_config = OrderConfigurations.create(
            order_id=order_id,
            configuration_id=data.configuration_id,
            quantity=data.quantity,
            price_at_time=config_price
        )

        order.total_amout += config_price * data.quantity
        order.save()
        
        return {
            'message': 'Конфигурация успешно добавлена в заказ.',
            'order_config_id': order_config.id,
            'added_price': float(config_price * data.quantity)
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при добавлении конфигурации в заказ: {e}')

@app.put('/order_configurations/admin/edit_order_config/', tags=['Order Configurations'])
async def update_order_configuration(
    config_id: int, 
    data: OrderConfigUpdate, 
    token: str = Header(...)
):
    """Изменение количества конфигурации в заказе (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order_config = OrderConfigurations.select().where(
            OrderConfigurations.id == config_id
        ).first()

        if not order_config:
            raise HTTPException(404, 'Конфигурация заказа не найдена.')

        order = Orders.select().where(Orders.id == order_config.order_id.id).first()
        if not order:
            raise HTTPException(404, 'Заказ не найден.')

        old_total = order_config.price_at_time * order_config.quantity
        order_config.quantity = data.quantity
        order_config.save()
        new_total = order_config.price_at_time * data.quantity
        order.total_amout = order.total_amout - old_total + new_total
        order.save()
        
        return {
            'message': 'Количество конфигурации в заказе успешно изменено.',
            'order_config_id': config_id,
            'old_quantity': order_config.quantity,
            'new_quantity': data.quantity,
            'price_change': float(new_total - old_total)
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при изменении конфигурации заказа: {e}')

@app.delete('/order_configurations/admin/delete_order_config/', tags=['Order Configurations'])
async def remove_configuration_from_order(config_id: int, token: str = Header(...)):
    """Удаление конфигурации из заказа (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:

        order_config = OrderConfigurations.select().where(
            OrderConfigurations.id == config_id
        ).first()
        
        if not order_config:
            raise HTTPException(404, 'Конфигурация заказа не найдена.')

        order = Orders.select().where(Orders.id == order_config.order_id.id).first()
        if not order:
            raise HTTPException(404, 'Заказ не найден.')

        config_total = order_config.price_at_time * order_config.quantity
        config_name = order_config.configuration_id.name_config
        order_config.delete_instance()
        order.total_amout -= config_total
        order.save()
        
        return {
            'message': f'Конфигурация "{config_name}" успешно удалена из заказа.',
            'removed_config_id': config_id,
            'removed_amount': float(config_total)
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при удалении конфигурации из заказа: {e}')

@app.get('/order_configurations/admin/get_all/', tags=['Order Configurations'])
async def admin_get_all_order_configurations(token: str = Header(...)):
    """Получение всех связей заказов и конфигураций (админ)"""
    current_user = get_user_by_token(token, 'Администратор')
    if not current_user:
        raise HTTPException(401, 'Недействительный токен.')
    
    try:
        order_configs = OrderConfigurations.select()
        
        result = []
        for oc in order_configs:
            result.append({
                'id': oc.id,
                'order_id': oc.order_id.id,
                'order_user_id': oc.order_id.user_id.id,
                'order_user_login': oc.order_id.user_id.email,
                'order_date': oc.order_id.order_date.isoformat(),
                'order_total': float(oc.order_id.total_amout),
                'order_status': oc.order_id.status_id.name,
                'configuration_id': oc.configuration_id.id,
                'configuration_name': oc.configuration_id.name_config,
                'configuration_user_id': oc.configuration_id.user_id.id,
                'configuration_user_login': oc.configuration_id.user_id.email,
                'quantity': oc.quantity,
                'price_at_time': float(oc.price_at_time),
                'total': float(oc.price_at_time * oc.quantity)
            })
        
        return {
            'total_count': len(result),
            'order_configurations': result
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при получении связей заказов и конфигураций: {e}')


    
