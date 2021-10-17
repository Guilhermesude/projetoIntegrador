''' Descritivo passo a passo do algoritmo empregado para atualizar o software do gateway 

    Passo 1 - Baixa as bibliotecas, métodos, classes e etc que serão utilizadas no processo.
    Passo 2 - Atribui à varriaveis valores que serão utilizados posteriormente pelo algoritomo.
    Passo 3 - Sinaliza que se iniciou uma atualização, busca no banco online o diretorio ftp e conecta-se ao FTP.  
    Passo 4 - Concede permisão a todos os diretorios utilizados e caso o diretorio nao exista cria.
    Passo 5 - Realiza backup completo de todo o sistema. 
    Passo 6 - Realiza o Download de todos os arquivos nescessários do diretorio FTP.
    Passo 7 - Coleta as versões dos arquivos baixados.
    Passo 8 - Verrifica se estão corretas as versões dos arquivos baixados, compatibilidade do banco e quais arquivos serão atualizados.
    Passo 9 - Apaga os arquivos antigos do diretorio /usr/lib/python3.x e copia os novos arquivos, e cria os executaveis.
    Passo 10 - Verrifica se é nescessario matar algum processo, e caso aconteça um erro recupera os antigos arquivos do backup.
'''

# Passo 1 ************************************************************************************************************************************************************
from os         import remove,path,makedirs,system,getpid,kill,listdir
from timeit     import default_timer as timer
from shutil     import rmtree,move,copyfile
from subprocess import getoutput,Popen
from traceback  import print_exc
from datetime   import datetime
from signal     import SIGTERM
from classes    import gateway
from time       import sleep
from classes    import MySQL
from classes    import eventosGateway
from sys        import argv
import configparser
import ftplib
import RPi.GPIO as GPIO
# fim passo 1 ********************************************************************************************************************************************************


# Passo 2 ************************************************************************************************************************************************************
def checkAtualizacao():
    
    
    # Argumentos enviados pelo bit 6
    arqINI = argv[1]
    arqOFF = argv[2]
    nSerie = argv[3]          # Número de série
    toKill = argv[4]          # Variável que refere-se ao PID do programa principal
    to0Bit = argv[5]          # Valor do bit ao recolher do banco de dados
    
    # Instância a classe
    mysql       = MySQL(arqINI, arqOFF)
    gate        = gateway()
    eventosGate = eventosGateway()
    
    # Versões dos arquivos
    verCLP         = argv[6] 
    verMain        = argv[7]
    verClasses     = argv[8]
    verSuper       = argv[9]
    verSuperBits   = argv[10] 
    verArqINI      = argv[11]
    verArqOff      = argv[12]
    verBDOff       = argv[13]
    verRestaurador = argv[14]
    try:        
        print('versao do python não existe')
        verPython      = argv[15]
    except:
        verPython      = argv[14]
        verRestaurador = '202001010000'
    
    tentativas           = 0
    supervisor           = 0
    supervisorBits       = 0
    restaurasupervisores = 0
    
    # Lista com nomes de diretorios, arquivos e numeros de versão 
    versoesDownload = []
    atualizar       = []
    toAtualizador   = ['connMySQL.ini','connMySQLOFF.ini','MAIN.py','classes.py','CLP.py','supervisor.py','restaurasupervisores.py','SupervisorBits.py','BCK.sql']
    diretorios      = ['/home/pi/dist','/home/pi/build','/home/pi/__pycache__','/usr/lib/'+verPython+'/backup-1','/usr/lib/'+verPython+'/backup','/usr/lib/'+verPython+'/download','/usr/lib/'+verPython,'/home/pi','/mnt/CLP']    
    versoesAtuais   = [verArqINI,verArqOff,verMain,verClasses,verCLP,verSuper,verRestaurador,verSuperBits,verBDOff] 


# fim passo 2 ********************************************************************************************************************************************************


