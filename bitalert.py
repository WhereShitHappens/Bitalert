import gi

import requests

import subprocess

import sched, time

import datetime

import threading

import sys



# bitcoin_api_url = 'https://api.coinmarketcap.com/v1/ticker/bitcoin/'
bitcoin_api_url = 'https://blockchain.info/ticker'
response = requests.get(bitcoin_api_url)
response_json = response.json()
type(response_json)

CURRENT_PRICE = str(response_json['USD']['15m'])
print(CURRENT_PRICE)

# Working towards redesigning the code to avoid using that many global variables
BITCOIN_LOW_THRESHOLD = 0.0
BITCOIN_HIGH_THRESHOLD = float(CURRENT_PRICE) * 2

ALLOW_NOTIFICATIONS = True
AUTO_REFRESH_INTERVAL = 10

refresh_counter = 0
time_label = 0

prog_bar = 0
label_current_price = ''


def refresh_price():
	global refresh_counter
	global response
	global CURRENT_PRICE
	global response_json
	global time_label
	response = requests.get(bitcoin_api_url)
	response_json = response.json()
	CURRENT_PRICE = str(response_json['USD']['15m'])
	print(CURRENT_PRICE)
	refresh_counter += 1
	print('Refresh count: ',refresh_counter)

refresh_price()


def sendmessage(message):
	global ALLOW_NOTIFICATIONS
	if ALLOW_NOTIFICATIONS == True:
		subprocess.Popen(['notify-send', message])
		return

########## Gtk ################# Gtk ############# Gtk ########### Gtk ##################

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


def desktop_notification(value):
	window = gtk.Window(title='Hello mufucka{}'.format(value))
	window.show()

	window.connect('destroy', gtk.main_quit)
	Gtk.main()



