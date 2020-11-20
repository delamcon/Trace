import requests  # для работы с http запросами
import sys
import sqlite3

from ApiCheck import Ui_MainWindow
from AllWindows import AllWindows
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt


class ApiCheckWindow(Ui_MainWindow):  # PyQt окно проверки API
    def __init__(self):
        super().__init__()


class AllWindows(AllWindows):
    def __init__(self):
        super().__init__()


class ApiCheck(QMainWindow, ApiCheckWindow):  # окно для ввода API
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.center()  # ссылается на функцию, выставляющую окно по центру
        self.MainButton.clicked.connect(self.check)
        # проверяем вводился ли корректный api до этого
        f = open("./last_api_key")
        line = f.readline().rstrip()
        head = "https://api.vk.com/method/"
        url = f"{head}users.get?user_ids=210700286&access_token={line}&v=5.124"
        result = requests.get(url).json()
        if 'error' not in result.keys():
            self.MainLineEdit.setText(line)
        f.close()

    def center(self):
        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - self.width()) // 2
        y = (desktop.height() - self.height()) // 2
        self.move(x, y)

    def check(self):  # проверка на корректность API
        self.gifLabel.show()
        head = "https://api.vk.com/method/"
        api_key = self.MainLineEdit.text()
        url = f"{head}users.get?user_ids=210700286&fields=city&lang=0" \
              f"&access_token={api_key}&v=5.124"
        path = 'loading.gif'
        gif = QtGui.QMovie(path)
        self.gifLabel.setMovie(gif)
        gif.start()
        result = requests.get(url).json()
        if 'error' in result.keys():  # если API некорректен, вывоиться ошибка
            self.gifLabel.hide()
            QtWidgets.QMessageBox.information(None, "Неверный API",
                      "Введите корректный API",
                      buttons=QtWidgets.QMessageBox.Close,
                      defaultButton=QtWidgets.QMessageBox.Close)
        else:  # если API корректен, он сохраняется в файл для удобства
            # и вывоиться основное окно Window
            f = open("./last_api_key", "w")
            f.write(api_key)
            f.close()

            self.wnd = Window(self.MainLineEdit.text())
            self.close()
            self.wnd.show()