# Passo 3 ************************************************************************************************************************************************************
    
    # Cria o arquivo atualizando para indicar que começou a atualizar
    arq = open('/usr/lib/'+verPython+'/Atualizando','w')
    arq.close()

    # Seleciona do banco de dados informações para o acesso aos arquivos no FTP
    SQL = "SELECT versaoSoftware, Host, Login, Senha FROM Nuvem_Gateway WHERE Cod_Gateway = '" + nSerie + "'"
    try: FTP = mysql.pesquisarBD(SQL,True)
    except: return

    # Cria um caminho
    pathServ = FTP[0]['versaoSoftware']     

    # Conecta ao FTP
    try:
        ftp = ftplib.FTP(host=FTP[0]['Host'])
        ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
    except: return

# fim passo 3 ********************************************************************************************************************************************************


# Passo 4 ************************************************************************************************************************************************************
    
    # Concede permissão a todos os diretorios utilizados ou cria caso nao exista
    for i in diretorios:
        
        condicoes = [i==diretorios[0],i==diretorios[1],i==diretorios[2],i==diretorios[3],i==diretorios[5]]  # Lista com condições para apagar diretorios
        
        if path.isdir(i):                                                                                   # Permissão maxima caso exista
            try:
                getoutput('sudo chmod 777 '+i)
            except:                                                                                                 
                print('não foi capaz de liberar permissão de '+i)
                return
            
        if any(condicoes) and path.isdir(i):                                                                # Apaga diretorio caso condição verdadeira
            try:
                getoutput('sudo rm -r '+i)
            except:
                print('não foi capaz de remover '+i)
                return
            
        if not path.isdir(i) and (i == diretorios[3] or i == diretorios[4] or i == diretorios[5]):          # Cria diretorio se nao existir 
            try:
                getoutput('sudo mkdir '+i)
                getoutput('sudo chmod 777 '+i)
            except:
                print('não foi capaz de criar e permitir '+i)
                return
            
# fim passo 4 ********************************************************************************************************************************************************


# Passo 5 ************************************************************************************************************************************************************

    # Se backup estiver completo: move de backup para backup-1 e copia do sistema para backup
    if len(listdir(diretorios[4])) == 13:
        print('Passo 5 nomes dos arquivos')
        # Move os arquivos da pasta de backup para backup-1 e copia arquivos do sistema para backup
        for i in toAtualizador:
            
            condicoesA = [i=='supervisor.py',i=='SupervisorBits.py',i=='restaurasupervisores.py']
            condicoesB = [i=='connMySQL.ini',i=='connMySQLOFF.ini']
            
            if any(condicoesA):
                i=i[0:-3]
                
            try:
                print('arquivo - '+i)
                if i == 'CLP.py':
                    getoutput('sudo mv '+diretorios[4]+'/'+i+' '+diretorios[3])
                    getoutput('sudo cp '+diretorios[7]+'/'+i+' '+diretorios[4]+'/'+i)  
                    
                else:                           
                    getoutput('sudo mv '+diretorios[4]+'/'+i+' '+diretorios[3])
                    getoutput('sudo cp '+diretorios[6]+'/'+i+' '+diretorios[4]+'/'+i)
                    
                    if any(condicoesB):
                        i=i[0:-4] 
                    
                    if i == 'supervisor' or i == 'SupervisorBits' or any(condicoesB):
                        getoutput('sudo mv '+diretorios[4]+'/'+i+'.new '+diretorios[3])
                        getoutput('sudo cp '+diretorios[6]+'/'+i+'.new '+diretorios[4])
                            
                getoutput('sudo chmod 777 '+diretorios[3]+'/'+i)
                getoutput('sudo chmod 777 '+diretorios[4]+'/'+i)
                
            except:print('Erro ao enviar ',i,' de backup para backup-1')        
            
    # Com backup incompleto: limpa a pasta de backup e então copia do sistema para backup e para backup-1
    else:
        print('backup incompleto, criando novo backup')
        getoutput('sudo rm -r '+diretorios[4])
        getoutput('sudo mkdir '+diretorios[4])
        getoutput('sudo chmod 777 '+diretorios[4])
        
        # Copia os arquivos atuais do sistema para backup e para backup-1
        for i in toAtualizador:
            
            condicoesA = [i=='supervisor.py',i=='SupervisorBits.py',i=='restaurasupervisores.py']
            condicoesB = [i=='connMySQL.ini',i=='connMySQLOFF.ini']
            
            if any(condicoesA):
                i=i[0:-3]
                
            try:
                print('arquivo - '+i)
                if i == 'CLP.py':
                    getoutput('sudo cp '+diretorios[7]+'/'+i+' '+diretorios[3]+'/'+i)
                    getoutput('sudo cp '+diretorios[7]+'/'+i+' '+diretorios[4]+'/'+i)          
                    
                else:                           
                    getoutput('sudo cp '+diretorios[6]+'/'+i+' '+diretorios[3]+'/'+i)
                    getoutput('sudo cp '+diretorios[6]+'/'+i+' '+diretorios[4]+'/'+i)
                
                    if any(condicoesB):
                        i=i[0:-4] 
                        
                    if i == 'supervisor' or i == 'SupervisorBits' or any(condicoesB):
                        getoutput('sudo cp '+diretorios[6]+'/'+i+' '+diretorios[6]+'/'+i+'.new')
                        getoutput('sudo cp '+diretorios[6]+'/'+i+'.new '+diretorios[3])
                        getoutput('sudo cp '+diretorios[6]+'/'+i+'.new '+diretorios[4])
                        
                getoutput('sudo chmod 777 '+diretorios[3]+'/'+i)
                getoutput('sudo chmod 777 '+diretorios[4]+'/'+i)
                
            except:print('Erro ao enviar ',i,' de backup para backup-1')  

