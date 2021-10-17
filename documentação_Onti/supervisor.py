#VERSAO:202012181200
versao = '202012181200'

# Bibliotecas
from subprocess    import getoutput,Popen, PIPE
from Crypto.Cipher import AES
from threading     import Thread
from classes       import MySQL
from time          import sleep
from sys           import argv
from os            import listdir
import RPi.GPIO as GPIO
import configparser

def getPythonVer():
    pastas = listdir("/usr/lib/")
    for i in pastas:
        if str(i[0:8]) == 'python3.':
            return str(i)

def pegarNoSerie():
        
        # Coleta o número serial do Gateway do arquivo cpuinfo

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
        
# Atualiza a hora para que, caso o gateway perca a referência,
# Possa iniciar e não altere a data de última modificação para
# Uma data muito velha, que poderia causar erros ao tentar abrir.
try:
    getoutput("sudo ntpd -gq")
    getoutput("sudo hwclock -w")
    getoutput("date; sudo hwclock -r")
except:pass

# Configuração dos Pinos do Watchdog
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
# Pino 29
GPIO.setup(29, GPIO.OUT)
GPIO.output(29, GPIO.HIGH)
# Pino 31
GPIO.setup(31, GPIO.OUT)
GPIO.output(31, GPIO.LOW)

# Função que habilita o banco de dados
def HabilitaBanco():

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        # Coleta as informações sobre o host para descobrir se é local  #
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        config_on = configparser.ConfigParser()
        config_on.read('/usr/lib/'+getPythonVer()+'/connMySQL.ini')

        # Chave para descriptografar. uma chave para cada informação
        obj0 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

        # A informação é guardada codificada, mas quando é coletada chega no formato str
        x = config_on['database']['servidor']
        # Codificação das informações        
        x = bytes(x, 'utf-8')
        # Descodificação
        x = x.decode('unicode-escape').encode('ISO-8859-1')
        # Descriptografia das informações e decodificação das informações
        servidor_on = (obj0.decrypt(x).decode("utf-8")).strip('0')

        #print(servidor_on)
        
        # Sequência de comandos para necessarios
        # para utilização do servidor mariadb respetivamente:
        # Configura o servidor, habilita, inicia, Cria novos bancos
        # e novos usuarios, importa arquivos para cada um dos bancos criados.
        
        getoutput("sudo mysql_install_db")
        print(getoutput("sudo mysql_install_db"))

        getoutput("sudo systemctl enable mysql")
        print(getoutput("sudo systemctl enable mysql"))

        getoutput("sudo systemctl start mysql")
        print(getoutput("sudo systemctl start mysql"))
    

        if servidor_on == 'localhost':

            """
            Executa os scripts SQL contidos nos arquivos 'montaBancos.sql, bancoOnline.sql e BCK.sql no servidor
            maria DB com o objetivo de montar toda a estrutura dos bancos onlineLocal e offline e seus dados armazenados
            dentro dos mesmos scripts
            """
            getoutput('sudo mysql -u root -h localhost < /usr/lib/'+getPythonVer()+'/montaBancos.sql')
            getoutput('sudo mysql -u root  onlineLocal < /usr/lib/'+getPythonVer()+'/bancoOnline.sql')
            getoutput('sudo mysql -u root  offline < /usr/lib/'+getPythonVer()+'/BCK.sql')
            sleep(0.5)

            backup = False                                                  #Variavel para sinalizar quando for utilizado o arquivo de backup do banco onlineLocal
            arqINI = '/usr/lib/'+str(getPythonVer())+'/connMySQL.ini'       #Credencias de acesso ao banco onlineLocal
            arqOFF = '/usr/lib/'+str(getPythonVer())+'/connMySQLOFF.ini'    #Credencias de acesso as banco offline

            while True:

                mysql = MySQL(arqINI,arqOFF)                                #Instância da classe mysql importada do arquivo classes.py

                """
                Com o objetivo de testar a integridade do banco onlineLocal é feito um select do código do gateway
                que está utilizando este arquivo
                """ 

                SQL  = "SELECT Cod_Gateway FROM Nuvem_Gateway" 
                SQL += " WHERE Cod_Gateway = '"+str(pegarNoSerie())+"'"
                codigoGateway = mysql.pesquisarBD(SQL,True)

                #print(SQL)
                #print(codigoGateway)    

                #Será falso quando houver problemas no banco de dados onlineLocal então imediatamente segue para o else
                #e tenta recuperar o banco através do backup
                
                if codigoGateway != False and codigoGateway[0]['Cod_Gateway'] == pegarNoSerie():

                    #Verifica se a variavel backup foi setada pela rotina que utiliza o script de backup do banco onlineLocal
                    #para então criar um novo arquivo bancoOnline.sql através do bancoOnlineBCK.sql ou atualizar o arquivo de backup
                    #de bancoOnline.sql para bancoOnlineBCK.sql
                    #print(backup)

                    if backup:
                        getoutput('sudo cp /usr/lib/'+getPythonVer()+'/bancoOnlineBCK.sql /usr/lib/'+getPythonVer()+'/bancoOnline.sql')

                    else:
                        getoutput('sudo cp /usr/lib/'+getPythonVer()+'/bancoOnline.sql /usr/lib/'+getPythonVer()+'/bancoOnlineBCK.sql')

                    #print('finalizou')
                    break

                else:
                    #print('erro no banco onlineLocal recuperando backup'
                    #Utiliza o arquivo bancoOnlineBCK.sql que contém um backup do banco onlineLocal para montar a estrutura no servidor
                    #visto que o arquivo bancoOnline.sql não funcionou corretamente.
                    
                    getoutput('sudo mysql -u root  onlineLocal < /usr/lib/'+getPythonVer()+'/bancoOnlineBCK.sql')
                    sleep(0.5)
                    backup = True
                

        else:
            
            #Este trecho é utilizado em qualquer gateway que não pussua um banco online local
            
            getoutput("mysql -u root offline < /usr/lib/"+str(getPythonVer())+"/BCK.sql")
            print(getoutput("mysql -u root offline < /usr/lib/"+str(getPythonVer())+"/BCK.sql"))

        
        
        # Sequência de comandos para levar os arquivos CLP,config on e off ao /mnt/CLP 
        getoutput(['sudo cp /usr/lib/'+str(getPythonVer())+'/connMySQLOFF.ini /mnt/CLP/connMySQLOFF.ini'])
        getoutput(['sudo cp /usr/lib/'+str(getPythonVer())+'/connMySQL.ini /mnt/CLP/connMySQL.ini'])
        getoutput(['sudo cp /home/pi/CLP.py /mnt/CLP/CLP.py'])
        getoutput(['sudo chmod 777 /mnt/CLP/connMySQLOFF.ini'])
        getoutput(['sudo chmod 777 /mnt/CLP/connMySQL.ini'])
        getoutput(['sudo chmod 777 /mnt/CLP/CLP.py'])
        #print('fim execução')

