"""
versao:202105101017

Este comando tem o objetivo de atualizar o software do gateway de forma independente
do classes.py que estiver rodando no gateway a ser atualizado.

Como  medida de controle para maior segurança ao executar esse arquivo, foi implementado
um algoritmo responsável por gravar as estapas de processos em um arquivo chamado "statusComando"
a saber os status são:

    0  - Inicio do sistema comandos.
    
    5  - Move o arquivo Comandos.py para o diretorio python.versão
    
    10 - Alterações no autostar (comenta a chamada de supervisor e restaura supervisores, e adiciona
         uma chamada para o arquivo de Comandos.py), realiza o passo 1° envia o arquivo status 10 para
         o FTP e reboot do sistema.

    20 - Realiza os passos 1° e 2° descritos abaixo.

    30 - Prepara o primeiro executavel.

    40 - Prepara o segundo executavel.

    50 - Prepara o terceiro executavel.

    60 - Realiza os passos 4° e 5° e então finaliza todos o processo.
    

1º - Conecta-se ao FTP utilizando as credências para faze-lo.

   - Vai utilizar o diretório que está definido no banco para o
     gateway do qual este comando estiver rodando.


2° - Baixar os novos arquivos na pasta de download.

3° - Cria executaveis de supervisor, supervisorBits e restauraSupervisores.

4° - Apaga todos os arquivos atuais do sistema incluindo pastas de backup e
     e arquivos sinalizadores para o sistema.

5° - Instala os arquivos nas pastas de backup e na pasta principal.

"""



# Bibliotecas ---

from subprocess import getoutput
from os         import listdir
from time       import sleep
import ftplib
import RPi.GPIO as GPIO



# Funções ---

def debug(mensagem):

    getoutput('sudo chmod 777 /home/pi/debug')

    try:
        arquivo =open('/home/pi/debug', 'r')
        arquivo.close()

        arquivo = open('/home/pi/debug','a')

        dados = list()

        dados.append(mensagem+'\n')

        arquivo.writelines(dados)

        arquivo.close()

    except:
        
        arquivo = open('/home/pi/debug','w')
        arquivo.write(mensagem)
        arquivo.close()


# Conecta ao banco de dados online ou offline

def conectarBD(online):

    import mysql.connector as mysql

    
    conn = mysql.connect(host='testescaio.mysql.dbaas.com.br',
                         user='testescaio',
                         password='Caio@1809',
                         db='testescaio',
                         charset='utf8',
                         connect_timeout=600,
                         compress=True)
                           #cursorclass=pymysql.cursors.DictCursor)
    return conn

    
# Retorna uma lista de dicionários, com os resultados da pesquisa

def pesquisarBD(SQL, online):
    try:
        conn = conectarBD(online)

        if conn == False:
            return False
        
        c = conn.cursor(dictionary=True)
        c.execute(SQL)

        r = c.fetchall()

        c.close()
        conn.commit()
        conn.close()

        return r

    except:
        conn.close()
        return False

# executa scripts SQL no banco de dados

def executaQueryBD(SQL, online):
    try:
        conn = conectarBD(online)

        if conn == False:
            return False

        c = conn.cursor(dictionary=True)
        c.execute(SQL)
        conn.commit()

        c.close()
        conn.close()
        return True

    except:
        conn.close()
        return False

        
# Função que busca a versão do python pelo nome de um diretorio

def getPythonVer():
    pastas = listdir("/usr/lib/")
    for i in pastas:
        if str(i[0:8]) == 'python3.':
            return str(i)


# Coleta o número serial do Gateway do arquivo cpuinfo 

def pegarNoSerie():
        
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    
    return cpuserial

# Envia o status do processo para o FTP

