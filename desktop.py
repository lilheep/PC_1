import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import requests
import os
import re

os.environ['TCL_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tk8.6'

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
        
            

if __name__ == '__main__':
    root = tk.Tk()
    app = AuthApp(root)
    root.mainloop()
        