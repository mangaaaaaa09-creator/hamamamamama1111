from flask import Flask, request, jsonify
import requests, warnings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

app = Flask(__name__)
warnings.filterwarnings("ignore")

K = b"Yg&tc%DEuh6%Zc^8"
IV = b"6oyZDr22E3ychjM%"

def aesEnc(b):
    n = 16 - (len(b) % 16)
    d = b + bytes([n] * n)
    c = Cipher(algorithms.AES(K), modes.CBC(IV), backend=default_backend())
    e = c.encryptor()
    return e.update(d) + e.finalize()

def varint(n):
    r = b""
    while True:
        b = n & 0x7F
        n >>= 7
        if n: r += bytes([b | 0x80])
        else: r += bytes([b]); break
    return r

@app.route('/clan', methods=['GET'])
def join_clan():
    u = request.args.get('uid')
    p = request.args.get('password')
    cid = request.args.get('clan_id')

    if not u or not p or not cid:
        return jsonify({"result": "Error", "message": "Missing parameters"})

    try:
        try:
            clan_id_int = int(cid)
        except ValueError:
            return jsonify({"result": "Error", "message": "Invalid clan_id format"})

        api_url = f"https://ff-jwt-gen-api.lovable.app/api/public/token?uid={u}&password={p}"
        r_api = requests.get(api_url, verify=False, timeout=10)
        
        try:
            res_json = r_api.json()
        except Exception:
            return jsonify({"result": "Error", "message": "Invalid response from token API"})

        at = res_json.get("token") or res_json.get("access_token")
        
        if not at:
            return jsonify({"result": "Error", "message": "Failed to get token"})

        headers = {
            "Authorization": f"Bearer {at}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip"
        }

        body = aesEnc(varint((1 << 3) | 0) + varint(clan_id_int))
        r = requests.post(
            "https://clientbp.ggpolarbear.com/RequestJoinClan",
            data=body,
            headers=headers,
            verify=False,
            timeout=10
        )

        if r.status_code == 200:
            return jsonify({"result": "Done"})
        else:
            return jsonify({"result": "Error", "status": r.status_code})

    except requests.exceptions.RequestException as e:
        return jsonify({"result": "Error", "message": f"Network error: {str(e)}"})
    except Exception as e:
        return jsonify({"result": "Error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