def enviaStatusFTP(FTP):
    
    getoutput('sudo chmod 777 /home/pi/statusComando')
    getoutput('sudo chmod 777 /home/pi/debug')

    try:
        file = open('/home/pi/statusComando', mode='rb')
        
        ftp = ftplib.FTP(host=FTP[0]['Host'])
        
        ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
        upload = pathServ+'/Upload'
        #debug(upload)
        
        ftp.cwd(upload)

        ftp.storlines("STOR statusComando", file)
        file.close()

    except:
        debug('erro ao enviar o arquivo statusComando ao FTP')
        pass

    try:
        file = open('/home/pi/debug', mode='rb')
        
        ftp = ftplib.FTP(host=FTP[0]['Host'])
        
        ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
        upload = pathServ+'/Upload'
        #debug(upload)
        
        ftp.cwd(upload)

        ftp.storlines("STOR debug", file)
        file.close()

    except:
        debug('erro ao enviar o arquivo debug ao FTP')
        pass


# Atualiza o status do processo a cada termino de bloco lógico

def controleStatus(status):

    getoutput('sudo chmod 777 /home/pi/statusComando')

    try:
        arquivo =open('/home/pi/statusComando', 'r')
        arquivo.close()

        arquivo = open('/home/pi/statusComando','w')
        arquivo.write(status)
        arquivo.close()

    except:
        
        arquivo = open('/home/pi/statusComando','w')
        arquivo.write(status)
        arquivo.close()



            
# Busca o status do processo

def statusAtual():

    getoutput('sudo chmod 777 /home/pi/statusComando')

    try:
        arquivo = open('/home/pi/statusComando', 'r')
        dados = arquivo.readlines()
        arquivo.close()

        return dados[0]

    except:
        return 0

def preparaInicializador(status):

    #Comando para abrir o autostart
    try:
        debug("Início do primeiro try do preparaInicializador")
        debug("")
        getoutput('sudo chmod 777 /home/pi/.config/lxsession/LXDE-pi/autostart')
        arq = open('/home/pi/.config/lxsession/LXDE-pi/autostart','r')
        autostart = arq.readlines()
        arq.close()

    except:
        getoutput('sudo chmod 777 /etc/xdg/lxsession/LXDE-pi/autostart')
        arq = open('/etc/xdg/lxsession/LXDE-pi/autostart','r')
        autostart = arq.readlines()
        arq.close()

        
    debug('status '+status)

    debug('autostart')
    if status == '10':
                
        try:
            autostart.remove('@/usr/lib/'+getPythonVer()+'/./supervisor\n')
            autostart.remove('@/usr/lib/'+getPythonVer()+'/./restaurasupervisores\n')
            autostart.remove('@/usr/bin/python3 /usr/lib/'+getPythonVer()+'Comandos.py\n')
            
        except:
            pass
        
        autostart.append('@/usr/bin/python3 /usr/lib/'+getPythonVer()+'/Comandos.py\n')

        #Abrir o autostart e escrever os novos supervisores
        try:
            getoutput('sudo chmod 777 /home/pi/.config/lxsession/LXDE-pi/autostart')
            arq = open('/home/pi/.config/lxsession/LXDE-pi/autostart', 'w')
            arq.writelines(autostart)
            arq.close()
         
        except:
            getoutput('sudo chmod 777 /etc/xdg/lxsession/LXDE-pi/autostart')
            arq = open('/etc/xdg/lxsession/LXDE-pi/autostart', 'w')
            arq.writelines(autostart)
            arq .close()

    elif status == '60':

        try:
            autostart.remove('@/usr/bin/python3 /usr/lib/'+getPythonVer()+'/Comandos.py\n')
            autostart.remove('@/usr/lib/'+getPythonVer()+'/./supervisor\n')
            autostart.remove('@/usr/lib/'+getPythonVer()+'/./restaurasupervisores\n')
            
        except:
            pass
        
        autostart.append('@/usr/lib/'+getPythonVer()+'/./restaurasupervisores\n')
        autostart.append('@/usr/lib/'+getPythonVer()+'/./supervisor\n')

        debug(' atualizou o autostart')
        
        #Abrir o autostart e escrever os novos supervisores
        try:
            getoutput('sudo chmod 777 /home/pi/.config/lxsession/LXDE-pi/autostart')
            arq = open('/home/pi/.config/lxsession/LXDE-pi/autostart', 'w')
            arq.writelines(autostart)
            arq.close()
         
        except:
            getoutput('sudo chmod 777 /etc/xdg/lxsession/LXDE-pi/autostart')
            arq = open('/etc/xdg/lxsession/LXDE-pi/autostart', 'w')
            arq.writelines(autostart)
            arq .close()


