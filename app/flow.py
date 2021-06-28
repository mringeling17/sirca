#from .configuraciones import *
import hmac
import hashlib
from requests import get, post

api_flow = '6079C6F0-32FB-42BF-85BE-33CL8481B1C3'
secret_flow = '0e122e73cad55c2c3d079d53257de86095f380b5'
url_flow = 'https://sandbox.flow.cl/api'

def flow_signature(params):
    sorted_params = dict(sorted(params.items()))
    to_sign = ""
    for key in sorted_params:
        to_sign = to_sign + str(key) + str(sorted_params[key])
    return hmac.new(bytes(secret_flow,'utf-8'), bytes(to_sign,'utf-8'),hashlib.sha256).hexdigest()

def flow_getStatus(token):
    url = url_flow + "/payment/getStatus"
    variables = {"apiKey":api_flow,"token":token}
    variables["s"] = flow_signature(variables)
    r = get(url,params=variables).json()
    return r

def flow_payment(id_interno,subject,monto,email_usuario):
    url = url_flow + "/payment/create"
    variables = {
                "apiKey":api_flow,
                "commerceOrder":id_interno,
                "subject": subject,
                "amount": monto,
                "email": email_usuario,
                "urlConfirmation": "https://sirca.cuy.cl",
                "urlReturn": "https://sirca.cuy.cl"
                }
    variables["s"] = flow_signature(variables)
    r = post(url, data = variables).json()
    return r

