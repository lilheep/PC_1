import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import requests
import os
import re
import json

os.environ['TCL_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tk8.6'

class MainApp:
    def __init__(self, root, token):
        self.root = root
        self.root.title('ANTech - Конфигуратор ПК')
        self.root.state('zoomed')
        self.root.configure(bg='#f5f5f5')
        self.token = token
        self.user_data = None
        self.base_url = 'http://127.0.0.1:8000'
        self.load_user_data()
         
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Normal.TLabel', font=('Arial', 12))
        self.style.configure('Accent.TButton', font=('Arial', 12), background='#5814ea', foreground='#ffffff')
        
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill='both', expand=True)
        
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill='x', pady=10)
        
        ttk.Label(self.header_frame, text=f'Добро пожаловать, {self.user_data["name"]}!', style='Header.TLabel').pack(side='left', padx=20)
        ttk.Button(self.header_frame, text='Выход', command=self.logout, style='Accent.TButton').pack(side='right', padx=20)
        
        self.tab_control = ttk.Notebook(self.main_container)
        
        self.tab_catalog = ttk.Frame(self.tab_control)
        self.tab_configurations = ttk.Frame(self.tab_control)
        self.tab_orders = ttk.Frame(self.tab_control)
        self.tab_profile = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_catalog, text='Каталог компонентов')
        self.tab_control.add(self.tab_configurations, text='Мои конфигурации')
        self.tab_control.add(self.tab_orders, text='Мои заказы')
        self.tab_control.add(self.tab_profile, text='Профиль')
        
        self.tab_control.pack(fill='both', expand=1)
        
        self.init_catalog_tab()
        self.init_configurations_tab()
        self.init_orders_tab()
        self.init_profile_tab()
    
    def load_user_data(self):
        """Загрузка данных пользователя по API"""
        try:
            headers = {'token': self.token}
            response = requests.get(f'{self.base_url}/users/me/', headers=headers)
            if response.status_code == 200:
                self.user_data = response.json()
            else:
                messagebox.showerror('Ошибка!', 'Не удалось получить данные пользователя')
                self.logout()
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения с сервером: {e}')
            self.logout()
    
    def logout(self):
        self.root.destroy()
        root = tk.Tk()
        AuthApp(root)
        root.mainloop()
        
    def init_catalog_tab(self):
        """Функция для отображения каталога с компонентами"""
        ttk.Label(self.tab_catalog, text='Каталог компонентов', style='Header.TLabel').pack(pady=10)
        ttk.Button(self.tab_catalog, text='Обновить', command=self.load_components, style='Accent.TButton').pack(pady=5)
        
        columns = ('id', 'name', 'type', 'manufacture', 'price', 'stock')
        self.tree = ttk.Treeview(self.tab_catalog, columns=columns, show='headings', height=20)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Название')
        self.tree.heading('type', text='Тип')
        self.tree.heading('manufacture', text='Производитель')
        self.tree.heading('price', text='Цена')
        self.tree.heading('stock', text='Наличие')
        
        self.tree.column('id', width=50)
        self.tree.column('name', width=200)
        self.tree.column('type', width=150)
        self.tree.column('manufacture', width=150)
        self.tree.column('price', width=100)
        self.tree.column('stock', width=100)
        
        scrollbar = ttk.Scrollbar(self.tab_catalog, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<<TreeviewSelect>>', self.show_component_specification)
        
        self.spec_frame = ttk.Frame(self.tab_catalog)   
        self.spec_frame.pack(fill='x', padx=10, pady=10)
        self.spec_text = ttk.Label(self.spec_frame, text='Спецификация:', height=8, state='disabled')
        self.spec_text.pack(fill='x', pady=5)
        
        self.load_components()
        
    def load_components(self):
        """Загрузка компонентов из API"""
        try:
            headers = {'token': self.token}
            response = requests.get(f'{self.base_url}/components/get_all/', headers=headers)
            
            if response.status_code == 200: 
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                components = response.json()
                
                self.components_data = components
                
                for component in components:
                    self.tree.insert('', 'end', values=(
                        component['id'],
                        component['name'],
                        component['type_name'],
                        component['manufacture_name'],
                        component['price'],
                        component['stock_quantity']
                    ))
            else:
                messagebox.showerror('Ошибка!', 'Не удалось загрузить данные о компонентах')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Не удалось получить данные от сервера: {e}')
    
    def show_component_specification(self):
        """Отображение выбранного элемента"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        item_index = self.tree.index(item)       
        
        component = self.components_data[item_index]
        specification = component.get('specification')
        
        
class AuthApp:
    """Класс для создания окна авторизации пользователей"""
    def __init__(self, root):
        """Инициализация окна авторизации"""
        self.root = root
        self.root.title('')
        self.root.geometry('1920x1080')
        self.root.state('zoomed')
        
        self.bg_color = '#f5f5f5'
        self.fg_color = '#333333'
        self.accent_color = "#5814ea"
        self.button_fg = '#ffffff'
        self.entry_bg = '#ffffff'
        
        self.title_font = Font(family='Helvetica', size=30, weight='bold')
        self.normal_font = Font(family='Arial', size=14, weight='normal') 
        self.root.configure(bg=self.bg_color)
        
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.create_auth_widgets()
        
        self.base_url = 'http://127.0.0.1:8000'
        self.token = None
    
    def create_auth_widgets(self):
        """Создание виджетов аутентификации"""
        tk.Label(self.main_frame,
                 text='Приветствуем вас в ANtech',
                 font=self.title_font,
                 bg=self.bg_color,
                 fg=self.fg_color
                 ).grid(row=0, column=0, columnspan=2, pady=(0, 40))

        tk.Label(
            self.main_frame, 
            text='Email или телефон:', 
            font=self.normal_font,
            bg=self.bg_color,
            fg=self.fg_color
        ).grid(row=1, column=0, sticky='e', padx=10, pady=5)
        
        self.login_entry = ttk.Entry(self.main_frame, width=30, font=self.normal_font)
        self.login_entry.grid(row=1, column=1, pady=5, ipady=5)
        
        tk.Label(
            self.main_frame,
            text='Пароль:',
            font=self.normal_font,
            bg=self.bg_color,
            fg=self.fg_color
        ).grid(row=2, column=0, sticky='e', padx=10, pady=5)
        
        self.password_entry = ttk.Entry(self.main_frame, width=30, show='*', font=self.normal_font)
        self.password_entry.grid(row=2, column=1, pady=5, ipady=5)

        btn_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        btn_frame.grid(row=3, columnspan=2, pady=30)
        
        style = ttk.Style()
        style.configure('TButton', 
                      font=self.normal_font, 
                      background=self.accent_color,
                      foreground=self.button_fg,
                      padding=10)
        
        ttk.Button(btn_frame,
                   text='Войти',
                   command=self.login,
                   style='TButton'
                   ).pack(side='left', padx=10)
        
        ttk.Button(btn_frame,
                   text='Регистрация',
                   command=self.show_register,
                   style='TButton'
                   ).pack(side='left', padx=10)
        
        ttk.Button(btn_frame,
                   text='Забыли пароль?',
                   command=self.show_forgot_password,
                   style='TButton'
                   ).pack(side='left', padx=10)
        
    def is_phone(self, text):
        """Проверяет, является ли текст номером телефона"""
        phone_pattern = r'^[\d\s\-\+\(\)]+$'
        return bool(re.match(phone_pattern, text)) and len(text) >= 5
        
    def login(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()
    
        if not login or not password:
            messagebox.showerror('Ошибка!', 'Заполните все поля.')
            return
        try:
            if self.is_phone(login):
                auth_data = {'phone': login, 'password': password}
            else:
                auth_data = {'email': login, 'password': password}
            
            response = requests.post(
                f'{self.base_url}/users/auth/',
                json=auth_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.token_expires = data.get('expires_at')
                self.open_main_app()
            else:
                error = response.json().get('detail', 'Ошибка авторизации')
                messagebox.showerror('Ошибка!', f'Ошибка авторизации: {error}')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')
    
    def open_main_app(self):
        self.root.destroy()
        root = tk.Tk()
        MainApp(root, self.token)
        root.mainloop()
    
    def show_register(self):
        register_window = tk.Toplevel(self.root)
        register_window.title('Регистрация')
        register_window.geometry('600x500')
        register_window.resizable(False, False)
        
        tk.Label(
            register_window,
            text='Регистрация',
            font=self.title_font
        ).pack(pady=20)
        
        form_frame = tk.Frame(register_window)
        form_frame.pack(pady=20)
        
        tk.Label(
            form_frame,
            text='Email:',
            font=self.normal_font
        ).grid(row=0, column=0, pady=5, ipady=5)
        
        self.reg_email = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_email.grid(row=0, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Пароль:',
            font=self.normal_font
        ).grid(row=1, column=0, padx=10, pady=5)
        
        self.reg_password = ttk.Entry(form_frame, width=30, show='*', font=self.normal_font)
        self.reg_password.grid(row=1, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Подтвердите пароль:',
            font=self.normal_font
        ).grid(row=2, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_confirm_password = ttk.Entry(form_frame, width=30, show='*', font=self.normal_font)
        self.reg_confirm_password.grid(row=2, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='ФИО:',
            font=self.normal_font
        ).grid(row=3, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_full_name = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_full_name.grid(row=3, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Телефон:',
            font=self.normal_font
        ).grid(row=4, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_phone = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_phone.grid(row=4, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Адрес:',
            font=self.normal_font
        ).grid(row=5, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_address = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_address.grid(row=5, column=1, sticky='e', padx=10, pady=5)
        
        ttk.Button(
            register_window,
            text='Зарегистрироваться',
            command=self.register,
            style='TButton'
        ).pack(pady=20)
        
    def register(self):
        """"Регистрация нового пользователя"""
        data = {
            'email': self.reg_email.get(),
            'password': self.reg_password.get(),
            'confirm_password': self.reg_confirm_password.get(),
            'full_name': self.reg_full_name.get(),
            'phone': self.reg_phone.get(),
            'address': self.reg_address.get()
        }
        
        if not all(data.values()):
            messagebox.showerror('Ошибка!', 'Все поля обязательны')
            return
        
        if data['password'] != data['confirm_password']:
            messagebox.showerror('Ошибка!', 'Пароли не совпадают')
            return
        
        try:
            response = requests.post(
                f'{self.base_url}/users/register/',
                params={
                    'email': data['email'],
                    'password': data['password'],
                    'full_name': data['full_name'],
                    'number_phone': data['phone'],
                    'address': data['address']
                    }
            )
            if response.status_code == 200:
                messagebox.showinfo('Успех!', 'Регистрация успешна')
                self.reg_email.master.destroy()
            else:
                error = response.json().get('detail', 'Ошибка регистрации')
                messagebox.showerror('Ошибка', error)
        except requests.exceptions.RequestException:
            messagebox.showerror('Ошибка', 'Не удалось подключиться к серверу')
            
    def show_forgot_password(self):
        """Отображение окна восстановления пароля"""           
        self.forgot_window = tk.Toplevel(self.root)
        self.forgot_window.title('Восстановление пароля')
        self.forgot_window.geometry('600x500')
        self.forgot_window.resizable(False, False)
        
        tk.Label(
            self.forgot_window,
            text='Введите email для восстановления пароля',
            font=self.normal_font
        ).pack(pady=20)
        
        self.email_entry = ttk.Entry(self.forgot_window, width=30, font=self.normal_font)
        self.email_entry.pack(pady=10)
        
        self.send_code_btn = ttk.Button(
            self.forgot_window,
            text='Отправить код',
            command=self.send_confirmation_code,
            style='TButton'
        )
        self.send_code_btn.pack(pady=20)
        
        self.code_frame = tk.Frame(self.forgot_window)
        
    def send_confirmation_code(self):
        """Отправка кода подтверждения"""
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showerror('Ошибка!', 'Введите email')
            return
        
        try:
            response = requests.post(
                f'{self.base_url}/users/change_password/',
                params={'email': email}
            )
            
            if response.status_code == 200:
                messagebox.showinfo('Успех!', 'Код подтверждения отправлен на ваш email')
                self.send_code_btn.pack_forget()
                
                tk.Label(
                    self.code_frame,
                    text='Введите код подтверждения:',
                    font=self.normal_font
                    ).pack(pady=10)
                
                self.code_entry = ttk.Entry(self.code_frame, width=30, font=self.normal_font)
                self.code_entry.pack(pady=10)
                
                tk.Label(
                    self.code_frame,
                    text='Новый пароль:',
                    font=self.normal_font
                ).pack(pady=10)
                
                self.new_password_entry = ttk.Entry(self.code_frame, width=30, show='*', font=self.normal_font)
                self.new_password_entry.pack(pady=10)
                
                ttk.Button(
                    self.code_frame,
                    text='Подтвердить',
                    command=self.confirm_change_password,
                    style='TButton'
                ).pack(pady=20)
                
                self.code_frame.pack()
            else:
                error = response.json().get('detail', 'Ошибка отправки кода')
                messagebox.showerror('Ошибка!', error)
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')
        
    def confirm_change_password(self):
        """Подтверждение смены пароля"""
        email = self.email_entry.get().strip()
        code = self.code_entry.get().strip()
        new_password = self.new_password_entry.get().strip()
        
        if not all([email, code, new_password]):
            messagebox.showerror('Ошибка!', 'Заполните все поля')
            return
        
        try:
            response = requests.post(
                f'{self.base_url}/users/confirm_change_password/',
                params={
                    'email': email,
                    'code': code,
                    'new_password': new_password
                }
            )
            
            if response.status_code == 200:
                messagebox.showinfo('Успех!', 'Пароль успешно изменен')
                self.forgot_window.destroy()
            else:
                error = response.json().get('detail', 'Ошибка смены пароля')
                messagebox.showerror('Ошибка!', error)
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')
        
        
if __name__ == '__main__':
    root = tk.Tk()
    app = AuthApp(root)
    root.mainloop()
        