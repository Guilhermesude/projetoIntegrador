# Biblioteca usada. para instalar: "sudo pip3 install pycrypto"
#                                  "sudo pip3 install Crypto"
from Crypto.Cipher import AES

# -------------------------------------------------------------------- #
# Chave de criptografia
chave = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

# A criptografia funciona em múltiplos de 16, por padrão, caso a informação
# não tenha tal tamanho o restante da informação é preenchida com zeros a esquerda
# no momento o tamanho usado para criptografia é 32
informacao = 'offline'.zfill(32)

# Função onde ocorre a criptografia
informacaoCriptografada = chave.encrypt(informacao)

print(informacaoCriptografada)
# --------------------------------------------------------------------- #

chave2 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

# Chave de descriptografia, decodificação e retirada do preenchimento de zeros
informacaoDescriptografada = chave2.decrypt(informacaoCriptografada).decode("utf-8").strip('0')

print(informacaoDescriptografada)
