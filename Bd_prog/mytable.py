import sqlite3

class Table():
    ALLOWED_TYPES = ['INTEGER', 'real', 'text']
    ALLOWED_CONSTRAINTS = ['primary key', 'foreign key', 'unique', 'AUTOINCREMENT', 'not null']

    def __init__(self, name: str, names: list, number: int):
        self.number = number
        self.table_name = name
        self.headline_names = []
        self.headline_types = []
        self.headline_cons = []
        self.headline_foreign_key = []

        for i in names:
            self.headline_names.append(i.strip())
            self.headline_types.append('text')
            self.headline_cons.append([])
            self.headline_foreign_key.append('')

    def add_headline_name(self, text: str):
        self.headline_names.append(text.strip())
        self.headline_types.append('text')
        self.headline_cons.append([])
        self.headline_foreign_key.append('')

    def change_headline_name(self, index: int, text: str):
        if index >= 0 and index < len(self.headline_names):
            self.headline_names[index] = text.strip()

    def set_headline_type(self, index: int, type_item:str):
         if type_item.strip() in self.ALLOWED_TYPES and index >= 0 and index < len(self.headline_types):
            self.headline_types[index] = type_item.strip()

    def set_headline_types(self, index:int, types: list):
        if index < 0 or index > len(self.headline_types):
            return

        self.headline_types[index].clear()
        for typeItem in types:
            if typeItem.strip() in self.ALLOWED_TYPES and index >=0 and index < len(self.headline_types):
                self.headline_types[index].append(typeItem.strip())

    def set_headline_cons(self, index:int, cons:list):
        if index < 0 or index > len(self.headline_cons):
            return

        self.headline_cons[index].clear()
        for consItem in cons:
            if consItem.strip() in self.ALLOWED_CONSTRAINTS:
                self.headline_cons[index].append(consItem.strip())

    def add_headline_cons(self, index: int, cons):
         if cons.strip() in self.ALLOWED_CONSTRAINTS and index >= 0 and index < len(self.headline_cons):
                self.headline_cons[index].append(cons.strip())

    def add_foreign_key(self, index: int, key):
        self.headline_foreign_key[index] = key.strip()

    def get_headline(self):
        res = ''
        for name in self.headline_names:
            res += "\'" + name + "\' "

        return res

    def get_create_command(self):
        command = ''
        primary_key = ''
        autoinc = False
        for i in range(len(self.headline_names)):
            command += ", \'" + self.headline_names[i] + "\'"
            command += ' ' + self.headline_types[i]
            for constr in self.headline_cons[i]:
                if constr == 'AUTOINCREMENT':
                    command += ' PRIMARY KEY AUTOINCREMENT'
                    autoinc = True
                elif constr == 'primary key':
                    primary_key += '\'' + self.headline_names[i] + '\', '  # создаем primary key
                else:
                    command += ' ' + constr

        command = command[2:]

        if not primary_key == '' and not autoinc:
            command += ', PRIMARY KEY (' + primary_key[:-2] + ')'

        for i in range(len(self.headline_names)):  # добавляем foreign key
            if not self.headline_foreign_key[i].strip() == '':
                command += ', FOREIGN KEY (' + self.headline_names[i] + ') REFERENCES '+ \
                          self.headline_foreign_key[i] + ' ON DELETE CASCADE ON UPDATE NO ACTION'

        command = 'CREATE TABLE ' + "\'" +self.table_name + "\'" + ' (' + command + ')'
        return command


class TablesView:

    def __init__(self, file_path):
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        command = 'SELECT name FROM sqlite_master WHERE type = "table"'

        self.table_names = []
        cursor.execute(command)
        rows = cursor.fetchall()
        for row in rows:
            self.table_names.append(row[0])

        self.headline_names = {}
        for name in self.table_names:
            command = 'SELECT * FROM ' + name
            cursor.execute(command)
            tmp_list = list(map(lambda x: x[0], cursor.description))
            self.headline_names[name] = tmp_list

        cursor.close()
        conn.close()