# Variaveis ---
debug("Variáveis")
debug("")
arquivos      = ['MAIN.py','classes.py','connMySQL.ini','connMySQLOFF.ini','CLP.py','supervisor.py','SupervisorBits.py','BCK.sql','restaurasupervisores.py','montaBancos.sql','localconnMySQL.ini']
arquivosSinal = ['Reiniciado','Reiniciado1','Reiniciado2','Reiniciado3','Reiniciado4','erroBackup','erroBackup-1','erroFTP','Desligado','atualizado']
executaveis   = ['supervisor','restaurasupervisores','SupervisorBits']
diretorios    = ['/home/pi/dist','/home/pi/build','/home/pi/__pycache__','/usr/lib/'+getPythonVer()+'/backup-1','/usr/lib/'+getPythonVer()+'/backup','/usr/lib/'+getPythonVer()+'/download','/usr/lib/'+getPythonVer(),'/home/pi','/mnt/CLP']    
SQL           = "SELECT versaoSoftware, Host, Login, Senha FROM Nuvem_Gateway WHERE Cod_Gateway = '" +pegarNoSerie()+ "'"



debug("vai esperar 5 s")
debug("")
sleep(5)

# Status 5

try:
    arquivo = open('/home/pi/statusComando', 'r')
    arquivo.close()
    
    if statusAtual() != '5':
        pass
        
except:
    controleStatus('5')
    debug('status 5, movendo o arquivo')
    getoutput('sudo cp /home/pi/Comandos.py /usr/lib/'+getPythonVer()+'/Comandos.py')
    getoutput('sudo chmod 777 /usr/lib/'+getPythonVer()+'/Comandos.py')
    getoutput('sudo rm /home/pi/Comandos.py')
    controleStatus('10')
    
# 1° Conexão com FTP ---
tentativa = 1

while tentativa < 11:

    try:
        FTP      = pesquisarBD(SQL,True)
        debug(FTP[0]['versaoSoftware'])
        debug(FTP[0]['Host'])
        debug(FTP[0]['Senha'])
        debug(FTP[0]['Login'])
        
        pathServ = FTP[0]['versaoSoftware']     
        ftp      = ftplib.FTP(host=FTP[0]['Host'])
        ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
        debug('conectado com sucesso')
        break
        
    except:
        debug('erro ao conectar com FTP')
        
    debug('tentativa '+tentativa)

    if tentativa == 10:

        getoutput('reboot')
        
    tentativa += 1
    
        


# Cria o arquivo e libera a permissão

getoutput('sudo chmod 777 /home/pi/statusComando')

try:
    arquivo = open('/home/pi/statusComando', 'r')
    arquivo.close()
except:
    controleStatus('10')



# Status 10
if statusAtual() == '10':
    debug(" dentro do if do 10")

    enviaStatusFTP(FTP)
    preparaInicializador(statusAtual())
    controleStatus('20')
    sleep(0.5)
    getoutput('reboot')    
    

# Status 20