class Window(QMainWindow, AllWindows):  # класс окна главного меню
    def __init__(self, api_key):
        super(Window, self).__init__()
        self.resize(750, 410)
        self.api_key = api_key
        self.center()  # ссылается на функцию, выставляющую окно по центру
        self.setupUi()
        self.backMenuButton1.clicked.connect(self.backButton)
        self.backMenuButton2.clicked.connect(self.targetBack)
        self.targetButton.clicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(2))
        self.whichCity.clicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(1))
        self.checkBox.stateChanged.connect(self.targetCheckB)
        self.pushButton.clicked.connect(self.targetFile)

        self.targetInputButton.clicked.connect(self.targetInput)
        self.mutualInputButton.clicked.connect(
            self.mutualInput)  # вызывается после нажатия кнопки Далее
        self.targetNextButton.clicked.connect(self.targetDo)
        self.listWidgetFill = []
        self.listWidgetFill2 = []
        self.checkFlag = False
        self.targetForFile = []

    def mutualInput(self):
        self.mutualLineEdit.setReadOnly(1)
        self.mutualNameLabel.setText('')
        self.mutualListWidget.clear()
        if self.idCheck():  # проверка корректности введенной ссылки
            head = "https://api.vk.com/method/"
            idIn = self.CheckedId
            # получаем основную информацию о человеке, фамилию, имя,
            # город, закрытый ли профиль
            mainInf = f"{head}users.get?user_ids={idIn}&fields=city&lang=0" \
                      f"&access_token={self.api_key}&v=5.124"
            infRes = requests.get(mainInf).json()['response'][0]
            idIn = infRes['id']
            # выводим имя и фамилию
            self.mutualNameLabel.setText(
                f'{infRes["first_name"]} {infRes["last_name"]}')
            # получаем список друзей
            friends = f"{head}friends.get?user_id={idIn}&fields=city" \
                      f"&lang=0&access_token={self.api_key}&v=5.124"
            result = requests.get(friends).json()
            # выводим количество друзей
            self.mutualNameLabel.setText(
                f'{self.mutualNameLabel.text()}     '
                f'Количество друзей: {result["response"]["count"]}')
            with sqlite3.connect("Trace.db") as con:
                cur = con.cursor()
                res = cur.execute('SELECT id_vk FROM people_data')
                res = list(res)
                dbIn = []
                for g in res:
                    dbIn.append(str(g[0]))
                if str(idIn) not in dbIn:
                    profName = infRes['first_name']
                    profSur = infRes['last_name']
                    profId = infRes['id']
                    profClose = infRes['is_closed']
                    profFrnds = []
                    if 'city' in infRes:
                        profCity = infRes['city']['title']
                    else:
                        profCity = 'Null'
                    for i in result['response']['items']:
                        profFrnds.append(f"{str(i['id'])}")
                    profFrnds = ', '.join(profFrnds)
                    dbIn = (
                    profName, profSur, profId, profClose, profFrnds, profCity)
                    cur.execute('''INSERT INTO people_data(first_name, 
                        last_name, id_vk, is_closed, friends, city) 
                        VALUES(?, ?, ?, ?, ?, ?)''', dbIn)
            with sqlite3.connect("Trace.db") as con:
                cur = con.cursor()
                friendsdb = cur.execute('''SELECT friends FROM people_data 
                                WHERE id_vk = ?''', (idIn,))
                friendsdb = list(friendsdb)[0][0].split(', ')
                res = cur.execute('SELECT id_vk FROM people_data')
                res = list(res)
                normRes = []
                for i in res:
                    normRes.append(i[0])
                friendsForList = []
                AllCities = dict()
                head = 'https://api.vk.com/method/'
                for i in friendsdb:  # перечисляем друзей человека
                    if int(
                            i) in normRes:
                        # проверяем есть ли человек в базе данных
                        tmpRes = cur.execute('''SELECT first_name, last_name, 
                                     city FROM people_data WHERE id_vk = ?''',
                                             (int(i),))
                        tmpRes = list(tmpRes)[0]
                        if tmpRes[2] != 'Null':
                            friendsForList.append(tmpRes)
                            if tmpRes[2] not in AllCities:
                                AllCities[tmpRes[2]] = 1
                            else:
                                AllCities[tmpRes[2]] += 1
                    else:
                        finf = f"{head}users.get?user_ids={i}&fields=city" \
                               f"&lang=0&access_token={self.api_key}&v=5.124"
                        fres = requests.get(finf).json()['response']
                        if 'deactivated' not in fres[0]:
                            profName = fres[0]['first_name']
                            profSur = fres[0]['last_name']
                            profId = fres[0]['id']
                            profClose = fres[0]['is_closed']
                            profFrnds = []
                            if 'city' in fres[0]:
                                profCity = fres[0]['city']['title']
                                if fres[0]['city']['title'] not in AllCities:
                                    AllCities[fres[0]['city']['title']] = 1
                                else:
                                    AllCities[fres[0]['city']['title']] += 1
                                friendsForList.append(
                                    (fres[0]['first_name'],
                                     fres[0]['last_name'],
                                     fres[0]['city']['title']))
                            else:
                                profCity = 'Null'
                            for i in result['response']['items']:
                                profFrnds.append(f"{str(i['id'])}")
                            profFrnds = ', '.join(profFrnds)
                            dbIn = (
                            profName, profSur, profId, profClose, profFrnds,
                            profCity)
                            cur.execute('''INSERT INTO people_data(first_name, 
                                last_name, id_vk, is_closed, friends, city) 
                                VALUES(?, ?, ?, ?, ?, ?)''',
                                        dbIn)
                c = []  # cities
                cc = []  # cities count
                for i in AllCities.keys():
                    c.append(i)
                    cc.append([AllCities[i]])

                if len(cc) == 0:
                    self.mutualListWidget.addItem(
                        f'Предположительный город не определен')
                else:
                    x = [i for i, ltr in enumerate(cc) if ltr == max(cc)]
                    print(AllCities)
                    x = [c[i] for i in x]
                    if len(x) == 1:
                        self.mutualListWidget.addItem(
                            f'Предположительный город - {x[0]}')
                    else:
                        self.mutualListWidget.addItem(
                            'Предположительные города:')
                        for i in x:
                            self.mutualListWidget.addItem(i)
                    self.mutualListWidget.addItem('----- друзья -----')
                    for i in friendsForList:
                        listIn = f"{i[0]} {i[1]}      {i[2]}"
                        self.mutualListWidget.addItem(listIn)

    def idCheck(self):
        url = self.mutualLineEdit.text()
        if 'https://vk.com/' in url:
            self.CheckedId = url[15:]  # извлекаем из ссылки только id
            id = self.CheckedId
            # if not self.mutualLineEdit.isReadOnly():
            head = "https://api.vk.com/method/"
            url = f"{head}users.get?user_ids={id}&fields=bdate" \
                  f"&access_token={self.api_key}&v=5.124"
            profile = requests.get(url).json()
            print(profile)
            if 'error' in profile:  # проверяем на ошибки
                QtWidgets.QMessageBox.information(None, "Аккаунт закрыт",
                          "Введите другой аккаунт",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            elif profile['response'][0]['first_name'] == 'DELETED':
                self.mutualLineEdit.setText('')
                QtWidgets.QMessageBox.information(None, "Аккаунт заблокирован",
                          "Введите другой аккаунт",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            elif 'deactivated' in profile['response'][0]:
                QtWidgets.QMessageBox.information(None,
                          "Аккаунт деактивирован",
                          "Введите другой аккаунт",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            elif profile['response'][0]['is_closed']:
                QtWidgets.QMessageBox.information(None, "Аккаунт закрыт",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            else:  # возвращаем True, если ссылка корректна
                return True

        else:
            QtWidgets.QMessageBox.information(None, "Неккоретная ссылка",
                      "Введите корректную ссылку",
                      buttons=QtWidgets.QMessageBox.Close,
                      defaultButton=QtWidgets.QMessageBox.Close)
            return False

    def targetInput(self):
        if self.targetCheck():
            url = self.targetLineEdit.text().rstrip().lstrip()
            self.targetLineEdit.setReadOnly(1)
            сheckedId = url.rstrip().lstrip()[15:]
            print(сheckedId)
            head = "https://api.vk.com/method/"
            groupCheck = f"{head}utils.resolveScreenName?" \
                         f"screen_name={сheckedId}&lang=0" \
                         f"&access_token={self.api_key}&v=5.124"
            print(groupCheck)
            groupCheck = requests.get(groupCheck).json()['response']
            print(groupCheck)
            idCheck = f"{head}groups.getMembers?group_id={сheckedId}" \
                      f"&offset=0&count=1000&lang=0" \
                      f"&access_token={self.api_key}&v=5.124"
            idCheck = requests.get(idCheck).json()['response']
            self.listWidgetFill2.append(сheckedId)
            with sqlite3.connect("Trace.db") as con:
                cur = con.cursor()
                allCom = cur.execute('SELECT group_id FROM communities')
                normAllCom = []
                for i in allCom:
                    normAllCom.append(i[0])
                if int(groupCheck['object_id']) not in normAllCom:
                    if idCheck['count'] > 1000:
                        peopleForDB = []
                        for i in range(idCheck['count'] // 1000 + 1):
                            peopleGet = f"{head}groups.getMembers?" \
                                f"group_id={сheckedId}&offset={i * 1000}" \
                                f"&count=1000&lang=0&" \
                                f"access_token={self.api_key}&v=5.124"
                            peopleGet = requests.get(peopleGet).json()[
                                'response']
                            print(peopleGet)
                            for i in peopleGet['items']:
                                peopleForDB.append(str(i))
                        peopleForDB = ','.join(peopleForDB)
                        cur.execute('''INSERT INTO communities(group_id, 
                            people_id) VALUES(?, ?)''',
                            (groupCheck['object_id'], peopleForDB))
                    else:
                        peopleForDB = []
                        peopleGet = f"{head}groups.getMembers?" \
                            f"group_id={сheckedId}&offset=0&count=1000" \
                            f"&lang=0&access_token={self.api_key}&v=5.124"
                        peopleGet = requests.get(peopleGet).json()['response']
                        for i in peopleGet['items']:
                            peopleForDB.append(str(i))
                        peopleForDB = ','.join(peopleForDB)
                        cur.execute('''INSERT INTO communities(group_id, 
                            people_id) VALUES(?, ?)''',
                            (groupCheck['object_id'], peopleForDB))
                self.targetLineEdit.setReadOnly(0)
                self.targetListWidget.addItem(f"{url}")
                self.targetLineEdit.setText('')
                self.listWidgetFill.append(groupCheck['object_id'])
                print(self.listWidgetFill)

    def targetCheckB(self):
        if self.checkFlag:
            self.checkFlag = False
        else:
            self.checkFlag = True

    def targetDo(self):
        self.targetLineEdit.setReadOnly(1)
        if len(self.listWidgetFill) <= 1:
            QtWidgets.QMessageBox.information(None, "Мало сообществ",
                      "Введите, как минимум, 2 сообщества",
                      buttons=QtWidgets.QMessageBox.Close,
                      defaultButton=QtWidgets.QMessageBox.Close)
        else:
            with sqlite3.connect("Trace.db") as con:
                cur = con.cursor()
                allPeople = []
                head = "https://api.vk.com/method/"
                self.targetListWidget.clear()
                for i in self.listWidgetFill:
                    peopleFromCom = cur.execute(
                        'SELECT people_id FROM communities WHERE group_id = ?',
                        (int(i),)).fetchall()[0][0]
                    peoples = peopleFromCom.split(',')
                    peoples = set(peoples)
                    allPeople.append(peoples)
                p = allPeople[0]
                for i in range(len(allPeople) - 1):
                    crossing = p.intersection(allPeople[i + 1])
                    p = crossing
                self.targetListWidget.clear()
                self.targetListWidget.addItem('----- Общие подписчики -----')
                p = list(p)
                print(p)
                print(len(p))
                if not self.checkFlag:
                    for i in p:
                        self.targetForFile.append(i)
                        self.targetListWidget.addItem(f'{i}')
                else:
                    for i in p:
                        selPeopleS = cur.execute(
                            'SELECT id_vk FROM people_data').fetchall()
                        selPeople = []
                        for y in selPeopleS:
                            selPeople.append(int(y[0]))
                        if int(i) in selPeople:
                            setPeople = cur.execute('''SELECT first_name, 
                                last_name, id_vk 
                                FROM people_data WHERE id_vk = ?''',
                                (int(i),)).fetchall()[0]
                            print(setPeople)
                            self.targetForFile.append(setPeople[2])
                            self.targetListWidget.addItem(f'{setPeople[0]} '
                                f'{setPeople[1]}    {setPeople[2]}')
                        else:
                            peopleInf = f"{head}users.get?user_ids={int(i)}"\
                                f"&fields=city&lang=0&access_token=" \
                                f"{self.api_key}&v=5.124"
                            peopleInf = \
                            requests.get(peopleInf).json()['response'][0]
                            friends = f"{head}friends.get?user_id={int(i)}" \
                                      f"&fields=city&lang=0" \
                                      f"&access_token={self.api_key}&v=5.124"
                            result = requests.get(friends).json()
                            print(result)
                            TestErr = 'error' not in peopleInf and \
                                      peopleInf['first_name'] != 'DELETED' \
                                      and 'deactivated' not in peopleInf and \
                                      not peopleInf['is_closed']
                            if TestErr:
                                print(peopleInf)
                                profName = peopleInf['first_name']
                                profSur = peopleInf['last_name']
                                profId = peopleInf['id']
                                profClose = peopleInf['is_closed']
                                profFrnds = []
                                if 'city' in peopleInf:
                                    profCity = peopleInf['city']['title']
                                else:
                                    profCity = 'Null'
                                for k in result['response']['items']:
                                    profFrnds.append(f"{str(k['id'])}")
                                profFrnds = ', '.join(profFrnds)
                                dbIn = (profName, profSur, profId, profClose,
                                        profFrnds, profCity)
                                cur.execute('''INSERT INTO people_data(
                                    first_name, last_name, id_vk, is_closed, 
                                    friends, city) 
                                    VALUES(?, ?, ?, ?, ?, ?)''', dbIn)
                                self.targetForFile.append(i)
                                self.targetListWidget.addItem(
                                    f'{peopleInf["first_name"]} '
                                    f'{peopleInf["last_name"]}    {i}')

    def checkBoxCheck(self, state):
        if state == Qt.Checked:
            return True
        else:
            return False

    def targetFile(self):
        print(self.targetForFile)
        if len(self.targetForFile) != 0:
            with open('ЦелеваяАудитория', 'w') as f:
                for i in self.targetForFile:
                    print(i, file=f)
            QtWidgets.QMessageBox.information(None, "Сделано",
                      "Данные в файле",
                      buttons=QtWidgets.QMessageBox.Close,
                      defaultButton=QtWidgets.QMessageBox.Close)

    def targetBack(self):
        self.listWidgetFill = []
        self.listWidgetFill2 = []
        self.checkFlag = False
        self.targetForFile = []
        self.targetLineEdit.setReadOnly(0)
        self.targetLineEdit.setText('')
        self.targetForFile = []
        self.targetListWidget.clear()
        self.stackedWidget.setCurrentIndex(0)

    def targetCheck(self):
        url = self.targetLineEdit.text()
        if 'https://vk.com/' in url:
            сheckedId = url.rstrip().lstrip()[15:]
            print(сheckedId)
            head = "https://api.vk.com/method/"
            idCheck = f"{head}utils.resolveScreenName?screen_name=" \
                      f"{сheckedId}&lang=0&access_token={self.api_key}&v=5.124"
            idCheck = requests.get(idCheck).json()
            if idCheck['response'] == []:
                QtWidgets.QMessageBox.information(None, "Неккоретная ссылка",
                          "Введите корректную ссылку",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            elif idCheck['response']['type'] != 'group':
                QtWidgets.QMessageBox.information(None, "Ошибка",
                          "Введена ссылка не на сообщество",
                          buttons=QtWidgets.QMessageBox.Close,
                          defaultButton=QtWidgets.QMessageBox.Close)
                return False
            else:
                return True
        else:
            QtWidgets.QMessageBox.information(None, "Неккоретная ссылка",
                      "Введите корректную ссылку",
                      buttons=QtWidgets.QMessageBox.Close,
                      defaultButton=QtWidgets.QMessageBox.Close)

    def backButton(self):
        self.mutualLineEdit.setText('')
        self.mutualNameLabel.setText('')
        self.mutualListWidget.clear()
        self.mutualLineEdit.setReadOnly(0)
        self.stackedWidget.setCurrentIndex(0)
        friendsForList = []

    def center(self):
        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - self.width()) // 2
        y = (desktop.height() - self.height()) // 2
        self.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    api = ApiCheck()
    api.show()
    sys.exit(app.exec())
