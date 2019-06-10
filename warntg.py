#!/usr/bin/env python3

# copyright (c) 2019-2024 by Rainer Fiedler DO6UK
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.


import json, sys, requests, time, urllib.parse

## ** variables **

VERSION='20190610'


## file to save last state
STATEFILE='./warntg.state'


## name for provider of this service (used for telegram-message)
SERVICE='*your*name*'


## set user-agent for http-requests
USER_AGENT='curl/7.61.0'


## url and jsonp-prefix/suffix to fetch dwd-warnings
DWD_URL='https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json'
DWD_PREFIX='warnWetter.loadWarnings('
DWD_SUFFIX=');'


## url to access brandmeister.network-api
BM_GETURL='https://api.brandmeister.network/v1.0/repeater/?action=profile&q=%BM_DMRID%'
BM_SETURL='https://api.brandmeister.network/v1.0/repeater/talkgroup/?action=%ACTION%&id=%BM_DMRID%'


## ApiKey used brandmeister.network-api
bm_apikey='*your*bmapikey*'


## url to send message via WebALARM_BOT
TG_WA_URL='https://wachalarm.ralsu.de/webalarm_bot/webalarm_bot.php?json={"command":"api_message","apikey":"%TG_API%","message":"%TG_MSG%","title":"%TG_TITEL%","sender": "'+SERVICE+'","gruppe":"%TG_GRP%"}'


## list of WebALARM_BOT-Keys to send telegram-message
tg_wa_api=['*your*webalarmkey*']


## url to send DAPNET-message
DN_URL='http://www.hampager.de:8080/calls'


## auth to send DAPNET-message
dn_auth=('*your*call*','*your*dapnetkey*')


## replace chars in DAPNET-message
dn_replace={'Ä':'a', 'ä':'A', 'Ö':'o', 'ö':'O', 'Ü':'u', 'ü':'U', 'ß':'S'}


## list of DAPNET-callsigns to send messages
dn_callsigns=['*you*call*','*your*friendcall*']


## list of DAPNET-TX-groups
dn_txgrp = ['dl-ni']


## dict with DMRIds and list of tuples which TGs will be removed on warning and restored after
## usage: bm_warn_tgs = {'dmrid': [(tg,ts),(tg,ts)]}

bm_warn_tgs={'*your*repeaterid*':[(*your*tg1*,*slot*),(*your*tg2*,*your*slot*)]}


## list of WarnCellIDs to be monitored !! '*' in warncellids overrides warncellid-check
## usage: warncellids = [warncellid1, warncellid2]

warncellids = ['*your*warncellid1*','*your*warncellid2*']

# warncellid-prefix
# 1 = Landkreis
# 2 = Seen
# 4 = Seegebiete
# 5 = Küstengebiete
# 6 = Objekte
# 7 = Stadtteile
# 8 = Gemeinden
# 9 = Bundesländer
#
# known warncell-ids
# 903000000 = Niedersachsen
# 103155000 = Landkreis Northeim
# 803155012 = Uslar
# 803155002 = Bodenfelde
# 806633027 = Wahlsburg (Lippoldsberg/Vernawahlshausen)


## list of warntypes and levels to be monitored
## usage: warntypelevel = {type: minlevel, type: [level2, level3]}

warntypelevel = {0:[1,3,4,5],1:4,2:[1,3,4,5]}

# warnlevels
# 1 = Vorabinfo
# 2 = Warnung
# 3 = markantes Wetter
# 4 = Unwetter
# 5 = Extremes Unwetter
# 10 = Hitzewarnung

# warntypes
# 0 = Gewitter
# 1 = Wind/Sturm/Orkan
# 2 = Stark oder Dauerregen
# 3 = Schnee
# 4 = Nebel
# 5 = Frost
# 6 = Glätte
# 7 = Tauwetter
# 8 = Hitze
# 9 = UV
# 10 = Küstenwetter
# 11 = Binnenwetter


## !! below this line there is no need to change anything !!


## ** functions **

def switch_bm_tgs(warn=False,state=True):
	# read tg-config from brandmeister.network via api
	# switch tg if warning true an state changed
	for dmrid in bm_warn_tgs:
		print('lese statische TG von',dmrid,'...')
		bm_response = requests.get(BM_GETURL.replace('%BM_DMRID%',dmrid), headers={'User-Agent': USER_AGENT})
		bm_state = json.loads(bm_response.text)
		bm_static = bm_state['staticSubscriptions']
		bm_current_tgs = {0:[],1:[],2:[]}
		temp_log = 'DMRId: %s   '%dmrid
		dn_log = 'DMRId:%s '%dmrid

		for static_tg in bm_static:
			bm_current_tgs[static_tg['slot']].append(static_tg['talkgroup'])

		for tg,slot in bm_warn_tgs[dmrid]:
			if tg in bm_current_tgs[slot]:
				if warn:
					print('>> TG',tg,'aus slot',slot,'entfernt')
					temp_log += 'TS %i TG %i : dynamisch  '%(slot,tg)
					dn_log += 'TS%i,TG%i:dyn '%(slot,tg)
					set_bm_tg(dmrid,tg,slot,False)
				else:
					print('>> TG',tg,'in slot',slot,'bereits gebucht')
			else:
				if warn:
					print('>> TG',tg,'in slot',slot,'nicht gebucht')
				else:
					print('>> TG',tg,'in slot',slot,'hinzugefügt')
					temp_log += 'TS %i TG %i : statisch  '%(slot,tg)
					dn_log += 'TS%i,TG%i:stat '%(slot,tg)
					set_bm_tg(dmrid,tg,slot,True)
		if warn and state != warn:
			send_tg_msg(temp_log,dmrid,event)
			send_dn_msg(event+' '+dn_log,dn_callsigns)
		elif not warn and state != warn:
			send_tg_msg(temp_log,dmrid,'Unwetter-Modus AUS')
			send_dn_msg('NORMALBETRIEB '+dn_log,dn_callsigns)