if statusAtual() == '20':
    
    # 2° Realiza o download dos arquivos
    enviaStatusFTP(FTP)
    #getoutput('sudo rm /mnt/CLP/bits')
    debug('inicio o download dos arquivos')
    getoutput('sudo rm -r '+diretorios[5])
    getoutput('sudo mkdir '+diretorios[5])
    getoutput('sudo chmod 777 '+diretorios[5])

    for i in arquivos:

        tentativas = 1

        while tentativas < 11:            
            # Abre a pasta de download e direciona o arquivo criado

            try:
                arquivo = open(diretorios[5]+'/'+i,'r')
                arquivo.close()
                debug('O arquivo '+i+' já está na pasta de download')
                break

            except:
                pass    
            
            try:
                file = open(diretorios[5]+'/'+i, mode='wb')
                debug('arquivo criado '+i)
                sleep(0.5)
                ftp = ftplib.FTP(host=FTP[0]['Host'])
                ftp.login(FTP[0]['Login'], FTP[0]['Senha'])

                sleep(0.5)
                ftp.cwd(pathServ)
            except:
                debug('erro ao criar o arquivo '+i)

            # Escreve dentro do arquivo criado
            try:
                debug('escrevendo o arquivo '+i)
                ftp.retrbinary("RETR " + i, file.write)
                file.close()
                
                getoutput('sudo chmod 777 '+diretorios[5]+'/'+i)
                debug('liberando as permissoes do arquivo '+i)
                break
                
            # Caso não consiga, excluí-se o arquivo
            except:
                debug('erro ao baixar ou escrever o arquivo '+i)
                file.close()
                continue

            
            if tentativas == 10:
                if i=='classes.py' or i=='MAIN.py' or i=='BCK.sql':
                    getoutput('sudo rm -r '+diretorios[5])
                    debug('reiniciando o sistema...')
                    getoutput('reboot')
                else:    
                    getoutput('sudo rm '+diretorios[5]+'/'+i)

            tentativas += 1
            
    controleStatus('30')


# Status 30
    
if statusAtual() == '30':

    debug('inicio do inicializador cod 30 ------------------------------------------')
    # 3° Cria os executáveis ---
    enviaStatusFTP(FTP)
    debug('Enviou arquivo para FTP')
    getoutput('sudo rm /mnt/CLP/bits')

    debug('removeu o arquivo bits')
    getoutput('sudo chmod 777 '+diretorios[5]+'/supervisor.py')

    debug('liberou a permissao de supervisor.py no diretorio de download')
    getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/supervisor.py')
    sleep(0.5)

    debug('sudo pyinstaller --onefile '+diretorios[5]+'/supervisor.py')
    
    debug('realizou o comando que cria o executavel do supervisor')
    
    #debug(arquivo+'.py  ok')
    getoutput('sudo chmod 777 '+diretorios[0]+'/supervisor')

    debug('liberou permissao do executavel supervisor no diretorio '+diretorios[0])
    getoutput('sudo chmod 777 '+diretorios[0])

    debug('liberou permissao do diretorio '+diretorios[0])
    getoutput('sudo chmod 777 '+diretorios[1])

    debug('liberou permissao do diretorio '+diretorios[1])
    controleStatus('40')
        
    debug('atualizou o arquivo status para 40')
     
if statusAtual() == '40':

    getoutput('sudo rm /mnt/CLP/bits')
    enviaStatusFTP(FTP)
    
    getoutput('sudo chmod 777 '+diretorios[5]+'/SupervisorBits.py')
    getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/SupervisorBits.py')
    sleep(0.5)

    #debug(arquivo+'.py  ok')
    getoutput('sudo chmod 777 '+diretorios[0]+'/SupervisorBits')
            
    getoutput('sudo chmod 777 '+diretorios[0])
    getoutput('sudo chmod 777 '+diretorios[1])
    

    controleStatus('50')

if statusAtual() == '50':

    enviaStatusFTP(FTP)
    getoutput('sudo rm /mnt/CLP/bits')
    
    getoutput('sudo chmod 777 '+diretorios[5]+'/restaurasupervisores.py')
    getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/restaurasupervisores.py')
    sleep(0.5)

    #debug(arquivo+'.py  ok')
    getoutput('sudo chmod 777 '+diretorios[0]+'/restaurasupervisores')
            
    getoutput('sudo chmod 777 '+diretorios[0])
    getoutput('sudo chmod 777 '+diretorios[1])
        
    controleStatus('60')


