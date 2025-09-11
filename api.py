from fastapi import FastAPI, HTTPException, Header
from typing import Optional
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
        if required_role:
            user_role = Roles.get_by_id(user.role_id)
            if user_role.name != required_role:
                raise HTTPException(403, 'Недостаточно прав для выполнения этого действия.')
        
        user_token.expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        user_token.save()
        
        return user
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(500, f'Ошибка при проверке токена: {e}')
        

class AuthRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str

class SetRoleRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    new_role: str
    
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
        
        