class Main:
	def __init__(self):
		gladeFile = 'bitalert.glade'
		self.builder = gtk.Builder()
		self.builder.add_from_file(gladeFile)
		self.builder.connect_signals(self)

		# This is another way to declare a button instead of doing it inside Glade
		# button = self.builder.get_object('button1')
		# button.connect('clicked', self.enter_low_point)

		window = self.builder.get_object('Main')
		window.connect('delete-event', gtk.main_quit)
		window.show()
				
		global label_current_price
		label_current_price = self.builder.get_object('current_btc_price')
		label_current_price.set_text('BTC Value: $' + CURRENT_PRICE)

		label_last_check = self.builder.get_object('label_last_check')
		label_last_check.set_text('')
		global time_label
		time_label = label_last_check

		switch = self.builder.get_object('switch_refresh')
		# switch.connect("notify::active", self.activate_switch)
		# switch.set_active(False)

		progress_bar = self.builder.get_object('progress_bar_range')
		progress_bar.set_text('low - high')
		progress_bar.set_fraction(0.5)
		global prog_bar
		prog_bar = progress_bar


	def enter_low_point(self, widget):
		global BITCOIN_LOW_THRESHOLD
		global BITCOIN_HIGH_THRESHOLD	
		global CURRENT_PRICE

		entry_bitcoin_input_low = self.builder.get_object('entry_low_value')
		bitcoin_input_low = float(entry_bitcoin_input_low.get_text().strip())
		BITCOIN_LOW_THRESHOLD = bitcoin_input_low

		if float(BITCOIN_LOW_THRESHOLD) > float(CURRENT_PRICE):
			sendmessage('Enter a value lower than the current BTC price')
		else:
			entry_bitcoin_input_low.set_text('')

			Main.progress_bar_update() 

			label_low = self.builder.get_object('label_bitcoin_low')
			label_low.set_text('Notify below: $' + str(bitcoin_input_low))

			prog_bar.set_text(str(BITCOIN_LOW_THRESHOLD) + ' - ' + str(BITCOIN_HIGH_THRESHOLD))

	def enter_high_point(self, widget):
		global BITCOIN_HIGH_THRESHOLD	
		global BITCOIN_LOW_THRESHOLD
		global CURRENT_PRICE

		entry_bitcoin_input_high = self.builder.get_object('entry_high_value')
		bitcoin_input_high = float(entry_bitcoin_input_high.get_text().strip())
		BITCOIN_HIGH_THRESHOLD = bitcoin_input_high

		if float(BITCOIN_HIGH_THRESHOLD) < float(CURRENT_PRICE):
			sendmessage('Enter a value lower than the current BTC price')
		else:
			entry_bitcoin_input_high.set_text('')

			Main.progress_bar_update() 

			label_high = self.builder.get_object('label_bitcoin_high')
			label_high.set_text('Notify above: $' + str(bitcoin_input_high))
			BITCOIN_HIGH_THRESHOLD = bitcoin_input_high

			prog_bar.set_text(str(BITCOIN_LOW_THRESHOLD) + ' - ' + str(BITCOIN_HIGH_THRESHOLD))



	def refresh_bitcoin_value(self, widget):
		global ALLOW_NOTIFICATIONS
		global BITCOIN_LOW_THRESHOLD
		global BITCOIN_HIGH_THRESHOLD
		global CURRENT_PRICE
		global label_current_price

		refresh_price()
		label_current_price = self.builder.get_object('current_btc_price')


		if BITCOIN_LOW_THRESHOLD > float(CURRENT_PRICE) or BITCOIN_HIGH_THRESHOLD < float(CURRENT_PRICE):
			sendmessage('The price of BTC is: ${}'.format(CURRENT_PRICE))

		label_current_price.set_text('BTC Value: $' + str(CURRENT_PRICE))

		Main.progress_bar_update()
		Main.label_update()


	def autorefresh_bitcoin_label():
		global label_current_price	
		global CURRENT_PRICE
		global BITCOIN_LOW_THRESHOLD
		global BITCOIN_HIGH_THRESHOLD

		label_current_price.set_text('BTC Value: $' + str(CURRENT_PRICE))	

		if BITCOIN_LOW_THRESHOLD > float(CURRENT_PRICE) or BITCOIN_HIGH_THRESHOLD < float(CURRENT_PRICE):
			sendmessage('The price of BTC is: ${}'.format(CURRENT_PRICE))


	def activate_switch(self, switch, active):
		global ALLOW_NOTIFICATIONS

		if switch.get_active():
			sendmessage('Notifications are on')
			ALLOW_NOTIFICATIONS = True
		else:
			sendmessage('Notifications are off')
			ALLOW_NOTIFICATIONS = False

	
	def progress_bar_update():
		global BITCOIN_LOW_THRESHOLD
		global BITCOIN_HIGH_THRESHOLD
		global CURRENT_PRICE
		global prog_bar

		if BITCOIN_LOW_THRESHOLD != 0 and BITCOIN_HIGH_THRESHOLD != 0.0:
			btc_low = BITCOIN_LOW_THRESHOLD
			btc_high = BITCOIN_HIGH_THRESHOLD
			btc_now = float(CURRENT_PRICE)
			prog_bar.set_text(str(BITCOIN_LOW_THRESHOLD) + ' - ' + str(BITCOIN_HIGH_THRESHOLD)) 
			# We need to normalize our data in order to produce a value between 0 and 1.
			# What we are doing is: fraction=(value-min)/(max-min)
			fraction = (btc_now-btc_low)/(btc_high-btc_low)
			prog_bar.set_fraction(fraction)


	def label_update():
		global time_label
		time_now = datetime.datetime.now().strftime('%H:%M:%S')
		time_label.set_text('Updated: ' + str(time_now))
		Main.autorefresh_bitcoin_label()
		Main.progress_bar_update()
		refresh_price()


	StartTime=time.time()
	def action() :
	    # print('action ! -> time : {:.1f}s'.format(time.time()-StartTime))
	    Main.label_update()


	class setInterval :
	    def __init__(self,interval,action) :
	        self.interval=interval
	        self.action=action
	        self.stopEvent=threading.Event()
	        thread=threading.Thread(target=self.__setInterval)
	        thread.start()

	    def __setInterval(self) :
	        nextTime=time.time()+self.interval
	        while not self.stopEvent.wait(nextTime-time.time()) :
	            nextTime+=self.interval
	            self.action()

	    def cancel(self) :
	        self.stopEvent.set()

	# start action every X seconds
	global AUTO_REFRESH_INTERVAL
	inter=setInterval(AUTO_REFRESH_INTERVAL,action)
	print('just after setInterval -> time : {:.1f}s'.format(time.time()-StartTime))


if __name__ == '__main__':
	main = Main()
	gtk.main()
		

