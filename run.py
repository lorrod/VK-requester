import sqlite3
import vk_api
import time
from config import anticaptcha_key
from python3_anticaptcha import ImageToTextTask
import os



## SQLCOMMANDS
selectAllCommand = "SELECT * FROM {}"
countCommand = "SELECT count(*) FROM {}"
selectCountCommand = "SELECT count(*) FROM {}"
createCommand = """CREATE TABLE IF NOT EXISTS {} ('id' INTEGER(10) UNIQUE);"""
searchIDcommand = """
	SELECT * FROM {table}
	 WHERE id like ({id});"""
addIDCommand = """
	INSERT INTO {table} ('id')
	VALUES ({id});"""


def captcha_handler(captcha):
	key = ImageToTextTask.ImageToTextTask(anticaptcha_key=anticaptcha_key, save_format='const') \
			.captcha_handler(captcha_link=captcha.get_url())

	# Пробуем снова отправить запрос с капчей
	return captcha.try_again(key['solution']['text'])

def readingBOTsinfo(): # returns [['id','firstbot', 'pass', 'proxyID', 'passwP'], ['id','secondbot', 'pas2s', 'proxy2ID', 'pas2sw'], ['']]
	file = open('botsinfo.txt', 'r')
	bots = file.read().split('\n')
	botsList = []
	for countBot in range(len(bots)):
		botparams = []
		for params in bots[countBot].split('||'):
			botparams.append(params)
		if botparams != ['']:
			botsList.append(botparams)
	file.close()
	return botsList


def creatingBDfriends():
	#createCommand = """CREATE TABLE IF NOT EXISTS friendsIDs ('id' INTEGER(10) UNIQUE);"""
	#addIDCommand = """
	#	INSERT INTO friendsIDs ('id')
	#	VALUES ({id});"""
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(createCommand.format('friendsIDs'))
	#cursor.execute(addIDCommand.format(id = '1236543'))
	botsList = readingBOTsinfo()
	listOfId = []
	for bot in botsList:
		listOfId.append(getFriends(bot))
	for friendsEachBot in listOfId:
		if friendsEachBot != 'none':
			for ids in friendsEachBot:
				if notInBDFriends(ids):
					try:
						cursor.execute(addIDCommand.format(table = 'friendsIDs',id = ids))
					except sqlite3.IntegrityError:
						print('Составляем список друзей ботов')
	connection.commit()


def getFriends(bot):
	#вернем список с ID каждого бота(или того пользователя id которого подаем на вход)
	proxies = {
	   "https": "https://{}:{}@{}:{}/".format(bot[2], bot[3], bot[1], '80'),
	   "http": "http://{}:{}@{}:{}/".format(bot[2], bot[3], bot[1], '80')
	   }
	vk = vk_api.VkApi(token=bot[4], captcha_handler=captcha_handler)
	#vk = vk_api.VkApi(login = bot[1], password = bot[2], captcha_handler=captcha_handler)
	vk.http.proxies = proxies
	output =  'none'
	try:
		response = vk.method('friends.get', {'user_id': bot[0]})
		time.sleep(0.4)
		if response['items']:
			output = response['items']
	except HTTPSConnectionPool(host='api.vk.com', port=443):
		print('cry BITHCH')
	except Exception as e:
		print('Возникла ошибка при получении списка друзей '+ str(e))
	except vk_api.exceptions.AccountBlocked:
		print('Аккаунт '+str(botsList[0][1])+ ' заблокирован.')
		time.sleep(10)
	except requests.exceptions.ProxyError:
		print('Возникла ошибка с прокси, повторите попытку.')
	return output#output = ['id1','id2'...]


def notInBDFriends(ids):
	notFriends = False
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(searchIDcommand.format(table = 'friendsIDs', id = ids))
	answer = cursor.fetchone()
	if not answer:
		notFriends = True
	return notFriends

def deleteTable(TABLE):
	deleteCom = "DROP TABLE {};".format(TABLE)
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	try:
		cursor.execute(deleteCom)
	except sqlite3.OperationalError:
		print('Таблицы '+str(TABLE)+' не существует, создаем новую.')