# fim passo 5 ********************************************************************************************************************************************************


# Passo 6 ************************************************************************************************************************************************************

    for i in toAtualizador:
                        
        # Abre a pasta de download e direciona o arquivo criado
        try:
            file = open(diretorios[5]+'/'+i, mode='wb')
            ftp = ftplib.FTP(host=FTP[0]['Host'])
            ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
            ftp.cwd(pathServ)
        except:pass

        # Escreve dentro do arquivo criado
        try:
            ftp.retrbinary("RETR " + i, file.write)
            file.close()
            getoutput('sudo chmod 777 '+diretorios[5]+'/'+i)
            
        # Caso não consiga, excluí-se o arquivo
        except:
            print('erro ao baixar ou escrever o arquivo')
            file.close()
            if i=='classes.py' or i=='MAIN.py' or i=='BCK.sql':
                getoutput('sudo rm -r '+diretorios[5])
                break
            else:    
                getoutput('sudo rm '+diretorios[5]+'/'+i)

# fim passo 6 ********************************************************************************************************************************************************


# Passo 7 ************************************************************************************************************************************************************

    # Coleta das versões baixadas
    try:
        config_on = configparser.ConfigParser()
        config_on.read(diretorios[5]+'/connMySQL.ini')
        verDownArqINI = config_on['database']['versao']
        versoesDownload.append(verDownArqINI)
    except:
        verDownArqINI = '0000000'
        versoesDownload.append(verDownArqINI)
        
    try:    
        config_off = configparser.ConfigParser()
        config_off.read(diretorios[5]+'/connMySQLOFF.ini')
        verDownArqOff = config_off['database']['versao']
        versoesDownload.append(verDownArqOff)
    except:
        verDownArqOff = '0000000'
        versoesDownload.append(verDownArqOff)
        
    try:                
        arq   = open(diretorios[5]+'/MAIN.py','r')
        lines = arq.readlines()
        verDownMain = ((lines[0])[8:20])
        versoesDownload.append(verDownMain)
        arq.close()
    except:
        verDownMain = '0000000'
        versoesDownload.append(verDownMain)
        
    try:
        arq = open(diretorios[5]+'/classes.py','r')
        lines = arq.readlines()
        verDownClasses = ((lines[0])[8:20])
        verCompativel  = ((lines[1])[17:29])
        versoesDownload.append(verDownClasses)
        arq.close()
    except:
        verDownClasses = '0000000'
        versoesDownload.append(verDownClasses)
        
    try:        
        arq = open(diretorios[5]+'/CLP.py','r')
        lines = arq.readlines()
        verDownCLP = ((lines[0])[8:20])
        versoesDownload.append(verDownCLP)
        arq.close()
    except:
        verDownCLP = '0000000'
        versoesDownload.append(verDownCLP)
        
    try:    
        arq = open(diretorios[5]+'/supervisor.py','r')
        lines = arq.readlines()
        verDownSuper = ((lines[0])[8:20])
        versoesDownload.append(verDownSuper)
        arq.close()
    except:
        verDownSuper = '0000000'
        versoesDownload.append(verDownSuper)
        
    try:    
        arq = open(diretorios[5]+'/restaurasupervisores.py','r')
        lines = arq.readlines()
        verDownrestaurador = ((lines[0])[8:20])
        versoesDownload.append(verDownrestaurador)
        arq.close()
    except:
        verDownrestaurador = '0000000'
        versoesDownload.append(verDownrestaurador)
        
    try:    
        arq = open(diretorios[5]+'/SupervisorBits.py','r')
        lines = arq.readlines()
        verDownSuperBits = ((lines[0])[8:20])
        versoesDownload.append(verDownSuperBits)
        arq.close()
    except:
        verDownSuperBits = '0000000'
        versoesDownload.append(verDownSuperBits)
        
    try:    
        getoutput('sudo mysql -u root -h localhost < '+diretorios[5]+'/BCK.sql')
        sleep(1)
        SQL = "SELECT verRdBDOff FROM Nuvem_Gateway"
        verDownBDOff, = mysql.pesquisarBD(SQL,False)
        verDownBDOff = verDownBDOff['verRdBDOff']
        versoesDownload.append(verDownBDOff)
        print('Versao do banco baixado '+verDownBDOff)
    except:
        print('erro ao buscar versao do banco de dados')
        verDownBDOff = '0000000'
        versoesDownload.append(verDownBDOff)
    
    getoutput('sudo mysql -u root -h localhost < '+diretorios[4]+'/BCK.sql')
        
