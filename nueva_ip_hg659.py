#!/usr/bin/env python

import sys, json, re, base64, hashlib
from requests import session
from bs4 import BeautifulSoup

############ CONFIG #################
IP_ADDR = '192.168.1.254'
USERNAME = 'TELMEX'
PASSWORD = '9sTznjmEqf'
#####################################

s = session()
pass_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
pass_hash = base64.b64encode(pass_hash.encode()).decode()
#sys.exit(pass_hash)
#pass_hash = ''

## INITIAL CSRF ##
try:
    r = s.get('http://{0}'.format(IP_ADDR))
    html = BeautifulSoup(r.text, 'html.parser')
    data = {
        'csrf_param': html.find('meta', {'name':'csrf_param'}).get('content'),
        'csrf_token': html.find('meta', {'name':'csrf_token'}).get('content'),
    }
    assert data['csrf_param'] and data['csrf_token'], 'Empty csrf_param or csrf_token'
    print("CSRF Adquirido")
except Exception as e:
    print('No se pudo obtener el CSRF: {0}'.format(e))
    sys.exit(1)

## LOGIN ##
try:
    pass_hash = USERNAME + pass_hash + data['csrf_param'] + data['csrf_token']
    pass_hash = hashlib.sha256(pass_hash.encode()).hexdigest()
    data = {'csrf':{'csrf_param':data['csrf_param'],'csrf_token':data['csrf_token']}, 'data':{'UserName':USERNAME,'Password':pass_hash}}
    r = s.post('http://{0}/api/system/user_login'.format(IP_ADDR), data=json.dumps(data, separators=(',', ':')))
    data = json.loads(re.search('({.*?})', r.text).group(1))
    assert data.get('errorCategory','').lower() == 'ok', data
    print("Sesión iniciada")
except Exception as e:
    print('Falló inicio de sesión: {0}'.format(e))
    sys.exit(1)

## REBOOT PPPoE ##
try:
    data = {'csrf':{'csrf_param':data['csrf_param'],'csrf_token':data['csrf_token']}, 'action':"pppreset",'data':{"ID":"Device.IP.Interface.4."}}
    r = s.post('http://{0}/api/ntwk/wan'.format(IP_ADDR), data=json.dumps(data, separators=(',', ':')))
    data = json.loads(re.search('({.*?})', r.text).group(1))
    assert data['errcode'] == 0, data
    print("Reiniciando via PPPoE")
except Exception as e:
    print('Reinicio fallido: {0}'.format(e))
    sys.exit(1)