if statusAtual() == '60':
    
    # 4° Apaga todos os arquivos locais

    enviaStatusFTP(FTP)
    getoutput('sudo rm /mnt/CLP/bits')
    
    for arquivo in arquivos:

        getoutput('sudo rm '+diretorios[6]+'/'+arquivo)

        if arquivo[:1] == 's' or arquivo[:1] == 'S' or arquivo[:1] == 'r':

            getoutput('sudo rm '+diretorios[6]+'/'+arquivo[:-3])
            getoutput('sudo rm '+diretorios[6]+'/'+arquivo[:-3]+'.new')

    for arquivo in arquivosSinal:

        getoutput('sudo rm '+diretorios[6]+'/'+arquivo)


    getoutput('sudo rm '+diretorios[7]+'/CLP.py')
    getoutput('sudo rm '+diretorios[6]+'/connMySQL.new')
    getoutput('sudo rm '+diretorios[6]+'/connMySQLOFF.new')
    getoutput('sudo rm -r '+diretorios[3])
    getoutput('sudo rm -r '+diretorios[4])

    getoutput('sudo mkdir '+diretorios[3])
    getoutput('sudo mkdir '+diretorios[4])

    getoutput('sudo chmod 777 '+diretorios[3])
    getoutput('sudo chmod 777 '+diretorios[4])



    # 5° Instala os arquivos nas pastas principais e backup
    getoutput('sudo rm /mnt/CLP/bits')
    for arquivo in arquivos:

        #debug(arquivo)

        if arquivo == 'connMySQL.ini' or arquivo == 'connMySQLOFF.ini' or arquivo[:1] == 's' or arquivo[:1] == 'S' or arquivo[:1] == 'r':

            #debug(arquivo)
            
            if arquivo[:1] == 's' or arquivo[:1] == 'S' or arquivo[:1] == 'r':

                debug('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[3])
                
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[3])
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[4])
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[6])

                debug('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[3]+'/'+arquivo[:-3]+'.new')
                    
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[3]+'/'+arquivo[:-3]+'.new')
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[4]+'/'+arquivo[:-3]+'.new')
                getoutput('sudo cp '+diretorios[0]+'/'+arquivo[:-3]+' '+diretorios[6]+'/'+arquivo[:-3]+'.new')

                
            else:
                debug('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3])
                
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3])
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[4])
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6])

                debug('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3]+'/'+arquivo[:-4]+'.new')
                
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3]+'/'+arquivo[:-4]+'.new')
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[4]+'/'+arquivo[:-4]+'.new')
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6]+'/'+arquivo[:-4]+'.new')

        else:
            getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3])
            getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[4])

            if arquivo != 'CLP.py':
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6])


    getoutput('sudo cp '+diretorios[5]+'/CLP.py '+diretorios[7])
    getoutput('sudo rm -r '+diretorios[5])
    getoutput('sudo rm '+diretorios[7]+'/restaurasupervisores.spec')
    getoutput('sudo rm '+diretorios[7]+'/supervisor.spec')
    getoutput('sudo rm '+diretorios[7]+'/SupervisorBits.spec')
    getoutput('sudo rm /mnt/CLP/bits')

    SQL = "UPDATE Nuvem_Gateway SET bits = '2' WHERE Cod_Gateway = '" +pegarNoSerie()+ "'"
    #debug(SQL)
    executaQueryBD(SQL, True)
    sleep(0.5)

    
    
    preparaInicializador(statusAtual())
    controleStatus('70')
    enviaStatusFTP(FTP)

    getoutput('sudo rm -r '+diretorios[0])
    getoutput('sudo rm -r '+diretorios[1])
    getoutput('sudo rm /home/pi/statusComando')
    getoutput('sudo rm /usr/lib/'+getPythonVer()+'/Comandos.py')
    getoutput('sudo rm /home/pi/debug')
    
    sleep(0.5)
    
    getoutput('reboot')






