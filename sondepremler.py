#!/usr/bin/env python3
import requests
import json
import datetime
import locale
import os
import operator

# Türkçe tarih formatı ve karakerler için 
# locale'yi tr_tr.utf8 yapıyorum.
locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')

# Kullanılacak değişkenler falan
temp_file        = '{}/.cache/son-depremler.json'.format(os.getenv("HOME"))
notification_str = "{4} tarihinde\n{0} bölgesinde büyüklükleri:\nML: {1} \nMW: {2} \nMD: {3} olan bir deprem gerçekleşti."
cmd_template     = "notify-send --urgency {} '{}'"
notification     = ""
last_quakes      = []
magnitudes       = []
# İsteği yap
req = requests.get('http://kandilli-son-depremler-api.herokuapp.com/')
# Bildirim öncelik parametresini al
def get_urgency(_magnitude):
	if (_magnitude >= 5.0): 
		return 'critical'
	elif (_magnitude >= 3.0):
		return 'normal'
	else:
		return 'low'
# Bunu neden ayrı yaptım bilmiyorum
def get_biggest(_mags):
	return max(_mags.items(), key=operator.itemgetter(1))[0]
# İstek gövdesini json'a dönüştür ve ilk 10 elemanı dön
for quake in req.json()[slice(10)]:
	# büyüklükleri float olarak ayıkla
	# daha sonra aralarından büyük olanı alacağız
	mags = {
		'ml': float(quake['ml'] or 0),
		'mw': float(quake['mw'] or 0),
		'md': float(quake['md'] or 0)
	}
	# Alacağız demiştim.
	biggest = get_biggest(mags)
	# Genel büyüklükler listesine en büyük M* değerini ekle
	# Üç büyüklük türünden en büyük olanı alıyoruz.
	magnitudes.append(quake[biggest])
	# Bildirim metnine verdiğimiz parametreleri yerleştiriyoruz.
	last_quakes.append(notification_str.format(
		*(
			str(quake['address']),
			str(quake['ml'] or 0),
                        str(quake['mw'] or 0),
                        str(quake['md'] or 0),
			# Lanet tarih formatlama işleri
			str(datetime
				.datetime
				.strptime(quake['timestamp'], '%Y.%m.%d %H:%M:%S')
				.strftime('%d %B %Y %A, %H:%M'))
			# Burada bitiyor. 
		)
	))

# Gelen ilk 10 satırdan en şiddetli olanın büyüklük türünü (ml,mw,md neyse işte) alıyoruz.
mag           = max(magnitudes)
# En şiddetli olanı bildirimler listesinden çekip alıyoruz.
biggest_index = magnitudes.index(mag)

# Bu bildirim daha önce gösterilmişse bu script biter.
if os.path.exists(temp_file):
	with open(temp_file, 'r') as outfile:
		if last_quakes[biggest_index] in json.load(outfile):
			exit()

# Bildirim komutunu çalıştır.
result = os.system(cmd_template.format(
	*(
		get_urgency(float(mag or 0)), # Önceliği al. 5 ve üstü kritik, 3-5 arası normal, kalanı düşük
		last_quakes[biggest_index]    # Formatlanmış bildirim metnini al
 	)
))

# 0 döner. dönmezse hata vardır.
if result != 0:
	exit()
else:
	# Gösterilen bildirimi cache'e kaydetsin. spam yapmasın.
	with open(temp_file, 'w') as outfile:
		json.dump([last_quakes[biggest_index]], outfile)
