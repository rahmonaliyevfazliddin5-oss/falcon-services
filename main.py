# PATCH
import bcrypt
if hasattr(bcrypt,'_orig_hashpw')==False:
 bcrypt._orig_hashpw=bcrypt.hashpw
 def _h(p,s):
  if isinstance(p,str): p=p.encode().;
  return bcrypt._orig_hashpw(p[:72],s)
 bcrypt.hashpw=_h

# --- BCRYPT 72-BYTE GLOBAL PATCH ---
import bcrypt
if not hasattr(bcrypt, '_orig_hashpw'):
    bcrypt._orig_hashpw = bcrypt.hashpw
    bcrypt._orig_checkpw = bcrypt.checkpw
    def _patched_hashpw(password, salt):
        if isinstance(password, str): password = password.encode('utf-8')
        return bcrypt._orig_hashpw(password[:72], salt)
    def _patched_checkpw(password, hashed_password):
        if isinstance(password, str): password = password.encode('utf-8')
        return bcrypt._orig_checkpw(password[:72], hashed_password)
    bcrypt.hashpw = _patched_hashpw
    bcrypt.checkpw = _patched_checkpw
# -----------------------------------

# init


