'''
MyMoney, версия 1
    Программа для отслеживания финансов.
    Используйте кнопку "обновить" для сортировки записей и подсчета баланса. 
    
Классы:
    
    MyModel
    
Функции:
    
    calculate_balance(model) -> int
    update(model)
    del_record(model, query)
    add_record(query, model)
    connect_db() -> tuple
    make_setts()
    settings(ui, setts, )
    
'''
from os.path import exists
from os import mkdir
import sys

from PyQt5 import QtWidgets, QtCore, QtSql

from form.MyMoney_py import Ui_Form



class MyModel(QtSql.QSqlTableModel):
    '''
    Класс унаследован от QSqlTableModel.
    
    Отличие от родителя - переопредилённый метод flags.
    '''
    def __init__(self, parent=None, db=QtSql.QSqlDatabase()):
        QtSql.QSqlTableModel.__init__(self, parent, db)
        
    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.column() < 2:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
    

    
def calculate_balance(model: MyModel) -> int:
    '''
    Подсчитывает и возращает баланс.

    Параметры
    ----------
   
    Возращает
    -------
    int
        Баланс.

    '''
    balance = 0
    for row in range(model.rowCount()):
        balance += int(model.data(model.index(row, 3)))
    return balance


def update(model: MyModel):
    '''
    Сортирует данные Бд и перезаписывает ini.

    Параметры
    ----------
    query : QtSql.QSqlQuery
        Объект запроса.

    Returns
    -------
    None.

    '''
    # получение дат начала и конца с компанентов
    date_start = ui.d_date_start.date().toString('yyyy-MM-dd')
    date_stop = ui.d_date_stop.date().toString('yyyy-MM-dd')
    # сортировка данных
    model.setFilter(f'dates BETWEEN "{date_start}" AND "{date_stop}"')
    model.select()
    # баланс
    newBalance = calculate_balance(model)
    ui.lcd_balance.display(newBalance)
    # ini
    setts.setValue('balance', newBalance)
    setts.setValue('date_start', date_start)
    setts.setValue('date_stop', date_stop)


def del_record(model: MyModel, query: QtSql.QSqlQuery):
    '''
    Удаляет запись из Бд.

    Параметры
    ----------
    query: QtSql.QSqlQuery
        Объект запроса.
    model: MyModel
        Своя модель.

    Возращает
    -------
    None.

    '''
    # получить id
    id_coll = model.data(model.index(ui.tv_table.currentIndex().row(), 0))
    # sql
    query.prepare('DELETE FROM balance WHERE id=?;')
    query.addBindValue(id_coll)
    query.exec_()
    query.clear()
    # обновить ini, баланс
    update(model)
    
    
def add_record(query: QtSql.QSqlQuery, model: MyModel):
    '''
    Добавляет пустую запись в Бд и обновляет модель.

    Parameters
    ----------
    query : QtSql.QSqlQuery
        Объект запроса.
    model : MyModel
        Своя модель.

    Returns
    -------
    None.

    '''
    query.prepare('INSERT INTO balance VALUES(NULL, :dates, :records, :money);')
    query.bindValue(':dates', QtCore.QDate.currentDate().toString('yyyy-MM-dd'))
    query.bindValue(':records', "новая запись")
    query.bindValue(':money', 0)
    query.exec_()
    query.clear()
    model.select()


def connect_db() -> tuple:
    '''
    Устанавливает соединение с Бд.

    Возращает
    -------
    tuple
        db: QSqlDatabase
        query: QSqlQuery.
        model: MyModel

    '''
    # создание каталога "database", если отсуствует
    if not exists('database'):
        mkdir('database')
    db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('database/MyMoney_db.sqlite')
    db.open()
    model = MyModel()
    query = QtSql.QSqlQuery()
    # создание Бд, если отсуствует
    if 'balance' not in db.tables():
        query.exec('''
                   CREATE TABLE balance(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       dates TEXT,
                       records TEXT,
                       money TEXT);
                      ''')
        query.clear()
        add_record(query, model)
    return db, query, model


def make_setts():
    '''Создаёт файл с настройками, если их нет.'''
    if not setts.allKeys():
        date_start = QtCore.QDate.currentDate()
        date_stop = QtCore.QDate(date_start.year(),
                                 date_start.month(),
                                 date_start.daysInMonth())
        setts.setValue('date_start', date_start.toString('yyyy-MM-dd'))
        setts.setValue('date_stop', date_stop.toString('yyyy-MM-dd'))
        setts.setValue('balance', 0)
    

def settings(ui: Ui_Form, setts: QtCore.QSettings, 
             model: MyModel, win: QtWidgets.QWidget, query: QtSql.QSqlQuery):
    '''Задает неизменяемые настройки.'''
    # установка формы
    ui.setupUi(win)
    # получение даты начала и даты конца
    date_start = setts.value('date_start') #2022-02-15
    date_stop = setts.value('date_stop') #2022-02-28
    # модель
    model.setTable('balance')
    model.setFilter(f'dates BETWEEN "{date_start}" AND "{date_stop}"')
    model.select()
    ui.tv_table.setModel(model)
    # комоненты (d_date_start, d_date_stop, lcd_balance)
    ui.d_date_start.setDate(QtCore.QDate.fromString(date_start, 'yyyy-MM-dd')) 
    ui.d_date_stop.setDate(QtCore.QDate.fromString(date_stop, 'yyyy-MM-dd'))
    ui.lcd_balance.display(setts.value('balance'))
    # заголовки
    ui.tv_table.horizontalHeader().setSectionResizeMode(
        QtWidgets.QHeaderView.Stretch) #авто распределение размеров секций
    ui.tv_table.hideColumn(0) #скрыть столбец "id"
    headers = ("id", "дата", "запись", "доход/расход")
    for idx in range(len(headers)):
        model.setHeaderData(idx, QtCore.Qt.Horizontal, headers[idx])
    # окно
    win.show()
    # сигналы
    ui.btn_update.clicked.connect(lambda: update(model))
    ui.btn_del.clicked.connect(lambda: del_record(model, query))
    ui.btn_add.clicked.connect(lambda: add_record(query, model))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QWidget()
    ui = Ui_Form()
    db, query, model = connect_db()
    setts = QtCore.QSettings('ini/MyMoney_ini.ini',
                             QtCore.QSettings.IniFormat)
    make_setts()
    settings(ui, setts, model, win, query)
    sys.exit(app.exec_())
         