# Função principal do supervisor
def Supervisor():

    while 1:
        
        # Verifica se há comunicação com o banco de dados
        mysql = len(getoutput('sudo mysql'))
        #print('mysql : ',mysql)
        # Se não houver comunicação com o banco, o resultado da tentativa é != 0
        if mysql != 0:pass
        
        # Caso haja comunicação o arquivo MAIN.py é executado
        else:

            arqINI = '/usr/lib/'+str(getPythonVer())+'/connMySQL.ini'       #Credencias de acesso ao banco onlineLocal
            arqOFF = '/usr/lib/'+str(getPythonVer())+'/connMySQLOFF.ini'    #Credencias de acesso as banco offline

            mysql = MySQL(arqINI,arqOFF)
            SQL = "SELECT Cod_Protocolo_Comunicacao FROM Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao"
            teste = mysql.pesquisarBD(SQL,False)
            #print('teste: ',teste)            
            if teste == False or teste == '':
                continue

            #print('continue')
            
            #getoutput('sudo cd /usr/lib/python3.4; sudo /usr/bin/idle3 -r /usr/lib/python3.4/MAIN.py 201904301601 python3.4')
            def print_lines(inp):

                line = inp.readline().decode('utf-8')
                
                while line:

                    try:
                        arq = open('/mnt/CLP/Shell', 'r')
                        a = arq.readlines()
                        arq.close()

                        arq = open('/mnt/CLP/Shell', 'w')
                        a.append(line)
                        arq.writelines(a)
                        arq.close()
                    except:
                        arq = open('/mnt/CLP/Shell','w')
                        a = ['']
                        a.append(line)
                        arq.writelines(a)
                        arq.close()
                
                    line    = inp.readline().decode('utf-8')

            proc = Popen(["sudo python3 -u /usr/lib/"+str(getPythonVer())+"/MAIN.py "+str(versao)+" "+str(getPythonVer())+""], shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)

            t1 = Thread(target=print_lines, args=(proc.stdout,))
            t2 = Thread(target=print_lines, args=(proc.stderr,))

            t1.start()
            t2.start()

            t1.join()
            t2.join()
            
        sleep(3)

# Durante a inicialização, ou reinicilização, chama-se a função que habilita o banco
BD = Thread(target = HabilitaBanco)
BD.start()

# Chamada da função principal, de plano de fundo, em looping, que executa o arquivo MAIN.py
Supervisor()

