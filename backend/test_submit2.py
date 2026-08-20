import urllib.request, json
try:
    login_data = json.dumps({'email': 'admin@localvest.vn', 'password': 'admin'}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'}, method='POST')
    res = urllib.request.urlopen(req)
    token = json.loads(res.read())['access_token']
except Exception as e:
    token = ''
    print(e)
if token:
    payload = {'name': 'Test', 'category': 'Cộng đồng', 'dob': '01/01/2000', 'current_address': 'Test', 'social_link': 'Test', 'bank_name': 'Test', 'bank_account_number': '123', 'bank_account_name': 'Test', 'description': 'Test', 'location_name': 'Test', 'target_amount': 1000000, 'lat': 10.0, 'lng': 106.0, 'milestones': []}
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = f'--{boundary}\r\nContent-Disposition: form-data; name="payload"\r\n\r\n{json.dumps(payload)}\r\n--{boundary}--\r\n'.encode('utf-8')
    req2 = urllib.request.Request('http://127.0.0.1:8000/api/campaigns', data=body, method='POST')
    req2.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req2.add_header('Authorization', f'Bearer {token}')
    try:
        res2 = urllib.request.urlopen(req2)
        print(res2.getcode(), res2.read())
    except urllib.error.HTTPError as e:
        print(e.code, e.read())