#notInBDFriends(121040)
#deleteTable()
#creatingBDfriends()



#
#
#1. User main logined
#2. getFriends from bots to the SQLBD if not exist in BD
#3. Reading bots info in massive
#4. checking isFriends
#
#
#
#
titleshowen = False

def searchkUser(hometown, sex, birthDay, birthYear, count, offset):#needcountID, count показывают одно число, сколько нужно id найти, но needcountID  не будет изменяться - его нужно достичь, а  count  будет меняться для вызова метода vk
	global titleshowen
	
	if count > 1000:
		count = 1000
	response =  'none'
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(createCommand.format('userIDs'))
	try:
		response = vkMainProfile.method('users.search', {'sort': 1, 'online': True, 'hometown': hometown, 'fields': 'can_send_friend_request', 'birth_day': birthDay, 'birth_year': birthYear, 'has_photo': True, 'count': count, 'offset': offset, 'sex': sex})
		for countAccount in range(len(response['items'])):
			cursor.execute(searchIDcommand.format(table = 'userIDs', id = response['items'][countAccount]['id']))
			answer = cursor.fetchone()
			if not answer:
				cursor.execute(addIDCommand.format(table = 'userIDs', id = response['items'][countAccount]['id']))
			connection.commit()
		if response['items']:
			if offset+len(response['items']) < response['count']:# len(response['items']) всегда будет меньше результата  -----    offset+len(response['items'])  тоже всегда меньше рез
				if titleshowen == False:
					print('По заданным параметрам поиска найдено ' + str(response['count'])+', проводится анализ и запись данных. ')
					titleshowen = True
				#print(response)
				time.sleep(1)
				offset = offset + len(response['items'])
				searchkUser(hometown, sex, birthDay, birthYear, count, offset)
				#print('Проверено '+ str(offset))
				time.sleep(1)
	except Exception as e:
		print('Возникла ошибка, возможно плохое интернет соединение... Запишите ошибку - '+str(e))

	return response
#по итогу в респонзе промежуточный вариант со списком list, который далее нужно обработать
#response[0]['items']

def howmuchalreadyaddedinbd():
	#countCommand = "SELECT count(*) FROM userIDs"
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(countCommand.format('userIDs'))
	count = cursor.fetchone()
	return count[0]

def controlSearchDetails(countIdTosearchFunc, needCountToFindIds):
	print('Минимум нужно найти '+str(countIdTosearchFunc)+' аккаунтов')
	print('Введите название города:')
	hometown = input()
	print('Наберите цифру для выбора пола (1-женщина, 2-мужчина, 0-любой):')
	sex = input()
	print('Введите день рождения (1-31):')
	birthDay = input()
	print('Введите год рождения (1900-2100):')
	birthYear = input()
	response = searchkUser(hometown, sex, birthDay, birthYear, countIdTosearchFunc, 0)
	howMuchAlreadyAdded = howmuchalreadyaddedinbd()
	#print(response)
	if not response['items']:
		print('Возможно какие-то данные были введены неверно, найдено 0 результатов, повторите ввод')
		controlSearchDetails(countIdTosearchFunc, needCountToFindIds)
	if howMuchAlreadyAdded < needCountToFindIds:
		countIdTosearchFunc = needCountToFindIds - howMuchAlreadyAdded
		print('Всего найдено '+ str(howMuchAlreadyAdded)+ ', это меньше, чем количество, которое могут  обработать боты. Проведем поиск еще раз с другими результатами, нужно добрать:  '+str(countIdTosearchFunc))
		controlSearchDetails(countIdTosearchFunc, needCountToFindIds)
	else:
		print('Записано')



'''
ОЧИСТКА и ЗАПУСК по результатам И ОТДАЧА ПО ПОИСКУ ВСЕГО ЧТО НАДО(И ДАЖЕ БОЛЬШЕ) в БД  TABLE --- 'userIDs', 'friendsIDs.db'
deleteTable('userIDs')
countId = len(readingBOTsinfo())*50
controlSearchDetails(countId, countId)
'''

