import time, json, hmac, hashlib
from django.conf import settings
from api import webhooks
s = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_test')
body = json.dumps({'type':'payment_intent.succeeded','data':{'object':{'id':'pi_test_123','status':'succeeded','amount':1000}},'id':'evt_test'})
payload = body.encode('utf-8')
t = int(time.time())
sig = hmac.new(s.encode('utf-8'), b"%d."%t + payload, hashlib.sha256).hexdigest()
header = f"t={t},v1={sig}"
print('secret=', repr(s))
print('header=', header)
print('verify helper =>', webhooks._verify_stripe_signature(payload, header, s))
