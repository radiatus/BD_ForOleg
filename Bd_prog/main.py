import os, sqlite3
import mytable
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from openpyxl import load_workbook

DB_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DBs')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

DEBUG = True

DATABASES = {} #словарь таблиц
ROWS = {}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            if filename[-2:] == 'db':
                file.save(os.path.join(DB_FOLDER, filename))
                return redirect(url_for('show_db', filename=filename))

    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):  # загрузка файла
    return create_tmp_db(filename)


@app.route('/download/<filename>')
def download(filename):  # скачивание файла
    return send_from_directory(DB_FOLDER, filename)


@app.route('/db_settings/<db_name>')
def db_settings(db_name):
    return render_template('TablesSettings.html', db_name=db_name, DB=DATABASES[db_name])


@app.route('/add_col/', methods=['POST'])
def add_col():
    db_name = request.form['db_name']
    DATABASES[db_name][request.form['table_name']].add_headline_name("New")
    return redirect(url_for('db_settings', db_name=db_name))
    #return render_template('TablesSettings.html', db_name=db_name, DB=DATABASES[db_name])


@app.route('/change_name/', methods=['POST'])
def change_name():
    db_name = request.form['db_name']
    table_name = request.form['table_name']
    loop_index = request.form['loop_index']
    name = request.form['value']

    DATABASES[db_name][table_name].change_headline_name(int(loop_index), name)
    return redirect(url_for('db_settings', db_name=db_name))
    #return render_template('TablesSettings.html', db_name=db_name, DB=DATABASES[db_name])


@app.route('/set_types/', methods=['POST'])
def set_types():
    db_name = request.form['db_name']
    table_name = request.form['table_name']

    for i in range(len(DATABASES[db_name][table_name].headline_names)):
        s = 'type' + str(i)
        type = request.form.get(s)
        if type == None:
            type = 'text'  # значение по умолчанию
        DATABASES[db_name][table_name].set_headline_type(i, type)

    return redirect(url_for('db_settings', db_name=db_name))
    #return render_template('TablesSettings.html', db_name=db_name, DB=DATABASES[db_name])


@app.route('/set_cons/', methods=['POST'])
def set_cons():
    db_name = request.form['db_name']
    table_name = request.form['table_name']

    possibles_cons = ['primary key', 'unique', 'AUTOINCREMENT', 'not null']
    for i in range(len(DATABASES[db_name][table_name].headline_names)):
        list = []
        for cons in possibles_cons:
            tmp = request.form.get(cons + str(i))
            if tmp == None:
                continue
            list.append(tmp)
        for_key = request.form.get('foreign key' + str(i))
        DATABASES[db_name][table_name].add_foreign_key(i, for_key)
        DATABASES[db_name][table_name].set_headline_cons(i, list)

    return redirect(url_for('db_settings', db_name=db_name))
    #return render_template('TablesSettings.html', db_name=db_name, DB=DATABASES[db_name])


@app.route('/create_data_base/', methods=['POST'])
def create_data_base():

    db_name = request.form['db_name']
    pathToDB = os.path.join(DB_FOLDER, (db_name + '.db'))
    try:
        if os.path.exists(pathToDB):  # удаляем, если такая имеется
            os.remove(pathToDB)
    except:
        print("Не могу удалить файл ", pathToDB)
        return redirect(url_for('db_settings', db_name=db_name))

    conn = sqlite3.connect(pathToDB)
    cursor = conn.cursor()

    for table_name in DATABASES[db_name].keys():
        command = DATABASES[db_name][table_name].get_create_command()
        try:
            cursor.execute(command)
            conn.commit()
        except:
            print(command)

    cursor.close()
    conn.close()

    if os.path.exists(pathToDB):
        os.remove(os.path.join(EXEL_FOLDER, db_name + '.xlsx'))

    filename = db_name + '.db'
    return redirect(url_for('show_db', filename=filename))


@app.route('/show_db/<filename>', methods=['GET', 'POST'])
def show_db(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_view = mytable.TablesView(path_to_db)

    if request.method == 'POST':
        table_name = request.form.get('name')
        rows = get_rows_from_bd(filename, table_name)
        return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows)

    return render_template('viewdb.html', filename=filename, table_view=table_view)


@app.route('/add_row/<filename>', methods=['POST'])
def add_row(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_name = request.form.get('table_name')
    command = ""
    headline = ""
    i = 0
    while request.form.get('name' + str(i)) != None:
        name = request.form.get('name' + str(i))
        newVal = request.form.get(name)
        if  newVal != '':
            headline += '\'' + name + '\', '
            command += '\'' + request.form.get(name)+ '\', '
        i += 1

    command = 'INSERT INTO ' + table_name + ' ( ' + headline[:-2] + ' ) VALUES (' + command[:-2] + ')'

    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
    try:
        cursor.execute(command)
        conn.commit()
    except:
        pass

    cursor.close()
    conn.close()
    table_view = mytable.TablesView(path_to_db)
    rows = get_rows_from_bd(filename, table_name)
    return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows)