#countId = len(readingBOTsinfo())*50
#controlSearchDetails(countId, countId)


def checkUserList(id):
	fileWithListOfFriends = open('listOfFriends.txt', 'r')
	goodToAddFriends = open('goodToAdd.txt', 'w')
	accountsID = fileWithListOfFriends.split('\n')
	fileWithListOfFriends.close()
	countAlreadyFriends = 0
	for idFriend in accountsID:
		if idFriend == id:
			countAlreadyFriends +=1
		else:
			goodToAddFriends.write(id + '\n')
	goodToAddFriends.close()

def creatingClearDB():
	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(createCommand.format('futuredFriends'))
	cursor.execute(selectAllCommand.format('userIDs'))
	massiveNotCheckedId = cursor.fetchall()
	time.sleep(5)
	for idForCheck in massiveNotCheckedId:
		if notInBDFriends(idForCheck[0]):
			try:
				cursor.execute(addIDCommand.format(table = 'futuredFriends', id = idForCheck[0]))
			except sqlite3.IntegrityError:
				print('Этот пользователь уже есть у одного из ботов в друзьях '+ str(idForCheck[0]))
	cursor.execute(selectCountCommand.format('futuredFriends'))
	futureFriendsCount = cursor.fetchone()
	connection.commit()
	return futureFriendsCount

#countId = len(readingBOTsinfo())*50
#creatingClearDB()
def addFriend(userID, bot):
	proxies = {
	   "https": "https://{}:{}@{}:{}/".format(bot[2], bot[3], bot[1], '80'),
	   "http": "http://{}:{}@{}:{}/".format(bot[2], bot[3], bot[1], '80')
	   }
	vk = vk_api.VkApi(token=bot[4], captcha_handler=captcha_handler)
	#vk = vk_api.VkApi(login = bot[1], password = bot[2], captcha_handler=captcha_handler)
	vk.http.proxies = proxies
	#vk.auth()
	try:
		vk.method('friends.add', {'user_id': userID})
		bot[5] = str(int(bot[5])+1)
	except Exception as e:
		file = open('notAddedIDs.txt', 'a')
		file.write(str(userID)+'\n')
		file.close()
		print('ошибка - 275 - '+str(e))
		print('ID пользователя и данные аккаунта бота сохраняются в файл notAddedIDs.txt')
	time.sleep(3)

def missedAccounts():
	print('Начинаем работу с файлом notAddedIDs.txt')
	file = open('notAddedIDs.txt', 'r')
	accountsIDs = file.read().split('\n')
	accountsIDs = list(set(accountsIDs))
	botlist = readingBOTsinfo()
	for bot in botlist:
		for num in range(len(accountsIDs)):
			if int(bot[5]) >= int(inputCount):
				break
			futuredFriend = accountsIDs.pop()
			print(futuredFriend)
			if futuredFriend:
				print('Отправляем запрос в друзья аккаунту id'+str(futuredFriend[0])+' c аккаунта id'+bot[0])
				print(futuredFriend[0])
				print(bot)
				addFriend(futuredFriend,bot)
				if int(bot[5]) >= int(inputCount):
					break


def checkNumInfo():
	botlist = readingBOTsinfo()
	divisionNum = 0
	for bot in botlist:
		divisionNum = divisionNum +(int(inputCount)-int(bot[5]))
	if divisionNum <= 0:
		print('Вы уверены, что хотите запустить программу? Количество отправленных заявок в день у всех ботов превышает поставленное значение ('+inputCount+'), для обнуления, нажмите [ENTER], либо закройте программу.')
		entered = input()
		fileinfo = ''
		if entered == '':
			for bot in botlist:
				fileinfo += bot[0]+'||'+bot[1]+'||'+bot[2]+'||'+bot[3]+'||'+bot[4]+'||'+'0\n'
			file = open('botsinfo.txt', 'w')
			file.write(fileinfo[:-1])
			file.close()
	else:
		print('Всего будет отправлено '+str(divisionNum)+' запросов с '+str(len(botlist))+' аккаунтов.')


