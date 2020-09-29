''' Prompt for password and return encrypted string '''
import sys
sys.path.append('../')

import common.security  # noqa: E402

prompt = "Password: "
password = input(prompt)
print("Encrypted password: {}".format(common.security.encrypt_password(password)))
