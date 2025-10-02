import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import Font
import requests
import os
import re
import json

# os.environ['TCL_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tcl8.6'
# os.environ['TK_LIBRARY'] = r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tk8.6'

class MainApp:
    def __init__(self, root, token):
        self.root = root
        self.root.title('ANTech - Конфигуратор ПК')
        self.root.state('zoomed')
        self.root.configure(bg='#40E0D0')
        self.token = token
        self.user_data = None
        self.base_url = 'http://127.0.0.1:8000'
        self.load_user_data()
        
        if self.user_data and self.user_data.get('role') == 'Администратор':
            self.open_admin_app()
            return
         
        self.style = ttk.Style()
        
        self.style.configure('Header.TLabel', 
                           font=('Arial', 16, 'bold'),
                           background='#40E0D0',
                           foreground='black')
        
        self.style.configure('Normal.TLabel', 
                           font=('Arial', 12),
                           background='#40E0D0',
                           foreground='black')
        
        self.style.configure('Accent.TButton', 
                           font=('Arial', 12), 
                           background='white',
                           foreground='black',
                           borderwidth=2,
                           focuscolor='none')
        
        self.style.configure('TFrame', 
                           background='#40E0D0')
        
        self.style.configure('TNotebook', 
                           background='#40E0D0')
        
        self.style.configure('TNotebook.Tab', 
                           background='white',
                           foreground='black')
        
        self.style.configure('Treeview',
                           background='white',
                           foreground='black',
                           fieldbackground='white')
        
        self.style.configure('Treeview.Heading',
                           background='#40E0D0',
                           foreground='black',
                           font=('Arial', 10, 'bold'))
        
        self.style.configure('TEntry',
                           fieldbackground='white',
                           foreground='black')
        
        self.style.configure('TCombobox',
                           fieldbackground='white',
                           foreground='black')
        
        self.main_container = ttk.Frame(root, style='TFrame')
        self.main_container.pack(fill='both', expand=True)
        
        self.header_frame = ttk.Frame(self.main_container, style='TFrame')
        self.header_frame.pack(fill='x', pady=10)
        
        ttk.Label(self.header_frame, text=f'Добро пожаловать, {self.user_data["name"]}!', style='Header.TLabel').pack(side='left', padx=20)
        ttk.Button(self.header_frame, text='Выход', command=self.logout, style='Accent.TButton').pack(side='right', padx=20)
        
        self.tab_control = ttk.Notebook(self.main_container)
        
        self.tab_catalog = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_configurations = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_orders = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_profile = ttk.Frame(self.tab_control, style='TFrame')
        
        self.tab_control.add(self.tab_catalog, text='Каталог компонентов')
        self.tab_control.add(self.tab_configurations, text='Мои конфигурации')
        self.tab_control.add(self.tab_orders, text='Мои заказы')
        self.tab_control.add(self.tab_profile, text='Профиль')
        
        self.tab_control.pack(fill='both', expand=1)
        
        self.init_catalog_tab()
        self.init_configurations_tab()
        self.init_orders_tab()
        self.init_profile_tab()
    
    def open_admin_app(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        AdminApp(self.root, self.token)
    
    def load_user_data(self):
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
        for widget in self.root.winfo_children():
            widget.destroy()
        AuthApp(self.root)
        
    def init_catalog_tab(self):
        ttk.Label(self.tab_catalog, text='Каталог компонентов', style='Header.TLabel').pack(pady=10)

        filter_frame = ttk.Frame(self.tab_catalog, style='TFrame')
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text='Тип:', style='Normal.TLabel').pack(side='left', padx=5)
        self.type_filter = tk.StringVar()
        self.type_combo = ttk.Combobox(filter_frame, textvariable=self.type_filter, state='readonly', width=15, style='TCombobox')
        self.type_combo.pack(side='left', padx=5)

        ttk.Label(filter_frame, text='Цена от:', style='Normal.TLabel').pack(side='left', padx=5)
        self.min_price_filter = tk.StringVar()
        min_price_entry = ttk.Entry(filter_frame, textvariable=self.min_price_filter, width=8, style='TEntry')
        min_price_entry.pack(side='left', padx=2)
        
        ttk.Label(filter_frame, text='до:', style='Normal.TLabel').pack(side='left', padx=2)
        self.max_price_filter = tk.StringVar()
        max_price_entry = ttk.Entry(filter_frame, textvariable=self.max_price_filter, width=8, style='TEntry')
        max_price_entry.pack(side='left', padx=5)
 
        ttk.Button(filter_frame, text='✔️', 
                command=self.apply_filters, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(filter_frame, text='🔄', 
                command=self.reset_filters, style='Accent.TButton').pack(side='left', padx=5)
     
        search_frame = ttk.Frame(self.tab_catalog, style='TFrame')
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text='Поиск:', style='Normal.TLabel').pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, style='TEntry')
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text='🔎', 
                command=self.search_components, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(search_frame, text='🔄', 
                command=self.clear_search, style='Accent.TButton').pack(side='left', padx=5)
        
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
        
        self.spec_frame = ttk.Frame(self.tab_catalog, style='TFrame')   
        self.spec_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(self.spec_frame, text='Характеристики:', style='Header.TLabel').pack(anchor='w')
        
        self.spec_text = scrolledtext.ScrolledText(self.spec_frame, height=8, state='disabled',
                                                bg='white', fg='black', font=('Arial', 10))
        self.spec_text.pack(fill='x', pady=5)
        
        search_entry.bind('<Return>', lambda event: self.search_components())

        self.all_components = []
        self.filtered_components = []
        self.available_types = set()
        
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
                
                self.all_components = components
                self.filtered_components = components.copy()

                self.available_types = set()
                for component in components:
                    if component.get('type_name'):
                        self.available_types.add(component['type_name'])

                self.type_combo['values'] = ["Все типы"] + sorted(list(self.available_types))
                self.type_combo.set("Все типы")

                self.display_filtered_components()
            else:
                messagebox.showerror('Ошибка!', 'Не удалось загрузить данные о компонентах')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Не удалось получить данные от сервера: {e}')
    
    def apply_filters(self):
        """Применение фильтров к каталогу компонентов"""
        if not hasattr(self, 'all_components') or not self.all_components:
            return
        
        filtered = self.all_components.copy()

        selected_type = self.type_filter.get()
        if selected_type and selected_type != "Все типы":
            filtered = [comp for comp in filtered if comp.get('type_name') == selected_type]

        min_price = self.min_price_filter.get()
        if min_price:
            try:
                min_price_val = float(min_price)
                filtered = [comp for comp in filtered if comp.get('price', 0) >= min_price_val]
            except ValueError:
                pass 

        max_price = self.max_price_filter.get()
        if max_price:
            try:
                max_price_val = float(max_price)
                filtered = [comp for comp in filtered if comp.get('price', 0) <= max_price_val]
            except ValueError:
                pass

        search_term = self.search_var.get().strip().lower()
        if search_term:
            filtered = [comp for comp in filtered if (
                search_term in comp['name'].lower() or 
                search_term in comp['type_name'].lower() or 
                search_term in comp['manufacture_name'].lower()
            )]
        
        self.filtered_components = filtered
        self.display_filtered_components()

    def reset_filters(self):
        """Сброс фильтров"""
        self.type_filter.set('')
        self.min_price_filter.set('')
        self.max_price_filter.set('')
        self.search_var.set('')
        self.filtered_components = self.all_components.copy()
        self.display_filtered_components()

    def display_filtered_components(self):
        """Отображение отфильтрованных компонентов"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for component in self.filtered_components:
            self.tree.insert('', 'end', values=(
                component['id'],
                component['name'],
                component['type_name'],
                component['manufacture_name'],
                component['price'],
                component['stock_quantity']
            ))
    
    def search_components(self):
        """Поиск компонентов по названию, типу или производителю"""
        self.apply_filters()
        
        if self.search_var.get().strip():
            messagebox.showinfo('Поиск', f'Найдено компонентов: {len(self.filtered_components)}')

    def clear_search(self):
        """Сброс поиска и отображение всех компонентов"""
        self.search_var.set('')
        self.apply_filters()

    def update_components_table(self, components):
        """Обновление таблицы с компонентами"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for component in components:
            self.tree.insert('', 'end', values=(
                component['id'],
                component['name'],
                component['type_name'],
                component['manufacture_name'],
                component['price'],
                component['stock_quantity']
            ))

        self.filtered_components_data = components
    
    def show_component_specification(self, event):
        """Отображение выбранного элемента"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        item_index = self.tree.index(item)       

        components_to_use = self.filtered_components
        
        if item_index >= len(components_to_use):
            return
            
        component = components_to_use[item_index]
        specification = component.get('specification')
        self.spec_text.config(state='normal')
        self.spec_text.delete(1.0, tk.END)
        
        if specification:
            try:
                formated_spec = json.dumps(specification, indent=2, ensure_ascii=False)
                self.spec_text.insert(tk.END, formated_spec)
            except:
                self.spec_text.insert(tk.END, str(specification))
        else:    
            self.spec_text.insert(tk.END, 'Дополнительная информация о товаре отсутствует.')
            
        self.spec_text.config(state='disabled')
    
    def init_configurations_tab(self):
        main_frame = ttk.Frame(self.tab_configurations, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(main_frame, text='Мои конфигурации ПК', style='Header.TLabel').pack(pady=10)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='➕', 
                command=self.create_new_configuration, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='🔄', 
                command=self.load_configurations, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='❌', 
                command=self.delete_configuration, style='Accent.TButton').pack(side='left', padx=5)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, pady=10)

        left_frame = ttk.Frame(paned_window, style='TFrame')
        paned_window.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text='Мои конфигурации:', style='Normal.TLabel').pack(anchor='w', pady=5)

        columns = ('id', 'name', 'description', 'created')
        self.config_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        
        self.config_tree.heading('id', text='ID')
        self.config_tree.heading('name', text='Название')
        self.config_tree.heading('description', text='Описание')
        self.config_tree.heading('created', text='Дата создания')
        
        self.config_tree.column('id', width=50)
        self.config_tree.column('name', width=150)
        self.config_tree.column('description', width=200)
        self.config_tree.column('created', width=120)
        
        scrollbar_left = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
        self.config_tree.configure(yscroll=scrollbar_left.set)
        
        self.config_tree.pack(side='left', fill='both', expand=True)
        scrollbar_left.pack(side='right', fill='y')

        right_frame = ttk.Frame(paned_window, style='TFrame')
        paned_window.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text='Сборка конфигурации:', style='Normal.TLabel').pack(anchor='w', pady=5)

        config_columns = ('type', 'component', 'price', 'quantity', 'total')
        self.config_components_tree = ttk.Treeview(right_frame, columns=config_columns, show='headings', height=10)
        
        self.config_components_tree.heading('type', text='Тип')
        self.config_components_tree.heading('component', text='Компонент')
        self.config_components_tree.heading('price', text='Цена')
        self.config_components_tree.heading('quantity', text='Кол-во')
        self.config_components_tree.heading('total', text='Итого')
        
        self.config_components_tree.column('type', width=100)
        self.config_components_tree.column('component', width=200)
        self.config_components_tree.column('price', width=80)
        self.config_components_tree.column('quantity', width=60)
        self.config_components_tree.column('total', width=80)
        
        scrollbar_right = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.config_components_tree.yview)
        self.config_components_tree.configure(yscroll=scrollbar_right.set)
        
        self.config_components_tree.pack(fill='both', expand=True)
        scrollbar_right.pack(side='right', fill='y')

        bottom_frame = ttk.Frame(right_frame, style='TFrame')
        bottom_frame.pack(fill='x', pady=10)
        
        self.total_label = ttk.Label(bottom_frame, text='Общая сумма: 0 руб.', style='Header.TLabel')
        self.total_label.pack(side='left', padx=10)

        manage_frame = ttk.Frame(bottom_frame, style='TFrame')
        manage_frame.pack(side='right', padx=10)
        
        ttk.Button(manage_frame, text='➕', 
                command=self.add_component_to_config, style='Accent.TButton').pack(side='left', padx=2)
        ttk.Button(manage_frame, text='❌', 
                command=self.remove_component_from_config, style='Accent.TButton').pack(side='left', padx=2)
        ttk.Button(manage_frame, text='Создать заказ', 
                command=self.create_order_from_config, style='Accent.TButton').pack(side='left', padx=2)

        self.config_tree.bind('<<TreeviewSelect>>', self.on_configuration_select)
        self.config_components_tree.bind('<<TreeviewSelect>>', self.on_component_select)

        self.load_configurations()

    def load_configurations(self):
        try:
            headers = {'token': self.token}
            response = requests.get(f'{self.base_url}/configurations/get_all/', headers=headers)
            
            if response.status_code == 200:
                for item in self.config_tree.get_children():
                    self.config_tree.delete(item)
                
                configurations = response.json()
                self.configurations_data = {}
                
                for config in configurations:
                    config_id = config['id']
                    self.configurations_data[config_id] = config

                    created_at = config.get('created_at', '')
                    if created_at:
                        try:
                            created_at = created_at.split('T')[0]
                        except:
                            pass
                    
                    self.config_tree.insert('', 'end', values=(
                        config_id,
                        config['name_config'] or f'Конфигурация #{config_id}',
                        config['description'] or '-',
                        created_at
                    ))
            else:
                messagebox.showerror('Ошибка!', 'Не удалось загрузить конфигурации')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

    def on_configuration_select(self, event):
        selected = self.config_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        config_id = self.config_tree.item(item)['values'][0]
        self.current_config_id = config_id

        self.load_configuration_components(config_id)

    def load_configuration_components(self, config_id):
        try:
            headers = {'token': self.token}
            response = requests.get(f'{self.base_url}/configurations/{config_id}/components/', headers=headers)
            
            if response.status_code == 200:
                for item in self.config_components_tree.get_children():
                    self.config_components_tree.delete(item)
                
                components = response.json()
                total_amount = 0
                
                for component in components:
                    total_price = component['total_price']
                    total_amount += total_price
                    
                    self.config_components_tree.insert('', 'end', values=(
                        component['type_name'] or '-',
                        component['component_name'],
                        f"{component['price']:.2f} руб.",
                        component['quantity'],
                        f"{total_price:.2f} руб."
                    ), tags=(component['id'],))
                
                self.total_label.config(text=f'Общая сумма: {total_amount:.2f} руб.')
            else:
                messagebox.showerror('Ошибка!', 'Не удалось загрузить компоненты конфигурации')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

    def on_component_select(self, event):
        self.selected_component_id = None
        selected = self.config_components_tree.selection()
        if selected:
            item = selected[0]
            self.selected_component_id = self.config_components_tree.item(item)['tags'][0]

    def create_new_configuration(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Создание новой конфигурации')
        dialog.geometry('500x300')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Название конфигурации:', style='Normal.TLabel').pack(pady=10)
        name_entry = ttk.Entry(dialog, width=40, style='TEntry')
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text='Описание (необязательно):', style='Normal.TLabel').pack(pady=10)
        desc_entry = ttk.Entry(dialog, width=40, style='TEntry')
        desc_entry.pack(pady=5)
        
        def create_config():
            name = name_entry.get().strip()
            description = desc_entry.get().strip()
            
            if not name:
                messagebox.showerror('Ошибка!', 'Введите название конфигурации')
                return
            
            try:
                headers = {'token': self.token}
                response = requests.post(
                    f'{self.base_url}/configurations/create/',
                    headers=headers,
                    json={'name_config': name, 'description': description}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Конфигурация создана')
                    dialog.destroy()
                    self.load_configurations()
                else:
                    error = response.json().get('detail', 'Ошибка создания')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
        
        button_frame = ttk.Frame(dialog, style='TFrame')
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text='✔️', command=create_config, style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(button_frame, text='❌', command=dialog.destroy, style='Accent.TButton').pack(side='left', padx=10)

    def add_component_to_config(self):
        if not hasattr(self, 'current_config_id') or not self.current_config_id:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию для добавления компонентов')
            return

        if not hasattr(self, 'all_components') or not self.all_components:
            messagebox.showwarning('Внимание!', 'Сначала загрузите каталог компонентов')
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title('Добавление компонента')
        dialog.geometry('600x400')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Выберите компонент:', style='Normal.TLabel').pack(pady=10)

        filter_frame = ttk.Frame(dialog, style='TFrame')
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text='Фильтр по типу:', style='Normal.TLabel').pack(side='left')
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(filter_frame, textvariable=type_var, style='TCombobox')

        types = list(set(comp['type_name'] for comp in self.all_components if comp['type_name']))
        type_combo['values'] = ['Все'] + types
        type_combo.set('Все')
        type_combo.pack(side='left', padx=5)

        columns = ('name', 'type', 'manufacture', 'price', 'stock')
        comp_tree = ttk.Treeview(dialog, columns=columns, show='headings', height=10)
        
        comp_tree.heading('name', text='Название')
        comp_tree.heading('type', text='Тип')
        comp_tree.heading('manufacture', text='Производитель')
        comp_tree.heading('price', text='Цена')
        comp_tree.heading('stock', text='Наличие')
        
        comp_tree.column('name', width=200)
        comp_tree.column('type', width=100)
        comp_tree.column('manufacture', width=100)
        comp_tree.column('price', width=80)
        comp_tree.column('stock', width=60)
        
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=comp_tree.yview)
        comp_tree.configure(yscroll=scrollbar.set)
        
        comp_tree.pack(fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y')

        quantity_frame = ttk.Frame(dialog, style='TFrame')
        quantity_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(quantity_frame, text='Количество:', style='Normal.TLabel').pack(side='left')
        quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=100, textvariable=quantity_var, width=10, style='TEntry')
        quantity_spin.pack(side='left', padx=5)
        
        def filter_components():
            for item in comp_tree.get_children():
                comp_tree.delete(item)
            
            selected_type = type_var.get()
            for component in self.all_components:
                if selected_type == 'Все' or component['type_name'] == selected_type:
                    comp_tree.insert('', 'end', values=(
                        component['name'],
                        component['type_name'] or '-',
                        component['manufacture_name'] or '-',
                        f"{component['price']:.2f} руб.",
                        component['stock_quantity']
                    ), tags=(component['name'],))
        
        def add_selected_component():
            selected = comp_tree.selection()
            if not selected:
                messagebox.showwarning('Внимание!', 'Выберите компонент')
                return
            
            item = selected[0]
            component_name = comp_tree.item(item)['tags'][0]
            quantity = quantity_var.get()
            
            try:
                headers = {'token': self.token}
                response = requests.post(
                    f'{self.base_url}/configurations/{self.current_config_id}/components/',
                    headers=headers,
                    json={'component_name': component_name, 'quantity': quantity}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Компонент добавлен')
                    dialog.destroy()
                    self.load_configuration_components(self.current_config_id)
                else:
                    error = response.json().get('detail', 'Ошибка добавления')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
    
        filter_components()

        type_combo.bind('<<ComboboxSelected>>', lambda e: filter_components())
        
        button_frame = ttk.Frame(dialog, style='TFrame')
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text='➕', command=add_selected_component, 
                style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(button_frame, text='❌', command=dialog.destroy, style='Accent.TButton').pack(side='left', padx=10)

    def remove_component_from_config(self):
        if not hasattr(self, 'current_config_id') or not self.current_config_id:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию')
            return
        
        if not hasattr(self, 'selected_component_id') or not self.selected_component_id:
            messagebox.showwarning('Внимание!', 'Выберите компонент для удаления')
            return
        
        try:
            headers = {'token': self.token}
            response = requests.delete(
                f'{self.base_url}/configurations/{self.current_config_id}/components/{self.selected_component_id}/',
                headers=headers
            )
            
            if response.status_code == 200:
                messagebox.showinfo('Успех!', 'Компонент удален')
                self.load_configuration_components(self.current_config_id)
            else:
                error = response.json().get('detail', 'Ошибка удаления')
                messagebox.showerror('Ошибка!', error)
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

    def create_order_from_config(self):
        if not hasattr(self, 'current_config_id') or not self.current_config_id:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию для заказа')
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title('Создание заказа')
        dialog.geometry('300x150')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Количество конфигураций:', style='Normal.TLabel').pack(pady=10)
        quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(dialog, from_=1, to=100, textvariable=quantity_var, width=10, style='TEntry')
        quantity_spin.pack(pady=5)
        
        def create_order():
            quantity = quantity_var.get()
            
            try:
                headers = {'token': self.token}
                response = requests.post(
                    f'{self.base_url}/orders/create_order/',
                    headers=headers,
                    json={'configuration_id': self.current_config_id, 'quantity': quantity}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    messagebox.showinfo('Успех!', f'Заказ создан! ID: {result["order_id"]}')

                    self.load_components()
                    
                    dialog.destroy()
                else:
                    error = response.json().get('detail', 'Ошибка создания заказа')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
        
        button_frame = ttk.Frame(dialog, style='TFrame')
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text='➕', command=create_order, 
                style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(button_frame, text='❌', command=dialog.destroy, style='Accent.TButton').pack(side='left', padx=10)

    def delete_configuration(self):
        if not hasattr(self, 'current_config_id') or not self.current_config_id:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию для удаления')
            return
        
        config_name = self.configurations_data[self.current_config_id]['name_config']
        
        if messagebox.askyesno('Подтверждение', f'Удалить конфигурацию "{config_name}"?'):
            try:
                headers = {'token': self.token}
                response = requests.delete(
                    f'{self.base_url}/configurations/delete_by_id/',
                    headers=headers,
                    params={'config_id': self.current_config_id}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Конфигурация удалена')
                    self.current_config_id = None
                    self.load_configurations()
                    for item in self.config_components_tree.get_children():
                        self.config_components_tree.delete(item)
                    self.total_label.config(text='Общая сумма: 0 руб.')
                else:
                    error = response.json().get('detail', 'Ошибка удаления')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
        
    def init_orders_tab(self):
        main_frame = ttk.Frame(self.tab_orders, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Мои заказы', style='Header.TLabel').pack(pady=10)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='🔄', 
                command=self.load_orders, style='Accent.TButton').pack(side='left', padx=5)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, pady=10)

        left_frame = ttk.Frame(paned_window, style='TFrame')
        paned_window.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text='Список заказов:', style='Normal.TLabel').pack(anchor='w', pady=5)

        columns = ('id', 'date', 'total', 'status')
        self.orders_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        
        self.orders_tree.heading('id', text='ID заказа')
        self.orders_tree.heading('date', text='Дата заказа')
        self.orders_tree.heading('total', text='Общая сумма')
        self.orders_tree.heading('status', text='Статус')
        
        self.orders_tree.column('id', width=80)
        self.orders_tree.column('date', width=120)
        self.orders_tree.column('total', width=100)
        self.orders_tree.column('status', width=120)
        
        scrollbar_left = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscroll=scrollbar_left.set)
        
        self.orders_tree.pack(side='left', fill='both', expand=True)
        scrollbar_left.pack(side='right', fill='y')

        right_frame = ttk.Frame(paned_window, style='TFrame')
        paned_window.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text='Детали заказа:', style='Normal.TLabel').pack(anchor='w', pady=5)

        order_columns = ('config_name', 'quantity', 'price', 'total')
        self.order_details_tree = ttk.Treeview(right_frame, columns=order_columns, show='headings', height=10)
        
        self.order_details_tree.heading('config_name', text='Конфигурация')
        self.order_details_tree.heading('quantity', text='Количество')
        self.order_details_tree.heading('price', text='Цена за шт.')
        self.order_details_tree.heading('total', text='Итого')
        
        self.order_details_tree.column('config_name', width=200)
        self.order_details_tree.column('quantity', width=80)
        self.order_details_tree.column('price', width=100)
        self.order_details_tree.column('total', width=100)
        
        scrollbar_right = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.order_details_tree.yview)
        self.order_details_tree.configure(yscroll=scrollbar_right.set)
        
        self.order_details_tree.pack(fill='both', expand=True)
        scrollbar_right.pack(side='right', fill='y')

        info_frame = ttk.Frame(right_frame, style='TFrame')
        info_frame.pack(fill='x', pady=10)
        
        button_frame_right = ttk.Frame(right_frame, style='TFrame')
        button_frame_right.pack(fill='x', pady=10)
        
        ttk.Button(button_frame_right, text='Оплатить',
                   command=self.pay_selected_order, style='Accent.TButton').pack(side='right', padx=10)
        
        ttk.Button(button_frame_right, text='❌', 
                command=self.cancel_selected_order, style='Accent.TButton').pack(side='right', padx=10)
        
        self.order_info_label = ttk.Label(info_frame, text='Выберите заказ для просмотра деталей', 
                                        style='Normal.TLabel')
        self.order_info_label.pack(anchor='w', padx=10)

        self.orders_tree.bind('<<TreeviewSelect>>', self.on_order_select)

        self.load_orders()
    
    def pay_selected_order(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите заказ для оплаты')
            return
        
        item = selected[0]
        order_id = self.orders_tree.item(item)['values'][0]
        order_total = self.orders_tree.item(item)['values'][2]
        order_status = self.orders_tree.item(item)['values'][3]
        
        if order_status == 'Оплачен':
            messagebox.showerror('Ошибка!', 'Выбранная конфигурация уже оплачена')
            return

        pay_window = tk.Toplevel(self.root)
        pay_window.title('Оплата заказа')
        pay_window.geometry('800x800')
        pay_window.resizable(False, False)
        pay_window.configure(bg='#40E0D0')
        pay_window.transient(self.root)
        pay_window.grab_set()

        pay_window.geometry(f'+{self.root.winfo_x() + 200}+{self.root.winfo_y() + 50}')

        title_font = ('Arial', 20, 'bold')
        label_font = ('Arial', 11)
        entry_font = ('Arial', 12)
        button_font = ('Arial', 12, 'bold')
        card_font = ('Arial', 16, 'bold')
        card_small_font = ('Arial', 10)

        ttk.Label(pay_window, text='Оплата заказа', font=title_font, 
                background='#40E0D0', foreground='black').pack(pady=20)
 
        ttk.Label(pay_window, text=f'Заказ №{order_id}', font=('Arial', 14), 
                background='#40E0D0', foreground='#27ae60').pack(pady=5)
        ttk.Label(pay_window, text=f'Сумма: {order_total}', font=('Arial', 12), 
                background='#40E0D0', foreground='black').pack(pady=5)
        
        card_frame = tk.Frame(pay_window, bg='#27ae60', bd=2, relief='raised', 
                            width=400, height=220)
        card_frame.pack(pady=20, padx=50, fill='both')
        card_frame.pack_propagate(False)

        tk.Label(card_frame, text='МИР', font=('Arial', 24, 'bold'), 
                bg='#27ae60', fg='white').place(x=610, y=20)

        tk.Label(card_frame, text='Номер карты', font=card_small_font, 
                bg='#27ae60', fg='#ecf0f1', anchor='w').place(x=30, y=80)
        card_display = tk.Label(card_frame, text='**** **** **** ****', 
                            font=card_font, bg='#27ae60', fg='white')
        card_display.place(x=30, y=100)

        tk.Label(card_frame, text='Срок действия', font=card_small_font, 
                bg='#27ae60', fg='#ecf0f1').place(x=30, y=150)
        tk.Label(card_frame, text='MM / ГГ', font=('Arial', 12), 
                bg='#27ae60', fg='white').place(x=30, y=170)
        
        tk.Label(card_frame, text='CVC / CVV', font=card_small_font, 
                bg='#27ae60', fg='#ecf0f1').place(x=150, y=150)
        tk.Label(card_frame, text='***', font=('Arial', 12), 
                bg='#27ae60', fg='white').place(x=150, y=170)

        form_frame = tk.Frame(pay_window, bg='#40E0D0')
        form_frame.pack(pady=20, padx=50, fill='both')

        ttk.Label(form_frame, text='Номер карты:', font=label_font, 
                background='#40E0D0', foreground='black').pack(anchor='w', pady=5)
        
        card_number_var = tk.StringVar()
        card_number_entry = ttk.Entry(form_frame, textvariable=card_number_var, 
                                    font=entry_font, width=25, style='TEntry')
        card_number_entry.pack(fill='x', pady=5)

        expiry_cvc_frame = tk.Frame(form_frame, bg='#40E0D0')
        expiry_cvc_frame.pack(fill='x', pady=10)

        expiry_frame = tk.Frame(expiry_cvc_frame, bg='#40E0D0')
        expiry_frame.pack(side='left', padx=(0, 20))
        
        ttk.Label(expiry_frame, text='Срок действия (ММ/ГГ):', font=label_font, 
                background='#40E0D0', foreground='black').pack(anchor='w')
        
        expiry_subframe = tk.Frame(expiry_frame, bg='#40E0D0')
        expiry_subframe.pack(fill='x', pady=5)
        
        month_var = tk.StringVar()
        month_entry = ttk.Entry(expiry_subframe, textvariable=month_var, 
                            font=entry_font, width=5, style='TEntry')
        month_entry.pack(side='left', padx=(0, 5))
        
        ttk.Label(expiry_subframe, text='/', font=entry_font, 
                background='#40E0D0', foreground='black').pack(side='left')
        
        year_var = tk.StringVar()
        year_entry = ttk.Entry(expiry_subframe, textvariable=year_var, 
                            font=entry_font, width=5, style='TEntry')
        year_entry.pack(side='left', padx=(5, 0))
 
        cvc_frame = tk.Frame(expiry_cvc_frame, bg='#40E0D0')
        cvc_frame.pack(side='left')
        
        ttk.Label(cvc_frame, text='CVC/CVV код:', font=label_font, 
                background='#40E0D0', foreground='black').pack(anchor='w')
        
        cvc_var = tk.StringVar()
        cvc_entry = ttk.Entry(cvc_frame, textvariable=cvc_var, 
                            font=entry_font, width=8, show='*', style='TEntry')
        cvc_entry.pack(fill='x', pady=5)

        ttk.Label(form_frame, text='Имя владельца карты:', font=label_font, 
                background='#40E0D0', foreground='black').pack(anchor='w', pady=5)
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=name_var, 
                            font=entry_font, width=25, style='TEntry')
        name_entry.pack(fill='x', pady=5)

        def update_card_display(*args):
            card_number = card_number_var.get().replace(' ', '')

            if len(card_number) == 0:
                displayed = '*' * 16
            else:
                displayed = card_number.ljust(16, '*')[:16]

            formatted = ' '.join([displayed[i:i+4] for i in range(0, 16, 4)])
            card_display.config(text=formatted)
        
        def update_expiry_display(*args):
            month = month_var.get().ljust(2, '*')
            year = year_var.get().ljust(2, '*')
        
        def update_cvc_display(*args):
            cvc = cvc_var.get().ljust(3, '*')

        card_number_var.trace('w', update_card_display)
        month_var.trace('w', update_expiry_display)
        year_var.trace('w', update_expiry_display)
        cvc_var.trace('w', update_cvc_display)

        def format_card_number(*args):
            value = card_number_var.get().replace(' ', '')[:16]
            formatted = ' '.join([value[i:i+4] for i in range(0, len(value), 4)])
            if card_number_var.get() != formatted:
                card_number_var.set(formatted)
        
        card_number_var.trace('w', format_card_number)

        def validate_month(*args):
            value = month_var.get()
            if value.isdigit() and len(value) <= 2:
                if value and int(value) > 12:
                    month_var.set('12')
                return True
            elif value == '':
                return True
            else:
                month_var.set(''.join(filter(str.isdigit, value)))
        
        def validate_year(*args):
            value = year_var.get()
            if value.isdigit() and len(value) <= 2:
                return True
            elif value == '':
                return True
            else:
                year_var.set(''.join(filter(str.isdigit, value)))
        
        def validate_cvc(*args):
            value = cvc_var.get()
            if value.isdigit() and len(value) <= 3:
                return True
            elif value == '':
                return True
            else:
                cvc_var.set(''.join(filter(str.isdigit, value)))
        
        month_var.trace('w', lambda *args: validate_month())
        year_var.trace('w', lambda *args: validate_year())
        cvc_var.trace('w', lambda *args: validate_cvc())

        button_frame = tk.Frame(pay_window, bg='#40E0D0')
        button_frame.pack(pady=20)
        
        def process_payment():
            if not all([card_number_var.get(), month_var.get(), 
                    year_var.get(), cvc_var.get(), name_var.get()]):
                messagebox.showerror('Ошибка!', 'Заполните все поля')
                return

            card_number = card_number_var.get().replace(' ', '')
            if len(card_number) != 16 or not card_number.isdigit():
                messagebox.showerror('Ошибка!', 'Введите корректный номер карты (16 цифр)')
                return

            if len(month_var.get()) != 2 or not month_var.get().isdigit():
                messagebox.showerror('Ошибка!', 'Введите корректный месяц (2 цифры)')
                return
            
            month = int(month_var.get())
            if month < 1 or month > 12:
                messagebox.showerror('Ошибка!', 'Месяц должен быть от 01 до 12')
                return
            
            if len(year_var.get()) != 2 or not year_var.get().isdigit():
                messagebox.showerror('Ошибка!', 'Введите корректный год (2 цифры)')
                return

            if len(cvc_var.get()) != 3 or not cvc_var.get().isdigit():
                messagebox.showerror('Ошибка!', 'Введите корректный CVC код (3 цифры)')
                return

            try:
                headers = {'token': self.token}
 
                update_response = requests.put(
                    f'{self.base_url}/orders/user/update_order_status/',
                    headers=headers,
                    params={
                        'order_id': order_id,
                        'new_status': 'Оплачен'
                    }
                )
                
                if update_response.status_code == 200:
                    messagebox.showinfo('Успех!', 
                        f'Заказ #{order_id} успешно оплачен!\n'
                        f'Сумма: {order_total}\n'
                        f'Спасибо за покупку!')
                    pay_window.destroy()
                    self.load_orders()
                else:
                    error = update_response.json().get('detail', 'Ошибка обновления статуса')
                    messagebox.showerror('Ошибка!', error)
                            
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
        
        style = ttk.Style()
        style.configure('Payment.TButton', font=button_font, padding=10, background='white', foreground='black')
        
        ttk.Button(button_frame, text='Оплатить', 
                command=process_payment, style='Payment.TButton').pack(side='left', padx=10)
        
        ttk.Button(button_frame, text='❌', 
                command=pay_window.destroy, style='Payment.TButton').pack(side='left', padx=10)

        card_number_entry.focus()

        expiry_display = tk.Label(card_frame, text='MM / ГГ', font=('Arial', 12), 
                                bg='#27ae60', fg='white')
        expiry_display.place(x=30, y=170)
        
        cvc_display = tk.Label(card_frame, text='***', font=('Arial', 12), 
                            bg='#27ae60', fg='white')
        cvc_display.place(x=150, y=170)
        
        name_display = tk.Label(card_frame, text='ВЛАДЕЛЕЦ КАРТЫ', font=('Arial', 10), 
                            bg='#27ae60', fg='white')
        name_display.place(x=30, y=190)

        def update_expiry_display(*args):
            month = month_var.get().ljust(2, '*')[:2]
            year = year_var.get().ljust(2, '*')[:2]
            expiry_display.config(text=f'{month} / {year}')
        
        def update_cvc_display(*args):
            cvc = cvc_var.get().ljust(3, '*')[:3]
            cvc_display.config(text=cvc)
        
        def update_name_display(*args):
            name = name_var.get().upper() or 'ВЛАДЕЛЕЦ КАРТЫ'
            name_display.config(text=name[:20])
        
        month_var.trace('w', update_expiry_display)
        year_var.trace('w', update_expiry_display)
        cvc_var.trace('w', update_cvc_display)
        name_var.trace('w', update_name_display)
            
    def cancel_selected_order(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите заказ для отмены')
            return
        
        item = selected[0]
        order_id = self.orders_tree.item(item)['values'][0]
        
        if messagebox.askyesno('Подтверждение', f'Вы уверены, что хотите отменить заказ #{order_id}?'):
            try:
                headers = {'token': self.token}
                response = requests.delete(
                    f'{self.base_url}/orders/cancel_order/',
                    headers=headers,
                    params={'order_id': order_id}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Заказ отменен')
                    self.load_orders()
                    for item in self.order_details_tree.get_children():
                        self.order_details_tree.delete(item)
                    self.order_info_label.config(text='Выберите заказ для просмотра деталей')
                else:
                    error = response.json().get('detail', 'Ошибка отмены заказа')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

    def load_orders(self):
        try:
            headers = {'token': self.token}
            response = requests.get(f'{self.base_url}/orders/get_user_orders/', headers=headers)
            
            if response.status_code == 200:
                for item in self.orders_tree.get_children():
                    self.orders_tree.delete(item)
                
                orders = response.json()
                self.orders_data = {}
                
                for order in orders:
                    order_id = order['id']
                    self.orders_data[order_id] = order

                    order_date = order.get('order_date', '')
                    if order_date:
                        try:
                            order_date = order_date.split('T')[0]
                        except:
                            pass

                    total_amount = order.get('total_amount', 0)
                    total_text = f"{total_amount:.2f} руб." if total_amount else "0 руб."
                    
                    self.orders_tree.insert('', 'end', values=(
                        order_id,
                        order_date,
                        total_text,
                        order.get('status_name', 'Неизвестно')
                    ))
            else:
                messagebox.showerror('Ошибка!', 'Не удалось загрузить заказы')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

    def on_order_select(self, event):
        selected = self.orders_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        order_id = self.orders_tree.item(item)['values'][0]
        
        if order_id in self.orders_data:
            order = self.orders_data[order_id]
            self.display_order_details(order)

    def display_order_details(self, order):
        for item in self.order_details_tree.get_children():
            self.order_details_tree.delete(item)

        order_id = order['id']
        order_date = order.get('order_date', 'Неизвестно')
        total_amount = order.get('total_amount', 0)
        status = order.get('status_name', 'Неизвестно')
        
        info_text = f"Заказ #{order_id} | Дата: {order_date} | Статус: {status} | Общая сумма: {total_amount:.2f} руб."
        self.order_info_label.config(text=info_text)

        configurations = order.get('configurations', [])
        for config in configurations:
            config_name = config.get('configuration_name', 'Неизвестно')
            quantity = config.get('quantity', 1)
            price = config.get('price_at_time', 0)
            total = config.get('total', price * quantity)
            
            self.order_details_tree.insert('', 'end', values=(
                config_name,
                quantity,
                f"{price:.2f} руб.",
                f"{total:.2f} руб."
            ))
        
    def init_profile_tab(self):
        profile_frame = ttk.Frame(self.tab_profile, style='TFrame')
        profile_frame.pack(fill='both', padx=10, pady=10)
        
        ttk.Label(profile_frame, text='Мой профиль', style='Header.TLabel').pack(pady=20)
        
        info_frame = ttk.LabelFrame(profile_frame, style='TFrame')
        info_frame.pack(fill='x', pady=10, padx=10)
        
        user_info = [
            ('ФИО:', self.user_data['name']),
            ('Email:', self.user_data['email']),
            ('Телефон:', self.user_data['phone']),
            ('Роль:', self.user_data['role']),
            ('Адрес:', self.user_data['address'] or 'Не указан')
        ]
        
        for i, (label, value) in enumerate(user_info):
            row_frame = ttk.Frame(info_frame, style='TFrame')
            row_frame.pack(fill='x', pady=5)
            
            ttk.Label(row_frame, text=label, style='Normal.TLabel', width=15, anchor='e').pack(side='left', padx=5)
            ttk.Label(row_frame, text=value, style='Normal.TLabel', anchor='w').pack(side='left', padx=5, fill='x', expand=True)
            
        button_frame = ttk.Frame(profile_frame, style='TFrame')
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text='Изменить адрес',
                   command=self.edit_address, style='Accent.TButton').pack(side='left', padx=10)
        
        ttk.Button(button_frame, text='🔄', 
                   command=self.load_user_data, style='Accent.TButton').pack(side='left', padx=10)
        
        ttk.Button(button_frame, text='Сменить пароль', command=self.change_password,
                   style='Accent.TButton').pack(side='left', padx=10)
        
        ttk.Button(button_frame, text='Выйти из аккаунта',
                   command=self.logout, style='Accent.TButton').pack(side='left', padx=10)
        
    def edit_address(self):
        edit_window = tk.Toplevel(self.root)
        edit_window.title('Изменение адреса')
        edit_window.geometry('600x500')
        edit_window.resizable(False, False)
        edit_window.configure(bg='#40E0D0')
        edit_window.grab_set()
        edit_window.transient(self.root)
        edit_window.geometry(f'+{self.root.winfo_x() + 100}+{self.root.winfo_y() + 100}')
        
        content_frame = ttk.Frame(edit_window, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(content_frame, text='Изменение адреса доставки', style='Header.TLabel').pack(pady=20)
        
        current_address = self.user_data.get('address', 'Не указан')
        ttk.Label(content_frame, text='Новый адрес:', style='Normal.TLabel').pack(pady=5, anchor='w')
        address_entry = ttk.Entry(content_frame, width=50, font=('Arial', 12), style='TEntry')
        address_entry.pack(pady=5, fill='x')
        
        def save_address():
            new_address = address_entry.get().strip()
            if not new_address:
                messagebox.showerror('Ошибка!', 'Поле адреса не может быть пустым')
                return
            
            try:
                token = self.token
                if not token:
                    messagebox.showerror('Ошибка!', 'Токен авторизации не найден')
                    return
                
                response = requests.put(
                    f'{self.base_url}/users/edit_address/',
                    params={'new_address': new_address},
                    headers={'token': self.token}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Адрес успешно изменен')
                    self.user_data['address'] = new_address
                    edit_window.destroy()
                else:
                    error = response.json().get('message', 'Не удалось изменить адрес')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')
        
        save_btn = ttk.Button(content_frame, text='✔️', command=save_address, style='Accent.TButton')
        save_btn.pack(pady=20)
        
        ttk.Button(content_frame, text='❌', command=edit_window.destroy, style='Accent.TButton').pack(pady=10)
    
    def change_password(self):
        password_window = tk.Toplevel(self.root)
        password_window.title('Смена пароля')
        password_window.geometry('600x500')
        password_window.resizable(False, False)
        password_window.configure(bg='#40E0D0')
        password_window.grab_set()
        
        password_window.transient(self.root)
        password_window.geometry(f'+{self.root.winfo_x() + 100}+{self.root.winfo_y() + 100}')
        
        user_email = self.user_data['email']
        content_frame = ttk.Frame(password_window, style='TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(content_frame, text='Смена пароля', style='Header.TLabel').pack(pady=20)
        ttk.Label(content_frame, text=f'Для смены пароля будет отправлен код на email: {user_email}', style='Normal.TLabel', wraplength=400).pack(pady=10)
        
        code_frame = ttk.Frame(content_frame, style='TFrame')

        def show_code_entry():
            send_btn.pack_forget()
            
            ttk.Label(code_frame, text='Код подтверждения', style='Normal.TLabel').pack(pady=5)
            code_entry = ttk.Entry(code_frame, width=30, font=('Arial', 12), style='TEntry')
            code_entry.pack(pady=5)
            
            ttk.Label(code_frame, text='Новый пароль:', style='Normal.TLabel').pack(pady=5)
            new_password_entry = ttk.Entry(code_frame, width=30, show='*', font=('Arial', 12), style='TEntry')
            new_password_entry.pack(pady=5)
            
            ttk.Label(code_frame, text='Подтвердите пароль:', style='Normal.TLabel').pack(pady=5)
            confirm_password_entry = ttk.Entry(code_frame, width=30, show='*', font=('Arial', 12), style='TEntry')
            confirm_password_entry.pack(pady=5)
            
            def confirm_change():
                code = code_entry.get().strip()
                new_password = new_password_entry.get().strip()
                confirm_password = confirm_password_entry.get().strip()
                
                if not all([code, new_password, confirm_password]):
                    messagebox.showerror('Ошибка!', 'Заполните все поля')
                    return
                
                if new_password != confirm_password:
                    messagebox.showerror('Ошибка!', 'Пароли не совпадают')
                    return
                
                try:
                    response = requests.post(
                        f'{self.base_url}/users/confirm_change_password/',
                        params={
                            'email': user_email,
                            'code': code,
                            'new_password': new_password
                        }
                    )
                    
                    if response.status_code == 200:
                        messagebox.showinfo('Успех!', 'Пароль успешно изменен')
                        password_window.destroy()
                    else:
                        error = response.json().get('detail', 'Ошибка смены пароля')
                        messagebox.showerror('Ошибка', error)
                except requests.exceptions.RequestException as e:
                    messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')
            
            ttk.Button(code_frame, text='✔️', command=confirm_change, style='Accent.TButton').pack(pady=20)
            code_frame.pack()
        
        def send_code():
            try:
                response = requests.post(
                    f'{self.base_url}/users/change_password/',
                    params={'email': user_email}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo('Успех!', 'Код подтверждения отправлен на ваш email')
                    show_code_entry()
                else:
                    error = response.json().get('detail', 'Не удалось отправить код подтверждения')
                    messagebox.showerror('Ошибка!', error)
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Не удалось подключиться к серверу: {e}')

        send_btn = ttk.Button(content_frame, text='Отправить код', command=send_code, style='Accent.TButton')
        send_btn.pack(pady=20)
        
        ttk.Button(content_frame, text='❌', command=password_window.destroy, style='Accent.TButton').pack(pady=10)

class AdminApp:
    def __init__(self, root, token):
        self.root = root
        self.root.title('ANTech - Панель администратора')
        self.root.state('zoomed')
        self.root.configure(bg='#40E0D0')
        self.token = token
        self.base_url = 'http://127.0.0.1:8000'
        
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), background='#40E0D0', foreground='black')
        self.style.configure('Normal.TLabel', font=('Arial', 12), background='#40E0D0', foreground='black')
        self.style.configure('Accent.TButton', font=('Arial', 12), background='white', foreground='black')
        self.style.configure('TFrame', background='#40E0D0')
        self.style.configure('TNotebook', background='#40E0D0')
        self.style.configure('TNotebook.Tab', background='white', foreground='black')
        self.style.configure('Treeview', background='white', foreground='black', fieldbackground='white')
        self.style.configure('Treeview.Heading', background='#40E0D0', foreground='black', font=('Arial', 10, 'bold'))
        self.style.configure('TEntry', fieldbackground='white', foreground='black')
        self.style.configure('TCombobox', fieldbackground='white', foreground='black')
        
        self.main_container = ttk.Frame(root, style='TFrame')
        self.main_container.pack(fill='both', expand=True)
        
        self.header_frame = ttk.Frame(self.main_container, style='TFrame')
        self.header_frame.pack(fill='x', pady=10)
        
        ttk.Label(self.header_frame, text='Панель администратора', style='Header.TLabel').pack(side='left', padx=20)
        ttk.Button(self.header_frame, text='Выход', command=self.logout, style='Accent.TButton').pack(side='right', padx=20)
        
        self.tab_control = ttk.Notebook(self.main_container)
        
        self.tab_users = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_manufactures = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_components = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_configurations = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_orders = ttk.Frame(self.tab_control, style='TFrame')
        
        self.tab_control.add(self.tab_users, text='Пользователи')
        self.tab_control.add(self.tab_manufactures, text='Производители')
        self.tab_control.add(self.tab_components, text='Компоненты')
        self.tab_control.add(self.tab_configurations, text='Конфигурации')
        self.tab_control.add(self.tab_orders, text='Заказы')
        
        self.tab_control.pack(fill='both', expand=1)
        
        self.init_users_tab()
        self.init_manufactures_tab()
        self.init_components_tab()
        self.init_configurations_tab()
        self.init_orders_tab()
    
    def logout(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        AuthApp(self.root)
    
    def make_api_request(self, endpoint, method='GET', params=None, json_data=None):
        try:
            headers = {'token': self.token}
            url = f'{self.base_url}{endpoint}'
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, params=params)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=json_data, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                error = response.json().get('detail', 'Ошибка API')
                messagebox.showerror('Ошибка!', error)
                return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
            return None
    
    def init_users_tab(self):
        """Вкладка управления пользователями"""
        main_frame = ttk.Frame(self.tab_users, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Управление пользователями', style='Header.TLabel').pack(pady=10)

        search_frame = ttk.Frame(main_frame, style='TFrame')
        search_frame.pack(fill='x', pady=10)
        
        ttk.Label(search_frame, text='Поиск пользователя:', style='Normal.TLabel').pack(side='left', padx=5)
        
        self.user_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.user_search_var, width=30, style='TEntry')
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text='🔎', 
                  command=self.search_user, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(search_frame, text='🔄', 
                  command=self.load_users, style='Accent.TButton').pack(side='left', padx=5)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='🔄', 
                  command=self.load_users, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='Изменить роль', 
                  command=self.change_user_role, style='Accent.TButton').pack(side='left', padx=5)

        columns = ('id', 'name', 'email', 'phone', 'role', 'address')
        self.users_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.users_tree.heading('id', text='ID')
        self.users_tree.heading('name', text='ФИО')
        self.users_tree.heading('email', text='Email')
        self.users_tree.heading('phone', text='Телефон')
        self.users_tree.heading('role', text='Роль')
        self.users_tree.heading('address', text='Адрес')
        
        self.users_tree.column('id', width=50)
        self.users_tree.column('name', width=150)
        self.users_tree.column('email', width=150)
        self.users_tree.column('phone', width=120)
        self.users_tree.column('role', width=100)
        self.users_tree.column('address', width=200)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=scrollbar.set)
        
        self.users_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        search_entry.bind('<Return>', lambda event: self.search_user())
        
        self.load_users()
    
    def search_user(self):
        """Поиск пользователя по email или номеру телефона"""
        search_text = self.user_search_var.get().strip()
        
        if not search_text:
            messagebox.showwarning('Внимание!', 'Введите email или номер телефона для поиска')
            return

        if self.is_phone(search_text):
            search_data = {'phone': search_text}
        else:
            search_data = {'email': search_text}
        
        try:
            headers = {'token': self.token}
            response = requests.post(
                f'{self.base_url}/users/get_user_by_email_or_phone/',
                headers=headers,
                json=search_data
            )
            
            if response.status_code == 200:
                user = response.json()

                for item in self.users_tree.get_children():
                    self.users_tree.delete(item)

                self.users_tree.insert('', 'end', values=(
                    user['id'],
                    user['name'],
                    user['email'],
                    user['phone'],
                    user['role'],
                    user['address']
                ))
                
                messagebox.showinfo('Успех!', f'Пользователь найден: {user["name"]}')
                
            else:
                error = response.json().get('detail', 'Пользователь не найден')
                messagebox.showerror('Ошибка!', error)
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')
        
    def is_phone(self, text):
        """Проверяет, является ли текст номером телефона"""
        phone_pattern = r'^[\d\s\-\+\(\)]+$'
        return bool(re.match(phone_pattern, text)) and len(text) >= 5
    
    def load_users(self):
        """Загрузка списка пользователей"""
        data = self.make_api_request('/users/get_all/')
        if data:
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            for user in data:
                self.users_tree.insert('', 'end', values=(
                    user['id'],
                    user['name'],
                    user['email'],
                    user['phone'],
                    user['role'],
                    user['address']
                ))
    
    def change_user_role(self):
        """Изменение роли пользователя"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите пользователя')
            return
        
        item = selected[0]
        user_data = self.users_tree.item(item)['values']
        user_email = user_data[2]
        current_role = user_data[4]
        
        dialog = tk.Toplevel(self.root)
        dialog.title('Изменение роли пользователя')
        dialog.geometry('350x200')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f'Пользователь: {user_email}', style='Normal.TLabel').pack(pady=10)
        ttk.Label(dialog, text=f'Текущая роль: {current_role}', style='Normal.TLabel').pack(pady=5)
        
        role_var = tk.StringVar(value=current_role)
        role_combo = ttk.Combobox(dialog, textvariable=role_var, state='readonly', style='TCombobox')
        role_combo['values'] = ('Пользователь', 'Администратор')
        role_combo.pack(pady=10)
        
        def save_role():
            new_role = role_var.get()
            if new_role == current_role:
                messagebox.showinfo('Информация', 'Роль не изменена')
                dialog.destroy()
                return
            
            data = self.make_api_request('/users/set_role/', method='POST',
                                       json_data={'email': user_email, 'new_role': new_role})
            if data:
                messagebox.showinfo('Успех!', 'Роль пользователя изменена')
                dialog.destroy()
                self.load_users()
        
        ttk.Button(dialog, text='✔️', command=save_role, style='Accent.TButton').pack(pady=10)
        
    def init_manufactures_tab(self):
        main_frame = ttk.Frame(self.tab_manufactures, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Управление производителями', style='Header.TLabel').pack(pady=10)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='➕', 
                  command=self.add_manufacture, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='🔄', 
                  command=self.load_manufactures, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='❌', 
                  command=self.delete_manufacture, style='Accent.TButton').pack(side='left', padx=5)

        columns = ('id', 'name')
        self.manufactures_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.manufactures_tree.heading('id', text='ID')
        self.manufactures_tree.heading('name', text='Название')
        
        self.manufactures_tree.column('id', width=50)
        self.manufactures_tree.column('name', width=200)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.manufactures_tree.yview)
        self.manufactures_tree.configure(yscroll=scrollbar.set)
        
        self.manufactures_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.load_manufactures()
    
    def load_manufactures(self):
        try:
            data = self.make_api_request('/manufactures/get_manufactures/')
            if data:
                for item in self.manufactures_tree.get_children():
                    self.manufactures_tree.delete(item)

                for manufacture in data:
                    self.manufactures_tree.insert('', 'end', values=(
                        manufacture.get('id', 'N/A'),
                        manufacture.get('name', 'Неизвестно')
                    ))
        except requests.exceptions.RequestException as e:
            messagebox.showerror('Ошибка!', f'Произошла ошибка при загрузке списка производителей: {e}')
      
    def add_manufacture(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Добавление производителя')
        dialog.geometry('300x150')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Название производителя:', style='Normal.TLabel').pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30, style='TEntry')
        name_entry.pack(pady=10)
        
        def save_manufacture():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror('Ошибка!', 'Введите название')
                return
            
            data = self.make_api_request('/manufactures/add_manufacture/', method='POST',
                                       params={'name': name})
            if data:
                messagebox.showinfo('Успех!', 'Производитель добавлен')
                dialog.destroy()
                self.load_manufactures()
        
        ttk.Button(dialog, text='✔️', command=save_manufacture, style='Accent.TButton').pack(pady=10)
    
    def delete_manufacture(self):
        selected = self.manufactures_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите производителя')
            return
        
        item = selected[0]
        manufacture_id = self.manufactures_tree.item(item)['values'][0]
        manufacture_name = self.manufactures_tree.item(item)['values'][1]
        
        if messagebox.askyesno('Подтверждение', f'Удалить производителя "{manufacture_name}"?'):
            data = self.make_api_request('/manufactures/del_manufacture_by_id/', method='DELETE',
                                       params={'manufacture_id': manufacture_id})
            if data:
                messagebox.showinfo('Успех!', 'Производитель удален')
                self.load_manufactures()
    
    def init_components_tab(self):
        main_frame = ttk.Frame(self.tab_components, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Управление компонентами', style='Header.TLabel').pack(pady=10)

        filter_frame = ttk.Frame(main_frame, style='TFrame')
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text='Тип:', style='Normal.TLabel').pack(side='left', padx=5)
        self.admin_type_filter = tk.StringVar()
        self.admin_type_combo = ttk.Combobox(filter_frame, textvariable=self.admin_type_filter, state='readonly', width=15, style='TCombobox')
        self.admin_type_combo.pack(side='left', padx=5)

        ttk.Label(filter_frame, text='Цена от:', style='Normal.TLabel').pack(side='left', padx=5)
        self.admin_min_price_filter = tk.StringVar()
        admin_min_price_entry = ttk.Entry(filter_frame, textvariable=self.admin_min_price_filter, width=8, style='TEntry')
        admin_min_price_entry.pack(side='left', padx=2)
        
        ttk.Label(filter_frame, text='до:', style='Normal.TLabel').pack(side='left', padx=2)
        self.admin_max_price_filter = tk.StringVar()
        admin_max_price_entry = ttk.Entry(filter_frame, textvariable=self.admin_max_price_filter, width=8, style='TEntry')
        admin_max_price_entry.pack(side='left', padx=5)
 
        ttk.Button(filter_frame, text='✔️', 
                command=self.admin_apply_filters, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(filter_frame, text='🔄', 
                command=self.admin_reset_filters, style='Accent.TButton').pack(side='left', padx=5)
     
        search_frame = ttk.Frame(main_frame, style='TFrame')
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text='Поиск:', style='Normal.TLabel').pack(side='left', padx=5)
        self.admin_search_var = tk.StringVar()
        admin_search_entry = ttk.Entry(search_frame, textvariable=self.admin_search_var, width=40, style='TEntry')
        admin_search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text='🔎', 
                command=self.admin_search_components, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(search_frame, text='🔄', 
                command=self.admin_clear_search, style='Accent.TButton').pack(side='left', padx=5)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='➕', 
                  command=self.add_component, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='🔄', 
                  command=self.load_components, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='✏️', 
                  command=self.edit_component, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='❌', 
                  command=self.delete_component, style='Accent.TButton').pack(side='left', padx=5)

        columns = ('id', 'name', 'type', 'manufacture', 'price', 'stock')
        self.components_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.components_tree.heading('id', text='ID')
        self.components_tree.heading('name', text='Название')
        self.components_tree.heading('type', text='Тип')
        self.components_tree.heading('manufacture', text='Производитель')
        self.components_tree.heading('price', text='Цена')
        self.components_tree.heading('stock', text='Наличие')
        
        self.components_tree.column('id', width=50)
        self.components_tree.column('name', width=150)
        self.components_tree.column('type', width=100)
        self.components_tree.column('manufacture', width=120)
        self.components_tree.column('price', width=80)
        self.components_tree.column('stock', width=80)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.components_tree.yview)
        self.components_tree.configure(yscroll=scrollbar.set)
        
        self.components_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        admin_search_entry.bind('<Return>', lambda event: self.admin_search_components())

        self.admin_all_components = []
        self.admin_filtered_components = []
        self.admin_available_types = set()
        
        self.load_components()
    
    def load_components(self):
        data = self.make_api_request('/components/get_all/')
        if data:
            for item in self.components_tree.get_children():
                self.components_tree.delete(item)
            
            self.admin_all_components = data
            self.admin_filtered_components = data.copy()

            self.admin_available_types = set()
            for component in data:
                if component.get('type_name'):
                    self.admin_available_types.add(component['type_name'])

            self.admin_type_combo['values'] = ["Все типы"] + sorted(list(self.admin_available_types))
            self.admin_type_combo.set("Все типы")

            self.admin_display_filtered_components()
    
    def admin_apply_filters(self):
        """Применение фильтров к каталогу компонентов в админке"""
        if not hasattr(self, 'admin_all_components') or not self.admin_all_components:
            return
        
        filtered = self.admin_all_components.copy()

        selected_type = self.admin_type_filter.get()
        if selected_type and selected_type != "Все типы":
            filtered = [comp for comp in filtered if comp.get('type_name') == selected_type]

        min_price = self.admin_min_price_filter.get()
        if min_price:
            try:
                min_price_val = float(min_price)
                filtered = [comp for comp in filtered if comp.get('price', 0) >= min_price_val]
            except ValueError:
                pass

        max_price = self.admin_max_price_filter.get()
        if max_price:
            try:
                max_price_val = float(max_price)
                filtered = [comp for comp in filtered if comp.get('price', 0) <= max_price_val]
            except ValueError:
                pass

        search_term = self.admin_search_var.get().strip().lower()
        if search_term:
            filtered = [comp for comp in filtered if (
                search_term in comp['name'].lower() or 
                search_term in comp['type_name'].lower() or 
                search_term in comp['manufacture_name'].lower()
            )]
        
        self.admin_filtered_components = filtered
        self.admin_display_filtered_components()

    def admin_reset_filters(self):
        """Сброс фильтров в админке"""
        self.admin_type_filter.set('Все типы')
        self.admin_min_price_filter.set('')
        self.admin_max_price_filter.set('')
        self.admin_search_var.set('')
        self.admin_filtered_components = self.admin_all_components.copy()
        self.admin_display_filtered_components()

    def admin_display_filtered_components(self):
        """Отображение отфильтрованных компонентов в админке"""
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)
        
        for component in self.admin_filtered_components:
            self.components_tree.insert('', 'end', values=(
                component['id'],
                component['name'],
                component['type_name'],
                component['manufacture_name'],
                component['price'],
                component['stock_quantity']
            ))

    def admin_search_components(self):
        """Поиск компонентов в админке"""
        self.admin_apply_filters()
        
        if self.admin_search_var.get().strip():
            messagebox.showinfo('Поиск', f'Найдено компонентов: {len(self.admin_filtered_components)}')

    def admin_clear_search(self):
        """Сброс поиска в админке"""
        self.admin_search_var.set('')
        self.admin_apply_filters()
    
    def add_component(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Добавление компонента')
        dialog.geometry('400x400')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text='Название:', style='Normal.TLabel').grid(row=0, column=0, padx=10, pady=5, sticky='e')
        name_entry = ttk.Entry(dialog, width=30, style='TEntry')
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text='Тип:', style='Normal.TLabel').grid(row=1, column=0, padx=10, pady=5, sticky='e')
        type_entry = ttk.Entry(dialog, width=30, style='TEntry')
        type_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text='Производитель:', style='Normal.TLabel').grid(row=2, column=0, padx=10, pady=5, sticky='e')
        manufacture_entry = ttk.Entry(dialog, width=30, style='TEntry')
        manufacture_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text='Цена:', style='Normal.TLabel').grid(row=3, column=0, padx=10, pady=5, sticky='e')
        price_entry = ttk.Entry(dialog, width=30, style='TEntry')
        price_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text='Количество:', style='Normal.TLabel').grid(row=4, column=0, padx=10, pady=5, sticky='e')
        stock_entry = ttk.Entry(dialog, width=30, style='TEntry')
        stock_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save_component():
            name = name_entry.get().strip()
            type_name = type_entry.get().strip()
            manufacture_name = manufacture_entry.get().strip()
            
            if not name:
                messagebox.showerror('Ошибка!', 'Введите название')
                return
            
            try:
                price = float(price_entry.get())
                stock = int(stock_entry.get())
            except ValueError:
                messagebox.showerror('Ошибка!', 'Цена и количество должны быть числами')
                return
            
            component_data = {
                'name': name,
                'type_name': type_name if type_name else None,
                'manufacture_name': manufacture_name if manufacture_name else None,
                'price': price,
                'stock_quantity': stock,
                'specification': []
            }
            
            data = self.make_api_request('/components/create/', method='POST', json_data=component_data)
            if data:
                messagebox.showinfo('Успех!', 'Компонент добавлен')
                dialog.destroy()
                self.load_components()
        
        ttk.Button(dialog, text='✔️', command=save_component, style='Accent.TButton').grid(row=5, column=0, columnspan=2, pady=20)
    
    def edit_component(self):
        selected = self.components_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите компонент')
            return

        item = selected[0]
        component_id = self.components_tree.item(item)['values'][0]
        current_data = None
        for component in self.components_tree.get_children():
            if self.components_tree.item(component)['values'][0] == component_id:
                current_data = self.components_tree.item(component)['values']
                break
        
        if not current_data:
            messagebox.showerror('Ошибка!', 'Не удалось получить данные компонента')
            return

        dialog = tk.Toplevel(self.root)
        dialog.title('Редактирование компонента')
        dialog.geometry('500x600')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text='Название:', style='Normal.TLabel').grid(row=0, column=0, padx=10, pady=5, sticky='e')
        name_entry = ttk.Entry(dialog, width=30, style='TEntry')
        name_entry.insert(0, current_data[1])
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text='Тип:', style='Normal.TLabel').grid(row=1, column=0, padx=10, pady=5, sticky='e')
        type_entry = ttk.Entry(dialog, width=30, style='TEntry')
        type_entry.insert(0, current_data[2] if current_data[2] else '')
        type_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text='Производитель:', style='Normal.TLabel').grid(row=2, column=0, padx=10, pady=5, sticky='e')
        manufacture_entry = ttk.Entry(dialog, width=30, style='TEntry')
        manufacture_entry.insert(0, current_data[3] if current_data[3] else '')
        manufacture_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text='Цена:', style='Normal.TLabel').grid(row=3, column=0, padx=10, pady=5, sticky='e')
        price_entry = ttk.Entry(dialog, width=30, style='TEntry')
        price_entry.insert(0, str(current_data[4]))
        price_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(dialog, text='Количество на складе:', style='Normal.TLabel').grid(row=4, column=0, padx=10, pady=5, sticky='e')
        stock_entry = ttk.Entry(dialog, width=30, style='TEntry')
        stock_entry.insert(0, str(current_data[5]))
        stock_entry.grid(row=4, column=1, padx=10, pady=5)

        spec_frame = ttk.LabelFrame(dialog, text='Спецификация (JSON)')
        spec_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky='nsew')

        ttk.Label(spec_frame, text='Формат: [{"key": "название", "value": "значение"}, ...] или {"ключ": "значение", ...}', 
                font=('Arial', 8), foreground='gray').pack(anchor='w', padx=5, pady=2)
        
        spec_text = scrolledtext.ScrolledText(spec_frame, width=60, height=8, bg='white', fg='black')
        spec_text.pack(fill='both', expand=True, padx=5, pady=5)

        def load_component_details():
            try:
                headers = {'token': self.token}
                response = requests.get(
                    f'{self.base_url}/components/get_by_id/',
                    headers=headers,
                    params={'component_id': component_id}
                )
                
                if response.status_code == 200:
                    component_data = response.json()
                    specification = component_data.get('specification', [])
                    if specification:
                        formatted_spec = json.dumps(specification, indent=2, ensure_ascii=False)
                        spec_text.insert('1.0', formatted_spec)
                else:
                    messagebox.showerror('Ошибка!', 'Не удалось загрузить детали компонента')
            except requests.exceptions.RequestException as e:
                messagebox.showerror('Ошибка!', f'Ошибка соединения: {e}')

        load_component_details()

        def validate_json(data):
            try:
                parsed = json.loads(data)
                if not isinstance(parsed, (dict, list)):
                    return False, "JSON должен быть объектом или массивом"
                return True, parsed
            except json.JSONDecodeError as e:
                return False, f"Ошибка JSON: {str(e)}"

        def save_component():
            name = name_entry.get().strip()
            type_name = type_entry.get().strip()
            manufacture_name = manufacture_entry.get().strip()
            
            if not name:
                messagebox.showerror('Ошибка!', 'Введите название компонента')
                return
            
            try:
                price = float(price_entry.get())
                stock_quantity = int(stock_entry.get())
            except ValueError:
                messagebox.showerror('Ошибка!', 'Цена и количество должны быть числами')
                return

            specification_text = spec_text.get('1.0', tk.END).strip()
            specification = []
            
            if specification_text:
                is_valid, result = validate_json(specification_text)
                if not is_valid:
                    messagebox.showerror('Ошибка!', result)
                    return
                specification = result

            component_data = {
                'new_name': name,
                'type_name': type_name if type_name else None,
                'manufacture_name': manufacture_name if manufacture_name else None,
                'price': price,
                'stock_quantity': stock_quantity,
                'specification': specification
            }

            data = self.make_api_request('/components/edit_by_id/', method='PUT',
                                    json_data=component_data,
                                    params={'component_id': component_id})
            if data:
                messagebox.showinfo('Успех!', 'Компонент обновлен')
                dialog.destroy()
                self.load_components()

        button_frame = ttk.Frame(dialog, style='TFrame')
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text='✔️', command=save_component, 
                style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(button_frame, text='❌', command=dialog.destroy, 
                style='Accent.TButton').pack(side='left', padx=10)

        dialog.grid_rowconfigure(5, weight=1)
        dialog.grid_columnconfigure(1, weight=1)

        help_label = ttk.Label(dialog, 
                            text='Подсказка: Используйте валидный JSON формат. Пример: [{"Сокет": "LGA 1700"}, {"Чипсет": "Intel Z690"}]',
                            font=('Arial', 8),
                            foreground='blue')
        help_label.grid(row=7, column=0, columnspan=2, pady=5)
    
    def delete_component(self):
        selected = self.components_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите компонент')
            return
        
        item = selected[0]
        component_id = self.components_tree.item(item)['values'][0]
        component_name = self.components_tree.item(item)['values'][1]
        
        if messagebox.askyesno('Подтверждение', f'Удалить компонент "{component_name}"?'):
            data = self.make_api_request('/components/delete_by_id/', method='DELETE',
                                       params={'component_id': component_id})
            if data:
                messagebox.showinfo('Успех!', 'Компонент удален')
                self.load_components()
    
    def init_configurations_tab(self):
        main_frame = ttk.Frame(self.tab_configurations, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Управление конфигурациями', style='Header.TLabel').pack(pady=10)

        # Добавляем рамку для поиска
        search_frame = ttk.Frame(main_frame, style='TFrame')
        search_frame.pack(fill='x', pady=10)
        
        ttk.Label(search_frame, text='Поиск по названию:', style='Normal.TLabel').pack(side='left', padx=5)
        
        self.config_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.config_search_var, width=30, style='TEntry')
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text='🔎', 
                  command=self.search_configurations, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(search_frame, text='🔄', 
                  command=self.load_configurations, style='Accent.TButton').pack(side='left', padx=5)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='🔄', 
                  command=self.load_configurations, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='👀', 
                  command=self.view_configuration, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='❌', 
                  command=self.delete_configuration, style='Accent.TButton').pack(side='left', padx=5)

        columns = ('id', 'user', 'name', 'description', 'created')
        self.configurations_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.configurations_tree.heading('id', text='ID')
        self.configurations_tree.heading('user', text='Пользователь')
        self.configurations_tree.heading('name', text='Название')
        self.configurations_tree.heading('description', text='Описание')
        self.configurations_tree.heading('created', text='Дата создания')
        
        self.configurations_tree.column('id', width=50)
        self.configurations_tree.column('user', width=120)
        self.configurations_tree.column('name', width=150)
        self.configurations_tree.column('description', width=200)
        self.configurations_tree.column('created', width=120)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.configurations_tree.yview)
        self.configurations_tree.configure(yscroll=scrollbar.set)
        
        self.configurations_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        search_entry.bind('<Return>', lambda event: self.search_configurations())
        
        self.all_configurations = []
        self.load_configurations()

    def search_configurations(self):
        """Поиск конфигураций по названию"""
        search_text = self.config_search_var.get().strip().lower()
        
        if not search_text:
            self.display_configurations(self.all_configurations)
            return

        filtered_configs = [
            config for config in self.all_configurations 
            if search_text in config['name_config'].lower()
        ]
        
        self.display_configurations(filtered_configs)
        
        messagebox.showinfo('Поиск', f'Найдено конфигураций: {len(filtered_configs)}')

    def load_configurations(self):
        data = self.make_api_request('/configurations/admin/get_all/')
        if data:
            self.all_configurations = data
            self.display_configurations(data)
            
    def display_configurations(self, configurations):
        """Отображение списка конфигураций в таблице"""
        for item in self.configurations_tree.get_children():
            self.configurations_tree.delete(item)
            
        for config in configurations:
            created_at = config.get('created_at', '')
            if created_at:
                try:
                    created_at = created_at.split('T')[0]
                except:
                    pass
            
            self.configurations_tree.insert('', 'end', values=(
                config['id'],
                config['user_name'],
                config['name_config'],
                config['description'] or '-',
                created_at
            ))
    
    def view_configuration(self):
        selected = self.configurations_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию')
            return
        
        item = selected[0]
        config_id = self.configurations_tree.item(item)['values'][0]
        
        data = self.make_api_request(f'/configurations/admin/{config_id}/components/')
        if data:
            dialog = tk.Toplevel(self.root)
            dialog.title(f'Компоненты конфигурации #{config_id}')
            dialog.geometry('1000x600')
            dialog.configure(bg='#40E0D0')
            dialog.transient(self.root)
            dialog.grab_set()
            
            columns = ('component', 'type', 'manufacture', 'price', 'quantity', 'total')
            tree = ttk.Treeview(dialog, columns=columns, show='headings', height=15)
            
            tree.heading('component', text='Компонент')
            tree.heading('type', text='Тип')
            tree.heading('manufacture', text='Производитель')
            tree.heading('price', text='Цена')
            tree.heading('quantity', text='Количество')
            tree.heading('total', text='Итого')
            
            tree.column('component', width=150)
            tree.column('type', width=100)
            tree.column('manufacture', width=120)
            tree.column('price', width=80)
            tree.column('quantity', width=80)
            tree.column('total', width=80)
            
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            
            tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
            scrollbar.pack(side='right', fill='y')
            
            total_amount = 0
            for component in data:
                total_price = component['total_price']
                total_amount += total_price
                
                tree.insert('', 'end', values=(
                    component['component_name'],
                    component['type_name'] or '-',
                    component['manufacture_name'] or '-',
                    f"{component['price']:.2f} руб.",
                    component['quantity'],
                    f"{total_price:.2f} руб."
                ))
            
            ttk.Label(dialog, text=f'Общая сумма: {total_amount:.2f} руб.', style='Header.TLabel').pack(pady=10)
    
    def delete_configuration(self):
        selected = self.configurations_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите конфигурацию')
            return
        
        item = selected[0]
        config_id = self.configurations_tree.item(item)['values'][0]
        config_name = self.configurations_tree.item(item)['values'][2]
        
        if messagebox.askyesno('Подтверждение', f'Удалить конфигурацию "{config_name}"?'):
            data = self.make_api_request('/configurations/admin/delete_by_id/', method='DELETE',
                                       params={'config_id': config_id})
            if data:
                messagebox.showinfo('Успех!', 'Конфигурация удалена')
                self.load_configurations()
    
    def init_orders_tab(self):
        main_frame = ttk.Frame(self.tab_orders, style='TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text='Управление заказами', style='Header.TLabel').pack(pady=10)

        search_frame = ttk.Frame(main_frame, style='TFrame')
        search_frame.pack(fill='x', pady=10)
        
        ttk.Label(search_frame, text='Поиск по email:', style='Normal.TLabel').pack(side='left', padx=5)
        
        self.order_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.order_search_var, width=30, style='TEntry')
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text='🔎', 
                  command=self.search_orders, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(search_frame, text='🔄', 
                  command=self.load_orders, style='Accent.TButton').pack(side='left', padx=5)

        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text='🔄', 
                  command=self.load_orders, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='✏️', 
                  command=self.change_order_status, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text='❌', 
                  command=self.delete_order, style='Accent.TButton').pack(side='left', padx=5)

        columns = ('id', 'user', 'date', 'total', 'status')
        self.orders_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.orders_tree.heading('id', text='ID заказа')
        self.orders_tree.heading('user', text='Пользователь')
        self.orders_tree.heading('date', text='Дата')
        self.orders_tree.heading('total', text='Сумма')
        self.orders_tree.heading('status', text='Статус')
        
        self.orders_tree.column('id', width=80)
        self.orders_tree.column('user', width=120)
        self.orders_tree.column('date', width=100)
        self.orders_tree.column('total', width=100)
        self.orders_tree.column('status', width=120)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscroll=scrollbar.set)
        
        self.orders_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        search_entry.bind('<Return>', lambda event: self.search_orders())
        
        self.all_orders = []
        self.load_orders()

    def search_orders(self):
        """Поиск заказов по email пользователя"""
        search_text = self.order_search_var.get().strip().lower()
        
        if not search_text:
            self.display_orders(self.all_orders)
            return

        filtered_orders = [
            order for order in self.all_orders 
            if search_text in order['user_login'].lower()
        ]
        
        self.display_orders(filtered_orders)
        
        messagebox.showinfo('Поиск', f'Найдено заказов: {len(filtered_orders)}')

    def load_orders(self):
        data = self.make_api_request('/orders/admin/get_all')
        if data:
            self.all_orders = data
            self.display_orders(data)
            
    def display_orders(self, orders):
        """Отображение списка заказов в таблице"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
            
        for order in orders:
            order_date = order.get('order_date', '')
            if order_date:
                try:
                    order_date = order_date.split('T')[0]
                except:
                    pass
            
            total_amount = order.get('total_amount', 0)
            total_text = f"{total_amount:.2f} руб." if total_amount else "0 руб."
            
            self.orders_tree.insert('', 'end', values=(
                order['id'],
                order['user_login'],
                order_date,
                total_text,
                order.get('status_name', 'Неизвестно')
            ))
    
    def change_order_status(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите заказ')
            return
        
        item = selected[0]
        order_id = self.orders_tree.item(item)['values'][0]
        current_status = self.orders_tree.item(item)['values'][4]

        statuses_data = self.make_api_request('/order_status/get_all/')
        if not statuses_data:
            return
        
        status_names = [status['name'] for status in statuses_data]
        
        dialog = tk.Toplevel(self.root)
        dialog.title('Изменение статуса заказа')
        dialog.geometry('400x200')
        dialog.configure(bg='#40E0D0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f'Заказ: #{order_id}', style='Normal.TLabel').pack(pady=10)
        ttk.Label(dialog, text=f'Текущий статус: {current_status}', style='Normal.TLabel').pack(pady=5)
        
        status_var = tk.StringVar(value=current_status)
        status_combo = ttk.Combobox(dialog, textvariable=status_var, state='readonly', style='TCombobox')
        status_combo['values'] = status_names
        status_combo.pack(pady=10)
        
        def save_status():
            new_status = status_var.get()
            if new_status == current_status:
                messagebox.showinfo('Информация', 'Статус не изменен')
                dialog.destroy()
                return

            status_id = None
            for status in statuses_data:
                if status['name'] == new_status:
                    status_id = status['id']
                    break
            
            if status_id is None:
                messagebox.showerror('Ошибка!', 'Статус не найден')
                return
            
            data = self.make_api_request('/orders/admin/edit_order_status/', method='PUT',
                                       json_data={'status_id': status_id},
                                       params={'order_id': order_id})
            if data:
                messagebox.showinfo('Успех!', 'Статус заказа изменен')
                dialog.destroy()
                self.load_orders()
        
        ttk.Button(dialog, text='✔️', command=save_status, style='Accent.TButton').pack(pady=10)
    
    def delete_order(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning('Внимание!', 'Выберите заказ')
            return
        
        item = selected[0]
        order_id = self.orders_tree.item(item)['values'][0]
        
        if messagebox.askyesno('Подтверждение', f'Удалить заказ #{order_id}?'):
            data = self.make_api_request('/orders/admin/delete_order/', method='DELETE',
                                       params={'order_id': order_id})
            if data:
                messagebox.showinfo('Успех!', 'Заказ удален')
                self.load_orders()

class AuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title('')
        self.root.geometry('1920x1080')
        self.root.state('zoomed')
        
        self.bg_color = '#40E0D0'
        self.fg_color = 'black'
        self.accent_color = "white"
        self.button_fg = "black"
        self.entry_bg = 'white'
        
        self.title_font = Font(family='Helvetica', size=30, weight='bold')
        self.normal_font = Font(family='Arial', size=14, weight='normal') 
        self.root.configure(bg=self.bg_color)
        
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.create_auth_widgets()
        
        self.base_url = 'http://127.0.0.1:8000'
        self.token = None
    
    def create_auth_widgets(self):
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
        register_window.configure(bg='#40E0D0')
        
        tk.Label(
            register_window,
            text='Регистрация',
            font=self.title_font,
            bg='#40E0D0',
            fg='black'
        ).pack(pady=20)
        
        form_frame = tk.Frame(register_window, bg='#40E0D0')
        form_frame.pack(pady=20)
        
        tk.Label(
            form_frame,
            text='Email:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
        ).grid(row=0, column=0, pady=5, ipady=5)
        
        self.reg_email = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_email.grid(row=0, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Пароль:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
        ).grid(row=1, column=0, padx=10, pady=5)
        
        self.reg_password = ttk.Entry(form_frame, width=30, show='*', font=self.normal_font)
        self.reg_password.grid(row=1, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Подтвердите пароль:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
        ).grid(row=2, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_confirm_password = ttk.Entry(form_frame, width=30, show='*', font=self.normal_font)
        self.reg_confirm_password.grid(row=2, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='ФИО:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
        ).grid(row=3, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_full_name = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_full_name.grid(row=3, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Телефон:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
        ).grid(row=4, column=0, sticky='e', padx=10, pady=5)
        
        self.reg_phone = ttk.Entry(form_frame, width=30, font=self.normal_font)
        self.reg_phone.grid(row=4, column=1, pady=5, ipady=5)
        
        tk.Label(
            form_frame,
            text='Адрес:',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
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
        self.forgot_window = tk.Toplevel(self.root)
        self.forgot_window.title('Восстановление пароля')
        self.forgot_window.geometry('600x500')
        self.forgot_window.resizable(False, False)
        self.forgot_window.configure(bg='#40E0D0')
        
        tk.Label(
            self.forgot_window,
            text='Введите email для восстановления пароля',
            font=self.normal_font,
            bg='#40E0D0',
            fg='black'
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
        
        self.code_frame = tk.Frame(self.forgot_window, bg='#40E0D0')
        
    def send_confirmation_code(self):
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
                    font=self.normal_font,
                    bg='#40E0D0',
                    fg='black'
                    ).pack(pady=10)
                
                self.code_entry = ttk.Entry(self.code_frame, width=30, font=self.normal_font)
                self.code_entry.pack(pady=10)
                
                tk.Label(
                    self.code_frame,
                    text='Новый пароль:',
                    font=self.normal_font,
                    bg='#40E0D0',
                    fg='black'
                ).pack(pady=10)
                
                self.new_password_entry = ttk.Entry(self.code_frame, width=30, show='*', font=self.normal_font)
                self.new_password_entry.pack(pady=10)
                
                ttk.Button(
                    self.code_frame,
                    text='✔️',
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
        