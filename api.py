from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from hashing_password import hash_password
import re
from models import Roles, Users, PasswordChangeRequest, UserToken, Manufactures, ComponentsTypes, Components, \
    Configurations, ConfigurationsComponents, OrdersStatus, Orders, OrderConfigurations
from database import db_connection
from pydantic import BaseModel

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

def get_user_by_token(token: str, ):
    pass

class AuthRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str
    
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
            raise(404, 'Пользователя с таким email/номером телефона не  существует.')
        enter_hash_password = hash_password(password)
        if enter_hash_password