@app.route('/find_row/<filename>', methods=['POST'])
def find_row(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_name = request.form.get('table_name')
    headline = []
    patterns = []
    search_val = []
    i = 0
    while request.form.get('name' + str(i)) != None:
        name = request.form.get('name' + str(i))
        headline.append(name)
        patterns.append(request.form.get(name))
        search_val.append(request.form.get(name))
        i += 1

    table_view = mytable.TablesView(path_to_db)
    rows = find_rows_from_bd(filename, table_name, headline, patterns)

    return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows, search_val=search_val)


@app.route('/del_row/<filename>', methods=['POST'])
def del_row(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_name = request.form.get('table_name')
    table_view = mytable.TablesView(path_to_db)

    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()

    command = "DELETE FROM " + table_name + ' WHERE ('
    cursor.execute('PRAGMA table_info(' + table_name + ')')
    table_info = cursor.fetchall()

    for i in range(len(table_view.headline_names[table_name])):
        value = request.form.get('cell_new' + str(i))
        if value is None:
            continue

        if len(table_info[i][2]) == 7:
            if table_info[i][2][:7] == 'INTEGER':
                command += table_view.headline_names[table_name][i] + ' = ' + value + ' AND '
        else:
            command += table_view.headline_names[table_name][i] + ' =  \'' + value + '\' AND '

    command = command[:-4] + ');'

    try:
        cursor.execute(command)
        conn.commit()
    except:
        pass

    cursor.close()
    conn.close()

    command = 'SELECT * FROM ' + table_name
    rows = get_rows_by_command(filename, command)
    return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows)


@app.route('/change_row/<filename>', methods=['POST'])
def change_row(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_name = request.form.get('table_name')
    table_view = mytable.TablesView(path_to_db)

    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()

    cursor.execute('PRAGMA table_info(' + table_name + ')')
    table_info = cursor.fetchall()

    command = "UPDATE " + table_name + ' SET '

    i = 0
    while request.form.get('name' + str(i)) != None:
        name = request.form.get('name' + str(i))
        new_value = request.form.get('cell_new' + str(i))

        if new_value == '':
            i += 1
            continue

        if len(table_info[i][2]) == 7:
            if  table_info[i][2][:7] == 'INTEGER':
                command += '"' + name + '" = ' + new_value + ', '
        else:
            command += '"' + name + '" = \'' + new_value + '\', '

        i += 1

    command = command[:-2] + ' WHERE ('

    for i in range(len(table_view.headline_names[table_name])):
        value = request.form.get('cell_old' + str(i))
        if len(table_info[i][2]) == 7:
            if table_info[i][2][:7] == 'INTEGER':
                command += '"' + table_view.headline_names[table_name][i] + '" = ' + value + ' AND '
        else:
            command += '"' + table_view.headline_names[table_name][i] + '" =  \'' + value + '\' AND '

    command = command[:-4] + ');'

    try:
        cursor.execute(command)
        conn.commit()
    except:
        pass

    cursor.close()
    conn.close()

    command = 'SELECT * FROM ' + table_name
    rows = get_rows_by_command(filename, command)
    return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows)


@app.route('/show_all_row/<filename>', methods=['POST'])
def show_all_row(filename):
    path_to_db = os.path.join(DB_FOLDER, filename)
    table_name = request.form.get('table_name')

    table_view = mytable.TablesView(path_to_db)
    rows = get_rows_from_bd(filename, table_name)
    return render_template('Table.html', filename=filename, table_view=table_view, tablename=table_name, rows=rows)


def find_rows_from_bd(filename, table_name, headline, patterns):

    path_to_db = os.path.join(DB_FOLDER, filename)
    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(' + table_name + ')')
    table_info = cursor.fetchall()
    cursor.close()
    conn.close()

    command = 'SELECT * FROM ' + table_name + ' WHERE ( '
    for i in range(len(headline)):
        if patterns[i] != '':
            #if table_info[i][2] == 'int':
            #    command += ' WHERE CAST( \'' + headline[i] + '\' AS TEXT) LIKE \'%' + patterns[i] + '%\' AND'
            #else:
            command += '\"' + headline[i] + '\" LIKE \'%' + patterns[i] + '%\' AND'

    if command[-3:] == 'AND':
        command = command[:-3] + ');'
        return get_rows_by_command(filename, command)
    else:
        pass


def get_rows_from_bd(filename, table_name):
    command = 'SELECT * FROM ' + table_name
    return get_rows_by_command(filename, command)


def get_rows_by_command(filename, command):
    pathToDB = os.path.join(DB_FOLDER, filename)
    conn = sqlite3.connect(pathToDB)
    cursor = conn.cursor()

    cursor.execute(command)
    rows = []
    for row in cursor.fetchall():
        tmplist = []
        for cell in row:
            tmplist.append(cell)
        rows.append(tmplist)

    cursor.close()
    conn.close()
    return rows


if __name__ == '__main__':
    app.run()