def send_tg_msg(msg,grp = '',titel = ''):
	# send message to telegram by WebALARM_BOT
	tg_url = TG_WA_URL.replace('%TG_MSG%', msg)
	tg_url = tg_url.replace('%TG_GRP%', grp)
	tg_url = tg_url.replace('%TG_TITEL%', titel)
	tg_data = {}
	tg_header = {'User-Agent': USER_AGENT}
	for apikey in tg_wa_api:
		temp_tg_url = tg_url.replace('%TG_API%',apikey)
		#print(temp_tg_url)
		tg_response = requests.post(temp_tg_url, headers=tg_header)
		#print(tg_response.text)


def set_bm_tg(dmrid,tg,slot,settg):
	# set brandmeister.network tg by api
	if settg:
		action='ADD'
	else:
		action='DEL'
	bm_url = BM_SETURL.replace('%BM_DMRID%',dmrid)
	bm_url = bm_url.replace('%ACTION%',action)
	bm_auth = (bm_apikey,'')
	bm_data = {'talkgroup': str(tg), 'timeslot': str(slot)}
	bm_header = {'User-Agent': USER_AGENT}
	bm_response = requests.post(bm_url, data=bm_data, auth=bm_auth, headers=bm_header)

	
def replace_multi(string,repl_dict):
	for key in repl_dict:
		string = string.replace(key,repl_dict[key])
	return string


def send_dn_msg(msg,callsigns):
	dn_header = {'user-agent': USER_AGENT, 'content-type': 'application/json'}
	dn_msg = SERVICE+': '+replace_multi(msg,dn_replace)

	for callsign in callsigns:
		if (len(dn_msg) > 80):
			dn_msg = dn_msg[:77]+'...'
		dn_data = {'text': dn_msg, 'callSignNames': [callsign], 'transmitterGroupNames': dn_txgrp}
		dn_response = requests.post(DN_URL, data=json.dumps(dn_data), auth=dn_auth, headers=dn_header)


## ** main thread **

if __name__ == "__main__":
	try:
		with open(STATEFILE,"r") as f:
			warnung_status = bool(int(f.read().strip()))
	except:
		warnung_status = false

	warnlage_response = requests.get(DWD_URL, headers={'User-Agent': USER_AGENT})
	warnlage_jsonp = warnlage_response.text

	## using static dump of json for debugging
	#with open('dwd.jsonp',"r") as f:
	#	warnlage_jsonp = f.read()

	warnlage_jsonp = warnlage_jsonp.strip(DWD_PREFIX)
	warnlage_json = warnlage_jsonp.strip(DWD_SUFFIX)

	warnlage = json.loads(warnlage_json)

	print('Warnlage von',time.ctime(warnlage['time']/1000),'\n')

	try:
		warnungen = {**warnlage['warnings'],**warnlage['vorabInformation']}
	except:
		warnungen = warnlage['warnings']

	warnung_aktiv = False
	warnung_event = ''

	for warncell in warnungen:
		if warncell in warncellids or '*' in warncellids:
			for warnung in warnungen[warncell]:
				if warnung['type'] in warntypelevel:
					if type(warntypelevel[warnung['type']]) is int:
						check = (warnung['level'] >= warntypelevel[warnung['type']])
					else:
						check = (warnung['level'] in warntypelevel[warnung['type']])
					if check:
						print('AKTIVE WARNUNG: ',warnung['headline'])
						print(' > ','Level',warnung['level'], 'Type',warnung['type'])
						print(' > ','Ort: ',warnung['regionName'])
						print(' > ','ausgegeben: ',time.ctime(warnung['start']/1000))
						if warnung['end'] == None:
							print(' > ','gültig bis: ','Widerruf')
						else:
							print(' > ','gültig bis: ',time.ctime(warnung['end']/1000))
						warnung_aktiv = True
						warnung_event = warnung['event']
						break						

	try:
		warnung_aktiv = bool(int(sys.argv[1]))
		print('override warnung',warnung_aktiv)
		warnung_event = 'TESTMODUS'
	except:
		pass

	if warnung_aktiv:
		print('\n','>>> WARNLAGE: %s <<<'%(warnung_event),'\n')
	else:
		print('\n','* NORMALBETRIEB *','\n')

	if warnung_status == warnung_aktiv:
		print('keine Änderungen ...')
		pass
	else:
		print('!! Lageänderung !!')
		with open(STATEFILE,"w") as f:
			f.write(str(int(warnung_aktiv)))

		print('update brandmeister.network ...')
		switch_bm_tgs(warnung_aktiv, warnung_status)

	print('... fertig!')