# fim passo 7 ********************************************************************************************************************************************************
 
  
# Passo 8 ************************************************************************************************************************************************************

    for indice,versaoDownload,versaoAtual,arquivo in zip(range(9),versoesDownload,versoesAtuais,toAtualizador):  # Percorre as listas {versoesDownload,versoesAtuais,toAtualizador} e usa um indice numerico atraves de um range
        print(versaoDownload+' - '+versaoAtual+' - '+arquivo)    
            
        if len(versaoDownload) < 12:                                                                             # Se isso for verdadeiro há erros na definição da versao do arquivo   
            versoesDownload[indice] = versaoAtual                                                                # Iguinora a versao do arquivo baixado e iguala a versao do arquivo do sistema
            print('Não foi possivel encontrar a versão correta de '+arquivo)
        
        elif versaoDownload != versaoAtual:
            atualizar.append(arquivo)
    
    print(atualizar)        
    print('Compatibilidade Banco   = ', verDownBDOff)
    print('Compatibilidade Classes = ', verCompativel)
    
    try:    
        if str(verDownBDOff) != str(verCompativel):

            toBill = getpid()

            getoutput('sudo rm -r '+diretorios[5])
            getoutput('sudo rm '+diretorios[6]+'/atualizador.py')
            getoutput('sudo rm '+diretorios[6]+'/Atualizando')
            getoutput('sudo rm '+diretorios[6]+'/Atualizado')
            
            SQL = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 1 WHERE Cod_Evento_Gateway = '12'"
            try:mysql.executaQueryBD(SQL,False) 
            except:pass

            SQL =  "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES('" + str(nSerie) + "', 12, '"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"')"
            try:    mysql.executaQueryBD(SQL,True)
            except: mysql.executaQueryBD(SQL,False)

            return
    except:
        print('Erro de compatibilidade e erro ao registrar historico de evento !')
        # Em caso de erro deve-se garantir que o diretorio e arquivos abaixo sejam deletados.
        getoutput('sudo rm -r '+diretorios[5])
        getoutput('sudo rm '+diretorios[6]+'/atualizador.py')
        getoutput('sudo rm '+diretorios[6]+'/Atualizando')
        getoutput('sudo rm '+diretorios[6]+'/Atualizado')
        return