def mainLogic():
	#selectAllCommand = "SELECT * FROM futuredFriends"
	#createCommand = """CREATE TABLE IF NOT EXISTS requestSendFriend ('id' INTEGER(10) UNIQUE);"""
	#addIDCommand = """
	#	INSERT INTO requestSendFriend ('id')
	#	VALUES ({id});"""
	creatingBDfriends()
	#deleteTable('userIDs')
	#deleteTable('futuredFriends')
	countId = len(readingBOTsinfo())*int(inputCount)
	controlSearchDetails(countId, countId)
	futureFriendsCount = creatingClearDB()
	while futureFriendsCount[0] < countId:
		print('Некоторые пользователи уже были в друзьях, повторите поиск.')
		countId -= futureFriendsCount
		controlSearchDetails(countId, countId)
		futureFriendsCount = creatingClearDB()

	connection = sqlite3.connect("friendsIDs.db")
	cursor = connection.cursor()
	cursor.execute(selectAllCommand.format('futuredFriends'))
	futuredFriends = cursor.fetchall()
	cursor.execute(createCommand.format('requestSendFriend'))
	botlist = readingBOTsinfo()
	for bot in botlist:
		for num in range(len(futuredFriends)):
			if int(bot[5]) >= int(inputCount):
				print('У аккаунта '+bot[0]+' исчерпан выставленный лимит('+inputCount+') добавления в друзья.')
				break
			futuredFriend = futuredFriends.pop()
			print('Отправляем запрос в друзья аккаунту id'+str(futuredFriend[0])+' c аккаунта id'+bot[0])
			try:
				cursor.execute(addIDCommand.format(table= 'requestSendFriend', id = futuredFriend[0]))
				addFriend(futuredFriend[0],bot)
			except sqlite3.IntegrityError:
				print('Этому пользователю, запрос в друзья уже был отправлен id'+str(futuredFriend[0]))
			if int(bot[5]) >= int(inputCount):
				print('У аккаунта '+bot[0]+'  исчерпан выставленный лимит('+inputCount+') добавления в друзья')
				break
	connection.commit()
	print('\nСтатистика по работе программы:')
	fileinfo = ''
	for bot in botlist:
		print('C id '+bot[0]+' отправлено '+bot[5]+' запросов на сегодня')
		fileinfo += bot[0]+'||'+bot[1]+'||'+bot[2]+'||'+bot[3]+'||'+bot[4]+'||'+bot[5]+'\n'
	file = open('botsinfo.txt', 'w')
	file.write(fileinfo[:-1])
	file.close()
	time.sleep(15)



inputCount = input("Введите лимит добавления в друзья(1-50): ")
checkNumInfo()

botsList = readingBOTsinfo()
proxies = {
   "https": "https://{}:{}@{}:{}/".format(botsList[0][2], botsList[0][3], botsList[0][1], '80'),
   "http": "http://{}:{}@{}:{}/".format(botsList[0][2], botsList[0][3], botsList[0][1], '80')
   }
#vk = vk_api.VkApi(token=bot[6], captcha_handler=captcha_handler)
#vk = vk_api.VkApi(login = bot[1], password = bot[2], captcha_handler=captcha_handler)
vkMainProfile = vk_api.VkApi(token=botsList[0][4], captcha_handler=captcha_handler)
vkMainProfile.http.proxies = proxies

try:
	deleteTable("futuredFriends")
except:
	print('Создаем таблицу 1')
try:
	deleteTable('userIDs')
except:
	print('Создаем таблицу 2')
try:
	deleteTable('friendsIDs')
except:
	print('Создаем таблицу 3')
#deleteTable('requestSendFriend')

choice = 0
if os.path.exists("notAddedIDs.txt"):
	print('Найден файл неуспешно добавленных пользователей. 1-работать с данным файлом / 0-запуск в обычном режиме')
	choice = input()
if choice == '1':
	missedAccounts()
else:
	print('Начинаем работу в обычном режиме')
	mainLogic()