# fim passo 8 ********************************************************************************************************************************************************

# Passo 9 ************************************************************************************************************************************************************

    if atualizar != []:
        supervisor     = ''
        supervisorBits = ''
        reinicializar  = False
        
        for arquivo in atualizar:
            if arquivo == 'supervisor.py':
                print('criando um executavel')
                getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/'+arquivo)
                getoutput('sudo chmod 777 '+diretorios[0])
                getoutput('sudo chmod 777 '+diretorios[0]+'/supervisor')
                getoutput('sudo rm '+diretorios[6]+'/supervisor')
                getoutput('sudo cp '+diretorios[0]+'/supervisor '+diretorios[6]+'/supervisor')
                getoutput('sudo rm '+diretorios[6]+'/supervisor.new')
                getoutput('sudo cp '+diretorios[0]+'/supervisor '+diretorios[6]+'/supervisor.new')
                getoutput('sudo rm '+diretorios[7]+'/supervisor.spec')
                getoutput('sudo rm -r '+diretorios[0])
                getoutput('sudo rm -r '+diretorios[1])
                getoutput('sudo rm -r '+diretorios[2])
                supervisor = 1
                
            elif arquivo == 'restaurasupervisores.py':
                getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/'+arquivo)
                getoutput('sudo chmod 777 '+diretorios[0])
                getoutput('sudo chmod 777 '+diretorios[0]+'/restaurasupervisores')
                getoutput('sudo rm '+diretorios[6]+'/restaurasupervisores')
                getoutput('sudo cp '+diretorios[0]+'/restaurasupervisores '+diretorios[6]+'/restaurasupervisores')
                getoutput('sudo rm '+diretorios[7]+'/restaurasupervisores.spec')
                getoutput('sudo rm -r '+diretorios[0])
                getoutput('sudo rm -r '+diretorios[1])
                getoutput('sudo rm -r '+diretorios[2])
                restaurasupervisores = 1
                
            elif arquivo == 'SupervisorBits.py':
                getoutput('sudo pyinstaller --onefile '+diretorios[5]+'/'+arquivo)
                getoutput('sudo chmod 777 '+diretorios[0])
                getoutput('sudo chmod 777 '+diretorios[0]+'/SupervisorBits')
                getoutput('sudo rm '+diretorios[6]+'/SupervisorBits')
                getoutput('sudo cp '+diretorios[0]+'/SupervisorBits '+diretorios[6]+'/SupervisorBits')
                getoutput('sudo rm '+diretorios[6]+'/SupervisorBits.new')
                getoutput('sudo cp '+diretorios[0]+'/SupervisorBits '+diretorios[6]+'/SupervisorBits.new')
                getoutput('sudo rm '+diretorios[7]+'/SupervisorBits.spec')
                getoutput('sudo rm -r '+diretorios[0])
                getoutput('sudo rm -r '+diretorios[1])
                getoutput('sudo rm -r '+diretorios[2])
                supervisorBits = 1
                
            elif arquivo == 'CLP.py':
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[7])
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[8])
               
            elif arquivo == 'MAIN.py' or arquivo == 'classes.py':
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6])
                reinicializar = True         
    
            elif arquivo == 'connMySQL.ini' or arquivo == 'connMySQLOFF.ini':
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6]+'/'+arquivo[:-4]+'.new')
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[4]+'/'+arquivo[:-4]+'.new')                
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[3]+'/'+arquivo[:-4]+'.new')
                                
            elif arquivo == 'BCK.sql':
                getoutput('sudo cp '+diretorios[5]+'/'+arquivo+' '+diretorios[6])
                gate.montarBDOff(arqINI,arqOFF,False)
                reinicializar = True
                
            getoutput('sudo chmod 777 '+diretorios[6]+'/'+arquivo)
            getoutput('sudo chmod 777 '+diretorios[7]+'/'+arquivo)
            getoutput('sudo chmod 777 '+diretorios[8]+'/'+arquivo)
            
            
        if supervisor == 1:
            getoutput('sudo pkill supervisor')
            Popen(['nohup',diretorios[6]+'/./supervisor'])
        
        if supervisorBits == 1:
            getoutput('sudo pkill SupervisorBits')
            Popen(['nohup',diretorios[6]+'/./SupervisorBits'])
            
        if restaurasupervisores == 1:
            Popen(['nohup',diretorios[6]+'/./restaurasupervisores'])

# fim passo 9 ********************************************************************************************************************************************************
# Passo 10 ************************************************************************************************************************************************************
        getoutput('sudo rm '+diretorios[6]+'/atualizador.py')               # Remove o arquivo atualizador
        getoutput('sudo rm -r '+diretorios[5])                              # Remove a pasta de download
        arq = open('/usr/lib/'+verPython+'/Atualizado','w')                 # Cria o arquivo Atualizado para indicar a atualizaçao concluida
        arq.close()
    
        print('Reinicializar = '+str(reinicializar))      
          
        if reinicializar != True:    
            # Verifica se 'Inicializar', no arquivo CLP esta em 1 ou 0
            # Indicando se o programa deve ser reinicializado ou não
            try:
                arq = open(diretorios[7]+'/CLP.py','r')
                lines = arq.readlines()
                Inicializar = ((lines[1])[13:14])
                arq.close()

                if int(Inicializar): 
                    getoutput('sudo rm '+diretorios[8]+'/CLPiniciou')    
                    print('Deve mudar o valor de self.inicializar')        
                
            except:
                print('As variaveis serão redefinidas pois houve erro na leitura de Inicializar')    
                      
            # Se o classes ou main não forem atualizados e clp for atualizado
            # Será feito a troca dos arquivos sem a reinicialização do programa atual
            # E os arquivos auxiliares serão excluídos
            
            #try:    toPie = getoutput("sudo pgrep idle3")
            #except: print_exc()

            toBill = getpid()

            getoutput('sudo rm -r '+diretorios[5])
            getoutput('sudo rm '+diretorios[6]+'/atualizador.py')
            getoutput('sudo rm '+diretorios[6]+'/Atualizando')
            getoutput('sudo rm '+diretorios[6]+'/Atualizado')
            
            try:getoutput("sudo pkill -9 idle3")
            except:pass
            
            try:kill(int(toBill), SIGTERM)
            except:pass
        
        elif reinicializar == True:    
            
            # A execução do arquivo principal é finalizada
            try:
                getoutput("sudo pkill -9 idle3")                            
                kill(int(toKill), SIGTERM)
                toPie = getoutput("sudo pgrep idle3")                       # pega id do processo do idle do python
                
            except:
                print('Erro ao matar a execusão atual')

            GPIO.setmode(GPIO.BOARD)                                        # Configura o watchdog para garantir que o Gateway não
            GPIO.setwarnings(False)                                         # reinicie ao longo da atualização
            GPIO.setup(29, GPIO.OUT)
            GPIO.output(29, GPIO.HIGH)
            GPIO.setup(31, GPIO.OUT)
            GPIO.output(31, GPIO.HIGH)

            # Espera-se 60 segundos para que o programa, com as novas atualizações inicie
            # E que consiga fazer, ao menos, um ciclo até o fim onde será gerado um arquivo
            # Chamado 'Iniciado'

            while tentativas < 180:
                try:
                    GPIO.output(29, GPIO.HIGH)
                    GPIO.output(31, GPIO.HIGH)

                    sleep(1)
                    # Se remover o arquivo iniciado significa que o programa esta funcionando
                    print('tenta apagar o arquivo Iniciado')
                    remove(diretorios[6]+'/Iniciado')

                    # Coleta o PID do programa e o idle e os finaliza
                    if    path.isdir('/home/pi/Report'): pass
                    else: makedirs('/home/pi/Report')

                    getoutput("sudo cp /mnt/CLP/Shell /home/pi/Report/"+str(datetime.now().strftime('%Y%m%d%H%M')))

                    toBill = getpid()
                    kill(int(toBill), SIGTERM)
                    getoutput("sudo kill "+str(toPie))
                    return
                except:
                    
                    tentativas +=1

                GPIO.output(29, GPIO.HIGH)
                GPIO.output(31, GPIO.HIGH)
            
            # Se o tempo de tentativas for excedido os arquivos movidos ao backup serão levados às pastas
            # Indicando que a atualização falhou em algum ponto
            for i in toAtualizador:
                try:
                    if i == 'supervisor.py':
                        getoutput('sudo cp '+diretorios[4]+'/supervisor '+diretorios[6]+'/supervisor')
                        
                    elif i == 'SupervisorBits.py':
                        getoutput('sudo cp '+diretorios[4]+'/SupervisorBits '+diretorios[6]+'/SupervisorBits')
                    
                    elif i == 'restaurasupervisores.py':
                        getoutput('sudo cp '+diretorios[4]+'/restaurasupervisores '+diretorios[6]+'/restaurasupervisores')
                        
                    elif i == 'CLP.py':
                        getoutput('sudo cp '+diretorios[4]+'/'+i+' '+diretorios[7]+'/'+i)
                        getoutput('sudo chmod 777 '+diretorios[7]+'/'+i)
                        
                    elif i == 'BCK.sql':
                        getoutput('sudo cp '+diretorios[4]+'/'+i+' '+diretorios[6]+'/'+i )
                        getoutput('mysql -u root -h localhost < '+diretorios[6]+'/BCK.sql')
                            
                    else:                           
                        getoutput('sudo cp '+diretorios[4]+'/'+i+' '+diretorios[6]+'/'+i)
                            
                    getoutput('sudo chmod 777 '+diretorios[6]+'/'+i)
                    
                except:print('Erro ao enviar ',i,' de backup para backup-1') 

            # Sinaliza ao banco de dados que a atualização ocorreu com erro
           
            SQL = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 1 WHERE Cod_Evento_Gateway = '23'"
            try:mysql.executaQueryBD(SQL,False) 
            except:pass

            SQL = "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES('" + str(nSerie) + "', 23, '"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"')"
            try:    mysql.executaQueryBD(SQL,True)
            except: mysql.executaQueryBD(SQL,False)

            # Zera-se o bit no banco
            toBD =  ((2**int(to0Bit)) * - 1) + (gate.getBit(arqINI,arqOFF))
            SQL = "UPDATE Nuvem_Gateway SET Bits = '"+str(toBD)+"' WHERE Cod_Gateway = '" + str(nSerie) + "'"
            try:mysql.executaQueryBD(SQL,True)
            except:pass

            getoutput('sudo rm -r '+diretorios[5])
            getoutput('sudo rm '+diretorios[6]+'/atualizador.py')
            getoutput('sudo rm '+diretorios[6]+'/Atualizando')
            getoutput('sudo rm '+diretorios[6]+'/Atualizado')
            
            # Finaliza tudo e reinicia o sistema
            getoutput('sudo pkill -9 idle3; sudo pkill -9 python3')
            getoutput("reboot")
            
    else:
        # Se não houverem arquivos para serem atualizados os arquivos auxiliares serão apagados

        toBill = getpid()

        getoutput('sudo rm -r '+diretorios[5])
        getoutput('sudo rm '+diretorios[6]+'/atualizador.py')
        getoutput('sudo rm '+diretorios[6]+'/Atualizando')
        getoutput('sudo rm '+diretorios[6]+'/Atualizado')
        
        try:kill(int(toBill), SIGTERM)
        except:pass

        # Evento para indicar que atualização não tem versões diferentes
        
checkAtualizacao()
# fim passo 10 ********************************************************************************************************************************************************
