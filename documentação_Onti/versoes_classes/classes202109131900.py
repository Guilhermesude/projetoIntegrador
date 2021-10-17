#VERSAO:202109131900
#COMPATIBILIDADE:202002260830
#Bibliotecas
from socket        import gethostbyname,create_connection,socket,AF_INET,SOCK_STREAM,SOL_SOCKET,SO_REUSEADDR
from os            import remove,path,makedirs,system,getpid,listdir,stat
from datetime      import datetime,timedelta,date
from timeit        import default_timer as tempor
from re            import compile as comp,findall
from subprocess    import getoutput,Popen,PIPE
from threading     import Thread, Event
from traceback     import print_exc
from shutil        import copyfile
from Crypto.Cipher import AES
from threading     import Timer
from smbus         import SMBus
from time          import sleep
import RPi.GPIO as GPIO
import configparser
import ftplib
import serial

# Declarações das variáveis auxiliares globais
global interromper
interromper = False

global wdt
wdt = ['','','','','','','','','','','']

global pid_modem

global novaCredencial
novaCredencial = False



class gateway:
    def __init__(self):
        self.verMain                = '000000000000'
        self.verClasses             = '000000000000'      
        self.verSuper               = '000000000000'  
        self.verAtt                 = '000000000000'
        self.verArqINI              = '000000000000'
        self.verArqOff              = '000000000000'
        self.verBDOff               = '000000000000'
        self.verCLP                 = '000000000000'
        self.verSuperBits           = '000000000000'
        self.verRestaurador         = '000000000000'
        self.noSerie                = self.__pegarNoSerie()
        self.nome                   = ""
        self.noED                   = 0
        self.noSD                   = 0
        self.noEA                   = 0
        self.noSA                   = 0
        self.endIP_externo          = '0.0.0.0'
        self.endIP_atual            = '0.0.0.0'
        self.portaServidor_ethernet = 8888
        self.portaComandos_ethernet = 8888
        self.ultimaConexaoServidor  = ''
        self.intervaloConfig        = 15
        self.bits                   = 0
        self.maquina                = []
        self.histVarNaoEnviado      = []
        self.histEventoNaoEnviado   = []
        self.info                   = []
        self.__listaTMRHistVar      = []
        self.__histVarRodando       = False
        self.entradasDigitais       = None
        self.saidasDigitais         = None
        self.entradasAnalogicas     = None
        self.saidasAnalogicas       = None
        self.variaveisInternas      = None
        self.variaveisEInternas     = None
        self.geradorCloro           = None
        self.ctrl                   = ControleEnergia()
        self.setBit                 = Event()
        self.loadError              = Event()
        self.ciclos                 = Event()
        self.clpAtualizado          = Event()
        self.usandoPonti            = Event()
        self.inicializar            = 0
        self.histGate               = []
        self.LDO                    = []
        self.LIC                    = []
        self.tempCiclo              = 1
        self.enviarVar              = Event()
        self.enviaTimestampPM       = 1
        self.peqInterDesligado      = False
        self.versaoPython           = self.getPythonVer()
        self.tmpEnvioRelatorio      = 86400
        self.codMaquina             = None

    # Função que verifica a versão do python
    def getPythonVer(self):

        pastas = listdir("/usr/lib/")
        for i in pastas:
            if str(i[0:8]) == 'python3.':
                return str(i)

    # Verifica se o banco é compatível com a versão do classes
    def bancoCompativel(self, arqINI, arqOFF, verCompativel, atualizacao):

        mysql = MySQL(arqINI, arqOFF)

        tentativas = 0

        print("\n Verificando Compatibilidade")
        # Verifica se o banco já esta estável e pronto para uso
        while tentativas < 6:
            
            try:
                # Coleta a versão do banco
                SQL = "SELECT verRdBDOff FROM Nuvem_Gateway"
                verCompBD, = mysql.pesquisarBD(SQL,False)
                verCompBD  = verCompBD['verRdBDOff']

                # Verifica se a versão do banco é compatível com a do classes
                if str(verCompativel) == str(verCompBD):

                    SQL  = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 0 WHERE Cod_Evento_Gateway = 15"
                    mysql.executaQueryBD(SQL,False)

                    try:remove('/usr/lib/'+self.versaoPython+'/Reiniciado')
                    except:pass
                    return True

                # Caso não seja compatível, os arquivos guardados no backup serão colocados no lugar
                # E um evento será gerado
                else:
                    # Registra no banco o evento
                    SQL  = "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES("
                    SQL += "'" + str(self.noSerie) + "', "
                    SQL += "'" + str(15) + "', "
                    SQL += "'" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "'"
                    SQL += ")"

                    try:    mysql.executaQueryBD(SQL,True)
                    except: mysql.executaQueryBD(SQL,False)

                    SQL  = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 1 WHERE Cod_Evento_Gateway = 15"
                    mysql.executaQueryBD(SQL,False)

                    fromBackup = ['MAIN.py','classes.py','supervisor','connMySQL.ini','connMySQLOFF.ini','BCK.sql','CLP.py','SupervisorBits','restaurasupervisores']
                 
                    # Se o tempo de tentativas for excedido os arquivos movidos ao backup serão levados às pastas
                    
                    for i in fromBackup:
                        try:
                            getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup/'+i)
                            
                            if i == 'CLP.py':
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /home/pi/'+i)
                                getoutput('sudo cp /home/pi/'+i+' /mnt/CLP/'+i)
                                getoutput('sudo chmod 777 /mnt/CLP/'+i)
                            
                            elif i == 'BCK.sql':
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)
                                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                                #getoutput('mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/'+i)
                                getoutput('mysql -u root offline < /usr/lib/'+self.versaoPython+'/'+i)

                            else:
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)    
                                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                            
                        except:print_exc()
                    return False
            except:
                print_exc()
                tentativas += 1
                sleep(3)

        return False
         
    # Função para salvar todas as informações necessárias antes de reiniciar o sistema
    def salvarTudo(self, arqINI, arqOFF): 

        global interromper
        global wdt
        interromper = True

        print('\nSalvando eventos\n')

        sleep(1)
        
        LDO = {}    

        print('vai decriptar')

        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        # Coleta as informações sobre o host para descobrir se é local  #
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        config_on = configparser.ConfigParser()
        config_on.read('/usr/lib/'+self.versaoPython+'/connMySQL.ini')

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

        print(servidor_on)

        
        # Envio de eventos sinalizados para o banco de dados online e offline
        try:
            for maq in self.maquina:
                maq.envioEvento(arqINI, arqOFF)
        except:pass

        # Procura o valor retentivo das saidas para escrever antes de desligar
        try:
            for maq in self.maquina:
                for var in maq.variavel:
                    if var.tipoVariavel.cod == 3:
                        LDO[var.nome] = int(var.retentividade)
                if self.useSD >=1: self.saidasDigitais.escreverSaidas(LDO)
        except:pass
        
        # Exporta o banco de dados offline para a pasta raíz e libera permissões do arquivo Shell

        if servidor_on == 'localhost':

            try:
                #se existir o arquivo "bancoOnlineBCK.sql" apaga
                #renomear o arquivo  "bancoOnline.sql" para "bancoOnlineBCK.sql"
                #realizar um dump do onlineLocal para bancoOnline.sql
                
                getoutput('sudo rm /usr/lib/'+self.versaoPython+'bancoOnlineBCK.sql')                                               #apaga o arquivo de backup
                getoutput('sudo cp /usr/lib/'+self.versaoPython+'bancoOnline.sql /usr/lib/'+self.versaoPython+'bancoOnlineBCK.sql') #copia o arquivo de banco atual para fazer um backup

                #getoutput('sudo mysqldump --databases --routines testescaio > /usr/lib/'+self.versaoPython+'/BancoOnline.sql')
                getoutput('sudo mysqldump --databases --routines onlineLocal > /usr/lib/'+self.versaoPython+'/bancoOnline.sql')     #Realiza um dump do banco online local
                sleep(5)

                getoutput('sudo cp /usr/lib/'+self.versaoPython+'bancoOnline.sql /usr/lib/'+self.versaoPython+'bancoOnlineBCK.sql') #Atualiza o backup do banco
                
                #getoutput('sudo mysqldump --databases BancoOffline > /usr/lib/'+self.versaoPython+'/BCK.sql')
                getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')
                sleep(5)
                getoutput('sudo chmod 777 /mnt/CLP/Shell')
            except:pass

        else:        
            
            try:
                getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')
                getoutput('sudo chmod 777 /mnt/CLP/Shell')
            except:pass

        
        # Cria o arquivo auxiliar
        try:open('/usr/lib/'+self.versaoPython+'/Desligado', "w")
        except:pass

        # Verifica se a pasta onde ficam os relatórios existe
        # Se não, cria
        if    path.isdir('/home/pi/Report'): pass
        else: makedirs('/home/pi/Report')

        # Envia o relatório para a pasta 
        try:getoutput("sudo cp /mnt/CLP/Shell /home/pi/Report/"+str(datetime.now().strftime('%Y%m%d%H%M'))) 
        except:pass

        # Reinicia
        system("reboot")
                
    # Registro de eventos do Gateway
    def eventosGateway(self, evento, estado):

        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") > '2018-01-01 00:00:00':

            histEventoGate           = eventoHistorico()
            histEventoGate.codEvento = evento
            histEventoGate.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if estado:
                #Registro de evento de gateway no histórico
                for evento in self.evntsGateway:
                    if evento.codEvntGate == histEventoGate.codEvento:
                        if not evento.sinalizadoGate or evento.sinalizadoGate == 0:
                            evento.sinalizadoGate = True
                            print('\nOcorreu o evento:', evento.nomeEvntGate)
                            self.histGate.append(histEventoGate)
                            
            else:
                for evento in self.evntsGateway:
                    if evento.codEvntGate == histEventoGate.codEvento:
                        if evento.sinalizadoGate or evento.sinalizadoGate == 1:
                            evento.sinalizadoGate = False
                            #print(evento.nomeEvntGate, ', Estado:', evento.sinalizadoGate)
                            #self.histGate.append(histEventoGate)
      
    def atualizarHora(self):

        # Tenta atualizar a hora dos sistema até conseguir
        while 1:
            sleep(0.5)
            try:
                getoutput("sudo ntpd -gq")
                getoutput("sudo hwclock -w")
                getoutput("date; sudo hwclock -r")
                break
            except:print_exc()

    def getVersao(self, arqINI, arqOFF, supervisor, classes, atualizacao):

        # Coleta as versões dos arquivos e guarda em variáveis
        # A versão dos arquivos se encontra em diferentes lugares
        # Dependendo do tipo arquivo:
        # Arquivos .py : A primeira linha comentada do programa é a versão
        # Arquivos .ini: Última linha com a chave [versao]
        # Arquivo  .exe: Envia sua versão ao MAIN (supervisor)
        # Arquivo  .sql: É armazenado na tabela Nuvem_Gateway, no campo verRdBDOff
    
        mysql = MySQL(arqINI, arqOFF)

        if not atualizacao:

            t = 0
            while t < 3:
                try:    
                    config_on = configparser.ConfigParser()
                    config_on.read(arqINI)
                    self.verArqINI         = config_on['database']['versao']
                    break
                except:
                    t+=1
                    print_exc()

            t = 0
            while t < 3:
                try:
                    config_off = configparser.ConfigParser()
                    config_off.read(arqOFF)
                    self.verArqOff         = config_off['database']['versao']
                    break
                except:
                    t+=1
                    print_exc()

            t = 0
            SQL = "SELECT verRdBDOff FROM Nuvem_Gateway"
            while t < 3:
                try:
                    self.verBDOff, = mysql.pesquisarBD(SQL,False)
                    self.verBDOff = self.verBDOff['verRdBDOff']
                    break
                except:
                    t+=1
                    print_exc()

            try:
                arq                    = open('/home/pi/CLP.py','r')
                lines                  = arq.readlines()
                self.verCLP            = ((lines[0])[8:20])
                arq.close()
            except: print_exc()

            try:
                self.verSuper          = supervisor
            except: print_exc()

            try:
                self.verClasses        = classes
            except: print_exc()

            try:
                arq = open('/usr/lib/'+self.versaoPython+'/MAIN.py','r')
                lines = arq.readlines()
                self.verMain = ((lines[0])[8:20])
                arq.close()
            except: print_exc()

        else:
            
            t = 0
            while t < 3:
                try:
                    config_on = configparser.ConfigParser()
                    config_on.read(arqINI)
                    self.verArqINI         = config_on['database']['versao']
                    break
                except:
                    t+=1
                    print_exc()

            t = 0
            while t < 3:
                try:
                    config_off = configparser.ConfigParser()
                    config_off.read(arqOFF)
                    self.verArqOff         = config_off['database']['versao']
                    break
                except:
                    t+=1
                    print_exc()

            try:
                arq                    = open('/home/pi/CLP.py','r')
                lines                  = arq.readlines()
                self.verCLP            = ((lines[0])[8:20])
                arq.close()
            except: print_exc()

    def setVersao(self, arqINI, arqOFF):

        # Envia as versões dos arquivos ao banco da dados online 

        mysql = MySQL(arqINI, arqOFF)

        print("\n2º - Enviando versões ao banco online\n")

        SQL  = "UPDATE Nuvem_Gateway SET "
        SQL += "verRdBDOff           = '" + self.verBDOff + "', "
        SQL += "verRdMain            = '" + self.verMain + "', "
        SQL += "verRdClasses         = '" + self.verClasses + "', "
        SQL += "verRdSuper           = '" + self.verSuper + "', "
        SQL += "verRdConnOff         = '" + self.verArqOff + "', "
        SQL += "verRdConnOn          = '" + self.verArqINI + "', "
        SQL += "verRdCLP             = '" + self.verCLP + "' "
        SQL += "WHERE Cod_Gateway    = '" + self.noSerie + "'"

        try:mysql.executaQueryBD(SQL,True)
        except:pass

    # pega a porta tty que esta sendo usado para comunicação serial    
    def getUSB(self):

        try:
            lista_de_disp = getoutput("sudo ls /dev | grep ttyUSB")

            for usb in lista_de_disp.split():

                #a = getoutput("sudo dmesg | grep -i "+usb+"")

                #b = comp("[^:]*\snow\s\w+\s\w+\s"+i+"")

                #c = b.findall(a)

                #c.reverse()

                info_disp_conectado = getoutput("sudo udevadm info --query=symlink /dev/"+usb+"")

                nomePadrao = comp("usb-[^:]*-i")
                
                nomeEncontrado = nomePadrao.findall(info_disp_conectado)
                #if 'ch341' in c[0]: return i
                if 'Serial' in nomeEncontrado[0]: return usb 
        except:
            print_exc()
            return 'Not Found' # PROVISÓRIO
            
    def verpOnti(self, arqINI, arqOFF):

        # Verifica se a classe de comunicação serial pOnti será usada
        mysql = MySQL(arqINI, arqOFF)
        
        t = 0

        while t < 3:
            try:
                SQL = "SELECT pOnti,pOnti_Timeout_Conexao FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
                usingpOnti = mysql.pesquisarBD(SQL,True)
        
                if usingpOnti[0]['pOnti']:

                    SQL = "SELECT Valor_Parametro FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina WHERE Cod_Maquina = '"+str(self.codMaquina)+"' AND Cod_Parametro = '"+str(11)+"'"
                    tempo = mysql.pesquisarBD(SQL,True)
                    
                    return usingpOnti[0]['pOnti'], usingpOnti[0]['pOnti_Timeout_Conexao'], tempo[0]['Valor_Parametro']

                else: return False, 0,0
            except:
                t += 1

        return False, 0,0
    
    def verificarRegistros(self, arqINI, arqOFF):

        # Verifica se existem dados a enviar 

        if rede.conectadoInternet():

            if len(self.histVarNaoEnviado)      == 0  and \
               len(self.histEventoNaoEnviado)   == 0  and \
               self.verificaVar(arqINI, arqOFF) == 0  and \
               self.verificaEvt(arqINI, arqOFF) == 0:
                return True
            else: return False

        else:
            if len(self.histVarNaoEnviado)      == 0  and \
               len(self.histEventoNaoEnviado)   == 0:
                return True
            else: return False

    def print(self, arqINI, arqOFF):

        # Exibe informações de memória e quantidade de dados históricos online e offline 
        
        #if not self.verificarRegistros(arqINI,arqOFF):

        print('PARA DBON:  Variaveis: {}   |   Eventos: {}   |   EventosGate: {}'.format(str(len(self.histVarNaoEnviado)).zfill(4),str(len(self.histEventoNaoEnviado)).zfill(4), str(len(self.histGate)).zfill(4)))
        print('PARA DBOFF: Variaveis: {}   |   Eventos: {}   |   EventosGate: {}'.format(str(self.verificaVar(arqINI, arqOFF)).zfill(4), str(self.verificaEvt(arqINI, arqOFF)).zfill(4), str(self.verificaEvtGate(arqINI, arqOFF)).zfill(4)))

        sleep(1)
           
    def memory(self):

        # Monitora memória do Gateway utilizada 
        try:
            cmd = getoutput(['free'])
            r = comp(r'\d{6}')
            valMem = r.findall(cmd)
            percentage = (int(valMem[0])-int(valMem[5]))*92/int(valMem[0])
        except: percentage = 0
        
        return int(percentage)
    
    def memory_disk(self):

        # Monitora memória em ramdisk utilizada 

        cmd = getoutput(['df -h -l /mnt/ramdisk'])
        total = cmd[cmd.find('% /')-2:-14]

        return int(total)

    def temperature_disk(self, arqINI, arqOFF):
        
        # Monitora a temperatura do processador do Gateway 

        try:
            temp = getoutput('sudo vcgencmd measure_temp')
            temp = temp[5:9]

            # Retirado desligamento por temperatura
            # Ao alcançar determinado valor o Rasp desacelera
            # Para resfriar CPU
            if int(temp[0:2]) > 85: self.eventosGateway(1, True)
            else:                   self.eventosGateway(1, False)
        
            return temp
        except:
            print_exc()
            return '00.0'

    # Tenta remover da pasta principal arquivos com o nome "reiniciado"
    # Se algum deles for encontrado no sistema ao reiniciar,
    # Significa que uma cópia do banco no backup foi usada
    def clearTry(self):

        try:
            remove('/usr/lib/'+self.versaoPython+'/Reiniciado')
            self.eventosGateway(24, True)
        except:
            try:
                remove('/usr/lib/'+self.versaoPython+'/Reiniciado1')
                self.eventosGateway(24, True)
            except:
                try:
                    remove('/usr/lib/'+self.versaoPython+'/Reiniciado2')
                    self.eventosGateway(24, True)
                except:
                    try:
                        remove('/usr/lib/'+self.versaoPython+'/Reiniciado3')
                        self.eventosGateway(24, True)
                    except:
                        try:
                            remove('/usr/lib/'+self.versaoPython+'/Reiniciado4')
                            self.eventosGateway(24, True)
                        except: self.eventosGateway(24, False)

    # Pega o último TimeStamp registrado pelo programa
    # E verifica com a hora atual para saber quantos minutos
    # Passou-se desde a última vez que foi desligado
    def pegaTimeStamp(self, arqINI, arqOFF):

        mysql = MySQL(arqINI, arqOFF)
        
        try:
            SQL = "SELECT Ultima_Conexao_Servidor FROM Nuvem_Gateway WHERE Cod_Gateway = '"+str(self.noSerie)+"'"
            a, = mysql.pesquisarBD(SQL,True)
            a  = a['Ultima_Conexao_Servidor']

            b = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            date1 = int(datetime.strptime(b, '%Y-%m-%d %H:%M:%S').strftime("%s"))
            date2 = int(datetime.strptime(a, '%Y-%m-%d %H:%M:%S').strftime("%s"))
            
            if (date1 - date2) > 300: self.peqInterDesligado = True
            
        except:pass

    def checkSize(self):
        # Verifica o tamanho do arquivo onde está sendo salvo
        # os print do Shell
        # Se o tamanho for maior que 9mb o arquivo será salvo
        # (O limite máximo do tamanho das pasta )
        try:
            arq = stat('/mnt/CLP/Shell')

            if int(arq.st_size) > 9000000: return True
            else:                          return False

        except: return False

    def ciclo(self, arqINI, arqOFF, LDO):
        
        global interromper
        global wdt

        setVariaveis = 0
        solucaoErro  = 0
        self.LDO     = LDO
        wdt[10]      = 1
        controleCLP  = 1
        self.clearTry()
        
        #self.pegaTimeStamp(arqINI, arqOFF)
        
        # Função auxiliar de saída do CLP
        def getDigitalOut(SD,IC,IL):
            self.LDO               = SD
            self.geradorCloro.LIC  = IC
            self.variaveisInternas.variaveisInternas(IL)
            
            
        perSec = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # O primeiro registro do histórico de Gateway é colocado ao inicializar
        for maq in self.maquina:
            for pac in maq.pacotesHistVar:
                self.__putHistoricoInRAM(pac,perSec)
                
        while 1:

            wdt[10] = 1
            
            while not interromper: #Interromper
                try:
                    
                    # identifica a mudança mínima de segundos para chamar o histórico
                    if perSec != datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
                        perSec = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.historicoVarInRAM(perSec)

                    # Se acabar a energia o programa verifica e envia registros e eventos ao BD antes de finalizar
                    while self.ctrl.getAcabouEnergia():
                        
                        self.salvarTudo(arqINI, arqOFF)

                    # Vefifica se as Saídas Digitais estão sendo usadas
                    if self.useSD >0: self.saidasDigitais.escreverSaidas(self.LDO)

                    # Verifica se as Entradas Digitais estão sendo usadas
                    if self.useED >0:

                        try:
                            self.entradasDigitais.entradasDigitais()
                            self.eventosGateway(10, False)
                        except: self.eventosGateway(10, True)
        
                    
                    #self.print(arqINI,arqOFF)
                    
                    self.eventosGateway(27, False)

                    # Coleta os dados das Threads
                    for maq in self.maquina: ED, SD, EA, SA, IL, IC, MB, SI, IE = maq.getValVariaveis(arqINI, arqOFF)

                    maq.verificaEventos(self.histVarNaoEnviado, self.histEventoNaoEnviado, self.info, arqINI, arqOFF)

                    # Verifica se as variáveis internas estão sendo usadas                        
                    if self.useVI >0: self.variaveisInternas.variaveisInternas(IL)
                   
                    # Lê o arquivo CLP

                    '''
                    - solucaoErro:

                      *0 -> não há erros sendo tratados ou foram tratados os erros.
                      *1 -> ignorou usuario e setou variaveis na tentativa de resolver erro.
                      *2 -> buscou arquivo de backup ou home pi e ignorou usuario setando variaveis.
                      *3 -> buscou arquivo de backup-1 e ignora usuario.
                      
                    - Abrir o arquivo CLP:
                      *Caso haja um erro:
                         - sinaliza o erro.
                         - Verifica se foi atualizado:
                           *sim: busca a versao antiga do backup e sinaliza que buscou em backup e seta variaveis.
                           *nao: busca o arquivo em home pi, seta variaveis:
                               -caso nao tenha um arquivo no home pi busca de backup e sinaliza.
                               
                    - Verrificar se foi atualizado:
                      *Em caso de atualização verifica se usuario quer que set as variaveis:
                          - sim: atribui a variavel " self.inicializar " o valor 0.
                          - não: atribui a variavel " self.inicializar " o valor 1 ou pass.

                    - Executar o arquivo CLP:
                      *Se houver erro deve:
                          - Sinalizar o erro.
                          - Verificar se foi atualizado:
                            *Sim: seta as variaveis, sinaliza que busca resolver um problema, busca de backup a versao anterior
                            *nao: seta as variaveis, sinaliza que busca resolver um problema, busca de backup a versao anterior
                            
                    - Verificar se checksize é verdadeiro:
                      *sim: chama metodo salvartudo()
                      *nao: pass
                      
                    - Acabar com a inteiração do loop.
                    '''

                        
                    if controleCLP:
                        try: 
                            arq = open('/mnt/CLP/CLP.py','r')
                            CLP = arq.read()
                            resetVariaveis = int(CLP[34:35])
                            arq.close()
                            
                        except:
                            print_exc()
                            mensagem  = 'LÓGICA DE CONTROLE NÃO ESTÁ FUNCIONANDO !!!\n'
                            mensagem += 'CLP NÃO ENCONTRADO E OU VALOR NÃO IDENTIFICADO EM COMENTARIO CLP "INICIALIZAR\n".'
                            self.inicializar = 0
                            
                            print(mensagem)

                            getoutput('sudo chmod 777 /mnt/CLP')        
                            getoutput('sudo chmod 777 /home/pi')        
                                    
                            if self.clpAtualizado.isSet():
                                print('atualizado = ',self.clpAtualizado.isSet())
                                mensagem    = 'RECUPERANDO BACKUP DO CLP...\n'
                                solucaoErro = 2            
                                sleep(5)
                                getoutput('sudo rm /mnt/CLP/CLP.py')
                                getoutput('sudo rm /home/pi/CLP.py')
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /mnt/CLP/CLP.py')
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /home/pi/CLP.py')
                                getoutput('sudo chmod 777 /mnt/CLP/CLP.py')        
                                getoutput('sudo chmod 777 /home/pi/CLP.py')        
                                    
                            else:
                                getoutput('sudo rm /mnt/CLP/CLP.py')
                                print('removel CLP da ram e buscou no /home/pi')
                                sleep(5)
                                try:
                                    arq = open('/home/pi/CLP.py', 'r')
                                    arq.close()

                                    mensagem    = 'RECUPERANDO CLP DO DIRETORIO PRINCIPAL...\n'
                                    solucaoErro = 1

                                    getoutput('sudo cp /home/pi/CLP.py /mnt/CLP/CLP.py')
                                    getoutput('sudo chmod 777 /mnt/CLP/CLP.py')
                                    
                                except:
                                    mensagem    = 'O CLP NÃO FOI ENCONTRADO NO DIRETORIO PRINCIPAL, RECUPERANDO BACKUP...'                                    
                                    solucaoErro = 2

                                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /mnt/CLP/CLP.py')
                                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /home/pi/CLP.py')
                                    getoutput('sudo chmod 777 /mnt/CLP/CLP.py')        
                                    getoutput('sudo chmod 777 /home/pi/CLP.py')
                                    print_exc()
                                    
                            print(mensagem)
                            sleep(5)
                            break

                        if self.clpAtualizado.isSet() and resetVariaveis and not setVariaveis:
                            setVariaveis     = 1
                            self.inicializar = 0
                            
                        try:
                            exec(CLP + "\ngetDigitalOut(SD,IC,IL)")
                            self.eventosGateway(34, False)
                            self.ciclos.set()
                            solucaoErro = 0
                            
                        except:   
                            print_exc()
                            print('HÁ UM ERRO NO CLP!\n')
                            self.eventosGateway(34, True)
                            sleep(1)
                            self.ciclos.clear()
                            self.inicializar = 0

                            if solucaoErro >0:
                                getoutput('sudo chmod 777 /mnt/CLP')
                                getoutput('sudo chmod 777 /home/pi')
                                getoutput('sudo rm /mnt/CLP/CLP.py')
                                getoutput('sudo rm /home/pi/CLP.py')
                                
                            if solucaoErro == 0:
                                solucaoErro = 1
                                print('REDEFININDO VARIAVEIS DO CLP !')

                            elif solucaoErro == 1:
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /mnt/CLP/CLP.py')
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/CLP.py /home/pi/CLP.py')
                                solucaoErro = 2                        
                                
                                print('RECUPERANDO CLP DE BACKUP !\n')
                                self.getVersao(arqINI, arqOFF, None, None, True)
                                # Envia as versões dos arquivos ao banco de dados online
                                self.setVersao(arqINI, arqOFF)

                            elif solucaoErro == 2:
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/CLP.py /mnt/CLP/CLP.py')
                                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/CLP.py /home/pi/CLP.py')
                                solucaoErro = 3

                                print('RECUPERANDO CLP DE BACKUP-1\n')
                                self.getVersao(arqINI, arqOFF, None, None, True)
                                # Envia as versões dos arquivos ao banco de dados online
                                self.setVersao(arqINI, arqOFF)
                            
                            elif solucaoErro == 3:
                                
                                mensagem  = 'DESLIGANDO TODAS AS SAIDAS DIGITAIS ...\n'
                                mensagem += '\nTODOS OS BACKUPs DE CLP FALHARAM ESPERANDO ATUALIZAÇÃO DE CLP\n'
                                print(mensagem)
                                for propriedades in self.LDO:
                                    SD[propriedades] = 0
                                    
                                getDigitalOut(SD,IC,IL)

                                if self.clpAtualizado.isSet():self.clpAtualizado.clear()
                                    
                                controleCLP = 0
                
                    elif self.clpAtualizado.isSet() and solucaoErro == 3:
                        getoutput('sudo cp /home/pi/CLP.py /usr/lib/'+self.versaoPython+'/backup/CLP.py')
                        getoutput('sudo cp /home/pi/CLP.py /usr/lib/'+self.versaoPython+'/backup-1/CLP.py')
                        getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup/CLP.py')    
                        getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup-1/CLP.py')
                        
                        controleCLP = 1

                    if self.checkSize(): self.salvarTudo(arqINI, arqOFF)
                                
                    break                                      

                except:
                    sleep(1)
                    print_exc()
                    self.ciclos.clear()
      
    # Função que verifica a integridade a atualização
    # Se a atualização ocorreu corretamente, após 10 minutos
    # Será feita uma cópia dos arquivos da pasta principal para
    # A pasta de backup
    def verAtualizacao(self):

        start = 0
        end   = 0
        
        while 1:

            sleep(0.1)

            if self.ciclos.isSet():
    
                arq = open('/usr/lib/'+self.versaoPython+'/Iniciado','w')
                arq.close()
                start = tempor()
                end   = tempor()

                break

        end1   = 0
        start1 = 0
        trava  = False
        
        while 1:

            end = tempor()

            if self.ciclos.isSet():

                trava = False

                if (end-start) > 600:
                    self.saveBackup()

                    return
            else:

                end1 = tempor()

                if not self.ciclos.isSet():

                    if not trava:
                        start1 = tempor()
                        trava = True

                    if (end1-start1) > 60:

                        fromBackup = ['MAIN.py','classes.py','supervisor','connMySQL.ini','connMySQLOFF.ini','BCK.sql','CLP.py','SupervisorBits','restaurasupervisores']
                 
                        # Se o tempo de tentativas for excedido os arquivos movidos ao backup serão levados às pastas
                        
                        for i in fromBackup:
                            try:
                                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup/'+i)
                                
                                if i == 'CLP.py':
                                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /home/pi/'+i)
                                    getoutput('sudo cp /home/pi/'+i+' /mnt/CLP/'+i)
                                    getoutput('sudo chmod 777 /mnt/CLP/'+i)
                                
                                elif i == 'BCK.sql':
                                    
                                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)
                                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                                    #getoutput('mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/'+i)
                                    getoutput('mysql -u root offline < /usr/lib/'+self.versaoPython+'/'+i)
    
                                else:
                                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)    
                                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                                
                            except:print_exc()

                        self.salvarTudo(arqINI, arqOFF)
                        
    # Salva os arquivos atuais na pasta de backup               
    def saveBackup(self):

        try:getoutput("sudo cp /usr/lib/"+self.versaoPython+"/MAIN.py /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:getoutput("sudo cp /usr/lib/"+self.versaoPython+"/classes.py /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/supervisor /usr/lib/"+self.versaoPython+"/backup")
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/supervisor.new /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/SupervisorBits /usr/lib/"+self.versaoPython+"/backup")
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/SupervisorBits.new /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/connMySQL.ini /usr/lib/"+self.versaoPython+"/backup")
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/connMySQL.new /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/connMySQLOFF.ini /usr/lib/"+self.versaoPython+"/backup")
            getoutput("sudo cp /usr/lib/"+self.versaoPython+"/connMySQLOFF.new /usr/lib/"+self.versaoPython+"/backup")    
        except:pass
        try:getoutput("sudo cp /usr/lib/"+self.versaoPython+"/BCK.sql /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:getoutput("sudo cp /home/pi/CLP.py /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        try:getoutput("sudo cp /usr/lib/"+self.versaoPython+"/restaurasupervisores /usr/lib/"+self.versaoPython+"/backup")
        except:pass
        
        
    def sendHistEvntGateInRAM(self, arqINI, arqOFF):
        
        mysql = MySQL(arqINI, arqOFF)
        global wdt
        wdt[0] = 1

        #Envia os eventos do Gateway ao banco de dados offline
        for evntGate in self.histGate:

            sleep(0.1)
            wdt[0] = 1

            SQL  = "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES("
            SQL += "'" + str(self.noSerie) + "', "
            SQL += "'" + str(evntGate.codEvento) + "', "
            SQL += "'" + str(evntGate.timestamp) + "'"
            SQL += ")"

            try:
                if rede.conectadoInternet():
                    teste = mysql.executaQueryBD(SQL,True)
                    if teste != False:
                        self.histGate.remove(evntGate)
                    else: return
                else: return
            except:
                wdt[0] = 1
                return

    def sendHistEventoGateInRAMToDBOff(self, arqINI, arqOFF):
        
        mysql = MySQL(arqINI, arqOFF)
        global wdt

        wdt[0] = 1
        
        try:
            for registro in self.histGate:

                sleep(0.1)
                wdt[0] = 1
                
                SQL  = "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES ("
                SQL += "'" + str(self.noSerie) + "', "
                SQL += "'" + str(registro.codEvento) + "', "
                SQL += "'" + str(registro.timestamp) + "'"
                SQL += ")"

                try:
                    if not rede.conectadoInternet():
                        teste = mysql.executaQueryBD(SQL,False)
                        if teste != False:
                            self.histGate.remove(registro)
                        else:return
                    else: return
                except:
                    wdt[0] = 1
                    return

            return True

        except:
            wdt[0] = 1
            return False

    def sendHistEventoGateInDBOffToDBOn(self, arqINI, arqOFF):
        
        # Envia histórico de evento do banco offline para banco online 
        global wdt
        mysql = MySQL(arqINI, arqOFF)
        wdt[0] = 1

        SQL = "SELECT * FROM Nuvem_Historico_Eventos_Gateway"
        try:
            resposta = mysql.pesquisarBD(SQL,False)
            if resposta != False:pass
            else: return
        except:
            return

        for r in resposta:

            sleep(0.1)
            wdt[0] = 1

            SQL  = "INSERT INTO Nuvem_Historico_Eventos_Gateway (Cod_Gateway, Cod_Evento_Gateway, TimeStamp) VALUES ("
            SQL += "'" + str(r['Cod_Gateway']) + "', "
            SQL += "'" + str(r['Cod_Evento_Gateway']) + "', "
            SQL += "'" + str(r['TimeStamp']) + "'"
            SQL += ")"

            try:
                if rede.conectadoInternet():
                    teste = mysql.executaQueryBD(SQL,True)
                    if teste != False: pass
                    else: return
                else: return
            except:
                wdt[0] = 1
                return
                
            SQL  = "DELETE FROM Nuvem_Historico_Eventos_Gateway WHERE "
            SQL += "Cod_Gateway = '" + str(r['Cod_Gateway']) + "'"
            SQL += " AND "
            SQL += "Cod_Evento_Gateway = '" + str(r['Cod_Evento_Gateway']) + "'"
            SQL += " AND "
            SQL += "TimeStamp = '" + str(r['TimeStamp'])  + "'"

            try:
                teste = mysql.executaQueryBD(SQL,False)
                if teste != False:pass
                else: return
            except:
                wdt[0] = 1
                return
        
    def verificaEvtGate(self, arqINI, arqOFF):

        # Verifica se existe historico de variaveis no banco offline 

        mysql = MySQL(arqINI, arqOFF)

        SQL = "SELECT COUNT(*) FROM Nuvem_Historico_Eventos_Gateway"

        count = mysql.executaCountBD(SQL,False)
        
        return int(count)

    # Função de envio de dados
    def sendOff(self, arqINI, arqOFF):

        global wdt
        global interromper
        
        trava  = False
        start  = 0
        end    = 0
        wdt[0] = 1
        
        while not self.usandoPonti.isSet():

            wdt[0] = 1
            sleep(0.5)

            try:
                self.eventosGateway(26, False)
                
                if (end-start) >= 3000: trava = False
                
                if not trava:
                    
                    # Verifica se a memória RAM é >= 65, se houver, limpa a RAM
                    if (int(self.memory())) >= 75:
                        
                        getoutput('echo 3 | sudo tee /proc/sys/vm/drop_caches')
                        start = tempor()
                        trava = True

                        print('\nLimpou a memória:', datetime.now().strftime("%Y/%m/%d %H:%M"))

                        # Se for maior que 75 é gerado um evento
                        if (int(self.memory())) >= 85:

                            self.eventosGateway(2, True)
                            
                            # Verifica se a memória RAM é >= 80, para assim, reiniciar
                            if (int(self.memory())) >= 92:

                                if not interromper:
                                    self.eventosGateway(0, True)
                                    interromper = True
                                    self.setBit.set()
                                    self.salvarTudo(arqINI, arqOFF)
                                
                            else: self.eventosGateway(0, False)
                        else:     self.eventosGateway(2, False)

                end = tempor()

            except: wdt[0] = 1
            
            try:
                # Envio de dados para banco online ou do banco offline para a ram 
                if rede.conectadoInternet():
                    for evt in self.evntsGateway:
                        if evt.codEvntGate == 3:
                            if evt.sinalizadoGate: gateway.eventosGateway(self, 18, True)
                            else:                  gateway.eventosGateway(self, 18, False)
            
                    self.eventosGateway(3, False)
                    if len(self.histEventoNaoEnviado)       > 0 : self.sendHistEventoInRAM(arqINI, arqOFF)
                    if len(self.histVarNaoEnviado)          > 0 : self.sendHistoricoVarInRAM(arqINI, arqOFF)
                    if len(self.histGate)                   > 0 : self.sendHistEvntGateInRAM(arqINI, arqOFF)
                    if self.verificaVar(arqINI, arqOFF)     > 0 : self.sendHistoricoVarInDBOff(arqINI, arqOFF)
                    if self.verificaEvt(arqINI, arqOFF)     > 0 : self.sendHistEventoInDBOffToDBOn(arqINI, arqOFF)
                    if self.verificaEvtGate(arqINI, arqOFF) > 0 : self.sendHistEventoGateInDBOffToDBOn(arqINI, arqOFF)

                    for maq in self.maquina:
                        maq.envioEventoOn(arqINI, arqOFF)
                        maq.envioEvento(arqINI, arqOFF)
                                       
                # Sinaliza que não há internet
                else: self.eventosGateway(3, True)
                
                if self.ctrl.getAcabouEnergia() or not rede.conectadoInternet():

                    self.sendHistEventoInRAMToDBOff(arqINI, arqOFF)
                    #self.sendHistoricoVarInRAMToBDOff(arqINI, arqOFF)
                    self.sendHistoricoVarInRAM(arqINI, arqOFF)
                    self.sendHistEventoGateInRAMToDBOff(arqINI, arqOFF)
                    
                    for maq in self.maquina:
                        maq.envioEvento(arqINI, arqOFF)
                
            except: wdt[0] = 1
              
    def attIP(self, arqINI, arqOFF):

        # Atualiza as informações de IP

        self.endIP_externo = rede.ipExterno()
        self.endIP_atual   = rede.ipAtual()

        mysql = MySQL(arqINI, arqOFF)
        
        SQL = "UPDATE Nuvem_Gateway SET "
        SQL += "EndIP_Externo = '" + self.endIP_externo + "', "
        SQL += "Off_line = 0, "
        SQL += "EndIP_Local = '" + self.endIP_atual + "' "
        SQL += "WHERE Cod_Gateway = '" + self.noSerie + "'"

     
        while 1:
            sleep(0.5)
            try:
                mysql.executaQueryBD(SQL,True)
                break
            except:pass
                
    def sendHistEventoInRAM(self, arqINI, arqOFF):

        # Envia histórico de evento da ram para banco online 
        global wdt
        mysql = MySQL(arqINI, arqOFF)
        wdt[0] = 1
        
        for registro in self.histEventoNaoEnviado:

            sleep(0.1)
            wdt[0] = 1
            
            SQL  = "INSERT INTO Nuvem_Historico_Eventos (Cod_Evento, TimeStamp) VALUES ("
            SQL += str(registro.codEvento) + ", "
            SQL += "'" + str(registro.timestamp) + "'"
            SQL += ")"

            try:
                if rede.conectadoInternet():
                    teste = mysql.executaQueryBD(SQL,True)
                    if teste != False:
                        self.histEventoNaoEnviado.remove(registro)
                    else: return
                else: return
            
                for registros in self.info:
                    
                    if registros.geraEmail and len(registros.email) > 0:

                        subject = registros.subject
                        message = registros.message
                                       
                        sendemail(registros.email, [], registros.subject, registros.message)
                        self.info.remove(registros)
            except:
                wdt[0] = 1
                return
             
    def sendHistEventoInRAMToDBOff(self, arqINI, arqOFF):

        # Envia histórico de evento da ram para banco offline      
        global wdt
        mysql = MySQL(arqINI, arqOFF)
        wdt[0] = 1
        
        for registro in self.histEventoNaoEnviado:

            sleep(0.1)
            wdt[0] = 1

            SQL  = "INSERT INTO Nuvem_Historico_Eventos (Cod_Evento, TimeStamp) VALUES ("
            SQL += str(registro.codEvento) + ", "
            SQL += "'" + str(registro.timestamp) + "'"
            SQL += ")"

            try:
                if not rede.conectadoInternet():   
                    teste = mysql.executaQueryBD(SQL,False)
                    if teste != False:
                        self.histEventoNaoEnviado.remove(registro)
                    else: pass
                else: return
            except:
                wdt[0] = 1
                return

    def sendHistEventoInDBOffToDBOn(self, arqINI, arqOFF):

        # Envia histórico de evento do banco offline para banco online 
        global wdt
        mysql = MySQL(arqINI, arqOFF)
        wdt[0] = 1

        SQL = "SELECT * FROM Nuvem_Historico_Eventos"
        try:
            resposta = mysql.pesquisarBD(SQL,False)
            if resposta != False:pass
            else: return
        except:
            wdt[0] = 1
            return

        for r in resposta:

            sleep(0.1)
            wdt[0] = 1

            SQL  = "INSERT INTO Nuvem_Historico_Eventos (Cod_Evento, TimeStamp) VALUES ("
            SQL += str(r['Cod_Evento']) + ", "
            SQL += "'" + r['TimeStamp'] + "'"
            SQL += ")"

            try:
                if rede.conectadoInternet():
                    teste = mysql.executaQueryBD(SQL,True)
                    if teste != False:pass
                    else: return
                else: return
            
                for registros in self.info:
                    
                    if registros.geraEmail and len(registros.email) > 0:

                        subject = registros.subject
                        message = registros.message
                                       
                        sendemail(registros.email, [], registros.subject, registros.message)
                        self.info.remove(registros)

            except:
                wdt[0] = 1
                return
            
            SQL  = "DELETE FROM Nuvem_Historico_Eventos WHERE "
            SQL += "Cod_Evento = " + str(r['Cod_Evento'])
            SQL += " AND "
            SQL += "TimeStamp = '" + r['TimeStamp'] + "'"

            try:
                teste = mysql.executaQueryBD(SQL,False)
                if teste != False:pass
                else:return
            except:
                wdt[0] = 1
                return
           
    def sendHistoricoVarInRAM(self, arqINI, arqOFF):

        global wdt
        mysql             = MySQL(arqINI, arqOFF)
        wdt[0]            = 1
        itensParaRemover  = []
        valoresINSERT     = ''
        limiteDeEnvio     = 300
            
        for registro in self.histVarNaoEnviado:

            sleep(0.005)
            wdt[0] = 1

            itensParaRemover.append(registro)
            
            valoresINSERT += "("+'"'+str(registro.codPropriedade)+'"'+","+'"'+str(registro.valorPropriedade)+'"'+","+'"'+str(registro.timestamp)+'"'+"),"

            limiteDeEnvio -= 1

            if limiteDeEnvio <= 0:
                break
            
        historicoGeral  = "INSERT INTO Nuvem_Historico_Propriedades_Maquinas (Cod_Propriedade, Valor_Propriedade, TimeStamp) VALUES "+valoresINSERT[0:-1]
        #historicoMensal = "INSERT INTO Hist_Prop_Maq201905 (Cod_Propriedade, Valor_Propriedade, TimeStamp) VALUES "+valoresINSERT[0:-1]

        try:
            if rede.conectadoInternet():
                enviaHistoricoGeral  = mysql.executaQueryBD(historicoGeral,True)
                
            else:
                enviaHistoricoGeral  = mysql.executaQueryBD(historicoGeral,False)  

            if enviaHistoricoGeral:        
                for iten in itensParaRemover:
                    self.histVarNaoEnviado.remove(iten)
                    
            else: return
            
        except:
            wdt[0] = 1
            return
                    
    def sendHistoricoVarInDBOff(self, arqINI, arqOFF):

        # Envia historico de variaveis do banco offline para o banco online 
        global wdt
        mysql         = MySQL(arqINI, arqOFF)
        wdt[0]        = 1
        valoresINSERT = ''
        valoresDELETE = ''
        limiteDeEnvio = 300
        
        SQL =  "SELECT * FROM Nuvem_Historico_Propriedades_Maquinas LIMIT 300"
        try:
            resultado = mysql.pesquisarBD(SQL,False)
            if resultado != False:pass
            else: return
        except:
            wdt[0] = 1
            return

        for r in resultado:

            
            wdt[0] = 1
            
            valoresINSERT += "("+'"'+str(r['Cod_Propriedade'])+'"'+","+'"'+str(r['Valor_Propriedade'])+'"'+","+'"'+str(r['TimeStamp'])+'"'+"),"
            valoresDELETE += "Cod = "+str(r['Cod'])+" or "

            limiteDeEnvio -= 1
            if limiteDeEnvio <= 0:
                break
            
        historicoGeral  = "INSERT INTO Nuvem_Historico_Propriedades_Maquinas (Cod_Propriedade, Valor_Propriedade, TimeStamp) VALUES "+valoresINSERT[0:-1]
        historicoBDOff  = "DELETE FROM Nuvem_Historico_Propriedades_Maquinas WHERE "+valoresDELETE[0:-4]

        try:
            if rede.conectadoInternet():

                enviaHistoricoGeral  = mysql.executaQueryBD(historicoGeral,True)  
                
                if enviaHistoricoGeral:
                    
                    deletaHistoricoBDOff = mysql.executaQueryBD(historicoBDOff,False)                        
                    if deletaHistoricoBDOff:
                        pass

                    else: deletaHistoricoBDOff = mysql.executaQueryBD(historicoBDOff,False)
                    
                else: return
                
            else: return
        except:
            wdt[0] = 1
            return

    def verificaVar(self, arqINI, arqOFF):

        # Verifica se existe historico de variaveis no banco offline 

        mysql = MySQL(arqINI,arqOFF)

        SQL = "SELECT COUNT(*) FROM Nuvem_Historico_Propriedades_Maquinas"
        
        count = mysql.executaCountBD(SQL,False)
        
        return int(count)

    def verificaEvt(self, arqINI, arqOFF):

        # Verifica se existe historico de variaveis no banco offline 

        mysql = MySQL(arqINI, arqOFF)

        SQL = "SELECT COUNT(*) FROM Nuvem_Historico_Eventos"

        count = mysql.executaCountBD(SQL,False)
        
        return int(count)

    # Verifica se precisa fazer algum registro no histórico
    def historicoVarInRAM(self, hora):
        
        horaAtual = hora

        # tranforma a data atual e a última data de registro em segundos
        # e subtrai, se for >= o tempo de registro do histórico adiciona o registro
        for maq in self.maquina:
            for pac in maq.pacotesHistVar:

                # Ano e mês
                a = date(int(pac[0].ultTimestamp[0:4]),int(pac[0].ultTimestamp[5:7]),1)
                b = date(int(horaAtual[0:4]),int(horaAtual[5:7]),1)

                # Dias,horas,minutos e segundos
                c = timedelta(days    = int(horaAtual[8:10]),
                              hours   = int(horaAtual[11:13]),
                              minutes = int(horaAtual[14:16]),
                              seconds = int(horaAtual[17:19]))

                d = timedelta(days    = int(pac[0].ultTimestamp[8:10]),
                              hours   = int(pac[0].ultTimestamp[11:13]),
                              minutes = int(pac[0].ultTimestamp[14:16]),
                              seconds = int(pac[0].ultTimestamp[17:19]))

                # Subtraí um ano/mês pelo outro
                e = (b-a).total_seconds()

                # Subtraí os dias/horas/minutos e segundo pelo outro
                f = (c-d).total_seconds()

                # Subtraí um pelo outro
                g = abs(f-e)

                # Se for maior que o tempo de registro da propridade, marca-se o evento
                if int(g) >= int(pac[0].tempoRegistroSegundos): self.__putHistoricoInRAM(pac, horaAtual)
                            
    def __putHistoricoInRAM(self, pacoteDoHistorico, now):

        # Gera dado de histórico
        # Adiciona ao historico na ram, cada uma das variaveis do pacote selecionado
        # Guarda o último timestamp do histórico para ser verificado com o tempo atual
        
        for var in pacoteDoHistorico:

            if var.ultTimestamp != now and now > '2019-01-01 00:00:00':

                varHist                  = variavelHistorico()
                varHist.codPropriedade   = var.cod
                varHist.valorPropriedade = var.valor
                varHist.timestamp        = now
                var.ultTimestamp         = now
            
                self.histVarNaoEnviado.append(varHist)

    def enviaVariaveis(self, arqINI, arqOFF, online):

        # Enviar as variaveis das maquinas para o site 
        
        connPMaq = None
        connSens = None
     
        # Pega o timestamp referencia 
        try: connPMaq = self.getTelaPMaq(arqINI,arqOFF)
        except: pass
        
        try: connSens = self.getTelaSens(arqINI,arqOFF)
        except: pass
        
        # Chama as threads que enviam as variaveis 
        for maq in self.maquina:
            
            if connPMaq != None:

                # Flag que indica se Thread já esta rodando
                if not self.enviarVar.isSet():
             
                    self.thrpmaq = Thread(name='sendPMaq' + maq.nome,
                                     target=self.__thEnviaVar,
                                     args=(maq, connPMaq, arqINI, arqOFF))

                    self.thrpmaq.start()
                    self.enviarVar.set()
                    print("\nenvia Variaveis\n")
                
            if connSens != None:

                thrsens = Thread(name='sendSens' + maq.nome,
                 target=self.__thEnviaCodSen,
                 args=(maq, connSens, arqINI, arqOFF))

                print('maquina:',maq,' codigoSensor:',connSens,'\n')

                thrsens.start()
                print("\nenvia CodSensores\n")      

    def __thEnviaVar(self, maq, TimestampRef, arqINI, arqOFF):

        # Sinaliza que está enviando dados 
        
        trava=None
        
        while 1:
            
            inicio = datetime.now()
            Timestamp = self.getTelaPMaq(arqINI, arqOFF)
            #print('\nEnviando variaveis maq:', maq.nome, 'TimestampRef:', TimestampRef, 'Timestamp:', Timestamp, 'Cont:', cont)
            
            if  Timestamp != TimestampRef:
                trava = False
                TimestampRef = Timestamp            

            if  TimestampRef == Timestamp:
                if not trava:
                    start = tempor()
                    trava=True
        
                end = tempor()
                
                if (end - start)>180: break
            
            # Envia as variaveis 
            while 1:
                try:
                    maq.sendVariaveis(arqINI, arqOFF)
                    maq.envioForcado(arqINI, arqOFF)
                    break
                except: print_exc()

            pausa = maq.intervalo-(datetime.now()-inicio).total_seconds()

            #print('subtração inicio final = ',(datetime.now()-inicio).total_seconds())
            #print('pausa = ',pausa)
            
            if pausa < 15:
                pausa = 15

            sleep(pausa)
        
        # Deleta registro da requisição de dados 
        mysql = MySQL(arqINI, arqOFF)
        
        SQL = "DELETE FROM Nuvem_Tela_Usuario "
        SQL += "WHERE Cod_Gateway = '" + str(self.noSerie) + "'"
        while 1:
            try:
                mysql.executaQueryBD(SQL,True)
                break
            except:pass

        self.enviarVar.clear()
                    
    def __thEnviaCodSen(self, maq, TimestampRef, arqINI, arqOFF):

        # Sinaliza que está enviando dados 

        trava=None
        
        while 1:
            sleep(maq.intervalo)            
            Timestamp = self.getTelaSens(arqINI, arqOFF)
            #print('\nEnviando variaveis maq:', maq.nome, 'TimestampRef:', TimestampRef, 'Timestamp:', Timestamp, 'Cont:', cont)

            if  Timestamp != TimestampRef:

                trava = False
                TimestampRef = Timestamp                
                
            if  TimestampRef == Timestamp:
                   
                if not trava:
                    start = tempor()
                    trava=True
        
                end = tempor()
                
                if (end - start)>180: break
                
            # Envia as variaveis 
            while 1:
                try:
                    maq.sendValSensores(arqINI, arqOFF)
                    break
                except:pass
                
        # Deleta registro da requisição de dados 
        mysql = MySQL(arqINI, arqOFF)
        
        SQL = "DELETE FROM Nuvem_Tela_Usuario "
        SQL += "WHERE Cod_Gateway = '" + str(self.noSerie) + "'"
        while 1:
            try:
                mysql.executaQueryBD(SQL,True)
                break
            except:pass

    def getTelaPMaq(self, arqINI, arqOFF):

        # Pegar o timestamp da tabela Nuvem_Tela_Usuario.
        # Para o a tela que monitora propriedades_maquina

        tela = 'princ_var_gates.php'
        mysql = MySQL(arqINI, arqOFF)

        SQL  = "SELECT * FROM Nuvem_Tela_Usuario "
        SQL += "WHERE Cod_Gateway = '" + str(self.noSerie) + "'"
        SQL += "AND Tela = '" + str(tela) + "'"
        SQL += "ORDER BY Timestamp DESC"

        try:
            r = mysql.pesquisarBD(SQL,True)
        except: pass
        
        Timestamp  = None
        
        try:
            if len(r) > 0:
                if r[0]['Timestamp'] != None: Timestamp = r[0]['Timestamp']

        except:pass

        return Timestamp

    def getTelaSens(self, arqINI, arqOFF):

        # Pegar o timestamp da tabela Nuvem_Tela_Usuario.
        # Para o a tela que monitora os sensores disponiveis.

        tela = 'sensores.php'
        mysql = MySQL(arqINI, arqOFF)

        SQL  = "SELECT * FROM Nuvem_Tela_Usuario "
        SQL += "WHERE Cod_Gateway = '" + str(self.noSerie) + "'"
        SQL += "AND Tela = '" + str(tela) + "'"
        SQL += "ORDER BY Timestamp DESC"

        try:
            r = mysql.pesquisarBD(SQL,True)
        except:pass
            
        Timestamp  = None

        try:
            if len(r) > 0:
                if r[0]['Timestamp'] != None: Timestamp = r[0]['Timestamp']
        except:pass

        return Timestamp
            
    def montarBDOff(self,arqINI,arqOFF,online):

        # Função para montar banco de dados offline 
     
        self.setBit.set()

        nSerie = self.__pegarNoSerie()

        Nuvem_Propriedades_Tipo_Usuario                         = []
        Nuvem_Tipo_de_cliente                                   = []
        Nuvem_Tipo_Maquina                                      = []
        Nuvem_Tipo_Propriedade_Maquina                          = []
        Nuvem_Tipo_Trigger_Evento                               = []
        Nuvem_Tipo_Usuario                                      = []
        Nuvem_Tipo_Valor_Propriedade_Maquina                    = []
        Nuvem_Parametros_Protocolo_Comunicacao                  = []
        Nuvem_Protocolo_Comunicacao                             = []
        Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao   = []
        Nuvem_Usuarios 					        = []
        Nuvem_Cliente 					        = []
        Nuvem_Unidades_Clientes				        = []
        Nuvem_Usuarios_Unidades				        = []
        Nuvem_Gateway					        = []
        Nuvem_Maquina					        = []
        Nuvem_Propriedades_Maquina			        = []
        Nuvem_Eventos_Maquina				        = []
        Nuvem_Sensores_Inteligentes			        = []
        Nuvem_Evento_Composto                                   = []
        Nuvem_Email_Evento				        = []
        Nuvem_Configuracao_Protocolo_Comunicacao_Maquina        = []
        Nuvem_Eventos_Gateway                                   = []

        mysql = MySQL(arqINI, arqOFF)

        # Verificará se esta sendo chamado pelo bit-1 ou pelo bit-6

        # Se estiver sendo chamado pelo bit-1: online = True
        # 1 - Excluirá todas as informações das tabelas do banco de dados offline
        # 2 - Coletará os novos dados do banco online e guardará em Ram
        # 3 - E por último colocará os novos dados no banco offline
    
        # Se estiver sendo chamado pelo bit-6: online = False
        # 1 - Coletará os dados do banco de dados offline
        # 2 - Fará a troca de arquivos da antiga estrutura do banco de dados para a nova
        # 3 - E então colocará os dados no novo banco de dados
        
        try:
            if online:
                
                print("\nBIT 1 - Montando Banco de Dados Offline\n")

                SQL = "DELETE FROM Nuvem_Tipo_Usuario"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Tipo_de_cliente"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Tipo_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Tipo_Propriedade_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Tipo_Trigger_Evento"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Tipo_Valor_Propriedade_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Protocolo_Comunicacao"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Parametros_Protocolo_Comunicacao"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Usuarios"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Cliente"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Unidades_Clientes"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Usuarios_Unidades"
                mysql.executaQueryBD(SQL,False)
                
                # Trecho provavelmente utilizado para debug
                SQL = "SELECT verRdBDOff FROM Nuvem_Gateway"
                try:
                    ver, = mysql.pesquisarBD(SQL,False)
                    ver = ver['verRdBDOff']
                except:
                    print_exc()
                    ver = self.verBDOff

                SQL = "DELETE FROM Nuvem_Gateway"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Propriedades_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Sensores_Inteligentes"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Eventos_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Evento_Composto"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Propriedades_Tipo_Usuario"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Email_Evento"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina"
                mysql.executaQueryBD(SQL,False)

                SQL = "DELETE FROM Nuvem_Eventos_Gateway"
                mysql.executaQueryBD(SQL,False)
                
            else: print("\nBIT 6 - Coletando Dados do Banco Offline\n")
        
            SQL  = "SELECT * FROM Nuvem_Tipo_Usuario"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_Usuario.append(r)
            
            SQL  = "SELECT * FROM Nuvem_Tipo_de_cliente"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_de_cliente.append(r)

            SQL  = "SELECT * FROM Nuvem_Tipo_Maquina"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_Maquina.append(r)
                   
            SQL  = "SELECT * FROM Nuvem_Tipo_Propriedade_Maquina"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_Propriedade_Maquina.append(r)

            SQL  = "SELECT * FROM Nuvem_Tipo_Trigger_Evento"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_Trigger_Evento.append(r)

            SQL  = "SELECT * FROM Nuvem_Tipo_Valor_Propriedade_Maquina"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Tipo_Valor_Propriedade_Maquina.append(r)

            SQL  = "SELECT * FROM Nuvem_Protocolo_Comunicacao"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Protocolo_Comunicacao.append(r)
                
            SQL  = "SELECT * FROM Nuvem_Parametros_Protocolo_Comunicacao"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Parametros_Protocolo_Comunicacao.append(r)
                
            SQL  = "SELECT * FROM Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao.append(r)
                        
            SQL  = "SELECT * FROM Nuvem_Usuarios"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Usuarios.append(r)
                        
            SQL  = "SELECT * FROM Nuvem_Cliente"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Cliente.append(r)

            SQL  = "SELECT * FROM Nuvem_Unidades_Clientes"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Unidades_Clientes.append(r)        

            SQL  = "SELECT * FROM Nuvem_Usuarios_Unidades"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Usuarios_Unidades.append(r)

            SQL  = "SELECT * FROM Nuvem_Gateway WHERE Cod_Gateway ='"+str(nSerie)+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Gateway.append(r)
            
            SQL  = "SELECT * FROM Nuvem_Maquina WHERE Cod_Gateway ='"+str(nSerie)+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Maquina.append(r)
            
            SQL  = "SELECT * FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina WHERE Cod_Maquina ='"+str(r['Cod_Maquina'])+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Configuracao_Protocolo_Comunicacao_Maquina.append(r)

            SQL  = "SELECT * FROM Nuvem_Propriedades_Maquina WHERE Cod_Maquina ='"+str(r['Cod_Maquina'])+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Propriedades_Maquina.append(r)

            SQL  = "SELECT * FROM Nuvem_Eventos_Maquina WHERE Cod_Maquina ='"+str(r['Cod_Maquina'])+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Eventos_Maquina.append(r)

            SQL = "SELECT * FROM (Nuvem_Email_Evento "
            SQL += "INNER JOIN Nuvem_Eventos_Maquina ON "
            SQL += "Nuvem_Email_Evento.Cod_Evento = Nuvem_Eventos_Maquina.Cod_Evento) "
            SQL += "WHERE Nuvem_Eventos_Maquina.Cod_Maquina = '"+str(r['Cod_Maquina'])+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Email_Evento.append(r)
            
            SQL  = "SELECT * FROM Nuvem_Sensores_Inteligentes WHERE Cod_Gateway ='"+str(nSerie)+"'"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Sensores_Inteligentes.append(r)
            
            SQL  = "SELECT * FROM Nuvem_Evento_Composto"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Evento_Composto.append(r)

            SQL  = "SELECT * FROM Nuvem_Propriedades_Tipo_Usuario"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Propriedades_Tipo_Usuario.append(r)

            SQL  = "SELECT * FROM Nuvem_Eventos_Gateway"
            if online: resp = mysql.pesquisarBD(SQL,True)
            else:      resp = mysql.pesquisarBD(SQL,False)
            for r in resp: Nuvem_Eventos_Gateway.append(r)
            
        except:
            print_exc()
            print(datetime.now())
        
        if not online:

            #definir o banco de dados para o qual será enviado a estrutura do banco
            #getoutput('sudo mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/BCK.sql')
            getoutput('sudo mysql -u root offline < /usr/lib/'+self.versaoPython+'/BCK.sql')
            print('Inseriu o banco offline no servidor')                 


            # Este trecho é provavelmente para debug
            SQL = "SELECT verRdBDOff FROM Nuvem_Gateway"
            try:
                ver, = mysql.pesquisarBD(SQL,False)
                ver = ver['verRdBDOff']
            except:
                print_exc()
                ver = self.verBDOff

            # Garante que não há nenhum dado no banco para atualização
            SQL = "DELETE FROM Nuvem_Tipo_Usuario"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Tipo_de_cliente"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Tipo_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Tipo_Propriedade_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Tipo_Trigger_Evento"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Tipo_Valor_Propriedade_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Protocolo_Comunicacao"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Parametros_Protocolo_Comunicacao"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Usuarios"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Cliente"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Unidades_Clientes"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Usuarios_Unidades"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Gateway"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Propriedades_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Sensores_Inteligentes"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Eventos_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Evento_Composto"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Propriedades_Tipo_Usuario"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Email_Evento"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina"
            mysql.executaQueryBD(SQL,False)

            SQL = "DELETE FROM Nuvem_Eventos_Gateway"
            mysql.executaQueryBD(SQL,False)

        print("\nEnviando Dados ao Banco Offline\n")

        try:
            for i in Nuvem_Tipo_Usuario:
                SQL = "INSERT INTO Nuvem_Tipo_Usuario ("
                SQL += "Cod_Tipo_Usuario, "
                SQL += "Tipo_Usuario) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Usuario']) + "', "
                SQL += "'" + str(i['Tipo_Usuario']) + "'"
                SQL += ")"
                
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_Usuario')

        try:
            for i in Nuvem_Tipo_de_cliente:
                SQL = "INSERT INTO Nuvem_Tipo_de_cliente ("
                SQL += "Cod_Tipo_Cliente, "
                SQL += "Tipo_Cliente) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Cliente']) + "', "
                SQL += "'" + str(i['Tipo_Cliente']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_de_Cliente')

        try:
            for i in Nuvem_Tipo_Maquina:

                SQL = "INSERT INTO Nuvem_Tipo_Maquina ("
                SQL += "Cod_Tipo_Maquina, "
                SQL += "Nome_Tipo_Maquina) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Maquina']) + "', "
                SQL += "'" + str(i['Nome_Tipo_Maquina']) + "'"
                SQL += ")"
                
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_Maquina')

        try:
            for i in Nuvem_Tipo_Propriedade_Maquina:
                SQL = "INSERT INTO Nuvem_Tipo_Propriedade_Maquina ("
                SQL += "Cod_Tipo_Propriedade_Maquina, "
                SQL += "Nome_Propriedade_Maquina) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Propriedade_Maquina']) + "', "
                SQL += "'" + str(i['Nome_Propriedade_Maquina']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_Propriedade_Maquina')

        try:
            for i in Nuvem_Tipo_Trigger_Evento:
                SQL = "INSERT INTO Nuvem_Tipo_Trigger_Evento ("
                SQL += "Cod_Tipo_Trigger_Evento, "
                SQL += "Nome_Trigger_Evento) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Trigger_Evento']) + "', "
                SQL += "'" + str(i['Nome_Trigger_Evento']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_Trigger_Evento')

        try:
            for i in Nuvem_Tipo_Valor_Propriedade_Maquina:
                SQL = "INSERT INTO Nuvem_Tipo_Valor_Propriedade_Maquina ("
                SQL += "Cod_Tipo_Valor, "
                SQL += "Nome_Tipo_Valor) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Tipo_Valor']) + "', "
                SQL += "'" + str(i['Nome_Tipo_Valor']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Tipo_Valor_Propriedade_Maquina')

        try:
            for i in Nuvem_Protocolo_Comunicacao:
                SQL = "INSERT INTO Nuvem_Protocolo_Comunicacao ("
                SQL += "Cod_Protocolo_Comunicacao, "
                SQL += "Nome_Protocolo) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Protocolo_Comunicacao']) + "', "
                SQL += "'" + str(i['Nome_Protocolo']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Protocolo_Comunicacao')
        
        try:
            for i in Nuvem_Parametros_Protocolo_Comunicacao:
                SQL = "INSERT INTO Nuvem_Parametros_Protocolo_Comunicacao ("
                SQL += "Cod_Parametro, "
                SQL += "Nome_Parametro, "
                SQL += "Cod_Protocolo_Comunicacao) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Parametro']) + "', "
                SQL += "'" + str(i['Nome_Parametro']) + "', "
                SQL += "'" + str(i['Cod_Protocolo_Comunicacao']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Parametros_Protocolo_Comunicacao')
        
        try:
            for i in Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao:
                SQL = "INSERT INTO Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao ("
                SQL += "Cod_Valor_Padrao, "
                SQL += "Valor, "
                SQL += "Cod_Parametro, "
                SQL += "Cod_Protocolo_Comunicacao) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Valor_Padrao']) + "', "
                SQL += "'" + str(i['Valor']) + "', "
                SQL += "'" + str(i['Cod_Parametro']) + "', "
                SQL += "'" + str(i['Cod_Protocolo_Comunicacao']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao')
       
        try:
            for i in Nuvem_Cliente:
                        
                SQL = "INSERT INTO Nuvem_Cliente("
                SQL += "Cod_Empresa, "
                SQL += "Nome_Empresa, "
                SQL += "Cod_Tipo_Cliente, "
                SQL += "Cod_Empresa_Responsavel, "
                SQL += "Cod_Acesso)"
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Empresa']) + "', "
                SQL += "'" + str(i['Nome_Empresa']) + "', "
                SQL += "'" + str(i['Cod_Tipo_Cliente']) + "', "
                SQL += "'" + str(i['Cod_Empresa_Responsavel']) + "', "
                SQL += "'" + str(i['Cod_Acesso']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Cliente')
        
        try:
            for i in Nuvem_Unidades_Clientes:
                        
                SQL = "INSERT INTO Nuvem_Unidades_Clientes("
                SQL += "Cod_Unidade, "
                SQL += "Nome_Unidade, "
                SQL += "Endereco_Unidade, "
                SQL += "Telefone_Unidade, "
                SQL += "Cod_Empresa, "
                SQL += "Servico_Habilitado)"
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Unidade']) + "', "
                SQL += "'" + str(i['Nome_Unidade']) + "', "
                SQL += "'" + str(i['Endereco_Unidade']) + "', "
                SQL += "'" + str(i['Telefone_Unidade']) + "', "
                SQL += "'" + str(i['Cod_Empresa']) + "', "
                SQL += "'" + str(i['Servico_Habilitado']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Unidades_Clientes')
        
        try:
            for i in Nuvem_Gateway:
                SQL = "INSERT INTO Nuvem_Gateway ("
                SQL += "Cod_Gateway, "
                SQL += "Nome, "
                SQL += "Numero_de_ED, "
                SQL += "Numero_de_SD, "
                SQL += "Numero_de_EA, "
                SQL += "Numero_de_SA, "
                SQL += "Porta_Servidor_Ethernet, "
                SQL += "Porta_Comandos_Ethernet, "
                SQL += "verRdBDOff, "
                SQL += "Cod_Unidade, "
                SQL += "Tempo_Ciclo, "
                SQL += "Tempo_Envio_Relatorio, "
                SQL += "Intervalo_Config) "
                SQL += "VALUES ("
                SQL += "'" + nSerie + "', "
                SQL += "'" + i['Nome'] + "', "
                SQL += "'" + str(i['Numero_de_ED']) + "', "
                SQL += "'" + str(i['Numero_de_SD']) + "', "
                SQL += "'" + str(i['Numero_de_EA']) + "', "
                SQL += "'" + str(i['Numero_de_SA']) + "', "
                SQL += "'" + str(i['Porta_Servidor_Ethernet']) + "', "
                SQL += "'" + str(i['Porta_Comandos_Ethernet']) + "', "
                SQL += "'" + str(ver) + "', "
                SQL += "'" + str(i['Cod_Unidade']) + "', "
                SQL += "'" + str(i['Tempo_Ciclo']) + "', "
                SQL += "'" + str(i['Tempo_Envio_Relatorio']) + "', "
                SQL += "'" + str(i['Intervalo_Config']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Gateway')
        
        try:
            for i in Nuvem_Maquina:
                    
                SQL = "INSERT INTO Nuvem_Maquina ("
                SQL += "Cod_Maquina, "
                SQL += "Nome_Maquina, "
                SQL += "Cod_Tipo_Maquina, "
                SQL += "Padrao, "
                SQL += "Cod_Maquina_Padrao, "
                SQL += "Cod_Gateway, "
                SQL += "Atualizar_Propriedades_no_site) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Maquina']) + "', "
                SQL += "'" + str(i['Nome_Maquina'])+ "', "
                SQL += "'" + str(i['Cod_Tipo_Maquina']) + "', "
                SQL += "'" + str(i['Padrao']) + "', "
                SQL += "'" + str(i['Cod_Maquina_Padrao']) + "', "
                SQL += "'" + str(i['Cod_Gateway'])+"',"
                SQL += "'" + str(i['Atualizar_Propriedades_no_site']) + ""
                SQL += "')"
                
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Maquina')
        
        try:
            for i in Nuvem_Propriedades_Maquina:
                SQL = "INSERT INTO Nuvem_Propriedades_Maquina ("
                SQL += "Cod_Propriedade_Maquina, "
                SQL += "Nome_da_Propriedade, "
                SQL += "Cod_Maquina, "
                SQL += "Cod_Tipo_Propriedade_Maquina, "
                SQL += "Endereco_Propriedade, "
                SQL += "Cod_Tipo_Valor, "
                SQL += "Valor, "
                SQL += "Novo_Valor, "
                SQL += "Leitura_Escrita, "
                SQL += "Valor_Min, "
                SQL += "Valor_Max, "
                SQL += "Unidade, "
                SQL += "Escrever, "
                SQL += "Forcar, "
                SQL += "Forcado, "
                SQL += "Retentividade, "
                SQL += "Escrever_Disp_Ext, "
                SQL += "Multiplicador, "
                SQL += "Somador, "
                SQL += "Segundos_Att_Site, "
                SQL += "Registrar_no_Historico, "
                SQL += "Tempo_Registro_segundos, "
                SQL += "Valor_de_Inicializacao, "
                SQL += "bit, "
                SQL += "Timestamp, "
                SQL += "Cod_Propriedade_Pai, "
                SQL += "Cod_Tipo_Trigger_Propriedade) "
                
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Propriedade_Maquina']) + "', "
                SQL += "'" + str(i['Nome_da_Propriedade']) + "', "
                SQL += "'" + str(i['Cod_Maquina']) + "', "
                SQL += "'" + str(i['Cod_Tipo_Propriedade_Maquina']) + "', "
                SQL += "'" + str(i['Endereco_Propriedade']) + "', "
                SQL += "'" + str(i['Cod_Tipo_Valor']) + "', "
                SQL += "'" + str(i['Valor']) + "', "
                SQL += "'" + str(i['Novo_Valor']) + "', "
                SQL += "'" + str(i['Leitura_Escrita']) + "', "
                SQL += "'" + str(i['Valor_Min']) + "', "
                SQL += "'" + str(i['Valor_Max']) + "', "
                SQL += "'" + str(i['Unidade'])+ "', "
                SQL += "'" + str(i['Escrever']) + "', "
                SQL += "'" + str(i['Forcar']) + "', "
                SQL += "'" + str(i['Forcado']) + "', "
                SQL += "'" + str(i['Retentividade']) + "', "
                SQL += "'" + str(i['Escrever_Disp_Ext']) + "', "
                SQL += "'" + str(i['Multiplicador']) + "', "
                SQL += "'" + str(i['Somador'])+"',"
                SQL += "'" + str(i['Segundos_Att_Site'])+"',"
                SQL += "'" + str(i['Registrar_no_Historico'])+"',"
                SQL += "'" + str(i['Valor_de_Inicializacao'])+"',"
                SQL += "'" + str(i['bit'])+"',"
                SQL += "'" + str(i['Timestamp'])+"',"
                SQL += "'" + str(i['Cod_Propriedade_Pai'])+"',"
                SQL += "'" + str(i['Cod_Tipo_Trigger_Propriedade'])+""
                SQL += "')"
                
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Propriedades_Maquina')
        
        try:
            for i in Nuvem_Eventos_Maquina:
                SQL = "INSERT INTO Nuvem_Eventos_Maquina ("
                SQL += "Cod_Evento, "
                SQL += "Nome_Evento, "
                SQL += "Cod_Maquina, "
                SQL += "Cod_Propriedade_Maquina, "
                SQL += "Cod_Tipo_Trigger_Evento, "
                SQL += "Valor_Trigger, "
                SQL += "Cod_Evento_Anterior, "
                SQL += "Cod_Eventos_Posteriores, "
                SQL += "Sinalizado, "
                SQL += "Gera_Email, "
                SQL += "Assunto, "
                SQL += "Mensagem) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Evento']) + "', "
                SQL += "'" + str(i['Nome_Evento']) + "', "
                SQL += "'" + str(i['Cod_Maquina']) + "', "
                SQL += "'" + str(i['Cod_Propriedade_Maquina']) + "', "
                SQL += "'" + str(i['Cod_Tipo_Trigger_Evento']) + "', "
                SQL += "'" + str(i['Valor_Trigger']) + "', "
                SQL += "'" + str(i['Cod_Evento_Anterior']) + "', "
                SQL += "'" + str(i['Cod_Eventos_Posteriores']) + "', "
                SQL += "'" + str(i['Sinalizado']) + "', "
                SQL += "'" + str(i['Gera_Email']) + "', "
                SQL += "'" + str(i['Assunto']) + "', "
                SQL += "'" + str(i['Mensagem']) + "' "
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Eventos_Maquina')

        try:
            for i in Nuvem_Sensores_Inteligentes:
                SQL = "INSERT INTO Nuvem_Sensores_Inteligentes ("
                SQL += "Cod_Sensor, "
                SQL += "Cod_Gateway, "
                SQL += "Cod_Propriedade_Maquina) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Sensor']) + "', "
                SQL += "'" + str(i['Cod_Gateway']) + "', "
                SQL += "'" + str(i['Cod_Propriedade_Maquina']) + "'"
                SQL += ")"

                mysql.executaQueryBD(SQL,False)
                
        except:print('Nuvem_Sensores_Inteligentes')
        
        try:
            for i in Nuvem_Evento_Composto:
                SQL  = "INSERT INTO Nuvem_Evento_Composto ("
                SQL += "Cod,"
                SQL += "Cod_Evento_Composto, "
                SQL += "Cod_Evento_Anterior) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod']) + "', "
                SQL += "'" + str(i['Cod_Evento_Composto']) + "', "
                SQL += "'" + str(i['Cod_Evento_Anterior']) + "'"
                SQL += ")"
                
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Eventos_Composto')
        
        try:      
            for i in Nuvem_Configuracao_Protocolo_Comunicacao_Maquina:
                SQL = "INSERT INTO Nuvem_Configuracao_Protocolo_Comunicacao_Maquina("
                SQL += "Cod, "
                SQL += "Cod_Maquina, "
                SQL += "Cod_Protocolo_Comunicacao, "
                SQL += "Cod_Parametro, "
                SQL += "Valor_Parametro) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod']) + "', "
                SQL += "'" + str(i['Cod_Maquina']) + "', "
                SQL += "'" + str(i['Cod_Protocolo_Comunicacao']) + "', "
                SQL += "'" + str(i['Cod_Parametro']) + "', "
                SQL += "'" + str(i['Valor_Parametro']) + "' "
                SQL += ")"

                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Configuracao_Protocolo_Comunicacao_Maquina')
        
        try:
            for i in Nuvem_Email_Evento:
                SQL = "INSERT INTO Nuvem_Email_Evento ("
                SQL += "Cod, "
                SQL += "Email, "
                SQL += "Cod_Evento) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod']) + "', "
                SQL += "'" + str(i['Email']) + "', "
                SQL += "'" + str(i['Cod_Evento']) + "'"
                SQL += ")"
            
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Email_Evento')

        try:
            for i in Nuvem_Eventos_Gateway:
                SQL = "INSERT INTO Nuvem_Eventos_Gateway ("
                SQL += "Cod_Evento_Gateway, "
                SQL += "Nome_Evento) "
                SQL += "VALUES ("
                SQL += "'" + str(i['Cod_Evento_Gateway']) + "', "
                SQL += "'" + str(i['Nome_Evento']) + "'"
                SQL += ")"
            
                mysql.executaQueryBD(SQL,False)

        except:print('Nuvem_Eventos_Gateway')

        #realizar um dump do banco offline e não de testescaio
        #getoutput('sudo mysqldump --databases testescaio > /usr/lib/'+self.versaoPython+'/BCK.sql')
        getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')
        getoutput('sudo cp /usr/lib/'+self.versaoPython+'/BCK.sql /usr/lib/'+self.versaoPython+'/backup')
        getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/BCK.sql')
        sleep(3)
        print('Realizou dump e backup do banco offline')
        print("Finalizou de enviar os eventos de gateway")
        # O evento não pode ser feito aqui self.eventosGateway(45, True)
        if online: self.setBit.clear()
             
    def carregaTudo(self, arqINI, arqOFF, online):

        # 1 - Loop : Verifica se os eventos e as variáveis em RAM já foram enviadas ao banco
        # 2 - Coleta as informações de todos os Loads
        # 3 - Se algum Load falhar, será refeito os Loads a partir do banco de dados offline
        # 4 - Se nenhum Load falhar, será salvo os novos dados no banco de dados offline

        self.setBit.set()

        sleep(3)
        
        global interromper
        
        print("\nBIT 2 - CarregaTudo\n")
        self.eventosGateway(29, True)
      
        print('\nSalvando eventos\n')
        for maq in self.maquina:

            gateway   = self.loadGateway(arqINI, arqOFF, self.noSerie, online)
            evntsGate = self.loadEvntsGateway(arqINI, arqOFF, online)
            loadMaq   = self.loadMaquinas(arqINI, arqOFF, self.noSerie, online)
            loadCom   = self.loadComunicacoes(arqINI, arqOFF, maq.cod, online)
            loadVar   = self.loadVariaveis(arqINI, arqOFF, maq.cod, online)
            loadEvt   = self.loadEventos(arqINI, arqOFF, maq.cod, online)
        
        if not self.loadError.isSet():

            interromper = True
            sleep(2)
            self.IO(arqINI, arqOFF, online, gateway, evntsGate)
            self.carregarDados(arqINI, arqOFF, online, loadMaq, loadCom, loadVar, loadEvt)

            #------------------#

            pOntiStart, pOntimeOut, pOntimeOut_c = self.verpOnti(arqINI, arqOFF)

            if pOntiStart:
                
                self.pOnti.Port_SA      = self.portaComandos_ethernet
                self.pOnti.Port_SP      = self.portaServidor_ethernet
                self.pOnti.pOntimeOut   = pOntimeOut
                self.pOnti.pOntimeOut_c = pOntimeOut_c

            #------------------#
            #realizar o dump para banco offline
            #getoutput('sudo mysqldump --databases testescaio > /usr/lib/'+self.versaoPython+'/BCK.sql')
            getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')    
            sleep(3)
            getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/BCK.sql')
            print('Dump do banco offline')
        print('Finalizado')
        
        interromper = False
        self.setBit.clear()
            
    def carregaEvento(self, arqINI, arqOFF, online):

        # 1 - Loop : Verifica se os eventos e as variáveis em RAM já foram enviadas ao banco
        # 2 - Coleta as informações de variáveis e eventos
        # 3 - Organiza as variáveis e eventos em pacotes
        # 4 - Se algum Load falhar, será refeito os Loads a partir do banco de dados offline
        # 5 - Se nenhum Load falhar, será salvo os novos dados no banco de dados offline

        self.setBit.set()
                
        print("\nBIT 3 - CarregaEvento\n")
        self.eventosGateway(30, True)
            
        print('\nSalvando eventos\n')
        for maq in self.maquina:
            
            loadVar = self.loadVariaveis(arqINI, arqOFF, maq.cod, online)
            loadEvt = self.loadEventos(arqINI, arqOFF, maq.cod, online)
            
            if not self.loadError.isSet():

                maq.variavel = []
                maq.evento   = []
                
                maq.variavel                 = loadVar
                maq.evento                   = loadEvt
                
                maq.orgPacotesVar()
                maq.orgPacotesHistVar()
                maq.getIntervaloMin()

                for maq in maq.variavel:
                    
                    print(maq.tipoVariavel.cod)
                    if maq.tipoVariavel.cod == 1:
                        try:self.modBus.start()
                        except:pass
                        wdt[4] = 1

                    if maq.tipoVariavel.cod == 6:
                        try:self.variaveisInternas.variaveisInternas()
                        except:pass
                    if maq.tipoVariavel.cod == 4 and self.useEA >= 1:
                        try:self.entradasAnalogicas.start()
                        except:pass
                        wdt[1] = 1
                        
                    elif maq.tipoVariavel.cod == 9:
                        try:self.geradorCloro.start()
                        except:pass
                        wdt[5] = 1

                    elif maq.tipoVariavel.cod == 10:
                        try:self.sensor.start()
                        except:pass
                        wdt[6] = 1

                    #concertar o dump do banco para banco offline
                    #getoutput('sudo mysqldump --databases testescaio > /usr/lib/'+self.versaoPython+'/BCK.sql')
                    getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')    
                    sleep(3)
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/BCK.sql')
                    print('Realizou dump do banco offline')

        print('Finalizado')
        self.eventosGateway(46, True)
        self.setBit.clear()
        
    def escreverValores(self, arqINI, arqOFF, online):

        # Bit responsável por forçar/escrever valores no Gateway ou em Disp.Externo a ele
    
        self.setBit.set()

        mysql = MySQL(arqINI, arqOFF)

        print("\nBIT 4 - Escrever / Forçar\n")
        self.eventosGateway(31, True)

        for maq in self.maquina:
            try:
                # Pega os valores das colunas para verificação
                SQL = "SELECT Cod_Propriedade_Maquina,Novo_Valor,Retentividade,Forcar,Escrever,Escrever_Disp_Ext FROM Nuvem_Propriedades_Maquina WHERE Cod_Maquina = " + str(maq.cod) + " ORDER BY Cod_Propriedade_Maquina"
                variaveis = mysql.pesquisarBD(SQL,True)

                # Assim que são coletados os valores as colunas de escrita são imediatamente zerados
                for v in variaveis:
                    SQL = "UPDATE Nuvem_Propriedades_Maquina SET Escrever = 0, Escrever_Disp_Ext = 0 WHERE Cod_Propriedade_Maquina ='"+str(v['Cod_Propriedade_Maquina'])+"'" 
                    mysql.executaQueryBD(SQL,True)

                    # As novas configurações são repassadas as variáveis do programa
                    for vari in maq.variavel:
                        if v['Cod_Propriedade_Maquina'] == vari.cod:
                            vari.novoValor = v['Novo_Valor']
                            vari.forcar = v['Forcar']
                            vari.retentividade = v['Retentividade']
                            if   v['Escrever']: vari.escreverNovoValor = True
                            elif v['Escrever_Disp_Ext']: vari.disp_ext = True

                            # É registrado o novo valor e configuração da coluna forçar
                            SQL = "UPDATE Nuvem_Propriedades_Maquina SET Forcar = '"+str(vari.forcar)+"', Novo_Valor = '"+str(vari.novoValor)+"' WHERE Cod_Propriedade_Maquina ='"+str(v['Cod_Propriedade_Maquina'])+"'"
                            mysql.executaQueryBD(SQL,False)

                            # Se retentividade for verdadeiro o novo valor se torna o valor atual
                            if bool(v['Retentividade']):
                                vari.valor = v['Novo_Valor']
                                
                                SQL = "UPDATE Nuvem_Propriedades_Maquina SET Valor = '" +str(v['Novo_Valor'])+ "' WHERE Cod_Propriedade_Maquina = '" +str(v['Cod_Propriedade_Maquina'])+ "'"
                                mysql.executaQueryBD(SQL,False)              
            except:
                # Se houver um erro em meio ao processo, por segurança, as variáveis não serão alteradas
                for vari in maq.variavel:
                    vari.escreverNovoValor = 0
                    vari.forcar = 0
                    vari.disp_ext = 0
                    
                    SQL = "UPDATE Nuvem_Propriedades_Maquina SET Forcar = 0, Novo_Valor = '"+str(vari.novoValor)+"' WHERE Cod_Propriedade_Maquina ='"+str(vari.cod)+"'"
                    mysql.executaQueryBD(SQL,False)

                print_exc()

        # Salva o arquivo do banco após fazer o bit na pasta principal e no backup

        #dump para o banco offline
        #getoutput('sudo mysqldump --databases testescaio > /usr/lib/'+self.versaoPython+'/BCK.sql')
        getoutput('sudo mysqldump --databases offline > /usr/lib/'+self.versaoPython+'/BCK.sql')
        sleep(1)
        #getoutput('sudo cp /usr/lib/'+self.versaoPython+'/BCK.sql /usr/lib/'+self.versaoPython+'/backup')
        getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/BCK.sql')
        sleep(2)
        self.setBit.clear()
        print('Backup e dump do banco offline')

    def rebootSystem(self, arqINI, arqOFF, online, bit):

        # Bit de reinicio do sistema
        global interromper
        
        interromper = True
        self.setBit.set()

        mysql = MySQL(arqINI, arqOFF)

        print("\nBIT 5 - Reinicializar\n")
        try:self.eventosGateway(32, True)
        except:pass

        sleep(1)
        
        try:self.eventosGateway(32, False)
        except:pass
        
        toBD =  ((2**bit) * - 1) + (self.getBit(arqINI,arqOFF))
        SQL = "UPDATE Nuvem_Gateway SET Bits = '"+str(toBD)+"' WHERE Cod_Gateway = '" + str(self.noSerie) + "'"

        try:mysql.executaQueryBD(SQL,True)      
        except:pass

        self.eventosGateway(47, True)
        try:self.salvarTudo(arqINI, arqOFF)
        except:pass
        
    # Atualização dos arquivos desatualizados
    def attSoftware(self, arqINI, arqOFF, online, bit):
        
        global interromper

        interromper = True                  
        self.setBit.set()

        try:
            print("\nBIT 6 - attSoftware\n")

            mysql = MySQL(arqINI, arqOFF)

            # Tenta excluir os arquivos 'Atualizando' e 'Atualizado' que indicaria que
            # Já houve uma atualização

            try:

                arq_1 = open('/usr/lib/'+self.versaoPython+'/Atualizando','r')
                arq_1.close()

                arq_2 = open('/usr/lib/'+self.versaoPython+'/Atualizado','r')
                arq_2.close()
                
                print('Removendo os arquivos auxiliares')
                remove('/usr/lib/'+self.versaoPython+'/Atualizando')
                remove('/usr/lib/'+self.versaoPython+'/Atualizado')
                
                try: remove('/usr/lib/'+self.versaoPython+'/atualizador.py')
                except: pass

                self.eventosGateway(13, True)

                print("\nAtualizado com sucesso\n\n")
                self.eventosGateway(48, True)
                interromper = False
                self.setBit.clear()

            except:

                # Acessa o banco de dados para coletar as informações de acesso ao FTP
                # E baixa primariamente o arquivo atualizador.
                SQL = "SELECT versaoSoftware, Host, Login, Senha FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
                try:
                    FTP = mysql.pesquisarBD(SQL,True)
                    pathServ = FTP[0]['versaoSoftware']
                except:
                    self.setBit.clear()
                    interromper = False
                    print('\nErro ao conectar no FTP.')
                    return
                
                # Conecta ao FTP
                try:
                    ftp = ftplib.FTP(host=FTP[0]['Host'])
                    ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
                except:
                    self.setBit.clear()
                    interromper = False
                    return

                # Acessa e cria o arquivo em download  
                try:
                    file = open('/usr/lib/'+self.versaoPython+'/atualizador.py', mode='wb')
                    ftp = ftplib.FTP(host=FTP[0]['Host'])
                    ftp.login(FTP[0]['Login'], FTP[0]['Senha'])
                    ftp.cwd(pathServ)
                except:
                    self.setBit.clear()
                    interromper = False
                    return

                # Escreve dentro do arquivo o código
                try:
                    ftp.retrbinary("RETR atualizador.py", file.write)
                    file.close()
                except:
                    file.close()
                    print_exc()
                    remove('/usr/lib/'+self.versaoPython+'/atualizador.py')
                    self.setBit.clear()
                    interromper = False
                    print('Não foi encontrado atualizador.py no FTP')
                    return

                # Garante acesso ao arquivo atualizador
                getoutput(['sudo chmod 777 /usr/lib/'+self.versaoPython+'/atualizador.py'])

                # Coleta o PID do programa atual
                toKill = getpid()
          
                # Executa o arquivo de atualização enviado informações necessárias
                # Sobre as versões e informações do programa atual
                # E envia a saída da execução para a pasta Report
                print('executa atualizador')
                getoutput("sudo python3 -u /usr/lib/"+self.versaoPython+"/atualizador.py "
                                     +str(arqINI)+" "
                                     +str(arqOFF)+" "
                                     +str(self.noSerie)+" "
                                     +str(toKill)+" "
                                     +str(bit)+" "
                                     +str(self.verCLP)+ " "
                                     +str(self.verMain)+ " "
                                     +str(self.verClasses)+ " "
                                     +str(self.verSuper)+ " "
                                     +str(self.verSuperBits)+ " "
                                     +str(self.verArqINI)+ " "
                                     +str(self.verArqOff)+ " "
                                     +str(self.verBDOff)+ " "
                                     +str(self.verRestaurador)+ " "
                                     +str(self.versaoPython)+ " > /home/pi/Report/Atualizacao"+str(datetime.now().strftime('%Y%m%d%H%M'))+" 2>&1")
                print('finalizado')
                print("\nAtualizado com sucesso\n\n")

                versaoAnterior = self.verCLP

                # Atualiza as versões que foram alteradas e
                # Envia ao banco de dados as novas versões
                try:remove('/usr/lib/'+self.versaoPython+'/atualizador.py')
                except:pass
                try:self.getVersao(arqINI, arqOFF, None, None, True)
                except:pass
                try:self.setVersao(arqINI, arqOFF)
                except:pass

                if versaoAnterior != self.verCLP:
                    print('Mudança das versões do CLP')
                    self.clpAtualizado.set()
                    print('versão anterior = ',versaoAnterior,' nova versão = ',self.verCLP)
                else:print('As versões do CLP são iguais!')                
                
        except: print_exc()
        
        self.setBit.clear()
        interromper = False
            
    def enviarComandos(self, arqINI, arqOFF, online):

        self.setBit.set()

        mysql = MySQL(arqINI, arqOFF)
        
        print("\nBIT 7 - Enviar Comandos e executar\n")
        try:self.eventosGateway(33, True)
        except:pass
        
        # Coleta as informações referentes a pasta do FTP para acesso
        SQL = "SELECT versaoSoftware, Host, Login, Senha FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
        try:
            FTP = mysql.pesquisarBD(SQL,True)
            pathServ = FTP[0]['versaoSoftware']
        except: return


        try:
            ftp = ftplib.FTP(host=FTP[0]['Host'])
            ftp.login(FTP[0]['Login'], FTP[0]['Senha'])

            ftp.cwd(pathServ)

        except:
            print("\nErro ao se conectar com o servidor FTP")
            self.setBit.clear()
            return

        # Procura dentre os arquivos o arquivo 'comandos.py'
        try:
            file = open('/usr/lib/'+self.versaoPython+'/Comandos.py', mode='wb')
            
            ftp.retrbinary("RETR Comandos.py", file.write)
            file.close()
        except:
            file.close()

        getoutput(['sudo chmod 777 /usr/lib/'+self.versaoPython+'/Comandos.py'])
         
        # Ao baixar os comandos executa-o e o remove em seguida
        try:    getoutput("sudo python3 /usr/lib/"+self.versaoPython+"/Comandos.py")
        except: print_exc()

        try:    getoutput(['sudo rm /usr/lib/'+self.versaoPython+'/Comandos.py'])
        except: print_exc()

        try:self.eventosGateway(33, False)
        except:pass

        self.eventosGateway(49, True)
        self.setBit.clear()


    def enviarRelatorio(self, arqINI, arqOFF, online):

        if not self.setBit.isSet():

            # Bit para enviar relatórios guardados e do processo atual ao FTP
            
            self.setBit.set()

            mysql = MySQL(arqINI, arqOFF)

            print("\nBIT 8 - Enviar Relatório\n")

            # Libera as permissões do arquivo
            # Copia o arquivo do shell do python para a pasta de Report

            try:self.eventosGateway(40, False)
            except:pass
            
            try:
                getoutput("sudo chmod 777 /mnt/CLP/Shell")
                if    path.isdir('Report'): pass
                else: makedirs('Report')
                getoutput('sudo chmod 777 /home/pi/Report')
                getoutput("sudo cp /mnt/CLP/Shell /home/pi/Report/"+str(datetime.now().strftime('%Y%m%d%H%M')))
                #getoutput("sudo rm /mnt/CLP/Shell")
                #print('BIT 8 o primeiro try está ok')
            except:
                self.setBit.clear()
                #print('Algo está errado no primeiro try')
                return

            # Informações necessárias para pasta do FTP
            SQL = "SELECT versaoSoftware, Host, Login, Senha FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
            try:
                FTP = mysql.pesquisarBD(SQL,True)
                pathServ = FTP[0]['versaoSoftware']+'/RPT' # + RPT para enviar direto à pasta
                #print(FTP,' Credenciais do FTP')
            except:
                self.setBit.clear()
                return
            
            relatos = listdir("/home/pi/Report") 

            # Envia, um a um, os relatórios do Gateway à pasta do FTP e em seguida os remove
            for i in relatos:
                try:
                    #print('preparando para comunicar com FTP')
                    file = open('/home/pi/Report/'+i, mode='rb')

                    ftp = ftplib.FTP(host=FTP[0]['Host'])
                    ftp.login(FTP[0]['Login'], FTP[0]['Senha'])

                    ftp.cwd(pathServ)

                    ftp.storlines("STOR "+i, file)
                    file.close()
                    #print('parece estar funcionando')
                    remove('Report/' + i)
                except:
                    print('\nErro ao conectar no servidor FTP ou envio de arquivo.')
                    pass

            try:
                self.eventosGateway(50, True)
                self.eventosGateway(40, True)
            except:pass

            self.setBit.clear()

    # Envio de emails de eventos de gateway
    def enviarEmailGate(self, arqINI, arqOFF, online):

        self.setBit.set()

        mysql = MySQL(arqINI, arqOFF)
        
        print("\nBIT 9 - Enviar Email de Gateway Offline\n\n")

        SQL  = "SELECT Cod_Registro, Cod_Gateway_Offline, Nome_Gateway_Offline, Ultima_Conexao_Servidor, Nome_Unidade, Nome_Cliente,"
        SQL += "Nome_Maquina_Offline, Timestamp_de_Deteccao, Nuvem_Eventos_Gateway.Assunto,Nuvem_Eventos_Gateway.Mensagem,"
        SQL += "Nuvem_Email_Evento_Gateway.Email FROM Dados_Envio_Email JOIN "
        SQL += "Nuvem_Email_Evento_Gateway ON Dados_Envio_Email.Cod_Gateway_Offline = Nuvem_Email_Evento_Gateway.Cod_Gateway JOIN "
        SQL += "Nuvem_Eventos_Gateway ON Nuvem_Eventos_Gateway.Cod_Evento_Gateway = Nuvem_Email_Evento_Gateway.Cod_Evento_Gateway"

        try:
            Email = mysql.pesquisarBD(SQL,True)
        except:pass
    
        try:
            for i in Email:
                
                email  = [str(i['Email'])]
                titulo = ("'"+str(i['Assunto'])+"'")
                corpo  = (
                    " '" + str(i['Mensagem']) + "', \n\n"
                    " Máquina:'" + str(i['Nome_Maquina_Offline']) + "', \n"
                    " Cliente:'" + str(i['Nome_Cliente']) + "', \n"
                    " Unidade:'" + str(i['Nome_Unidade']) + "', \n"
                    " Gateway:'" + str(i['Nome_Gateway_Offline']) + "', \n"
                    " Última Conexão com servidor:'" + str(i['Ultima_Conexao_Servidor']) + "', \n"
                    " Horário de Detecção:'" + str(i['Timestamp_de_Deteccao']) + "' "
                    " \n\n\nNão responda este email.")

                try:sendemail(email, [], titulo, corpo)
                except:pass

                SQL = "DELETE FROM Dados_Envio_Email WHERE Cod_Gateway_Emissor = '" + self.noSerie + "' AND Cod_Registro = '" + str(i['Cod_Registro']) + "'"
                try:mysql.executaQueryBD(SQL,True)
                except:pass
        except:pass
        
        self.setBit.clear()

    def checkBits(self, arqINI, arqOFF):

        #self.eventosGateway(41, False)
        #self.eventosGateway(42, False)
        
        try: remove('/mnt/CLP/bits')
        except:pass
        
        global interromper
        
        mysql = MySQL(arqINI, arqOFF)
        
        for maq in self.maquina:

            # Atualiza informação de última conexão com gateway
            SQL = "UPDATE Nuvem_Maquina SET Ultima_comunicacao_gateway = '" + maq.ultimaConexaoGateway + "' "
            SQL += "WHERE Cod_Maquina = " + str(maq.cod)

            try:    mysql.executaQueryBD(SQL,True)                    
            except: pass

            # Atualiza as informações de: temperatura da CPU,Ramdisk e memória
            SQL  = "UPDATE Nuvem_Gateway SET "
            SQL += "Temp_CPU = '" + str(self.temperature_disk(arqINI, arqOFF)) + "', "
            SQL += "Ramdisk = '" + str(self.memory_disk()) + "', "
            SQL += "Memoria_Gateway = '" + str(self.memory()) + "' "
            SQL += "WHERE Cod_Gateway = '" + self.noSerie + "'"
            
            try:    mysql.executaQueryBD(SQL,True)
            except: pass

            # Verifica qual interface esta sendo usada no momento
            rede.interfaceCheck()
            
            # Atualiza o endereço de IP externo se houver mudança
            if str(rede.ipExterno()) != str(self.endIP_externo):

                self.endIP_externo = rede.ipExterno()
                self.eventosGateway(41, True)
                
                SQL = "UPDATE Nuvem_Gateway SET EndIP_Externo = '"+str(self.endIP_externo)+"' WHERE Cod_Gateway = '" + self.noSerie + "'"

                try:    mysql.executaQueryBD(SQL,True)
                except: pass
            
            if str(rede.ipAtual()) != str(self.endIP_atual):

                a = rede.ipAtual()
                self.endIP_atual = a
                self.eventosGateway(42, True)

                if self.endIP_atual != '0.0.0.0':
                    try:
                        self.pOnti.IP = a
                        self.pOnti.SA_emExecucao  = False
                    except: pass

                    SQL = "UPDATE Nuvem_Gateway SET EndIP_Local = '"+str(self.endIP_atual)+"' WHERE Cod_Gateway = '" + self.noSerie + "'"
                    try:    mysql.executaQueryBD(SQL,True)
                    except: pass
                
            #Coleta a versão do supervisorbits do banco
            SQL = "SELECT verRdSuperBits,verRestaurador FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
            try:
                self.verSuperBits,  = mysql.pesquisarBD(SQL,True)
                self.verRestaurador = self.verSuperBits['verRestaurador']
                self.verSuperBits   = self.verSuperBits['verRdSuperBits']
            except:pass
            

        if not self.setBit.isSet() and not self.usandoPonti.isSet():

            self.loadError.clear()
            
            vWord = self.bits = (self.getBit(arqINI,arqOFF))
            if not vWord: return
            
            bitList = []

            for i in range(16):

                vBit = (self.bits & 1)
                self.bits = self.bits >> 1
                if vBit > 0: bitList.append(i)
                
            # A prioridade dos bits é do menor para o maior
            for bit in bitList:
                if not self.setBit.isSet(): # Redundante
                    bitsFunc(2**bit,
                             self.enviaVariaveis,
                             self.montarBDOff,
                             self.carregaTudo,
                             self.carregaEvento,
                             self.escreverValores,
                             self.rebootSystem,
                             self.attSoftware,
                             self.enviarComandos,
                             self.enviarRelatorio,
                             self.enviarEmailGate,
                             None,
                             None,
                             None,
                             None,
                             None,
                             None,
                             paramsF1=[arqINI,arqOFF,True],
                             paramsF2=[arqINI,arqOFF,True],
                             paramsF3=[arqINI,arqOFF,True],
                             paramsF4=[arqINI,arqOFF,True],
                             paramsF5=[arqINI,arqOFF,True],
                             paramsF6=[arqINI,arqOFF,True,bit],
                             paramsF7=[arqINI,arqOFF,True,bit],
                             paramsF8=[arqINI,arqOFF,True],
                             paramsF9=[arqINI,arqOFF,True],
                             paramsF10=[arqINI,arqOFF,True]
                             )

                    # Registra o evento do bit que foi acionado
                    if   bit == 0:pass
                    elif bit == 1:
                        try:self.eventosGateway(28, False)
                        except:pass
                    elif bit == 2: self.eventosGateway(29, False)
                    elif bit == 3: self.eventosGateway(30, False)
                    elif bit == 4: self.eventosGateway(31, False)
                    elif bit == 5: self.eventosGateway(32, False)
                    elif bit == 6: self.eventosGateway(13, False)
                    elif bit == 7: self.eventosGateway(33, False)
                    elif bit == 8: self.eventosGateway(40, False)
                        
                    if not self.loadError.isSet():
                        # Zera o bit no banco de dados online
                        toBD =  ((2**bit) * - 1) + (self.getBit(arqINI,arqOFF))
                        SQL = "UPDATE Nuvem_Gateway SET Bits = '"+str(toBD)+"' WHERE Cod_Gateway = '" + str(self.noSerie) + "'"
                        try:mysql.executaQueryBD(SQL,True)      
                        except:pass

    def __pegarNoSerie(self):

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

    def existeGatewayOnline(self, arqINI, arqOFF):

        try:
            SQL = "SELECT COUNT(*) FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
            mysql = MySQL(arqINI, arqOFF)
            count = mysql.executaCountBD(SQL,True)

            if count > 0: return True
        
        except: return False

    def existeGatewayOffline(self, arqINI, arqOFF):

        print("\n Verificando se existe gateway")
        
        try:
            SQL = "SELECT COUNT(*) FROM Nuvem_Gateway WHERE Cod_Gateway = '" + self.noSerie + "'"
            mysql = MySQL(arqINI, arqOFF)
            count = mysql.executaCountBD(SQL,False)
            
            if count > 0: return True
        
        except: return False

    def verificaGateway(self, arqINI, arqOFF, atualizacao, verCompativel):
        
        try:
            if self.verificaBanco(arqINI,arqOFF):

                if self.bancoCompativel(arqINI, arqOFF, verCompativel, atualizacao):

                    if self.existeGatewayOffline(arqINI, arqOFF): return True
                    else:
                        if self.ctrl.getAcabouEnergia(): self.salvarTudo(arqINI, arqOFF)
                        else:
                            sleep(5)
                            # Os bits aceitáveis pelo programa, neste momento, são apenas aquele que
                            # não dependem do banco montado para funcionarem
                            if self.getBit(arqINI,arqOFF) & 482: self.checkBits(arqINI, arqOFF)
                            return False
                else:
                    try:
                        try:
                            remove('/usr/lib/'+self.versaoPython+'/Reiniciado1')
                            print('\n Tentativas excedidas, esperando atualização')
                            while 1:
                                sleep(5)
                                if self.getBit(arqINI,arqOFF) & 482:self.checkBits(arqINI, arqOFF)   
                        except:
                            remove('/usr/lib/'+self.versaoPython+'/Reiniciado')
                            self.getBackup1()
                            try:open('/usr/lib/'+self.versaoPython+'/Reiniciado1', "w")
                            except:pass
                        
                            self.salvarTudo(arqINI, arqOFF)
                                                    
                    except:
                        # Indicar ao programa que já foi reiniciado uma vez ao pegar arquivos do backup
                        try:open('/usr/lib/'+self.versaoPython+'/Reiniciado', "w")
                        except:pass
                    
                        self.salvarTudo(arqINI, arqOFF)
            else:

                print('\n Estrutura incompleta: Resgatando backup')
                
                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup/BCK.sql')
                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup-1/BCK.sql')

                try:
                    #direcionar para o banco offline
                    #getoutput('sudo mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/backup/BCK.sql')
                    getoutput('sudo mysql -u root offline < /usr/lib/'+self.versaoPython+'/backup/BCK.sql')
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/BCK.sql /usr/lib/'+self.versaoPython)
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/BCK.sql')
                    print('Montou banco offline do backup')
                    
                    if self.verificaBanco(arqINI,arqOFF):
                        if    self.existeGatewayOffline(arqINI, arqOFF): return True
                        else:
                            if rede.conectadoInternet():
                                try:
                                    self.montarBDOff(arqINI,arqOFF,True)
                                    return False
                                except:
                                    try:
                                        remove('/usr/lib/'+self.versaoPython+'/Reiniciado3')
                                        print('\n Tentativas excedidas, esperando atualização')
                                        while 1:
                                            sleep(5)
                                            if self.getBit(arqINI,arqOFF) & 482:self.checkBits(arqINI, arqOFF)

                                    except:
                                        self.getBackup1()
                                        try:open('/usr/lib/'+self.versaoPython+'/Reiniciado3', "w")
                                        except:pass
                                     
                                        self.salvarTudo(arqINI, arqOFF)
                    else:
                        try:
                            remove('/usr/lib/'+self.versaoPython+'/Reiniciado2')
                            print('\n Tentativas excedidas, esperando atualização')
                            while 1:
                                sleep(5)
                                if self.getBit(arqINI,arqOFF) & 482:self.checkBits(arqINI, arqOFF)
                        except:
                            self.getBackup1()
                            try:open('/usr/lib/'+self.versaoPython+'/Reiniciado2', "w")
                            except:pass
                         
                            self.salvarTudo(arqINI, arqOFF)
                except:
                    try:
                        remove('/usr/lib/'+self.versaoPython+'/Reiniciado4')
                        print('\n Não conseguiu acesso ao backup, esperando atualização')
                        while 1:
                            sleep(5)
                            if self.getBit(arqINI,arqOFF) & 482:self.checkBits(arqINI, arqOFF)
                    except:
                        self.getBackup1()
                        try:open('/usr/lib/'+self.versaoPython+'/Reiniciado4', "w")
                        except:pass
                       
                        self.salvarTudo(arqINI, arqOFF)
        except:
            print('\n Não conseguiu executar recuperação, esperando atualização')
            while 1:
                sleep(5)
                if self.getBit(arqINI,arqOFF) & 482:self.checkBits(arqINI, arqOFF)

    def getBackup(self):
        
        fromBackup = ['MAIN.py','classes.py','supervisor','connMySQL.ini','connMySQLOFF.ini','BCK.sql','CLP.py','SupervisorBits','restaurasupervisores']
                 
        # Se o tempo de tentativas for excedido os arquivos movidos ao backup serão levados às pastas
        
        for i in fromBackup:
            
            condicoes=[i=='connMySQL.ini',i=='connMySQLOFF.ini',i=='SupervisorBits',i=='supervisor']
            
            try:
                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup/'+i)
                
                if i == 'CLP.py':
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /home/pi/'+i)
                    getoutput('sudo cp /home/pi/'+i+' /mnt/CLP/'+i)
                    getoutput('sudo chmod 777 /mnt/CLP/'+i)
                
                elif i == 'BCK.sql':
                    #
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                    #getoutput('mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/'+i)
                    getoutput('mysql -u root offline < /usr/lib/'+self.versaoPython+'/'+i)
                    print('montou banco offline do backup')
                else:
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+' /usr/lib/'+self.versaoPython+'/'+i)    
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                    
                    if (any(condicoes)):
                        if i[-4:] == '.ini':
                            i=i[0:-4]
                            getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+'.new /usr/lib/'+self.versaoPython)
                        
                        else:
                            getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup/'+i+'.new /usr/lib/'+self.versaoPython)
                
            except:print_exc()
   
        self.salvarTudo(arqINI, arqOFF)
                 
    def getBackup1(self):
        
        fromBackup = ['MAIN.py','classes.py','supervisor','connMySQL.ini','connMySQLOFF.ini','BCK.sql','CLP.py','SupervisorBits','restaurasupervisores']
                 
        # Se o tempo de tentativas for excedido os arquivos movidos ao backup serão levados às pastas
        
        for i in fromBackup:
            
            condicoes=[i=='connMySQL.ini',i=='connMySQLOFF.ini',i=='SupervisorBits',i=='supervisor']
            
            try:
                getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/backup-1/'+i)
                
                if i == 'CLP.py':
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/'+i+' /home/pi/'+i)
                    getoutput('sudo cp /home/pi/'+i+' /mnt/CLP/'+i)
                    getoutput('sudo chmod 777 /mnt/CLP/'+i)
                
                elif i == 'BCK.sql':
                    #
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/'+i+' /usr/lib/'+self.versaoPython+'/'+i)
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                    #getoutput('mysql -u root -h localhost < /usr/lib/'+self.versaoPython+'/'+i)
                    getoutput('mysql -u root offline < /usr/lib/'+self.versaoPython+'/'+i)

                    print('montou banco offline do backup-1')
                else:
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/'+i+' /usr/lib/'+self.versaoPython+'/'+i)    
                    getoutput('sudo chmod 777 /usr/lib/'+self.versaoPython+'/'+i)
                    
                    if (any(condicoes)):
                        if i[-4:] == '.ini':
                            i=i[0:-4]
                            getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/'+i+'.new /usr/lib/'+self.versaoPython)
                        
                        else:
                            getoutput('sudo cp /usr/lib/'+self.versaoPython+'/backup-1/'+i+'.new /usr/lib/'+self.versaoPython)
                
            except:print_exc()

        self.salvarTudo(arqINI, arqOFF)
        
    def verificaBanco(self, arqINI, arqOFF):

        mysql = MySQL(arqINI, arqOFF)

        print("\n Verificando Estrutura")
        
        # Verifica a última coluna da última tabela, para informar se toda a estrutura esta completa
        try:
            SQL = "SELECT Cod_Protocolo_Comunicacao FROM Nuvem_Valores_Padrao_Parametros_Protocolo_Comunicacao"
            teste = mysql.pesquisarBD(SQL,False)
            if teste == False:
                return False
            else: return True
        except:
            print_exc()
            return False
            
    def valorInicial(self, arqINI, arqOFF):

        LDO = dict()
        self.LIC = dict()

        # O valor inicial das propriedades é configurada pelo banco
        # e será o valor das saídas no primeiro ciclo antes mesmo da lógica
         
        for maq in self.maquina:
            for var in maq.variavel:
                if var.tipoVariavel.cod == 3:
                    if var.valor_inic == 2:
                        LDO[var.nome] = int(var.retentividade)
                    else:LDO[var.nome] = int(var.valor_inic)

                elif var.tipoVariavel.cod == 9:
                    if var.valor_inic == 2:pass
                    else:self.LIC[var.nome] = int(var.valor_inic)

                #Necessária a inclusão de outros tipos
        
        return LDO

    def IO(self, arqINI, arqOFF, online, gate, evnts):

        mysql = MySQL(arqINI, arqOFF)

        if not online:

            # Carrega as informações do Gateway
            gate  = self.loadGateway(arqINI, arqOFF, self.noSerie, online)

            # Lista de eventos Gateway
            self.evntsGateway = self.loadEvntsGateway(arqINI, arqOFF, online)

        else: self.evntsGateway = evnts

        # Guarda o valor de quantas entradas ou saídas estão sendo usadas
        self.useED                   = int(gate.noED)
        self.useSD                   = int(gate.noSD)
        self.useEA                   = int(gate.noEA)
        self.useSA                   = int(gate.noSA)
        self.useVI                   = 10
        self.tempCiclo               = float(gate.tempCiclo)

        try:
            tentativas = 0

            while tentativas < 3:

                try:
                    self.entradasDigitais    = EntradasDigitais()
                    self.saidasDigitais      = SaidasDigitais(False)

                    self.eventosGateway(10, False)
                    self.eventosGateway(39, False)
                    self.eventosGateway(37, False)

                    # Maybe not necessary
                    SQL  = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 0 WHERE Cod_Evento_Gateway = 10"
                    mysql.executaQueryBD(SQL,False)
                    break

                except:
                    print_exc()
                    tentativas += 1
            
            if tentativas >= 3: raise GeneratorExit
               
        except:
            # Se a tentativa de iniciar o módulo não funcionar
            # será feito uma sinalização e um reinicio do sistema

            SQL = "SELECT Sinalizado_Gateway FROM Nuvem_Eventos_Gateway WHERE Cod_Evento_Gateway = 10"
            
            try:
                resp = mysql.pesquisarBD(SQL,False)
                resp = int(resp[0]['Sinalizado_Gateway'])
            except:
                print_exc()
                resp = 0

            if resp >= 0 and resp < 3:
                
                self.eventosGateway(10, True)
                resp += 1
                SQL  = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = '" + str(resp) + "' WHERE Cod_Evento_Gateway = 10" 
                mysql.executaQueryBD(SQL,False)
                sleep(10)
                
                self.salvarTudo(arqINI, arqOFF)
               
            if resp >= 3:
               
                self.eventosGateway(39, True)
                self.eventosGateway(37, True)
                self.useED = 0
                self.useSD = 0

        try:
            tentativas = 0

            while tentativas < 3:
                try:
                    self.entradasAnalogicas  = EntradasAnalogicas()

                    self.eventosGateway(9, False)
                    self.eventosGateway(38, False)
                    self.eventosGateway(36, False)

                    SQL  = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = 0 WHERE Cod_Evento_Gateway = 9"
                    mysql.executaQueryBD(SQL,False)
                    break

                except: tentativas += 1
            if tentativas >= 3: raise GeneratorExit

        except:

            SQL = "SELECT Sinalizado_Gateway FROM Nuvem_Eventos_Gateway WHERE Cod_Evento_Gateway = 9"

            try:
                resp = mysql.pesquisarBD(SQL,False)
                resp = int(resp[0]['Sinalizado_Gateway'])
            except:
                print_exc()
                resp = 0

            if resp >= 0 and resp < 3:
                
                self.eventosGateway(9, True)
                resp += 1
                SQL = "UPDATE Nuvem_Eventos_Gateway SET Sinalizado_Gateway = '" + str(resp) + "' WHERE Cod_Evento_Gateway = 9" 
                mysql.executaQueryBD(SQL,False)
                sleep(10)
                
                self.salvarTudo(arqINI, arqOFF)

            if resp >= 3:
                
                self.eventosGateway(38, True)
                self.eventosGateway(36, True)
                self.useEA = 0

        self.variaveisInternas       = VariaveisInternas()
        self.geradorCloro            = GeradorCloro(self.usandoPonti)
        self.modBus                  = Modbus(self.usandoPonti)
        self.sensor                  = SensorInteligente()
        self.wdt                     = watchDogReset()
        
        self.portaServidor_ethernet = gate.portaServidor_ethernet
        self.portaComandos_ethernet = gate.portaComandos_ethernet
        self.ultimaConexaoServidor  = gate.ultimaConexaoServidor
        self.intervaloConfig        = gate.intervaloConfig
        self.bits                   = gate.bits

        return gate
    
    def carregarDados(self, arqINI, arqOFF, online, maquina, comunicacao, variavel, eventos):

        # 1 - Carrega as informações da máquina
        # 2 - Faz uma cópia dos dados da máquina nas classes de entrada/coleta
        # 3 - Carrega as informações de comunicações / Propriedades de máquina e Eventos de máquina
        # 4 - Passa as informações das classes para variáveis na classe de Máquina
        # 5 - Organiza pacotes de variáveis, histórico e pega o intervalo em minutos
        # 6 - Inicializa as classes de coletas de dados e sinaliza ao watchdog.
        
        if not online:
            self.maquina                         = self.loadMaquinas(arqINI, arqOFF, self.noSerie, online)
        else: self.maquina                       = maquina
        
        # Repassando lista de eventos do Gateway às classes
        if not self.useEA == 0:
            self.entradasAnalogicas.evntsGateway = self.evntsGateway
        self.sensor.evntsGateway                 = self.evntsGateway
        self.modBus.evntsGateway                 = self.evntsGateway
        self.ctrl.evntsGateway                   = self.evntsGateway
        self.wdt.evntsGateway                    = self.evntsGateway
        
        # Repassando lista de históricodo Gateway às classes
        if not self.useEA == 0:
            self.entradasAnalogicas.histGate     = self.histGate

        self.sensor.histGate                     = self.histGate
        self.modBus.histGate                     = self.histGate
        self.ctrl.histGate                       = self.histGate
        self.wdt.histGate                        = self.histGate

        # Repassando listas de Máquina às classes
        self.modBus.getMaq                       = self.maquina
        self.geradorCloro.getMaq                 = self.maquina
        self.sensor.getMaq                       = self.maquina

        if not self.useED == 0:
            self.entradasDigitais.getMaq         = self.maquina

        if not self.useEA == 0:    
            self.entradasAnalogicas.getMaq       = self.maquina

        self.variaveisInternas.getMaq            = self.maquina

        if not self.useSD == 0:
            self.saidasDigitais.getMaq           = self.maquina

        self.wdt.getMaq                          = self.maquina
        
        for maq in self.maquina:

            if not online:
                maq.comunicacao                  = self.loadComunicacoes(arqINI, arqOFF, maq.cod, online)
                maq.variavel                     = self.loadVariaveis(arqINI, arqOFF, maq.cod, online)
                maq.evento                       = self.loadEventos(arqINI, arqOFF, maq.cod, online)
            else:
                maq.comunicacao                  = comunicacao
                maq.variavel                     = variavel
                maq.evento                       = eventos
                
            maq.evntsGateway                     = self.evntsGateway
            maq.entradasDigitais                 = self.entradasDigitais
            maq.saidasDigitais                   = self.saidasDigitais
            maq.entradasAnalogicas               = self.entradasAnalogicas
            maq.saidasAnalogicas                 = self.saidasAnalogicas
            maq.variaveisInternas                = self.variaveisInternas
            maq.geradorCloro                     = self.geradorCloro
            maq.modBus                           = self.modBus
            maq.sensorInteligente                = self.sensor
            
            maq.orgPacotesVar()
            maq.orgPacotesHistVar()
            maq.getIntervaloMin()

            TiposVariaveis = []

            for maq in maq.variavel:
                TiposVariaveis.append(maq.tipoVariavel.cod)
                
            TiposVariaveis = sorted(set(TiposVariaveis))

            for codVariavel in TiposVariaveis:

                # Verifica quais dos tipos de variaveis estão sendo usadas
                # E inicia a rotina referente
                
                if codVariavel == 1:
                    try:self.modBus.start()
                    except:pass
                    wdt[4] = 1
            
                if codVariavel == 4 and self.useEA > 0:
                    try:self.entradasAnalogicas.start()
                    except:pass
                    wdt[1] = 1
        
                #Alternar o uso da porta serial quando houve 9 e 1
                elif codVariavel == 9:
                    print('inicializa o gerador de cloro')
                    try:self.geradorCloro.start()
                    except:pass
                    wdt[5] = 1
                    
                elif codVariavel == 8 and self.useED >0:
                    try:self.entradasDigitais.start()
                    except:print_exc()
                
                elif codVariavel == 10:
                    try:self.sensor.start()
                    except:pass
                    wdt[6] = 1

        if not online:
            self.wdt.start()
            self.ctrl.start()

    def startpOnti(self, arqINI, arqOFF):
        
        pOntiStart, pOntimeOut, pOntimeOut_c = self.verpOnti(arqINI, arqOFF)
        usb_to_c = self.getUSB()
        self.SA_emExecucao = False
        self.pOntiStart = pOntiStart

        if pOntiStart:
            self.pOnti  = pOnti(self.usandoPonti,
                                self.codMaquina,
                                arqINI,
                                arqOFF,
                                self.endIP_atual,
                                self.portaComandos_ethernet,
                                self.portaServidor_ethernet,
                                pOntimeOut,
                                pOntimeOut_c,
                                usb_to_c,
                                self.setBit)
            
            self.pOnti.SA_emExecucao = self.SA_emExecucao
            self.pOnti.start()
        
    def getMaqByCod(self, cod):
        return next((maq for maq in self.maquina if maq.cod == cod), None)

    def getBit(self, arqINI, arqOFF):
        
        # 1 - Atualiza no banco de dados online a última conexão com servidor
        # 2 - Coleta os bits do banco de dados online

        nSerie = self.__pegarNoSerie()
        mysql = MySQL(arqINI, arqOFF)
        
        SQL = "UPDATE Nuvem_Gateway SET "
        SQL += "Ultima_Conexao_Servidor = '" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "' "
        SQL += "WHERE Cod_Gateway = '" + nSerie + "'"
        
        try:mysql.executaQueryBD(SQL,True)
        except: pass
        
        try:
            SQL = "SELECT bits FROM Nuvem_Gateway WHERE Cod_Gateway = '" + nSerie + "'"
            resp = mysql.pesquisarBD(SQL,True)
            resp = int(resp[0]['bits'])

            return resp
        except: return False

    def loadGateway(self, arqINI, arqOFF, noSerie, online):
 
        SQL = "SELECT * FROM Nuvem_Gateway WHERE Cod_Gateway = '" + noSerie + "'"
        mysql = MySQL(arqINI, arqOFF)

        tentativas = 0

        while tentativas < 4:

            tentativas += 1

            while mysql.conectarBD(online):

                resp = mysql.pesquisarBD(SQL,online)

                if str(resp) == 'False': break

                gate = gateway()

                #Condição para ocorrer apenas quando online for igual a True
                for r in resp:
                    if online:
                        SQL  = "UPDATE Nuvem_Gateway SET "
                        SQL += "Nome                    = '" + str(r['Nome']) + "', "
                        SQL += "Cod_Unidade             = '" + str(r['Cod_Unidade']) + "', "
                        SQL += "Tempo_Ciclo             = '" + str(r['Tempo_Ciclo']) + "', "
                        SQL += "Numero_de_ED            = '" + str(r['Numero_de_ED']) + "', "
                        SQL += "Numero_de_SD            = '" + str(r['Numero_de_SD']) + "', "
                        SQL += "Numero_de_EA            = '" + str(r['Numero_de_EA']) + "', "
                        SQL += "Numero_de_SA            = '" + str(r['Numero_de_SA']) + "', "
                        SQL += "Intervalo_Config        = '" + str(r['Intervalo_Config']) + "', "
                        SQL += "Tempo_Envio_Relatorio   = '" + str(r['Tempo_Envio_Relatorio']) + "', "
                        SQL += "Porta_Servidor_Ethernet = '" + str(r['Porta_Servidor_Ethernet']) + "', "
                        SQL += "Porta_Comandos_Ethernet = '" + str(r['Porta_Comandos_Ethernet']) + "' "
                        SQL += "WHERE Cod_Gateway       = '" + str(r['Cod_Gateway']) + "'"

                        mysql.executaQueryBD(SQL,False)
                    
                    if r['Nome']                    != None: gate.nome                   = r['Nome']
                    if r['Numero_de_ED']            != None: gate.noED                   = r['Numero_de_ED']
                    if r['Numero_de_SD']            != None: gate.noSD                   = r['Numero_de_SD']
                    if r['Numero_de_EA']            != None: gate.noEA                   = r['Numero_de_EA']
                    if r['Numero_de_SA']            != None: gate.noSA                   = r['Numero_de_SA']
                    if r['Tempo_Ciclo']             != None: gate.tempCiclo              = r['Tempo_Ciclo']
                    if r['Intervalo_Config']        != None: gate.intervaloConfig        = r['Intervalo_Config']
                    if r['Tempo_Envio_Relatorio']   != None: gate.tmpEnvioRelatorio      = r['Tempo_Envio_Relatorio']
                    if r['Porta_Servidor_Ethernet'] != None: gate.portaServidor_ethernet = r['Porta_Servidor_Ethernet']
                    if r['Porta_Comandos_Ethernet'] != None: gate.portaComandos_ethernet = r['Porta_Comandos_Ethernet']
                    
                print("LoadGateway")

                return gate
                                        
        self.loadError.set()

    def loadMaquinas(self, arqINI, arqOFF, noSerieGateway, online):
        
        SQL = "SELECT * FROM Nuvem_Maquina WHERE Cod_Gateway = '" + noSerieGateway + "'"
        mysql = MySQL(arqINI, arqOFF)

        tentativas = 0

        while tentativas < 4 :

            tentativas += 1

            while mysql.conectarBD(online):

                resp = mysql.pesquisarBD(SQL,online)

                maquinas = []

                if str(resp) == 'False': break
                
                for r in resp:

                    if online:

                        SQL  = "UPDATE Nuvem_Maquina SET "
                        SQL += "Padrao                         = '" + str(r['Padrao']) + "', "
                        SQL += "Cod_Maquina                    = '" + str(r['Cod_Maquina']) + "', "
                        SQL += "Nome_Maquina                   = '" + str(r['Nome_Maquina']) + "', "
                        SQL += "Cod_Tipo_Maquina               = '" + str(r['Cod_Tipo_Maquina']) + "', "
                        SQL += "Cod_Maquina_Padrao             = '" + str(r['Cod_Maquina_Padrao']) + "', "
                        SQL += "Atualizar_Propriedades_no_site = '" + str(r['Atualizar_Propriedades_no_site']) + "' "
                        SQL += "WHERE Cod_Gateway              = '" + str(r['Cod_Gateway']) + "'"

                        mysql.executaQueryBD(SQL,False)
                    
                    maq = maquina()

                    if r['Cod_Maquina']                != None: maq.cod                  = r['Cod_Maquina']
                    if r['Nome_Maquina']               != None: maq.nome                 = r['Nome_Maquina']
                    if r['Cod_Tipo_Maquina']           != None:

                        maq.tipoMaquina.cod = r['Cod_Tipo_Maquina']

                        SQL = "SELECT * FROM Nuvem_Tipo_Maquina"# WHERE Cod_Tipo_Maquina = " + str(maq.tipoMaquina.cod)

                        rtm = mysql.pesquisarBD(SQL,online)

                        if str(rtm) == 'False': break

                        if online:

                            lOn  = []
                            lOff = []

                            ntm = mysql.pesquisarBD(SQL,False)

                            if str(ntm) == 'False': break

                            if not ntm:break

                            for rOn  in rtm: lOn.append(rOn['Cod_Tipo_Maquina'])
                            for rOff in ntm: lOff.append(rOff['Cod_Tipo_Maquina'])

                            for off in ntm:
                                if not off['Cod_Tipo_Maquina'] in lOn:
                                    
                                    SQL  = "DELETE FROM Nuvem_Tipo_Maquina WHERE Cod_Tipo_Maquina = '"+str(off['Cod_Tipo_Maquina'])+"'"
                                    mysql.executaQueryBD(SQL,False)

                            for on in rtm:
                                if not on['Cod_Tipo_Maquina'] in lOff:

                                    SQL = "INSERT INTO Nuvem_Tipo_Maquina ("
                                    SQL += "Cod_Tipo_Maquina, "
                                    SQL += "Nome_Tipo_Maquina) "
                                    SQL += "VALUES ("
                                    SQL += "'" + str(on['Cod_Tipo_Maquina']) + "', "
                                    SQL += "'" + str(on['Nome_Tipo_Maquina']) + "'"
                                    SQL += ")"
                                        
                                    mysql.executaQueryBD(SQL,False)

                                SQL = "UPDATE Nuvem_Tipo_Maquina SET Nome_Tipo_Maquina = '" + str(on['Nome_Tipo_Maquina']) + "' WHERE Cod_Tipo_Maquina = '" + str(on['Cod_Tipo_Maquina']) + "'"
                                mysql.executaQueryBD(SQL,False)

                                if on['Cod_Tipo_Maquina'] == str(maq.tipoMaquina.cod):

                                    maq.tipoMaquina.tipo = on['Nome_Tipo_Maquina']         
                        else:

                            for off in rtm:
                                if off['Cod_Tipo_Maquina'] == str(maq.tipoMaquina.cod):

                                    maq.tipoMaquina.tipo = off['Nome_Tipo_Maquina']
                                    
                    if r['Ultima_comunicacao_gateway'] != None: maq.ultimaConexaoGateway = r['Ultima_comunicacao_gateway']

                    maquinas.append(maq)

                self.codMaquina = maq.cod

                print("LoadMaquina")

                return maquinas
                
        self.loadError.set()

    def loadEvntsGateway(self, arqINI, arqOFF, online):

        SQL = "SELECT * FROM Nuvem_Eventos_Gateway"
        mysql = MySQL(arqINI, arqOFF)

        tentativas = 0

        while tentativas < 4:

            tentativas += 1

            while mysql.conectarBD(online):

                evntG = []

                respOff = mysql.pesquisarBD(SQL,False)

                if str(respOff) == 'False': break
                
                if online:

                    lOn  = []
                    lOff = []
                    
                    try:
                        respOn  = mysql.pesquisarBD(SQL,True)
                    except:break
                    
                    if str(respOn) == 'False': break
                    
                    for rOn  in respOn  : lOn.append(rOn['Cod_Evento_Gateway'])
                    for rOff in respOff : lOff.append(rOff['Cod_Evento_Gateway'])

                    for off in respOff:
                        if not off['Cod_Evento_Gateway'] in lOn:

                            SQL  = "DELETE FROM Nuvem_Eventos_Gateway WHERE Cod_Evento_Gateway = '"+str(off['Cod_Evento_Gateway'])+"'"
                            mysql.executaQueryBD(SQL,False)

                    for on in respOn:
                        if not on['Cod_Evento_Gateway'] in lOff:

                            SQL = "INSERT INTO Nuvem_Eventos_Gateway ("
                            SQL += "Nome_Evento, "
                            SQL += "Cod_Evento_Gateway, "
                            SQL += "Sinalizado_Gateway) "
                            SQL += "VALUES ("
                            SQL += "'" + str(on['Nome_Evento']) + "', "
                            SQL += "'" + str(on['Cod_Evento_Gateway']) + "', "
                            SQL += "'" + str(on['Sinalizado_Gateway'])+ ""
                            SQL += "')"
                            mysql.executaQueryBD(SQL,False)

                        SQL  = "UPDATE Nuvem_Eventos_Gateway SET Nome_Evento = '" + str(on['Nome_Evento']) + "' WHERE Cod_Evento_Gateway = '" + str(on['Cod_Evento_Gateway']) + "'"
                        mysql.executaQueryBD(SQL,False)

                resp = respOff
                
                try: resp = respOn
                except: pass
                
                for r in resp:

                    evntGate = eventosGateway()

                    if r['Cod_Evento_Gateway'] != None: evntGate.codEvntGate    = r['Cod_Evento_Gateway']
                    if r['Nome_Evento']        != None: evntGate.nomeEvntGate   = r['Nome_Evento']

                    SQL = "SELECT Sinalizado_Gateway FROM Nuvem_Eventos_Gateway WHERE Cod_Evento_Gateway = " + str(evntGate.codEvntGate)
                    sin = mysql.pesquisarBD(SQL,False)
                     
                    for s in sin:
                        
                        if s['Sinalizado_Gateway'] != None: evntGate.sinalizadoGate = int(s['Sinalizado_Gateway'])                    
                        else: evntGate.sinalizadoGate == 0
                        
                    #if r['Sinalizado_Gateway'] != None: evntGate.sinalizadoGate = r['Sinalizado_Gateway'] 

                    evntG.append(evntGate)

                print("LoadEvntsGateway")
                
                return evntG
                                        
        self.loadError.set()

    def loadComunicacoes(self, arqINI, arqOFF, codMaquina, online):
        
        SQL = "SELECT * FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina WHERE Cod_Maquina = " + str(codMaquina) + " ORDER BY Cod_Protocolo_Comunicacao"
        mysql = MySQL(arqINI, arqOFF)

        tentativas = 0

        while tentativas < 4:

            tentativas += 1

            while mysql.conectarBD(online):

                respOff = mysql.pesquisarBD(SQL,False)

                if str(respOff) == 'False': break

                comunicacoes = []

                if online:

                    lOn  = []
                    lOff = []

                    try:
                        respOn = mysql.pesquisarBD(SQL,True)
                    except:break
                    
                    if str(respOn) == 'False': break

                    for rOn  in respOn  : lOn.append(rOn['Cod'])
                    for rOff in respOff : lOff.append(rOff['Cod'])

                    for off in respOff:
                        if not off['Cod'] in lOn:

                            SQL  = "DELETE FROM Nuvem_Configuracao_Protocolo_Comunicacao_Maquina WHERE Cod = '"+str(off['Cod'])+"'"
                            mysql.executaQueryBD(SQL,False)

                    for on in respOn:
                        if not on['Cod'] in lOff:

                            SQL = "INSERT INTO Nuvem_Configuracao_Protocolo_Comunicacao_Maquina ("
                            SQL += "Cod, "
                            SQL += "Cod_Parametro, "
                            SQL += "Cod_Protocolo_Comunicacao, "
                            SQL += "Cod_Maquina, "
                            SQL += "Valor_Parametro) "
                            SQL += "VALUES ("
                            SQL += "'" + str(on['Cod']) + "', "
                            SQL += "'" + str(on['Cod_Parametro']) + "', "
                            SQL += "'" + str(on['Cod_Protocolo_Comunicacao']) + "', "
                            SQL += "'" + str(on['Cod_Maquina']) + "', "
                            SQL += "'" + str(on['Valor_Parametro'])+ ""
                            SQL += "')"
                            
                            mysql.executaQueryBD(SQL,False)

                        SQL  = "UPDATE Nuvem_Configuracao_Protocolo_Comunicacao_Maquina SET "
                        SQL += "Cod_Parametro             = '" + str(on['Cod_Parametro']) + "', "
                        SQL += "Valor_Parametro           = '" + str(on['Valor_Parametro']) + "', "
                        SQL += "Cod_Protocolo_Comunicacao = '" + str(on['Cod_Protocolo_Comunicacao']) + "' "
                        SQL += "WHERE Cod                 = '" + str(on['Cod']) + "'"

                        mysql.executaQueryBD(SQL,False)


                resp = respOff
                try: resp = respOn
                except:pass

                for r in resp:
                    if not any(x.cod == r['Cod_Protocolo_Comunicacao'] for x in comunicacoes):

                        com = comunicacao()
                        
                        com.cod = r['Cod_Protocolo_Comunicacao']
                        
                        SQL = "SELECT * FROM Nuvem_Protocolo_Comunicacao"# WHERE Cod_Protocolo_Comunicacao = " + str(com.cod)

                        rs = mysql.pesquisarBD(SQL,online)

                        if str(rs) == 'False': break

                        if online:

                            lOn  = []
                            lOff = []

                            pc = mysql.pesquisarBD(SQL,False)

                            if str(pc) == 'False': break

                            for rOn  in rs: lOn.append(rOn['Cod_Protocolo_Comunicacao'])
                            for rOff in pc: lOff.append(rOff['Cod_Protocolo_Comunicacao'])

                            for off in pc:
                                if not off['Cod_Protocolo_Comunicacao'] in lOn:
                                    print(off['Cod_Protocolo_Comunicacao'])

                                    SQL = "DELETE FROM Nuvem_Protocolo_Comunicacao WHERE Cod_Protocolo_Comunicacao = '"+str(off['Cod_Protocolo_Comunicacao'])+"'"
                                    mysql.executaQueryBD(SQL,False)

                            for on in rs:
                                if not on['Cod_Protocolo_Comunicacao'] in lOff:

                                    print(on['Cod_Protocolo_Comunicacao'])

                                    SQL = "INSERT INTO Nuvem_Protocolo_Comunicacao ("
                                    SQL += "Cod_Protocolo_Comunicacao, "
                                    SQL += "Nome_Protocolo) "
                                    SQL += "VALUES ("
                                    SQL += "'" + str(on['Cod_Protocolo_Comunicacao']) + "', "
                                    SQL += "'" + str(on['Nome_Protocolo']) + "'"
                                    SQL += ")"
                                    mysql.executaQueryBD(SQL,False)

                                SQL = "UPDATE Nuvem_Protocolo_Comunicacao SET Nome_Protocolo = '" + str(on['Nome_Protocolo']) + "' WHERE Cod_Protocolo_Comunicacao = '" + str(on['Cod_Protocolo_Comunicacao']) + "'"
                                mysql.executaQueryBD(SQL,False)

                                if on['Cod_Protocolo_Comunicacao'] == str(com.cod):

                                    com.protocolo = on['Nome_Protocolo']

                        else:

                            for off in rs:

                                 if off['Cod_Protocolo_Comunicacao'] == str(com.cod):

                                     com.protocolo = off['Nome_Protocolo']
                                     
                    #adiciona parâmetros para a última comunicacao adicionada.
                    param = parametro()

                    if r['Cod_Parametro']          != None: param.cod     = r['Cod_Parametro']
                    if r['Valor_Parametro']        != None: param.valor   = r['Valor_Parametro']
                    
                    SQL = "SELECT * FROM Nuvem_Parametros_Protocolo_Comunicacao"# WHERE Cod_Parametro = " + str(param.cod)

                    pp = mysql.pesquisarBD(SQL,online)
                    
                    if str(pp) == 'False': break

                    if online:

                        lOn  = []
                        lOff = []

                        pm = mysql.pesquisarBD(SQL,False)

                        if str(pm) == 'False': break

                        for rOn  in pp: lOn.append(rOn['Cod_Parametro'])
                        for rOff in pm: lOff.append(rOff['Cod_Parametro'])

                        for off in pm:
                            if not off['Cod_Parametro'] in lOn:
                                print(off['Cod_Parametro'])

                                SQL = "DELETE FROM Nuvem_Parametros_Protocolo_Comunicacao WHERE Cod_Parametro = '"+str(off['Cod_Parametro'])+"'"
                                mysql.executaQueryBD(SQL,False)

                        for on in pp:
                            if not on['Cod_Parametro'] in lOff:
                                print(on['Cod_Parametro'])

                                SQL = "INSERT INTO Nuvem_Parametros_Protocolo_Comunicacao ("
                                SQL += "Cod_Parametro, "
                                SQL += "Nome_Parametro, "
                                SQL += "Cod_Protocolo_Comunicacao) "
                                SQL += "VALUES ("
                                SQL += "'" + str(on['Cod_Parametro']) + "', "
                                SQL += "'" + str(on['Nome_Parametro']) + "', "
                                SQL += "'" + str(on['Cod_Protocolo_Comunicacao']) + "'"
                                SQL += ")" 
                                mysql.executaQueryBD(SQL,False)

                            SQL = "UPDATE Nuvem_Parametros_Protocolo_Comunicacao SET "
                            SQL += "Nome_Parametro            = '" + str(on['Nome_Parametro']) + "', "
                            SQL += "Cod_Protocolo_Comunicacao = '" + str(on['Cod_Protocolo_Comunicacao']) + "' "
                            SQL += "WHERE Cod_Parametro       = '" + str(on['Cod_Parametro']) + "'"

                            mysql.executaQueryBD(SQL,False)

                            if on['Cod_Parametro'] == str(param.cod):
                                param.nome = on['Nome_Parametro']

                                comunicacoes[len(comunicacoes) - 1].parametro.append(param)
                    else:

                        for off in pp:
                            if off['Cod_Parametro'] == str(param.cod):
                                param.nome = off['Nome_Parametro']

                                comunicacoes[len(comunicacoes) - 1].parametro.append(param)

                print("LoadComunicacoes")
                return comunicacoes

        self.loadError.set()

    def loadVariaveis(self, arqINI, arqOFF, codMaquina, online):

        mysql      = MySQL(arqINI, arqOFF)
        codGateway = self.__pegarNoSerie()      # Pega o cód do Gateway
        
        SQL         = "SELECT * FROM Nuvem_Propriedades_Maquina WHERE Cod_Maquina = " + str(codMaquina)
        SQLSensores = "SELECT * FROM Nuvem_Sensores_Inteligentes WHERE Cod_Gateway = " +'"'+ str(codGateway)+'"' 
                        
        tentativas = 0

        while tentativas < 4:

            tentativas += 1

            while mysql.conectarBD(online):

                respOff     = mysql.pesquisarBD(SQL,False)
                sensoresOff = mysql.pesquisarBD(SQLSensores,False)

                
                if str(respOff) == 'False': break

                variaveis = []
                sensor    = []
                
                if online:

                    lOn  = []
                    lOff = []

                    sensoresBdOn  = []
                    sensoresBdOff = []
                    
                    try:
                        respOn     = mysql.pesquisarBD(SQL,True)
                        sensoresOn = mysql.pesquisarBD(SQLSensores,True)

                    except:break

                    
                    if str(respOn) == 'False': break


                    for rOn  in respOn  : lOn.append(rOn['Cod_Propriedade_Maquina'])
                    for rOff in respOff : lOff.append(rOff['Cod_Propriedade_Maquina'])


                    for dados in sensoresOn  : sensoresBdOn.append(dados['Cod_Sensor'])
                    for dados in sensoresOff : sensoresBdOff.append(dados['Cod_Sensor'])
                    
                    
                    for off in respOff:
                        if not off['Cod_Propriedade_Maquina'] in lOn:

                            SQL  = "DELETE FROM Nuvem_Propriedades_Maquina WHERE Cod_Propriedade_Maquina = '"+str(off['Cod_Propriedade_Maquina'])+"'"
                            mysql.executaQueryBD(SQL,False)


                            #se a propriedade não existir é então apagado de sensores inteligentes os dados do sensores associados a propriedade em questão
                            if off['Cod_Tipo_Propriedade_Maquina'] == 10:

                                
                                SQL = "DELETE FROM Nuvem_Sensores_Inteligentes WHERE Cod_Propriedade_Maquina = '"+str(off['Cod_Propriedade_Maquina'])+"'"
                                mysql.executaQueryBD(SQL,False)


                    for dados in sensoresOff:
                        
                        if not dados['Cod_Sensor'] in sensoresBdOn:

                            SQL = "DELETE FROM Nuvem_Sensores_Inteligentes WHERE Cod_Sensor = '"+str(dados['Cod_Sensor'])+"'"
                            mysql.executaQueryBD(SQL,False)
    
                    
                    for dados in sensoresOn:

                            if not dados['Cod_Sensor'] in sensoresBdOff:
                                
                                SQL  = "INSERT INTO Nuvem_Sensores_Inteligentes ("
                                SQL += "Cod_Sensor,"
                                SQL += "Cod_Gateway,"
                                SQL += "Cod_Propriedade_Maquina) "
                                SQL += "VALUES ("
                                SQL += "'" + str(dados['Cod_Sensor'])+ "',"
                                SQL += "'" + str(dados['Cod_Gateway'])+ "',"
                                SQL += "'" + str(dados['Cod_Propriedade_Maquina'])+ "'"
                                SQL += ")"
                               
                                mysql.executaQueryBD(SQL,False)    
                            

                            elif dados['Cod_Sensor'] in sensoresBdOff:

                                SQL  = "UPDATE Nuvem_Sensores_Inteligentes SET "
                                SQL += "Cod_Sensor              = '" + str(dados['Cod_Sensor']) +"',"
                                SQL += "Cod_Gateway             = '" + str(dados['Cod_Gateway']) +"',"
                                SQL += "Cod_Propriedade_Maquina = '" + str(dados['Cod_Propriedade_Maquina']) +"'"
                                SQL += "WHERE Cod_Sensor        = '" + str(dados['Cod_Sensor']) +"'"
                                

                                mysql.executaQueryBD(SQL,False)
   
                    for on in respOn:     
                        
                        if not on['Cod_Propriedade_Maquina'] in lOff:
    
                            SQL = "INSERT INTO Nuvem_Propriedades_Maquina ("
                            SQL += "Cod_Propriedade_Maquina, "
                            SQL += "Nome_da_Propriedade, "
                            SQL += "Cod_Maquina, "
                            SQL += "Cod_Tipo_Propriedade_Maquina, "
                            SQL += "Endereco_Propriedade, "
                            SQL += "Cod_Tipo_Valor, "
                            SQL += "Valor, "
                            SQL += "Novo_Valor, "
                            SQL += "Leitura_Escrita, "
                            SQL += "Valor_Min, "
                            SQL += "Valor_Max, "
                            SQL += "Unidade, "
                            SQL += "Escrever, "
                            SQL += "Forcar, "
                            SQL += "Forcado, "
                            SQL += "Retentividade, "
                            SQL += "Escrever_Disp_Ext, "
                            SQL += "Multiplicador, "
                            SQL += "Somador, "
                            SQL += "Segundos_Att_Site, "
                            SQL += "Registrar_no_Historico, "
                            SQL += "Tempo_Registro_segundos, "
                            SQL += "Valor_de_Inicializacao, "
                            SQL += "bit, "
                            SQL += "Timestamp, "
                            SQL += "Cod_Propriedade_Pai, "
                            SQL += "Cod_Tipo_Trigger_Propriedade) "
                            SQL += "VALUES ("
                            SQL += "'" + str(on['Cod_Propriedade_Maquina']) + "', "
                            SQL += "'" + str(on['Nome_da_Propriedade']) + "', "
                            SQL += "'" + str(on['Cod_Maquina']) + "', "
                            SQL += "'" + str(on['Cod_Tipo_Propriedade_Maquina']) + "', "
                            SQL += "'" + str(on['Endereco_Propriedade']) + "', "
                            SQL += "'" + str(on['Cod_Tipo_Valor']) + "', "
                            SQL += "'" + str(on['Valor']) + "', "
                            SQL += "'" + str(on['Novo_Valor']) + "', "
                            SQL += "'" + str(on['Leitura_Escrita']) + "', "
                            SQL += "'" + str(on['Valor_Min']) + "', "
                            SQL += "'" + str(on['Valor_Max']) + "', "
                            SQL += "'" + str(on['Unidade'])+ "', "
                            SQL += "'" + str(on['Escrever']) + "', "
                            SQL += "'" + str(on['Forcar']) + "', "
                            SQL += "'" + str(on['Forcado']) + "', "
                            SQL += "'" + str(on['Retentividade']) + "', "
                            SQL += "'" + str(on['Escrever_Disp_Ext']) + "', "
                            SQL += "'" + str(on['Multiplicador']) + "', "
                            SQL += "'" + str(on['Somador'])+"', "
                            SQL += "'" + str(on['Segundos_Att_Site'])+"', "
                            SQL += "'" + str(on['Registrar_no_Historico'])+"', "
                            SQL += "'" + str(on['Tempo_Registro_segundos'])+"', "
                            SQL += "'" + str(on['Valor_de_Inicializacao'])+"', "
                            SQL += "'" + str(on['bit'])+"', "
                            SQL += "'" + str(on['Timestamp'])+"', "
                            SQL += "'" + str(on['Cod_Propriedade_Pai'])+"',"
                            SQL += "'" + str(on['Cod_Tipo_Trigger_Propriedade'])+"'"
                            SQL += ")"
                            
                            
                            mysql.executaQueryBD(SQL,False)
                        
                        
                        SQL  = "UPDATE Nuvem_Propriedades_Maquina SET "
                        SQL += "Nome_da_Propriedade                     = '" + str(on['Nome_da_Propriedade']) + "', "
                        SQL += "Cod_Tipo_Propriedade_Maquina            = '" + str(on['Cod_Tipo_Propriedade_Maquina']) + "', "
                        SQL += "Endereco_Propriedade                    = '" + str(on['Endereco_Propriedade']) + "', "
                        SQL += "Cod_Tipo_Valor                          = '" + str(on['Cod_Tipo_Valor']) + "', "
                        SQL += "Valor                                   = '" + str(on['Valor']) + "', "
                        SQL += "Novo_Valor                              = '" + str(on['Novo_Valor']) + "', "
                        SQL += "Leitura_Escrita                         = '" + str(on['Leitura_Escrita']) + "', "
                        SQL += "Valor_Min                               = '" + str(on['Valor_Min']) + "', "
                        SQL += "Valor_Max                               = '" + str(on['Valor_Max']) + "', "
                        SQL += "Unidade                                 = '" + str(on['Unidade']) + "', "
                        SQL += "Escrever                                = '" + str(on['Escrever']) + "', "
                        SQL += "Forcar                                  = '" + str(on['Forcar']) + "', "
                        SQL += "Forcado                                 = '" + str(on['Forcado']) + "', "
                        SQL += "Retentividade                           = '" + str(on['Retentividade']) + "', "
                        SQL += "Escrever_Disp_Ext                       = '" + str(on['Escrever_Disp_Ext']) + "', "
                        SQL += "Multiplicador                           = '" + str(on['Multiplicador']) + "', "
                        SQL += "Somador                                 = '" + str(on['Somador']) + "', "
                        SQL += "Segundos_Att_Site                       = '" + str(on['Segundos_Att_Site']) + "', "
                        SQL += "Registrar_no_Historico                  = '" + str(on['Registrar_no_Historico']) + "', "
                        SQL += "Tempo_Registro_segundos                 = '" + str(on['Tempo_Registro_segundos']) + "', "
                        SQL += "Cod_Propriedade_Pai                     = '" + str(on['Cod_Propriedade_Pai']) + "', "
                        SQL += "Cod_Tipo_Trigger_Propriedade            = '" + str(on['Cod_Tipo_Trigger_Propriedade']) + "', "
                        SQL += "Valor_de_Inicializacao                  = '" + str(on['Valor_de_Inicializacao']) + "' "
                        SQL += "WHERE Cod_Propriedade_Maquina           = '" + str(on['Cod_Propriedade_Maquina']) + "'"

                        mysql.executaQueryBD(SQL,False)

                resp = respOff
                
                try: resp = respOn
                except: pass

                for r in resp:

                    vari = variavel()

                    vari.cod = r['Cod_Propriedade_Maquina']

                    if r['Nome_da_Propriedade'] != None: vari.nome = r['Nome_da_Propriedade']

                    if r['Cod_Tipo_Propriedade_Maquina'] != None:
                        vari.tipoVariavel.cod = r['Cod_Tipo_Propriedade_Maquina']

                        if vari.tipoVariavel.cod == 10:

                            try:
                                SQL = "SELECT Cod_Sensor FROM Nuvem_Sensores_Inteligentes WHERE Cod_Propriedade_Maquina = '" + str(vari.cod) + "'"
                                rs = mysql.pesquisarBD(SQL,online)

                                if str(rs) == 'False': break
                            
                                vari.codSensor = rs[0]['Cod_Sensor']

                                print('vari.codSensor',vari.codSensor)
                                print('online ',online)
                            except: pass
                        
                        SQL = "SELECT Nome_Propriedade_Maquina FROM Nuvem_Tipo_Propriedade_Maquina WHERE Cod_Tipo_Propriedade_Maquina = " + str(vari.tipoVariavel.cod)

                        rs = mysql.pesquisarBD(SQL,online)

                        if str(rs) == 'False': break
                    
                        if rs[0]['Nome_Propriedade_Maquina'] != None:
                            vari.tipoVariavel.tipo = rs[0]['Nome_Propriedade_Maquina']
                            
                    if r['Endereco_Propriedade'] != None: vari.endereco = r['Endereco_Propriedade']

                    if r['Cod_Tipo_Valor'] != None:
                        vari.tipoValor.cod = r['Cod_Tipo_Valor']

                        SQL = "SELECT Nome_Tipo_Valor FROM Nuvem_Tipo_Valor_Propriedade_Maquina WHERE Cod_Tipo_Valor = " + str(vari.tipoValor.cod)

                        rs = mysql.pesquisarBD(SQL,online)

                        if str(rs) == 'False': break
                   
                        if rs[0]['Nome_Tipo_Valor'] != None: vari.tipoValor.tipo = rs[0]['Nome_Tipo_Valor']

                    if r['Valor'] != None: vari.valor = r['Valor']

                    if r['Novo_Valor'] != None: vari.novoValor = r['Novo_Valor']

                    if r['Escrever'] != None: vari.escreverNovoValor = r['Escrever'] 

                    if r['Unidade'] != None: vari.unidadeValor = r['Unidade']

                    if r['Multiplicador'] != None: vari.multiplicador = r['Multiplicador']

                    if r['Somador'] != None: vari.somador = r['Somador']

                    if r['Valor_Min'] != None: vari.valorMin = r['Valor_Min']

                    if r['Valor_Max'] != None: vari.valorMax = r['Valor_Max']

                    if r['Segundos_Att_Site'] != None: vari.segundosAttSite = r['Segundos_Att_Site']

                    if r['Registrar_no_Historico'] != None: vari.registraHistorico = r['Registrar_no_Historico']
                    
                    if r['Tempo_Registro_segundos'] != None: vari.tempoRegistroSegundos = r['Tempo_Registro_segundos']

                    if r['bit'] != None: vari.bit = r['bit']

                    if r['Forcar'] != None: vari.forcar = r['Forcar']

                    if r['Forcado'] != None: vari.forcado = r['Forcado']

                    if r['Leitura_Escrita'] != None: vari.leitura_escrita = r['Leitura_Escrita']

                    if r['Retentividade'] != None: vari.retentividade = r['Retentividade']

                    if r['Escrever_Disp_Ext'] != None: vari.disp_ext = r['Escrever_Disp_Ext']

                    if r['Valor_de_Inicializacao'] != None: vari.valor_inic = r['Valor_de_Inicializacao']

                    if r['Cod_Propriedade_Pai'] != None: vari.propriedadePai = r['Cod_Propriedade_Pai']

                    if r['Cod_Tipo_Trigger_Propriedade'] != None and str(r['Cod_Tipo_Trigger_Propriedade']) != '0':

                        vari.trigger.cod = r['Cod_Tipo_Trigger_Propriedade']

                        SQL = "SELECT * FROM Nuvem_Tipo_Trigger_Evento WHERE Cod_Tipo_Trigger_Evento = " + str(vari.trigger.cod)

                        rs = mysql.pesquisarBD(SQL,online)
                        
                        if str(rs) == 'False': break

                        if rs[0]['Nome_Trigger_Evento'] != None: vari.trigger.nome = rs[0]['Nome_Trigger_Evento']
                    
                    variaveis.append(vari)
                    
                print("LoadVariaveis")
                return variaveis
            
        self.loadError.set()

    def loadEventos(self, arqINI, arqOFF, codMaquina, online):

        mysql = MySQL(arqINI, arqOFF)
        SQL = "SELECT * FROM Nuvem_Eventos_Maquina WHERE Cod_Maquina = " + str(codMaquina) + " ORDER BY Cod_Evento"

        tentativas  = 0

        while tentativas < 4:

            tentativas += 1

            while mysql.conectarBD(online):

                respOff = mysql.pesquisarBD(SQL,False)

                if str(respOff) == 'False': break
                
                eventos = []

                if online:

                    lOn  = []
                    lOff = []

                    try:
                        respOn = mysql.pesquisarBD(SQL,True)
                    except: break
                    
                    if str(respOn) == 'False': break

                    for rOn  in respOn  : lOn.append(rOn['Cod_Evento'])
                    for rOff in respOff : lOff.append(rOff['Cod_Evento'])

                    for off in respOff:
                        if not off['Cod_Evento'] in lOn:

                            SQL  = "DELETE FROM Nuvem_Eventos_Maquina WHERE Cod_Evento = '"+str(off['Cod_Evento'])+"'"
                            mysql.executaQueryBD(SQL,False)

                    for on in respOn:
                        if not on['Cod_Evento'] in lOff:
                            
                            SQL = "INSERT INTO Nuvem_Eventos_Maquina ("
                            SQL += "Cod_Evento, "
                            SQL += "Nome_Evento, "
                            SQL += "Cod_Maquina, "
                            SQL += "Cod_Propriedade_Maquina, "
                            SQL += "Cod_Tipo_Trigger_Evento, "
                            SQL += "Valor_Trigger, "
                            SQL += "Cod_Evento_Anterior, "
                            SQL += "Cod_Eventos_Posteriores, "
                            SQL += "Sinalizado, "
                            SQL += "Gera_Email, "
                            SQL += "Assunto, "
                            SQL += "Mensagem) "
                            SQL += "VALUES ("
                            SQL += "'" + str(on['Cod_Evento']) + "', "
                            SQL += "'" + str(on['Nome_Evento']) + "', "
                            SQL += "'" + str(on['Cod_Maquina']) + "', "
                            SQL += "'" + str(on['Cod_Propriedade_Maquina']) + "', "
                            SQL += "'" + str(on['Cod_Tipo_Trigger_Evento']) + "', "
                            SQL += "'" + str(on['Valor_Trigger']) + "', "
                            SQL += "'" + str(on['Cod_Evento_Anterior']) + "', "
                            SQL += "'" + str(on['Cod_Eventos_Posteriores']) + "', "
                            SQL += "'" + str(on['Sinalizado']) + "', "
                            SQL += "'" + str(on['Gera_Email']) + "', "
                            SQL += "'" + str(on['Assunto']) + "', "
                            SQL += "'" + str(on['Mensagem']) + "' "
                            SQL += ")"

                            mysql.executaQueryBD(SQL,False)

                        SQL  = "UPDATE Nuvem_Eventos_Maquina SET "
                        SQL += "Nome_Evento                        = '" + str(on['Nome_Evento']) + "', "
                        SQL += "Cod_Propriedade_Maquina            = '" + str(on['Cod_Propriedade_Maquina']) + "', "
                        SQL += "Cod_Tipo_Trigger_Evento            = '" + str(on['Cod_Tipo_Trigger_Evento']) + "', "
                        SQL += "Valor_Trigger                      = '" + str(on['Valor_Trigger']) + "', "
                        SQL += "Cod_Evento_Anterior                = '" + str(on['Cod_Evento_Anterior']) + "', "
                        SQL += "Cod_Eventos_Posteriores            = '" + str(on['Cod_Eventos_Posteriores']) + "', "
                        SQL += "Gera_Email                         = '" + str(on['Gera_Email']) + "', "
                        SQL += "Assunto                            = '" + str(on['Assunto']) + "', "
                        SQL += "Mensagem                           = '" + str(on['Mensagem']) + "' "
                        SQL += "WHERE Cod_Evento                   = '" + str(on['Cod_Evento']) + "'"

                        mysql.executaQueryBD(SQL,False)

                resp = respOff
                
                try: resp = respOn
                except: pass

                for r in resp:

                    evnt = evento()
                    
                    evnt.cod = r['Cod_Evento']

                    if r['Nome_Evento'] != None: evnt.nome = r['Nome_Evento']

                    if r['Cod_Tipo_Trigger_Evento'] != None:
                        evnt.trigger.cod = r['Cod_Tipo_Trigger_Evento']

                        SQL = "SELECT * FROM Nuvem_Tipo_Trigger_Evento WHERE Cod_Tipo_Trigger_Evento = " + str(evnt.trigger.cod)

                        rs = mysql.pesquisarBD(SQL,online)

                        if str(rs) == 'False': break

                        if rs[0]['Nome_Trigger_Evento'] != None: evnt.trigger.nome = rs[0]['Nome_Trigger_Evento']

                    if r['Valor_Trigger'] != None: evnt.trigger.valor = r['Valor_Trigger']

                    if r['Cod_Propriedade_Maquina'] != None: evnt.codVarAssoc = r['Cod_Propriedade_Maquina']
                    
                    # Usar o Where de alguma forma para especificar os dados
                    SQL = "SELECT * FROM Nuvem_Evento_Composto"

                    ans = mysql.pesquisarBD(SQL,online)

                    if str(ans) == 'False': break
                
                    for a in ans:
                        
                        if a['Cod_Evento_Composto'] != None:evnt.eveComp.append(a['Cod_Evento_Composto'])
                        
                        if a['Cod_Evento_Anterior'] != None:evnt.eveAntComp.append(a['Cod_Evento_Anterior'])
                    
                    if r['Assunto'] != None: evnt.assunto = r['Assunto']

                    if r['Mensagem'] != None: evnt.mensagem = r['Mensagem']

                    if r['Gera_Email'] == 1:
                        evnt.geraEmail = True

                        SQL = "SELECT * FROM Nuvem_Email_Evento WHERE Cod_Evento = " + str(evnt.cod)

                        re = mysql.pesquisarBD(SQL,online)

                        if str(re) == 'False': break
                    
                        for e in re:
                            evnt.email.append(e['Email'])

                    SQL = "SELECT Sinalizado FROM Nuvem_Eventos_Maquina WHERE Cod_Evento = " + str(evnt.cod)
                    sin = mysql.pesquisarBD(SQL,False)
                    
                    if str(sin) == 'False': break
                     
                    for s in sin:
                        
                        if s['Sinalizado'] != None: evnt.sinalizado = int(s['Sinalizado'])                    
                        else: evnt.sinalizado == 0

                    eventos.append(evnt)

                print("LoadEventos")
                
                return eventos

        self.loadError.set()
        
class maquina:
    def __init__(self):

        self.cod                  = 0
        self.nome                 = ''
        self.tipoMaquina          = tipoMaquina()
        self.ultimaConexaoGateway = ''
        self.evntsGateway         = []
        self.comunicacao          = []
        self.variavel             = []
        self.evento               = []
        self.pacotesVar           = []
        self.intervalo            = 600.0
        self.enviando             = Event()
        self.pacotesHistVar       = []
        self.entradasDigitais     = None
        self.saidasDigitais       = None
        self.entradasAnalogicas   = None
        self.saidasAnalogicas     = None
        self.variaveisInternas    = None
        self.geradorCloro         = None
        self.modBus               = None
        self.sensorInteligente    = None
        self.ctrl                 = ControleEnergia()
        self.infoEvento           = False
        self.nomeUnidade          = None
        self.nomeCliente          = None
        self.nomeMaquina          = None

        # Flag de verificação de evento composto
        self.verEvntComp = Event()
        
    def __pegarNoSerie(self):
        
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

    def findValInComunicacao(self, nomeProtocolo, nomeParametro):

        # Verifica as configurações de comunicação e retorna 
        val = -1

        for c in self.comunicacao:
            if nomeProtocolo.upper() in c.protocolo.upper():
                val = next((q.valor for q in c.parametro if q.nome.upper() == nomeParametro.upper()), 1)
                break

        return val

    def envioEvento(self, arqINI, arqOFF):

        # Se houver uma queda de energia ou atualização : Envia o estado atual dos eventos
        mysql = MySQL(arqINI,arqOFF)

        global wdt
        wdt[0] = 1

        try:
        
            for evento in self.evntsGateway:

                sleep(0.1)
                wdt[0] = 1
                
                SQL = "UPDATE Nuvem_Eventos_Gateway SET "
                SQL += "Sinalizado_Gateway = '" + str(int(evento.sinalizadoGate))+ "' "
                SQL += "WHERE Cod_Evento_Gateway = '" + str(evento.codEvntGate)+ "'"

                mysql.executaQueryBD(SQL,False)
                
            for evnt in self.evento:

                sleep(0.1)
                wdt[0] = 1
                
                SQL = "UPDATE Nuvem_Eventos_Maquina SET "
                SQL += "Sinalizado = '" + str(int(evnt.sinalizado))+ "' "
                SQL += "WHERE Cod_Evento = '" + str(evnt.cod)+ "'"

                mysql.executaQueryBD(SQL,False)
                
            #print("\nEnviou todos os Eventos")
            return True
    
        except:
            wdt[0] = 1
            return False

    def envioEventoOn(self, arqINI, arqOFF):

        # Se houver uma queda de energia ou atualização : Envia os estado atual dos eventos
        mysql = MySQL(arqINI,arqOFF)

        global wdt
        wdt[0] = 1

        try:
            for evnt in self.evento:

                sleep(0.1)
                wdt[0] = 1
                
                SQL = "UPDATE Nuvem_Eventos_Maquina SET "
                SQL += "Sinalizado = '" + str(int(evnt.sinalizado))+ "' "
                SQL += "WHERE Cod_Evento = '" + str(evnt.cod)+ "'"
                
                mysql.executaQueryBD(SQL,True)
        except:
            wdt[0] = 1
            return
            
    def __ocorreuEvento(self, evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info):
        
        # Condições para evento foram alcançadas, checa se já foi sinalizado 
        # Envia email (se necessário)
        
        if not self.ctrl.getAcabouEnergia():

            if not self.infoEvento:

                mysql = MySQL(arqINI,arqOFF)
                nSerie = self.__pegarNoSerie()
                
                SQL  = "SELECT Nuvem_Unidades_Clientes.Nome_Unidade, Nuvem_Cliente.Nome_Empresa, Nuvem_Maquina.Nome_Maquina "
                SQL += "FROM ((( Nuvem_Unidades_Clientes "
                SQL += "INNER JOIN Nuvem_Gateway ON Nuvem_Unidades_Clientes.Cod_Unidade = Nuvem_Gateway.Cod_Unidade) "
                SQL += "INNER JOIN Nuvem_Cliente ON Nuvem_Unidades_Clientes.Cod_Empresa = Nuvem_Cliente.Cod_Empresa) "
                SQL += "INNER JOIN Nuvem_Maquina ON Nuvem_Maquina.Cod_Gateway = Nuvem_Gateway.Cod_Gateway) "
                SQL += "WHERE Nuvem_Gateway.Cod_Gateway = '" + str(nSerie) + "'"

                try:        
                    resp, = mysql.pesquisarBD(SQL,False)
                    self.nomeUnidade = resp['Nome_Unidade']
                    self.nomeCliente = resp['Nome_Empresa']
                    self.nomeMaquina = resp['Nome_Maquina']
                    self.infoEvento = True

                except:print_exc()
                
            if not evnt.sinalizado or evnt.sinalizado == 0:
               
                if  evnt.timestamp == None:
                    evnt.timestamp = datetime.now()
                else:
                    #difTime = datetime.now() - evnt.timestamp

                    #if (difTime.total_seconds() > 0.5):

                    evnt.sinalizado = True

                    if evnt.ultTimestamp != evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S") and evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S") > '2015-01-01 00:00:00':
                        # Adiciona o evento a lista de eventos ocorridos na memoria RAM
                        histEvento = eventoHistorico()
                        histEvento.codEvento = str(evnt.cod)
                        histEvento.timestamp = evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        evnt.ultTimestamp = evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        
                        histEventoNaoEnviado.append(histEvento)

                        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'Ocorreu o evento:', evnt.nome)
                        
                    infoEvento = EmailEvento()
                    infoEvento.geraEmail = evnt.geraEmail
                    infoEvento.email = evnt.email
                    infoEvento.subject = (str(evnt.nome) + ": " + str(evnt.assunto) + ' - (' + str(self.nomeUnidade) + ')' + str(self.nomeCliente) + 'MAQ: ' + str(self.nomeMaquina))
                    infoEvento.message = str(evnt.mensagem + "\n\n" + evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S"))

                    info.append(infoEvento)

                    # Ao ocorrer um evento será salvo no banco de dados um registro de todos
                    # os valores das variáveis no momento, e com o mesmo TimeStamp do evento 
                    for var in self.variavel:
                    
                        if var.ultTimestamp != evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S") and evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S") > '2015-01-01 00:00:00':
                
                            varHist = variavelHistorico()
                            
                            varHist.codPropriedade = var.cod
                            varHist.valorPropriedade = var.valor
                            varHist.timestamp = evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            var.ultTimestamp = evnt.timestamp.strftime("%Y-%m-%d %H:%M:%S")

                            histVarNaoEnviado.append(varHist)
            
    def __naoOcorreuEvento(self, evnt):
        
        evnt.timestamp = None
        evnt.sinalizado = False
                
    def _verificaEvento(self, evnt, histVarNaoEnviado, histEventoNaoEnviado, info, arqINI, arqOFF):
            
        # 1 - Verifica se o evento é composto e, caso seja, registra o evento
        # 2 - Verifica se os eventos cumprem seus requisitos.
         
        var = self.getVarByCod(evnt.codVarAssoc)

        # Verifica se o evento é composto por outros eventos
        if evnt.cod in evnt.eveComp:
            
            evento = evnt.cod # Guarda o evento verificado
            self.verEvntComp.set()

            for evnt in self.evento:
                
                if evnt.cod in evnt.eveAntComp:

                    if evnt.sinalizado == 1:pass
                    else:                   self.verEvntComp.clear()

            for evnt in self.evento:

                # Encontra qual evento estava sendo verificado
                if evnt.cod == evento:
                    if self.verEvntComp.isSet(): self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
                    else:                        self.__naoOcorreuEvento(evnt)  
        
        if evnt.trigger.nome == 'Igual à':
            
            if (float(var.valor) * var.multiplicador + var.somador) == float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
                
            else: self.__naoOcorreuEvento(evnt)
                
        elif evnt.trigger.nome == 'Diferente de':

            if (float(var.valor) * var.multiplicador + var.somador) != float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
                
            else: self.__naoOcorreuEvento(evnt)
                
        elif evnt.trigger.nome == 'Menor que':
            if (float(var.valor) * var.multiplicador + var.somador) < float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
        
            else: self.__naoOcorreuEvento(evnt)
                
        elif evnt.trigger.nome == 'Menor igual à':
            if (float(var.valor) * var.multiplicador + var.somador) <= float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
                
            else: self.__naoOcorreuEvento(evnt)
                
        elif evnt.trigger.nome == 'Maior que':
            if (float(var.valor) * var.multiplicador + var.somador) > float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
            
            else: self.__naoOcorreuEvento(evnt)
                
        elif evnt.trigger.nome == 'Maior igual à':
            if (float(var.valor) * var.multiplicador + var.somador) >= float(evnt.trigger.valor):
                self.__ocorreuEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, arqINI, arqOFF, info)
            
            else: self.__naoOcorreuEvento(evnt)

    def verificaEventos(self, histVarNaoEnviado, histEventoNaoEnviado, info, arqINI, arqOFF):

        # 1 - Verifica cada um dos eventos, comparar com os valores que os triggers possuem
        # 2 - Verificar se atendeu as requisições para setar o alarme, se sim, verifica se o alarme já esta ativo.
        
        try:
            for evnt in self.evento:
                if not self.ctrl.getQuedaEnergia():
                    self._verificaEvento(evnt, histVarNaoEnviado, histEventoNaoEnviado, info, arqINI, arqOFF)
        except: print_exc()
             
    def orgPacotesHistVar(self):

        from operator import attrgetter
       
        # 1 - Organiza os pacotes de variaveis que sejam registradas no historico
        # 2 - Os pacotes serão divididos pelo intervalo de tempo

        # Lista declarada vazia para não gerar duplicatas
        self.pacotesHistVar       = []
        
        self.variavel.sort(key=attrgetter('tempoRegistroSegundos'))
        varLast = variavel()
        
        for var in self.variavel:
            
            if var.registraHistorico:
                ultPac = len(self.pacotesHistVar) - 1
                
                if ultPac == -1 or self.pacotesHistVar[ultPac][0].tempoRegistroSegundos != var.tempoRegistroSegundos:
                    self.pacotesHistVar.append([var])
                else:
                    self.pacotesHistVar[ultPac].append(var)
                
                varLast = var
        
    def getVarByCod(self, cod):
        return next((var for var in self.variavel if var.cod == cod), None)

    def getVarByName(self, nome):
        return next((var for var in self.variavel if var.nome.upper() == nome.upper()), None)

    def getEvntByCod(self, cod):
        return next((evnt for evnt in self.evento if evnt.cod == cod), None)

    def envioForcado(self, arqINI, arqOFF):

        mysql = MySQL(arqINI,arqOFF)

        # Quando houver um usuário na tela de propriedades de máquina
        # as informações de variáveis forçadas serão atualizadas

        for pacTVar in self.pacotesVar:
            for conjVar in pacTVar:
                if type(conjVar) == list:
                    for var in conjVar:
                        
                        SQL = "UPDATE Nuvem_Propriedades_Maquina SET "
                        SQL += "Forcado = '" + str(int(var.forcado)) + "' "
                        SQL += "WHERE Cod_Propriedade_Maquina = " + str(var.cod)

                        try:    mysql.executaQueryBD(SQL,True)
                        except:pass
                else:
                    
                    SQL = "UPDATE Nuvem_Propriedades_Maquina SET "
                    SQL += "Forcado = '" + str(int(conjVar.forcado)) + "' "
                    SQL += "WHERE Cod_Propriedade_Maquina = " + str(conjVar.cod)

                    try:    mysql.executaQueryBD(SQL,True)
                    except:pass
                    
    def getValVariaveis(self, arqINI, arqOFF):
 
        # 1 - Cria dicionários
        # 2 - Separa as variáveis por tipos
        # 3 - Coleta os dados das respectivas classes
        # 4 - Retorna os dicionários com o nome das propriedades e valores
        #   Para serem usados pelo arquivo CLP
        
        ED = dict()
        SD = dict()
        EA = dict()
        SA = dict()
        IL = dict()
        IC = dict()
        MB = dict()
        SI = dict()
        IE = dict()
        
      
        #Atualiza os valores das variaveis de maquina.
        for pacTVar in self.pacotesVar:
            for conjVar in pacTVar:
                if type(conjVar) == list:
                    for var in conjVar:
                        MB[var.nome] = var.valor
                        #print('\nModbus', var.endereco ,'-', var.nome, '- Valor:', var.valor)
                else:
                    #checa se é uma ED,SD,EA,SA, e colhe o valor de acordo.
                    
                    if conjVar.tipoVariavel.tipo == 'ED' and self.entradasDigitais != None:
                        ED[conjVar.nome] = int(conjVar.valor)
                        #print('\nED', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'SD' and self.saidasDigitais != None:
                        SD[conjVar.nome] = int(conjVar.valor)
                        #print('\nSD', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'EA' and self.entradasAnalogicas != None:
                        try:    EA[conjVar.nome] = int(conjVar.valor)
                        except: EA[conjVar.nome] = float(conjVar.valor)
                        #print('\nEA', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'SA' and self.saidasAnalogicas != None:
                        try:    SA[conjVar.nome] = int(conjVar.valor)
                        except: SA[conjVar.nome] = float(conjVar.valor)
                        #print('\nSA', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'IL' and self.variaveisInternas != None:
                        try:    IL[conjVar.nome] = int(conjVar.valor)
                        except: IL[conjVar.nome] = float(conjVar.valor)
                        #print('\nInterna', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'IC' and self.geradorCloro != None:
                        IC[conjVar.nome] = conjVar.valor
                        #print('\nIntellichlor', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'SI' and self.sensorInteligente != None:
                        SI[conjVar.nome] = (float(conjVar.valor)/1000)
                        #print('\nSensor Inteligente', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

                    elif conjVar.tipoVariavel.tipo == 'IE':
                        if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                            if conjVar.forcar:
                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                else:                                            conjVar.forcado = False
                            else: conjVar.forcado = False
                            conjVar.valor = conjVar.novoValor
                        else: conjVar.forcado = False
                        try:    IE[conjVar.nome] = int(conjVar.valor)
                        except: IE[conjVar.nome] = float(conjVar.valor)
                        #print('\nVariável Interna', conjVar.endereco ,'-', conjVar.nome, '- Valor:', conjVar.valor)

        # Horario em que colheu as variaveis:
        self.ultimaConexaoGateway = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ED, SD, EA, SA, IL, IC, MB, SI, IE

    def sendVariaveis(self, arqINI, arqOFF):

        # Envia o valor das variáveis ao banco de dados online 
        # lógica está defeituosa ...
        """
            - Envia_Timestamp_PM deve ser uma variavel acessivel no método sendVariaveis()
            - Ao rodar o for que fará o envio dos dados ao banco online a verificação do 
              envio de timestamp deve ocorrer apenas uma vez. 
        
        """
        mysql = MySQL(arqINI,arqOFF)
        nSerie = self.__pegarNoSerie()

        # Consulta direta ao banco, pode ser passado pelo próprio programa
        SQL = "SELECT Envia_Timestamp_PM FROM Nuvem_Gateway WHERE Cod_Gateway = '"+str(nSerie)+"'"
        try:tms, = mysql.pesquisarBD(SQL,False)
        except:pass
        
        for var in self.variavel:
            #if var.tipoVariavel.tipo == 'IE' or var.leitura_escrita == 1: pass
            #else:
            #print('timeStamp = ',var.timeStamp)
            
            # lógica está defeituosa !!!!
            
            if tms['Envia_Timestamp_PM'] == 1 or tms['Envia_Timestamp_PM'] == True or tms['Envia_Timestamp_PM'] == '1':
                SQL = "UPDATE Nuvem_Propriedades_Maquina SET "
                SQL += "Valor = '" + str(var.valor) + "', "
                SQL += "Timestamp = '" + str(var.timeStamp) + "' "
                SQL += "WHERE Cod_Propriedade_Maquina = " + str(var.cod)
                
            else:
                SQL = "UPDATE Nuvem_Propriedades_Maquina SET "
                SQL += "Valor = '" + str(var.valor) + "' "
                SQL += "WHERE Cod_Propriedade_Maquina = " + str(var.cod)
            
            while 1:
                try:
                    mysql.executaQueryBD(SQL,True)
                    break
                except:pass
        
        SQL  = "UPDATE Nuvem_Gateway SET "
        SQL += "Envio_Propriedades ='" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "'"
        SQL += "WHERE Cod_Gateway =  +'"+str(nSerie)+"'"
        mysql.executaQueryBD(SQL,True)

##        SQL = "call onlineLocal.sp_Contagem_de_Registros()"    
##        dadosParaApagar = mysql.pesquisarBD(SQL,False)
##
##        if dadosParaApagar['permisao']==True and dadosParaApagar['qtdeApagar'] > 0:
##            SQL = "call onlineLocal.controle_Historico(Nuvem_Propriedades_Maquina,"+dadosParaApagar['qtdeApagar']+")"
##            print(SQL);

                
        #print('Enviado em : ',datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    def sendValSensores(self, arqINI, arqOFF):

        from glob import glob

        mysql = MySQL(arqINI,arqOFF)

        # Coleta de informações
        diretorio = '/sys/bus/w1/devices/'      # Caminho
        cod_past = glob(diretorio +'28*')  # Procura os sensores pelo padrão *28
        cod_past.sort()                         # Organiza o pelo os códigos por OAB
        qtde = len(cod_past)                    # Identifica o número de sensores
        codGateway = self.__pegarNoSerie()      # Pega o cód do Gateway
        
        
        for i in range (qtde):
            
            #cod      = cod_past[i].strip('/sys/bus/w1/devices/')

            cod      = cod_past[i][20:]

            read     = cod_past[i] + '/w1_slave'
            
            arq = open(read,'r')
            lines = arq.readlines()
            arq.close()

            if lines[0].strip()[-3:] == 'YES':
                temperatura = lines[1]
                temperatura = temperatura[lines[1].find('t=')+2:]
                
                #temperatura = float(lines[1][temperatura+2:-1])
                #temperatura = round((temperatura/1000),1)

            SQL   = 'Set_ValSensores'
            param = (cod,codGateway,temperatura)        

            
                      
            while 1:
                try:
                    mysql.executaProcedure(SQL, True, param)
                    break
                except:pass

    # Retorna, em segundos, o tempo de atualização do valor da variavel ao site
    def getIntervaloMin(self):

        from operator import attrgetter

        if len(self.variavel) > 0:
            self.intervalo =  float(min(self.variavel, key=attrgetter('segundosAttSite')).segundosAttSite)

        return self.intervalo

    def orgPacotesVar(self):

        from operator import attrgetter

        # Lista declarada vazia para não gerar duplicatas
        self.pacotesVar = []
        
        # Ordena as variaveis pelo tipo e pelo endereço
        self.variavel.sort(key=attrgetter('tipoVariavel.cod', 'endereco'))
        varLast = variavel()
    
        for var in self.variavel:
            ultPac = (len(self.pacotesVar) - 1)

            # Novo tipo de variavel
            if ultPac == -1 or var.tipoVariavel.cod != varLast.tipoVariavel.cod:
                if var.tipoVariavel.tipo == 'Endereço Modbus':
                    self.pacotesVar.append([[var]])
                else:
                    self.pacotesVar.append([var])
            else:
                # Adiciona variável ao último pacote
                if var.tipoVariavel.tipo == 'Endereço Modbus':

                    # Pega a quantidade máxima de enderecos/pacote na configuracao do protocolo modbus.
                    qntMax = int(self.findValInComunicacao('modbus', 'Qnt. Máxima de endereços na resposta'))
                    
                    ultConj = (len(self.pacotesVar[ultPac]) - 1)
                    ultVar = (len(self.pacotesVar[ultPac][ultConj]) - 1)
                    qntEnd = var.endereco - self.pacotesVar[ultPac][ultConj][0].endereco

                    # Adiciona a variavel ao conjunto de variaveis, de acordo com a quantidade maxima de enderecos/pacote
                    if qntEnd < qntMax: self.pacotesVar[ultPac][ultConj].append(var)
                    else: self.pacotesVar[ultPac].append([var])

                else: # Variaveis que nao sejam modbus
                    ultConj = (len(self.pacotesVar[ultPac]) - 1)
                    self.pacotesVar[ultPac].append(var)
            
            varLast = var

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
# Classe de verificação e coleta de dados da rede e internet #   
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
class rede:

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
    
    # Verifica quais interfaces estão disponíveis para o Gateway
    # E quais delas estão sendo usadas
    def interfaceCheck():

        global pid_modem
        mysql = MySQL('/mnt/CLP/connMySQL.ini', '/mnt/CLP/connMySQLOFF.ini')

        try:

            eth0 = getoutput("sudo ip link show eth0 | grep eth0 | awk '{print $9 }'")
        
            if eth0 == 'UP':

                if rede.conectadoInternet():
                    try:getoutput('sudo kill '+str(pid_modem[0]))
                    except: pass

                    SQL = "UPDATE Nuvem_Gateway SET Interface = 'C' WHERE Cod_Gateway = '" + str(rede.pegarNoSerie()) + "'"
                    try:mysql.executaQueryBD(SQL,True)
                    except:pass
            else:

                wlan0 = getoutput("sudo ip link show wlan0 | grep wlan0 | awk '{print $9 }'")

                if wlan0 == 'UP':

                    if rede.conectadoInternet():
                        try:getoutput('sudo kill '+str(pid_modem[0]))
                        except: pass

                        SQL = "UPDATE Nuvem_Gateway SET Interface = 'W' WHERE Cod_Gateway = '" + str(rede.pegarNoSerie()) + "'"
                        try:mysql.executaQueryBD(SQL,True)
                        except:pass

        except:pass
        
    # Retorna o endereço de ip externo
    def ipExterno():
        
        try: endIp = getoutput(['python3 -m ipgetter'])
        except: endIp = getoutput(['curl ifconfig.me'])
    
        if len(endIp) < 8: endIp = "0.0.0.0"

        return endIp

    # Verifica se esta conectado a internet
    def conectadoInternet():
        
        # Demais tentativas de conexão com internet
        tentativas = 0
        servidorRemoto = 'www.google.com.br'

        while tentativas < 3:
            if tentativas == 1:
                servidorRemoto = 'www.lds.org'
            elif tentativas == 2:
                servidorRemoto = 'www.msn.com'

            try:
                host = gethostbyname(servidorRemoto)
                s = create_connection((host, 80), 2)
                return True
            except: tentativas += 1
               
        return False

    def ipAtual():

        try:    endIP = getoutput('sudo hostname -I')
        except: endIP = "0.0.0.0"

        r = comp("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        a = r.findall(endIP)

        try:
            return a[0]
        except:
            return "0.0.0.0"

    # Conecta e desconecta ao modem se dispoível
    def conectadoModem():

        mysql = MySQL('/mnt/CLP/connMySQL.ini', '/mnt/CLP/connMySQLOFF.ini')
        
        while True:

            sleep(1)

            try:
                # Se nenhuma outra interface metricamente acima estiver sendo usada ele passará
                if not rede.conectadoInternet():

                    # Procura pelas portas USB's que estão sendo usadas
                    usbEncontrada = getoutput("sudo ls /dev | grep ttyUSB")

                    for usb in usbEncontrada.split():

                        dispConectado = getoutput("sudo dmesg | grep -i "+usb+"")
            
                        ttyUsb_do_dispositivo = comp("[^:]*\snow\s\w+\s\w+\s"+usb+"")

                        historico = ttyUsb_do_dispositivo.findall(dispConectado)
                    
                        historico.reverse()

                        if not rede.conectadoInternet():

                            # Verifica se alguma delas é um modem
                            if 'modem' in historico[0]:
                                
                                try:getoutput("sudo rm /etc/wvdial.conf")
                                except:pass

                                getoutput("sudo wvdialconf")

                                # Comando AT que verifica a operadora do CHIP
                                pegar_operadora = 'Init3 = AT+COPS?\n'
                                stupid          = 'Stupid mode = 1\n'
                                
                                arq = open('/etc/wvdial.conf','r')
                                linhas_wvdial = arq.readlines()
                                arq.close()

                                for linha in linhas_wvdial:
                                    if linha[0:7] == 'Modem =': local = linha[8:20]

                                getoutput("sudo chmod 777 /etc/wvdial.conf")

                                ## a lista pode ser menor
                                arq = open('/etc/wvdial.conf','w')
                                linhas_wvdial.insert(2,pegar_operadora)
                                linhas_wvdial.insert(3,stupid)
                                arq.writelines(linhas_wvdial)
                                arq.close()
                                
                                pegarOperadora = getoutput("sudo wvdial")

                                encontrarOperadora = comp('(?<=\")(.*?)(?=\")')

                                operadoraEncontrada = encontrarOperadora.findall(pegarOperadora)

                                 ## Seleção de configuração para a operadora
                                
                                if operadoraEncontrada[0][0:5] == 'claro' or operadoraEncontrada[0][0:5] == 'CLARO' or operadoraEncontrada[0][0:5] == 'Claro': oper = 'Claro'
                                if operadoraEncontrada[0][0:4] == 'vivo'  or operadoraEncontrada[0][0:4] == 'VIVO'  or operadoraEncontrada[0][0:4] == 'Vivo' : oper = 'Vivo'
                                if operadoraEncontrada[0][0:3] == 'tim'   or operadoraEncontrada[0][0:3] == 'TIM'   or operadoraEncontrada[0][0:3] == 'Tim'  : oper = 'Tim'
                                if operadoraEncontrada[0][0:2] == 'oi'    or operadoraEncontrada[0][0:2] == 'OI'    or operadoraEncontrada[0][0:2] == 'Oi'   : oper = 'Oi'

                                # Insere no arquivo de configuração informações sobre a operadora do CHIP
                                
                                try:
                                    arq = open('/home/pi/Área de Trabalho/'+oper,'r')
                                    configPadrao = arq.readlines()
                                    arq.close()

                                except:
                                    arq = open('/home/pi/Desktop/'+oper,'r')
                                    configPadrao = arq.readlines()
                                    arq.close()
                                    
                                for linha in configPadrao:
                                    if linha[0:7] == 'Modem =':
                                        configPadrao.remove(linha)
                                        configPadrao.append('\nModem = '+local)

                                arq = open('/etc/wvdial.conf','w')
                                arq.writelines(configPadrao)
                                arq.close()

                                # Leitura da saída do comando de conexão com o modem
                                def return_lines(inp):

                                    line = inp.readline().decode('latin-1')
                                    count_dns = 0
                            
                                    while line:

                                        sleep(0.1)

                                         # Coleta o PID e verifica se os IP's são iguais
                                        if 'Pid' in line:

                                            global pid_modem
                                            
                                            padraoPID = comp("\d[^:]\d+")
                                            pid_modem = padraoPID.findall(line)

                                            while 1:

                                                pegarIP = getoutput('sudo ifconfig ppp0')

                                                encontrarIP = comp("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
                                            
                                                ipEncontrado = encontrarIP.findall(pegarIP)
                                            
                                                sleep(0.1)
                                                
                                                pegarIPext = getoutput('sudo curl ifconfig.me')
                                                getoutput('sudo cat /etc/resolv.conf.bkp > /etc/resolv.conf')
                                                getoutput('sudo chmod 777 /etc/resolv.conf')

                                                ipExtEncontrado = encontrarIP.findall(pegarIPext)

                                                # Se os IP's forem iguais o programa continua
                                                if ipExtEncontrado != [] and ipEncontrado != []:
                                                    try:
                                                        if str(ipExtEncontrado[0]) != str(ipEncontrado[0]):

                                                            print("IP's diferentes, reconectando", ipExtEncontrado[0], ipEncontrado[0])
                                                            sleep(0.2)
                                                            getoutput('sudo kill '+str(pid_modem[0]))
                                                            break
                                                        else:
                                                            print("IP's iguais")

                                                            SQL = "UPDATE Nuvem_Gateway SET Interface = 'M' WHERE Cod_Gateway = '" + str(rede.pegarNoSerie()) + "'"

                                                            try:mysql.executaQueryBD(SQL,True)
                                                            except:pass

                                                            break
                                                    except:
                                                        print_exc()
                                                        print("IP's inválidos, reconectando")
                                                        getoutput('sudo kill '+str(pid_modem[0]))
                                                        break

                                        # Preenchimento do arquivo de configuração do DNS e envio 
                                        if 'DNS' in line:

                                            encontrarDNS = comp("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
                                            dnsEncontrado = encontrarDNS.findall(line)
                                            
                                            try:
                                                getoutput('sudo chmod 777 /home/pi/resolv.conf.bkp')
                                                
                                                arq = open('/home/pi/resolv.conf.bkp','r')
                                                configDNS   = arq.readlines()
                                                arq.close()

                                                arq = open('/home/pi/resolv.conf.bkp','w')
                                                configDNS.append('nameserver '+dnsEncontrado[0]+'\n')
                                                arq.writelines(configDNS)
                                                arq.close()

                                                getoutput('sudo chmod 777 /home/pi/resolv.conf.bkp')

                                            except:
                                                arq = open('/home/pi/resolv.conf.bkp','w')
                                                configDNS   = ["domain www."+str(oper)+".com.br\n"]
                                                configDNS.append('nameserver '+dnsEncontrado[0]+'\n')
                                                arq.writelines(configDNS)
                                                arq.close()

                                                getoutput('sudo chmod 777 /home/pi/resolv.conf.bkp')

                                            count_dns += 1

                                            if count_dns > 1:
                                                
                                                getoutput('sudo chmod 777 /home/pi/resolv.conf.bkp')
                                                getoutput('sudo mv /home/pi/resolv.conf.bkp /etc/resolv.conf.bkp')
                                                getoutput('sudo chmod 777 /etc/resolv.conf')
                                                getoutput('sudo cat /etc/resolv.conf.bkp > /etc/resolv.conf')
                                                getoutput('sudo chmod 777 /etc/resolv.conf')

                                        #print(line,end='')

                                        line = inp.readline().decode('latin-1')

                                # Comando para conexão com o modem
                                proc = Popen(["sudo wvdial"], shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)

                                t1 = Thread(target=return_lines, args=(proc.stdout,))
                                t2 = Thread(target=return_lines, args=(proc.stderr,))

                                t1.start()
                                t2.start()

                                t1.join() 
                                t2.join()

            except: pass
                #print_exc() 

# +++++++++++++++++++++++++++++++++++++ #
# Funções básicas para manipular MySQL  #      
# +++++++++++++++++++++++++++++++++++++ #
class MySQL:
    
    def __init__(self, arqINI, arqOFF):
        
        tentativas = 0
        self.versaoPython = self.getPythonVer()
        try:
            while tentativas < 3:
                      
                # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
                # Coleta as configurações de acesso ao banco de dados online  #
                # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
                config_on = configparser.ConfigParser()
                config_on.read(arqINI)

                # Chave para descriptografar. uma chave para cada informação
                obj0 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

                # A informação é guardada codificada, mas quando é coletada chega no formato str
                x = config_on['database']['servidor']
                # Codificação das informações        
                x = bytes(x, 'utf-8')
                # Descodificação
                x = x.decode('unicode-escape').encode('ISO-8859-1')
                # Descriptografia das informações e decodificação das informações
                self.servidor_on = (obj0.decrypt(x).decode("utf-8")).strip('0')

                obj1 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')
                
                a = config_on['database']['usuario']
                a = bytes(a, 'utf-8')
                a = a.decode('unicode-escape').encode('ISO-8859-1')
                self.usuario_on = (obj1.decrypt(a).decode("ISO-8859-1")).strip('0')

                obj2 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')
                
                b = config_on['database']['senha']
                b = bytes(b, 'utf-8')
                b = b.decode('unicode-escape').encode('ISO-8859-1')
                self.senha_on = (obj2.decrypt(b).decode("utf-8")).strip('0')

                obj3 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')
                
                c = config_on['database']['db']
                c = bytes(c, 'utf-8')
                c = c.decode('unicode-escape').encode('ISO-8859-1')
                self.db_on = (obj3.decrypt(c).decode("utf-8")).strip('0')

                # ----------------------------------------------------------- #
                # Coleta as configurações de acesso ao banco de dados offline #
                # ----------------------------------------------------------- #
                config_off = configparser.ConfigParser()
                config_off.read(arqOFF)

                obj4 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')
                
                d = config_off['database']['servidor']
                d = bytes(d, 'utf-8')
                d = d.decode('unicode-escape').encode('ISO-8859-1')
                self.servidor_off = (obj4.decrypt(d).decode("utf-8")).strip('0')

                obj5 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

                e = config_off['database']['usuario']
                e = bytes(e, 'utf-8')
                e = e.decode('unicode-escape').encode('ISO-8859-1')
                self.usuario_off = (obj5.decrypt(e).decode("utf-8")).strip('0')

                obj6 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

                f = config_off['database']['senha']
                f = bytes(f, 'utf-8')
                f = f.decode('unicode-escape').encode('ISO-8859-1')
                self.senha_off = (obj6.decrypt(f).decode("utf-8")).strip('0')

                obj7 = AES.new('OntiAutomacao123', AES.MODE_CBC, 'This is an IV456')

                g = config_off['database']['db']
                g = bytes(g, 'utf-8')
                g = g.decode('unicode-escape').encode('ISO-8859-1')
                self.db_off = (obj7.decrypt(g).decode("utf-8")).strip('0')
                break

        except: tentativas += 1
    
    def getPythonVer(self):

        pastas = listdir("/usr/lib/")
        for i in pastas:
            if str(i[0:8]) == 'python3.':
                return str(i)
 
    #Conecta ao banco de dados online ou offline
    def conectarBD(self, online):

        #import pymysql
        import mysql.connector as mysql
        global novaCredencial
        
        # Se a conexão com o banco estiver ok retorna-se a conexão
        # Se online = Verdade, a conexão será feita com o banco de dados online
        # Se online = False, a conexão será feita com banco de dados offline
        try:
            if online:

                conn = mysql.connect(host=self.servidor_on,
                                     user=self.usuario_on,
                                     password=self.senha_on,
                                     db=self.db_on,
                                     charset='utf8',
                                     connect_timeout=600,
                                     compress=True)
                                       #cursorclass=pymysql.cursors.DictCursor)
                #print(self.usuario_on)
                #print('conexao bem sucedida')
                if novaCredencial:
                    getoutput('sudo cp /usr/lib/'+self.versaoPython+'/connMySQL.new /usr/lib/'+self.versaoPython+'/connMySQL.ini')
                    novaCredencial = False
            else:

                conn = mysql.Connect(host=self.servidor_off,
                                     user=self.usuario_off,
                                     password=self.senha_off,
                                     db=self.db_off,
                                     charset='utf8',
                                     connect_timeout=600,
                                     compress=True)
                                       #cursorclass=pymysql.cursors.DictCursor)

            return conn

        # Retorna-se falso caso não
        except:
            #print('erro conexao')
            #print(novaCredencial)
            #sleep(5)
            
            if novaCredencial:
                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/connMySQL.ini /mnt/CLP/connMySQL.ini')
                novaCredencial = False
            
            else:
                getoutput('sudo cp /usr/lib/'+self.versaoPython+'/connMySQL.new /mnt/CLP/connMySQL.ini')
                novaCredencial = True
                
            
            return False

    #Executa instrução SQL no banco de dados
    def executaQueryBD(self, SQL, online):
        try:
            conn = self.conectarBD(online)

            if conn == False:
                return False

            c = conn.cursor(dictionary=True)
            c.execute(SQL)
            conn.commit()

            c.close()
            conn.close()
            return True

        except:
            return False

    #Retorna o resultado do SELECT COUNT(*)
    def executaCountBD(self,SQL,online):
        try:
            conn = self.conectarBD(online)

            if conn == False:
                return False

            c = conn.cursor(dictionary=True)
            c.execute(SQL)

            r = c.fetchone()
            
            c.close()
            conn.commit()
            conn.close()

            return r[next(iter(r))]

        except:
            return False

    #Retorna uma lista de dicionários, com os resultados da pesquisa
    def pesquisarBD(self, SQL, online):
        try:
            conn = self.conectarBD(online)

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
            return False

    # Executa uma procedure criada no banco
    def executaProcedure(self, SQL, online, *args):
        try:
            conn = self.conectarBD(online)

            if conn == False:
                return False

            c = conn.cursor(dictionary=True)
            c.callproc(SQL, *args)
            conn.commit()

            c.close()
            conn.close()

            return True

        except:
            return False
        
# ++++++++++++++++++++++++++++++++++++ #
# Classes auxiliares de armazenamento  #
# ++++++++++++++++++++++++++++++++++++ #
class tipoMaquina:
    def __init__(self):
        self.cod = 0
        self.tipo = ''

class comunicacao:
    def __init__(self):
        self.cod = 0
        self.protocolo = ''
        self.parametro = []
        
class parametro:
    def __init__(self):
        self.cod = 0
        self.nome = ''
        self.valor = ''

class variavel:
    def __init__(self):
        self.cod = 0
        self.nome = ''
        self.tipoVariavel = tipoVariavel()
        self.trigger = trigger()
        self.ultEstado = 0
        self.propriedadePai = None
        self.endereco = 0
        self.tipoValor = tipoValor()
        self.valor = ''
        self.novoValor = ''
        self.escreverNovoValor = False
        self.unidadeValor = ''
        self.multiplicador = 1.0
        self.somador = 0.0
        self.valorMin = ''
        self.valorMax = ''
        self.segundosAttSite = 15
        self.registraHistorico = False
        self.tempoRegistroSegundos = 60
        self.bit = 1
        self.forcar = False
        self.forcado = False
        self.codSensor = ''
        self.leitura_escrita = ''
        self.retentividade = ''
        self.disp_ext = ''
        self.valor_inic = ''
        self.ultTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timeStamp = ''

class variavelHistorico:
    def __init__(self):
        self.codPropriedade = 0
        self.valorPropriedade = ''
        self.timestamp = ''
        
class tipoVariavel:
    def __init__(self):
        self.cod = 0
        self.tipo = ''

class tipoValor:
    def __init__(self):
        self.cod = 0
        self.tipo = ''

class evento:
    def __init__(self):
        self.cod = 0
        self.nome = ''
        self.trigger = trigger()
        self.codVarAssoc = 0
        self.eveAnt = 0
        self.evePost = []
        self.eveComp = []
        self.eveAntComp = []
        self.geraEmail = False
        self.email = []
        self.assunto = ''
        self.mensagem = ''
        self.timestamp = None
        self.sinalizado = False
        self.ultTimestamp = ''
        
class eventoHistorico:
    def __init__(self):
        self.codEvento = 0
        self.timestamp = ''

class EmailEvento:
    def __init__(self):
        self.geraEmail = 0
        self.email = ''
        self.subject = ''
        self.message = ''

class trigger:
    def __init__(self):
        self.cod = 0
        self.nome = ''
        self.valor = ''

class eventosGateway:
    def __init__(self):
        self.codEvntGate = 0
        self.nomeEvntGate = ''
        self.sinalizadoGate = 0
        
class repeatedTimer(object):
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
    # Repeat the call of a function with the determined interval  #
    # interval -- in seconds (float)                              #  
    # function -- function to be triggered                        #
    # *args, **kwargs -- arguments of the function                #
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
    
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        #self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def bitsFunc(bits, *args, **kwargs):

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
    # Chama até 16 funções, de acordo com os bits ativos na word 'bits'                   #
    # bits -- unsigned inteiro contendo os bits que ativarão ou não as                    #
    # 16 funções passadas como parâmetro *args -- 1 a 16 funções                          #
    # paramsF1 - paramsF16 (argumento, ou lista de argumentos de cada uma das funções)    #
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

    params = []
    for i in range(16):
        params.append(kwargs.get('paramsF' + str(i+1) , []))

    if len(args) > 16:
        raise ValueError("Podem ser passadas no máximo 16 funções")

    #Chama a função referente ao bit acionado
    i = 0
    while i < len(args):
        if (bits & 2**i):
            if args[i] != None:
                if isinstance(params[i], list) or isinstance(params[i], tuple):
                    try:
                        args[i](*params[i])
                    except:
                        args[i](params[i])
                else:
                    args[i](params[i])

        i += 1

def sendemail(to_addr_list, cc_addr_list,
              subject, message,
              login='alarme@eyesys.com.br', password='alarme@12',
              smtpserver='pop.onti.com.br', smtpport=587):
    # ----------------------------------------------------------- #
    # Envia e-mail via smtp:                                      #
    # to_addr_list -- lista dos endereços para enviar             #      
    # cc_addr_list -- lista dos enderecos para enviar com cópia   #
    # login='alarme@eyesys.com.br', password='alarme@12',         #
    # smtpserver='pop.onti.com.br', smtpport=587                  #
    # ----------------------------------------------------------- #
    from smtplib import SMTP
    from email.header import Header
    from email.mime.text import MIMEText

    msg = MIMEText(message, 'plain', 'utf-8')
    
    msg['From'] = login
    msg['To'] = ','.join(to_addr_list)
    msg['Cc'] = ','.join(cc_addr_list)
    msg['Subject'] = Header(subject, 'utf-8')

    server = SMTP(host=smtpserver, port=smtpport, timeout=110)
    server.starttls()
    server.login(login, password)
    problems = server.send_message(msg)
    server.quit()

# Classe de coleta de valores de Entradas Digitais 
class EntradasDigitais(Thread):
    def __init__(self):

        Thread.__init__(self)
        #cria as entradas digitais
        
        #bus = SMBus(0)  # Rev 1 Pi uses 0
        self.__bus = SMBus(1)

        # Inicializa EDs
        self.__DEVICE = 0x20 # Device address (A0-A2)
        self.__IODIRA = 0x00 # Pin direction register
        self.__IODIRB = 0x01 # Pin direction register
        self.__GPPUA  = 0x0C # Register for internal pull-up 
        self.__GPIOA  = 0x12 # Register for inputs
        self.__GPIOB  = 0x13 # Register for inputs
        
        # Set first 8 GPA pins as inputs.
        self.__bus.write_byte_data(self.__DEVICE,self.__IODIRA,0xFF)

        # Set all 8 input internal pull-up
        self.__bus.write_byte_data(self.__DEVICE,self.__GPPUA,0xFF)
        
        self.Entradas = 0
        self.getMaq = None

    def run(self):

        while not interromper:
            for maq in self.getMaq:            # Máquina por máquina
                for pacTVar in maq.pacotesVar: # Propriedade de máquina
                    for conjVar in pacTVar:    # Propriedade por propriedade
                        if not type(conjVar) == list:
                            if conjVar.tipoVariavel.tipo == 'Contador':
                                for allPro in maq.pacotesVar:
                                    for proMaq in allPro:
                                        if not type(proMaq) == list:
                                            if conjVar.propriedadePai == proMaq.cod:
                                                bit = 0
                                                for DI in range(8):
                                                    valBit = self.Entradas & 2**bit
                                                    bit += 1
                                                    if proMaq.endereco == bit:
                                                        if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                                            if conjVar.forcar:
                                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                                else:                                            conjVar.forcado = False
                                                            else: conjVar.forcado = False

                                                            conjVar.valor = conjVar.novoValor

                                                        else:
                                                            conjVar.forcado = False

                                                            if conjVar.ultEstado != (1 if valBit > 0 else 0):
                                                                if   conjVar.trigger.nome == 'Transição 0 -> 1':
                                                                    if (1 if valBit > 0 else 0) != 0:
                                                                        conjVar.valor = int(conjVar.valor)
                                                                        conjVar.valor += 1
                                                                        #print(conjVar.valor)
                                                                 
                                                                elif conjVar.trigger.nome == 'Transição 1 -> 0':
                                                                    if (1 if valBit > 0 else 0) != 1:
                                                                        conjVar.valor += 1
                                         
                                                                elif conjVar.trigger.nome == 'Qualquer transição':
                                                                    conjVar.valor += 1

                                                                conjVar.ultEstado = (1 if valBit > 0 else 0)

                                                        if conjVar.escreverNovoValor:conjVar.escreverNovoValor = False

                                                conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def entradasDigitais(self):

        global Entradas
        global wdt
        global interromper
       
        #bus = SMBus(0)  # Rev 1 Pi uses 0
        self.__bus = SMBus(1)
        
        # Inicializa EDs
        self.__DEVICE = 0x20 # Device address (A0-A2)
        self.__IODIRA = 0x00 # Pin direction register
        self.__IODIRB = 0x01 # Pin direction register
        self.__GPPUA  = 0x0C # Register for internal pull-up
        self.__GPIOA  = 0x12 # Register for inputs
        self.__GPIOB  = 0x13 # Register for inputs
        #
        # Set first 8 GPA pins as inputs.
        self.__bus.write_byte_data(self.__DEVICE,self.__IODIRA,0xFF)
        #
        # Set all 8 input internal pull-up
        self.__bus.write_byte_data(self.__DEVICE,self.__GPPUA,0xFF)
        self.Entradas = self.__bus.read_byte_data(self.__DEVICE, self.__GPIOA)
        self.Entradas = self.Entradas ^ 255
        #
     
        Entradas = self.Entradas
    
        # Colhe o valor de cada uma das entradas digitais

        # Acessa as listas repassadas da classe de Máquina onde há as variaveis
        for maq in self.getMaq:
            for pacTVar in maq.pacotesVar:
                for conjVar in pacTVar:
                    if type(conjVar) == list:pass
                    else:
                        # Encontra variaveis do tipo Entrada Digital 'ED'
                        if conjVar.tipoVariavel.tipo == 'ED':
                            bit = 0
                            for DI in range(8):                 # Número de entradas físicas
                                valBit = self.Entradas & 2**bit # Endereço
                                bit += 1                        # Variável auxiliar

                                if conjVar.endereco == bit:
                                    # Palavra-Chave : PZ1
                                    if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                        if conjVar.forcar:
                                            if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                            else:                                            conjVar.forcado = False
                                        else: conjVar.forcado = False

                                        conjVar.valor = conjVar.novoValor

                                    else:
                                        conjVar.forcado = False
                                        conjVar.valor = (1 if valBit > 0 else 0)

                                    if conjVar.escreverNovoValor:conjVar.escreverNovoValor = False

                                    conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ # 
# Classe de coleta de valores de Entradas Analógicas   #         
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ # 
class EntradasAnalogicas(Thread): 
    def __init__(self):
        Thread.__init__(self)
        self.__fechar = False
        #bus = SMBus(0)  # Rev 1 Pi uses 0
        self.__bus = SMBus(1)
        self.ctrl = ControleEnergia()
        self.getMaq = None
        self.evntsGateway = None
        self.histGate = []

    def run(self):

        global wdt
        global interromper

        while 1:
            wdt[1] = 1
            # Enquanto não houver interrupções, o looping continua em funcionamento
            while not interromper:
                sleep(0.5)
                # Acessa as listas repassadas da classe de Máquina, onde há as variaveis
                for maq in self.getMaq:
                    for pacTVar in maq.pacotesVar:
                        end0 = 0xC4
                        bit  = 0
                        for conjVar in pacTVar:
                            if type(conjVar) == list:pass
                            else:
                                # Encontra variaveis do tipo Entrada Analógica 'EA'
                                if conjVar.tipoVariavel.tipo == 'EA':
##                                    bit = 0     # Variável auxiliar
##                                    end0 = 0xC4 # Endereço
                                                               
                                    bit += 1
                                    
                                    if conjVar.endereco == bit:
                                            
                                        try:
                                            data = [end0, 0x83]
                                            self.__bus.write_i2c_block_data(0x48, 0x01, data)
                                            sleep(0.02) # Tempo para troca de canais

                                            # Lê o dado de 0x00(00), 2 bytes
                                            data = self.__bus.read_i2c_block_data(0x48, 0x00, 2)

                                            gateway.eventosGateway(self, 9 , False)
                                        except:
                                            gateway.eventosGateway(self, 9 , True)
                                            break
                                        
                                        # Conversão do dado
                                        val = data[0] * 256 + data[1]
                                                                           
                                        if conjVar.endereco == bit:
                                            # Palavra-Chave : PZ1
                                            if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                                if conjVar.forcar:
                                                    try:
                                                        if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                        else:                                            conjVar.forcado = False
                                                    except:
                                                        if float(conjVar.valor) == float(conjVar.novoValor): conjVar.forcado = True
                                                        else:                                            conjVar.forcado = False
    
                                                                                                                    
                                                else: conjVar.forcado = False
                                                conjVar.valor = conjVar.novoValor
                                            else:
                                                conjVar.valor = (val - 65535 if val > 32767 else val)
                                                conjVar.forcado = False
                                                
                                            if conjVar.escreverNovoValor:conjVar.escreverNovoValor = False

                                            conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                        # Soma para acessar novo endereço fisíco de entrada analógica
                                        end0 += 0x10

                                        
                # Palavra-Chave : PZ2
                break

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ # 
# Classe de coleta de valores de variaveis internas    #
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ #
class VariaveisInternas(Thread):
    def __init__(self):

        Thread.__init__(self)
        self.ctrl = ControleEnergia()
        self.getMaq = None
        self.IL     = []
        
    def variaveisInternas(self,IL):
        self.IL = IL
        # Acessa as listas repassadas da classe de Máquina, onde há as variaveis
        for maq in self.getMaq:
            for pacTVar in maq.pacotesVar:
                for conjVar in pacTVar:
                    if type(conjVar) == list:pass
                    else:
                        # Encontra variaveis do tipo 'Interna'
                        if conjVar.tipoVariavel.tipo == 'IL':
                            
                            for IL in self.IL:
                                if conjVar.nome == IL:
                                    if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                        if conjVar.forcar:
                                            if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                            else:                                            conjVar.forcado = False
                                        else: conjVar.forcado = False
                                        conjVar.valor = conjVar.novoValor
                                    else:
                                        conjVar.valor = self.IL[conjVar.nome]
                                        conjVar.forcado = False

                                    if conjVar.escreverNovoValor:conjVar.escreverNovoValor = False
                                    conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ++++++++++++++++++++++++++++++++++++++++++ #
# Classe de coleta de valores dos sensores   #
# ++++++++++++++++++++++++++++++++++++++++++ #
class SensorInteligente(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.getMaq = None
        self.evntsGateway = None
        self.histGate = []
        
    def run(self):

        global interromper

        while 1:

            wdt[6]   = 1
            count    = 0
            sensorOk = 0
            
            # Enquanto não houver interrupções, o looping continua em funcionamento
            while not interromper:
                sleep(0.3)
                # Acessa as listas repassadas da classe de Máquina, onde há as variaveis
                for maq in self.getMaq:
                    for vari in maq.variavel:
                        # Encontra variaveis do tipo sensor inteligente
                        if vari.tipoVariavel.cod == 10:
                
                            # Monta o caminho com o código do sensor
                            read = '/sys/bus/w1/devices/' + vari.codSensor + '/w1_slave'

                            #print('tamanho do codigo:',len(vari.codSensor),'Codigo:',vari.codSensor)
                            #print(read)
                            count += 1
                            
                            try:
                                #print('entrou no try')
                                # Abre o arquivo e lê todas as linhas
                                arq = open(read,'r')
                                lines = arq.readlines()
                                arq.close()

                                #print('arquivo',arq)
                                # Se o CRC for igual a 'YES' significa que o sensor esta ok
                                # e então é pego a temperatura
                                if lines[0].strip()[-3:] == 'YES':
                                    temperatura = lines[1]
                                    temperatura = temperatura[lines[1].find('t=')+2:-1]

                                    sensorOk += 1
                                    #gateway.eventosGateway(self, 8 , False)

                                    vari.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")#data e hora atual
                                
                                    
                                # Caso o CRC seja 'NO' significa que o sensor não esta ok
                                else:
                                    temperatura = vari.valor
                                    #gateway.eventosGateway(self, 8 , True)

                                #print(vari.timeStamp)
                                
                            except:
                                #print('erro no try')
                                temperatura = vari.valor

                            wdt[6] = 1
                            
                            # Palavra-Chave : PZ1
                            if vari.escreverNovoValor == True or vari.forcar == True:
                                if vari.forcar:
                                    if int(vari.valor) == int(vari.novoValor): vari.forcado = True
                                    else:                                      vari.forcado = False
                                else: vari.forcado = False
                            else:
                                if str(temperatura) != '85000':
                                    vari.valor = temperatura
                                    vari.forcado = False
                            
                            if vari.escreverNovoValor:vari.escreverNovoValor = False

                            
                if count == sensorOk: gateway.eventosGateway(self, 8 , False)
                else:                 gateway.eventosGateway(self, 8 , True)
                # Palavra-Chave : PZ2                
                break
                                    
class GeradorCloro(Thread):
     
    def __init__(self, usandoPonti):
        Thread.__init__(self)

        self.checksum = 0
        self.respID = 0

        self.porta_serial = serial.Serial()

        self.porta_serial.port = '/dev/ttyUSB0'
        self.porta_serial.baudrate = 9600
        self.porta_serial.databits = 8
        self.porta_serial.parity = serial.PARITY_NONE
        self.porta_serial.stopbits = serial.STOPBITS_ONE
        try:self.porta_serial.open()
        except:pass
        self.tambuffer = False
        
        # Pergunta - Percentual   - b'\x10\x02\x50\x11\x64\xD7\x10\x03'
        # Pergunta - Obter Status - b'\x10\x02\x50\x00\x00\x62\x10\x03'
        # Pergunta - Obter Versão - b'\x10\x02\x50\x14\x00\x76\x10\x03'
        
        self.request = b'\x10\x02\x50\x14\x00\x76\x10\x03'
        self.errCloro = Event()
        self.getMaq = None
        self.LIC  = None

        self.usandoPonti = usandoPonti
        
    def run(self):

        global interromper
        global wdt

        while 1:
            wdt[5] = 1
            while not interromper and not self.usandoPonti.isSet():
                
                sleep(0.5)
                wdt[5] = 1
                for maq in self.getMaq:
                    for pacTVar in maq.pacotesVar:
                        for conjVar in pacTVar:
                            if type(conjVar) == list:pass
                            else:
                                if conjVar.tipoVariavel.tipo == 'IC':
                                    if int(conjVar.endereco) == 1:
                                        if    conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False
                                            porcentagem = str(conjVar.novoValor).zfill(2)
                                        else:
                                            conjVar.forcado = False
                                            porcentagem = str(conjVar.valor).zfill(2)
                                            try:
                                                if self.LIC[conjVar.nome] != None:
                                                    if int(self.LIC[conjVar.nome]) != int(porcentagem):
                                                        porcentagem = str(self.LIC[conjVar.nome]).zfill(2)
                                            except:pass

                                        conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                usb  = getoutput('ls /dev/ttyUSB0')
                usb1 = getoutput('ls /dev/ttyUSB1')
                usb2 = getoutput('ls /dev/ttyUSB2')
                usb3 = getoutput('ls /dev/ttyUSB3')

                if usb == '/dev/ttyUSB0' or usb1 == '/dev/ttyUSB1' or usb2 == '/dev/ttyUSB2' or usb3 == '/dev/ttyUSB3':
                    
                    if not self.errCloro.isSet(): self.request = b'\x10\x02\x50\x14\x00\x76\x10\x03'
                    else:
                        try:
                            self.request = str(porcentagem)
                            prefixo = b'\x10\x02\x50\x11'
                            radical = bytes([int(self.request)])
                            check = bytes([(int(prefixo[2]) + int(prefixo[3]) + int(self.request) + 18)])
                            sufixo  = b'\x10\x03'
                            self.request = prefixo + radical + check + sufixo
                        except: self.request = b'\x10\x02\x50\x14\x00\x76\x10\x03'

                    try:
                        self.porta_serial.flushInput()
                        self.porta_serial.write(self.request)
                        self.getAnswer()
                    except:pass
                break

    def getAnswer(self):

        self.checksum = 0
        self.tambuffer = 0
        trava=None
        
        #Aguarda chegar os primeiros bytes:
        while not self.tambuffer:
        
            sleep(0.0365)
            
            if not trava:
                start = tempor()
                trava=True
    
            end = tempor()

            try:self.tambuffer = self.porta_serial.inWaiting()
            except:break
            
            # se não houver resposta em dois segundos, pergunta novamente
            if (end - start)>2:
                self.errCloro.clear()
                return
            
        # Tenta ler a resposta
        try:answer = self.porta_serial.read(self.tambuffer)
        except:pass
        
        # Verifica bytes de entrada, saida e destino
        if answer[0]  == 16 and answer[1]  == 2 and \
           answer[-2] == 16 and answer[-1] == 3 and \
           answer[2]  == 0:

            # Identifica o tipo da resposta 
            if len(answer) == 9:
                
                for i in range(4):
                    self.checksum = self.checksum + answer[2+i]
                self.checksum = self.checksum + 18

                # Verifica o Checksum
                if answer[6] == self.checksum:

                    # Direciona a função correspondente
                    if   self.request[3] == 0  and answer[3] == 1:  self.respID = 1 #getSinal(resp)
                    elif self.request[3] == 17 and answer[3] == 18: self.respID = 2 #setPercentual(resp)
                    else:
                        self.errCloro.clear()
                        return #color.write("\nResposta invalida\n","ERROR")                        
                else:
                    self.errCloro.clear()
                    return #color.write("\nChecksum invalido\n","ERROR")            
            else:
                if self.request[3] == 20 and answer[3] == 3:
                    
                    for i in range(19):
                        self.checksum = self.checksum + answer[2+i]
                    self.checksum = self.checksum + 18
                
                    if answer[21]+(5*256) == self.checksum: self.respID = 3
                        
                    else:
                        self.errCloro.clear()
                        return #color.write("\nChecksum invalido\n","ERROR")                    
                else:
                    self.errCloro.clear()
                    return #color.write("\nResposta invalida\n","ERROR")            
        else:
            self.errCloro.clear()
            return #color.write("\nPadrão de resposta desconhecido\n","ERROR")
            
        if self.respID == 1: pass
        if self.respID == 2:

            try:
                perc = self.request[4]
                PPM = answer[5]*50
                status =  answer[6]

                for maq in self.getMaq:
                    for pacTVar in maq.pacotesVar:
                        for conjVar in pacTVar:
                            if type(conjVar) == list:pass
                            else:
                                if conjVar.tipoVariavel.tipo == 'IC':
                                    if   int(conjVar.endereco) == 1:
                                        if    conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False
                                            conjVar.valor = conjVar.novoValor
                                        else:
                                            conjVar.valor = perc
                                            conjVar.forcado = False
                                            
                                    elif int(conjVar.endereco) == 2:
                                        if    conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False
                                            conjVar.valor = conjVar.novoValor
                                        else:
                                            conjVar.valor = PPM
                                            conjVar.forcado = False
                                            
                                    elif int(conjVar.endereco) >= 10:
                                        if    conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False
                                            conjVar.valor = conjVar.novoValor
                                        else:
                                            conjVar.forcado = False
                                            vBit = (status & 1)
                                            status = status >>  1
                                            conjVar.valor = vBit

                                    conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return
            except:pass                       
                                        
        if self.respID == 3:
                
            try:
                versao = str(answer)
                versao = versao[22:38]

                for maq in self.getMaq:
                    for pacTVar in maq.pacotesVar:
                        for conjVar in pacTVar:
                            if type(conjVar) == list:pass
                            else:
                                if conjVar.tipoVariavel.tipo == 'IC':
                                    if int(conjVar.endereco) == 3:
                                        if    conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False
                                            conjVar.valor = conjVar.novoValor
                                        else:
                                            conjVar.forcado = False
                                            conjVar.valor = versao

                                        conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        
                                        self.errCloro.set()
                                        return
            except: ('erro')

# +++++++++++++++++++++++++++++++++++++++++++++++++++ #
# Classe de escrita nas saídas digitais do Gateway    #
# +++++++++++++++++++++++++++++++++++++++++++++++++++ #
class SaidasDigitais(Thread):          
    def __init__(self, DesligarDOs=False):

        Thread.__init__(self)
        
        #bus = SMBus(0)  # Rev 1 Pi uses 0
        self.__bus = SMBus(1)
    
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        # Inicializa SDs                                                   #
        self.__DEVICE = 0x20 # Device address (A0-A2)                      #
        #self.__IODIRA = 0x00 # Pin direction register                     #
        self.__IODIRB = 0x01 # Pin direction register                      #
        #self.__GPPUA  = 0x0C # Register for internal pull-up              #
        #self.__OLATA  = 0x14 # Register for outputs                       #
        self.__OLATB  = 0x15 # Register for outputs                        #
        #self.__GPIOA  = 0x12 # Register for inputs                        #
        self.__GPIOB  = 0x13 # Register for inputs                         #
        #                                                                  #
        # Set last 8 GPA pins as outputs.                                  #
        self.__bus.write_byte_data(self.__DEVICE, self.__IODIRB, 0x00)     #
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

        # Set output all 8 output bits to 0
        if (DesligarDOs):
            Saidas=0
            self.__bus.write_byte_data(self.__DEVICE, self.__OLATB, Saidas)

        # Variaveis auxiliares
        self.Entradas = 0
        self.trava = False
        self.ctrl = ControleEnergia()
        self.getMaq = None
        
    def escreverSaidas(self, LDO):

        global wdt
        global interromper

        # A lista de saídas digitais pode estar vazia se:
        # Não ocorreu nenhuma alteração nas saídas no último ciclo lógico
        # Se for a primeira vez do programa rodando
        if not LDO == {}:        

            #bus = SMBus(0)  # Rev 1 Pi uses 0                                  # 
            self.__bus = SMBus(1)                                               #
            #                                                                   #
            self.__DEVICE = 0x20 # Device address (A0-A2)                       #
            self.__IODIRB = 0x01 # Pin direction register                       #
            self.__OLATB  = 0x15 # Register for outputs                         #
            self.__GPIOB  = 0x13 # Register for inputs                          #
            #                                                                   #
            # Set last 8 GPA pins as outputs.                                   #
            self.__bus.write_byte_data(self.__DEVICE, self.__IODIRB, 0x00)      #

            # Listas dentro de lista auxiliar
            Saidas = [[0],[0],[0],[0],[0],[0],[0],[0]]

            # Acessa as listas repassadas da classe de Máquina, onde há as variaveis
            for maq in self.getMaq:
                for pacTVar in maq.pacotesVar:
                    for conjVar in pacTVar:
                        if type(conjVar) == list:pass
                        else:
                            # Encontra na lista variaveis do tipo Saída Digital (SD)
                            if conjVar.tipoVariavel.tipo == 'SD': 
                                #Percorre a lista de Saídas Digitais a serem escritas
                                for DO in LDO:
                                    # Até encontrar a qual variável se refere
                                    if conjVar.nome == DO:
                                        # Palavra-Chave = PZ1
                                        if conjVar.escreverNovoValor == True or conjVar.forcar == True:
                                            if conjVar.forcar:
                                                if int(conjVar.valor) == int(conjVar.novoValor): conjVar.forcado = True
                                                else:                                            conjVar.forcado = False
                                            else: conjVar.forcado = False

                                            Saidas[conjVar.endereco - 1][0] = int(conjVar.novoValor)*(2**(conjVar.endereco - 1))
                                            conjVar.valor = conjVar.novoValor

                                        else:
                                            # ------------------------------------------------------------------------------------------- #
                                            # Preenche na lista de Saidas os valores a serem escritos.                                    #
                                            # Cada endereço de saída esta diretamente ligado a sua posição em bytes, por exemplo,         #
                                            # o bit mais significativo da saída digital 8 é o de 8° posição, logo seu valor é 2**8 = 128  #
                                            # ------------------------------------------------------------------------------------------- #
                                            Saidas[conjVar.endereco - 1][0] = LDO[DO]*(2**(conjVar.endereco - 1)) 
                                            conjVar.valor = LDO[DO]

                                            conjVar.forcado = False
                                            
                                        if conjVar.escreverNovoValor:conjVar.escreverNovoValor = False

                                        conjVar.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
            # Reúne e soma as listas em uma única variável para ser escrita nas saídas fisícas
            Escrever = Saidas[0][0] + Saidas[1][0] + Saidas[2][0] + Saidas[3][0] + Saidas[4][0] + Saidas[5][0] + Saidas[6][0] + Saidas[7][0]
            self.__bus.write_byte_data(self.__DEVICE, self.__OLATB, Escrever)

# +++++++++++++++++++++++++++++++++ #
# Classe de supervisão da energia   #
# +++++++++++++++++++++++++++++++++ #
class ControleEnergia(Thread):
    def __init__ (self, gpioSD=38, gpioED=40):
        Thread.__init__(self)

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        # Objeto para controle de energia.                                                       #
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
        # gpioSD: Numero do pino do GPIO que será a saída para o relé que mantém o RPi ligado.   #
        # gpioED: Numero do pino do GPIO que será a entrada que detecta a queda de energia.      #
        # parametrosDesligamento: lista de parâmetros para a função de desligamento.             #
        # parametrosInicioNormal: lista de parâmetros para a função de inicio normal.            # 
        # parametrosInicioAnormal: lista de parâmetros para a função de inicio anormal.          #
        #                                                                                        #
        self.__gpioSD = gpioSD                                                                   #
        self.__gpioED = gpioED                                                                   #
        #                                                                                        #
        GPIO.setmode(GPIO.BOARD)                                                                 # 
        GPIO.setwarnings(False)                                                                  #
        #                                                                                        #
        GPIO.setup(self.__gpioSD, GPIO.OUT)                                                      #
        GPIO.setup(self.__gpioED, GPIO.IN, pull_up_down= GPIO.PUD_DOWN)                          #
        #                                                                                        #
        GPIO.output(self.__gpioSD, GPIO.HIGH)                                                    #
        #                                                                                        #
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

        self.arquivo = "Desligado.txt"
        self.interromper = interromper
        self.acabouEnergia = None
        self.quedaEnergia  = False
        try: remove(self.arquivo)
        except:pass

        self.histGate     = None
        self.evntsGateway = None
        
        # Começa a verificar a energia
        #self.start()
    
    def getAcabouEnergia(self):
        # Indica que não há energia a pelo menos 10s
        return self.acabouEnergia

    def getQuedaEnergia(self):
        # Indica que houve queda de energia
        return self.quedaEnergia
    
    def getAtualizacao(self):
        # Indica se algum bit está em execução
        return self.interromper

    # -------------------------------------------------------------- #
    # Função responsável por:                                        #
    # 1 - Criar um arquivo de texto chamado de "Desligado"           #
    # 2 - Copiar o banco de dados atual e colocar na pasta de backup #
    # 3 - Levar o arquivo de dados da RAM à pasta raíz do Gateway    #
    # 4 - Cria a pasta de relatório e salva o relatório do shell     #
    # 5 - Ocorre o desligamento                                      #
    # -------------------------------------------------------------- #
               
    def run(self):

        # Variaveis auxiliares
        global wdt
        Tem24V = False
        Temporizando_Acabou24V = None
        agora = None       
        wdt[7] = 1
        
        while 1:
            sleep(1)
            # Variavel usada como flag para indificar se há atualização:    
            self.interromper = interromper
            
            # Verifica se há energia:                
            Tem24V = (GPIO.input(self.__gpioED) == 1)

            
            try:gateway.eventosGateway(self, 25, False)
            except:pass
            
            # Se não houver, um contador é iniciado e flags são levantadas
            if not Tem24V:

                self.quedaEnergia = True
                try:gateway.eventosGateway(self, 5, True)
                except:pass
    
                if not Temporizando_Acabou24V:
                    t_acabou24V = tempor()
                    Temporizando_Acabou24V = True

                agora = tempor()
                
                # Após 10 segundos sem alimentação procede com o desligamento

                if (agora - t_acabou24V) > 10:
                    self.acabouEnergia = True
                    try:gateway.eventosGateway(self, 4, True)
                    except:pass

            else:
                # Se houver alimentação mantém o temporizador em zero
                Temporizando_Acabou24V  = False
                self.acabouEnergia      = False
                self.quedaEnergia       = False

                try:
                    for evt in self.evntsGateway:
                        if evt.codEvntGate == 4:
                            if evt.sinalizadoGate:
                                try:
                                    arq = open('/usr/lib/'+str(gateway.getPythonVer(self))+'/Desligado','r')
                                    arq.readlines()
                                    arq.close()
                                    gateway.eventosGateway(self, 16, True)
                                    getoutput('sudo rm /usr/lib/'+str(gateway.getPythonVer(self))+'/Desligado')
                                except: gateway.eventosGateway(self, 17, True)
                                    
                    gateway.eventosGateway(self, 16, False)
                    gateway.eventosGateway(self, 17, False)
                    gateway.eventosGateway(self, 4, False)
                    gateway.eventosGateway(self, 5, False)

                except:pass
            
            wdt[7] = 1

# +++++++++++++++++++++++++++++++++++++++++++++++ #
# Classe de supervisão dos loopings do programa   #
# +++++++++++++++++++++++++++++++++++++++++++++++ #
class watchDogReset(Thread):

    def __init__ (self):

        Thread.__init__(self)
    
        # Configuração dos pinos 29 e 31 reservados para o watchdog
        GPIO.setup(29, GPIO.OUT)
        GPIO.output(29, GPIO.HIGH)

        # Habilita somente o WDT de 180 s. Deve ser dado um pulso de 01 S, a cada 15 S, se todas as
        # rotinas estiverem normais.
        GPIO.setup(31, GPIO.OUT)
        GPIO.output(31, GPIO.LOW)

        self.evntsGateway = None
        self.histGate     = None
        self.getMaq       = None

        self.arqINI   = '/mnt/CLP/connMySQL.ini'    
        self.arqOFF   = '/mnt/CLP/connMySQLOFF.ini' 
        
    # ++++++++++++++++++++++++++++++++++++++++++++++++ #
    # Looping de reset dos pinos 29 e 31 do Gateway.   #
    # Os pinos são constamente jogados em baixo nível  #
    # ++++++++++++++++++++++++++++++++++++++++++++++++ #

    def run(self):

        global interromper
        global wdt

        GPIO.output(29, GPIO.HIGH)

        def reset():

            while 1:

                sleep(3)
                
                start = 0
                end   = 0
                trava = False
                
                if GPIO.input(29) == 1 and GPIO.input(31) == 1:

                    while (end - start) < 1:
                        
                        if not trava:
                            start = tempor()
                            trava=True

                            GPIO.output(29, GPIO.LOW) # Temporizador de segundos
                            GPIO.output(31, GPIO.LOW) # Temporizador de minutos                   
                            
                        end = tempor()   

        # Inicialização do looping de reset
        rst = Thread(target=reset)
        rst.start()

    # ------------------------------------------------------------------------ #
    # Se algum dos pinos ficar por muito tempo em baixo nível, significa que   #
    # algum looping parou de funcionar e então o Gateway será reiniciado       #
    # ------------------------------------------------------------------------ #

        start = tempor()
        end   = tempor()
        trava = False

        inicio = tempor()
        fim    = tempor()
        block  = False

        i_evento = tempor()
        f_evento = tempor()
        barragem = False

        while 1:

            sleep(0.5)
            
            if not interromper:

                if not trava:
                    start = tempor()
                    trava=True

                end = tempor()
                fim = tempor()
                f_evento = tempor()

            else:
                GPIO.output(29, GPIO.HIGH)
                GPIO.output(31, GPIO.HIGH)
                
            if (end-start) > 10:
                for i in range(len(wdt)):
                    if wdt[i] == 0:
                        if   i == 7:gateway.eventosGateway(self, 25, True)
                        elif i == 10:gateway.eventosGateway(self, 27, True)
                        elif i == 0:gateway.eventosGateway(self, 26, True)

                print(wdt)
                
                getoutput("sudo cp /mnt/CLP/Shell /home/pi/Report/"+str(datetime.now().strftime('%Y%m%d%H%M')))
                trava = False
                
            if (fim-inicio) > 600:

                gateway.eventosGateway(self, 26, True)
                sleep(2)
                gateway.salvarTudo(self, self.arqINI, self.arqOFF)

            wdt[0] = 1

            if wdt[0] == 0 and not 0 in wdt[1:]:

                GPIO.output(29, GPIO.HIGH)
                GPIO.output(31, GPIO.HIGH)

                for i in range(len(wdt)):
                    if not i == 0:
                        if wdt[i] == 1: wdt[i] = 0

                trava = False

                if not barragem:
                    i_evento = tempor()
                    barragem = True

                if (f_evento-i_evento) > 60:
                    gateway.eventosGateway(self, 6, True)
                    gateway.eventosGateway(self, 26, False)
                    if not block:
                        inicio = tempor()
                        block = True 
            else: 

                while not 0 in wdt:
                    
                    GPIO.output(29, GPIO.HIGH)
                    GPIO.output(31, GPIO.HIGH)

                    for i in range(len(wdt)):
                        if wdt[i] == 1: wdt[i] = 0

                    trava = False
                    block = False
                    barragem = False
                    inicio = tempor()
                    i_evento = tempor()

                    gateway.eventosGateway(self, 6, False)
                    gateway.eventosGateway(self, 26, False)
                    
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ #
# Classe de comunicação e coleta de variáveis ModBus   #
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ #
class Modbus(Thread):
    def __init__(self, usandoPonti):
        Thread.__init__(self)
        self.ctrl         = ControleEnergia()
        self.getMaq       = None
        self.evntsGateway = None
        self.histGate     = None

        self.usandoPonti = usandoPonti
        
    # Looping principal
    def run(self):

        # ++++++++++++++++++++++++++++ #
        # Configurações e bibliotecas  #
        # ++++++++++++++++++++++++++++ #
        global interromper
        import minimalmodbus as mmodbus
        mmodbus.CLOSE_PORT_AFTER_EACH_CALL=True
        from struct import pack,unpack
        global wdt

        while 1:
            # Sinaliza à classe de Watchdog que o looping esta em funcionamento
            wdt[4] = 1

            # Enquanto não houver interrupções, o looping continua em funcionamento
            while not interromper and not self.usandoPonti.isSet():
                
                # Acessa as listas repassadas da classe de Máquina, onde há as variaveis
                for maq in self.getMaq:
                    for pacTVar in maq.pacotesVar:
                        for conjVar in pacTVar:
                            sleep(0.1)
                            wdt[4] = 1
                            # Se um conjunto de Variáveis é do tipo lista significa que são variaveis do tipo ModBus 
                            if type(conjVar) == list:
                                # Verifica se alguma das portas USB esta sendo utilizado e coleta o retorno para guardar em variaveis
                                usb  = getoutput('ls /dev/ttyUSB0')
                                usb1 = getoutput('ls /dev/ttyUSB1')
                                usb2 = getoutput('ls /dev/ttyUSB2')
                                usb3 = getoutput('ls /dev/ttyUSB3')
                                
                                if usb == '/dev/ttyUSB0' or usb1 == '/dev/ttyUSB1' or usb2 == '/dev/ttyUSB2' or usb3 == '/dev/ttyUSB3':

                                    # Pega o endereço do escravo que foi passado
                                    endEscravo = int(maq.findValInComunicacao('modbusrtu', 'Endereço Escravo'))
                                    
                                    if endEscravo > 0:

                                        # Discrimina qual porta esta sendo usada para comunicação, repassa o endereço e configura para modo 'rtu'
                                        try:mbus = mmodbus.Instrument('/dev/ttyUSB0', endEscravo, mode='rtu')
                                        except FileNotFoundError as ex:
                                            if 'No such file or directory' in str(ex):
                                                try:mbus = mmodbus.Instrument('/dev/ttyUSB1', endEscravo, mode='rtu')
                                                except FileNotFoundError as ex:
                                                    if 'No such file or directory' in str(ex):
                                                        try:mbus = mmodbus.Instrument('/dev/ttyUSB2', endEscravo, mode='rtu')
                                                        except FileNotFoundError as ex:
                                                            if 'No such file or directory' in str(ex):
                                                                try:mbus = mmodbus.Instrument('/dev/ttyUSB3', endEscravo, mode='rtu')
                                                                except FileNotFoundError as ex:
                                                                    gateway.eventosGateway(self, 7 , True)
                                                                    break 
                                        except:
                                            try:mbus = mmodbus.Instrument('/dev/ttyUSB1', endEscravo, mode='rtu')
                                            except:
                                                try:mbus = mmodbus.Instrument('/dev/ttyUSB2', endEscravo, mode='rtu')
                                                except:
                                                    try:mbus = mmodbus.Instrument('/dev/ttyUSB3', endEscravo, mode='rtu')
                                                    except:
                                                        gateway.eventosGateway(self, 7 , True)
                                                        break

                                        # Coleta, respectivamente, as informações de baudrate, bytesize, parity, stopbit e timeout
                                        mbus.serial.baudrate = int(maq.findValInComunicacao('modbusrtu', 'Baudrate'))
                                        mbus.serial.bytesize = int(maq.findValInComunicacao('modbusrtu', 'BitSize'))
                                        mbus.serial.parity   = maq.findValInComunicacao('modbusrtu', 'paridade')[:1].upper()
                                        mbus.serial.stopbits = int(maq.findValInComunicacao('modbusrtu', 'stopbits'))
                                        mbus.serial.timeout  = 3

                                        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
                                        # Verifica se irá escrever em algum dos registros                                                                                                           #
                                        # A escrita de um registro em um dispositivo externo é feita a partir do bit 4                                                                              #
                                        #                                                                                                                                                           #
                                        for vari in maq.variavel:                                                                                                                                   #
                                            if vari.disp_ext:                                                                                                                                       #
                                                # Escreve se a variável for do tipo BOOl                                                                                                            #
                                                if   vari.tipoValor.cod == 1:    mbus.write_bit((vari.endereco - 1), int(vari.novoValor), 5)                                                        #
                                        #                                                                                                                                                           #
                                                # Escreve se a variável for do tipo INT                                                                                                             #
                                                elif vari.tipoValor.cod == 2:    mbus.write_register((vari.endereco - 1), int(vari.novoValor), 0, 16, False)                                        #
                                        #                                                                                                                                                           #
                                                # Escreve se a variável for do tipo INT CS                                                                                                          #
                                                elif vari.tipoValor.cod == 6:    mbus.write_register((vari.endereco - 1), int(vari.novoValor), 0, 16, True)                                         #
                                        #                                                                                                                                                           #
                                                # ---------------------------------------------------------------------------------------------------------------------------------------- #        #
                                                # Variáveis do tipo : Real, longa e longa com sinal recebem um tratamento diferente das demais. Quando se trata dos                        #        # 
                                                # tipos: REAL, LONGA E LONGA CS o valor, antes de ser armazenado dentro do dispositivo, tem as words trocadas, ou seja,                    #        #
                                                # a posição da word de maior valor e de menor valor são invertidas pela função de escrita do modbus, armazenando um valor no dispositivo,  #        #
                                                # equivalente,mas diferente, podendo causar confusão ao usuário, então uma adaptação foi feita.                                            #        #
                                                #                                                                                                                                          #        #
                                                # Utilizando a biblioteca 'struct' é possivel transformar, estruturar e desestruturar valores de um tipo para outro,                       #        #
                                                # sendo assim, as variaveis passaram pelas seguintes mudanças:                                                                             #        #
                                                # 1 - Foram estruturadas em um pacote de acordo com seu tipo, e em seguida desestruturadas como double unsigned short (2 bytes)            #        #
                                                # 2 - Estando no formato de bytes, foi invertido a word mais significativa com a menor significativa                                       #        #
                                                # 3 - O novo valor gerado é enviado para ser escrito. Por função da própria biblioteca de escrita do modbus, o valor                       #        #
                                                #     será novamente invertido, escrevendo assim o valor correto a ser armazenado                                                          #        #
                                                #                                                                                                                                          #        #
                                                # ---------------------------------------------------------------------------------------------------------------------------------------- #        #
                                        #                                                                                                                                                           #
                                                # Escreve se a variável for do tipo REAL                                                                                                            #
                                                elif vari.tipoValor.cod == 3:                                                                                                                       #
                                                    a = float(vari.novoValor)                                                                                                                       #
                                                    pergunta = unpack('HH',pack('f', a))                                                                                                            #
                                                    nova = unpack('L',pack('HH',pergunta[1],pergunta[0]))[0]                                                                                        #
                                                    mbus.write_long((vari.endereco - 1), nova, False)                                                                                               #
                                        #                                                                                                                                                           #
                                                # Escreve se a variável for do tipo LONGA                                                                                                           #
                                                elif vari.tipoValor.cod == 4:                                                                                                                       #
                                                    pergunta = unpack('HH',pack('L', int(vari.novoValor)))                                                                                          #
                                                    nova = unpack('L',pack('HH',pergunta[1],pergunta[0]))[0]                                                                                        #
                                                    mbus.write_long((vari.endereco - 1), int(nova), False)                                                                                          #
                                        #                                                                                                                                                           #
                                                # Escreve se a variável for do tipo LONGA CS                                                                                                        #
                                                elif vari.tipoValor.cod == 7:                                                                                                                       #
                                                    pergunta = unpack('HH',pack('l', int(vari.novoValor)))                                                                                          #
                                                    nova = unpack('l',pack('HH',pergunta[1],pergunta[0]))[0]                                                                                        #
                                                    mbus.write_long((vari.endereco - 1), int(nova), True)                                                                                           #
                                        #                                                                                                                                                           #
                                        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

                                        # --------------------------------------------------------------------------------------------------------------------------------------------- #
                                        # A pergunta feita para coletar valores do modbus é feita de forma genérica e única, para evitar multiplos acessos de leitura ao dispositivo,   #
                                        # que pode gerar estresse e muito tempo. Tendo isso em mente, a função de leitura usada nos traz vários valores de uma vez,                     # 
                                        # a consequência disto é que os valores registrados nos endereços são interpretados como únicos, sendo que, por exemplo,                        #
                                        # um valor do tipo REAL pode ocupar 2 registros.                                                                                                #
                                        #                                                                                                                                               #
                                        # A pergunta e a verificação da resposta é montada da seguinte maneira:                                                                         #
                                        # 1 - O menor endereço de registro é pego como referência, será o ponto de partida:                                                             #
                                        ref = int(conjVar[0].endereco)                                                                                                                  #
                                        #                                                                                                                                               #
                                        # 2 - A função lerá 16 registros, então o último endereço de referência poderá ser até 16 registros acima da nossa referência inicial,          #
                                        #     porém pode ocorrer que o último registro seja uma variável do tipo REAL, sendo assim, não seria coletado o valor correto armazenado,      #
                                        #     já que valores do tipo REAL usam 2 espaços de registro. Então foi adicionado ao último endereço uma folga de +1:                          #
                                        enderecoDaUltimaRef = (len(conjVar) - 1)                                                                                                        #
                                        uRef = int(conjVar[enderecoDaUltimaRef].endereco)                                                                                               #                                                                                                                                              #
                                        #                                                                                                                                               #
                                        # 3 - Com os parâmetros definidos é feita a pergunta:                                                                                           #
                                        try:resp = mbus.read_registers((ref - 1),((uRef - ref)+2), 3)                                                                                   #
                                        #                                                                                                                                               #
                                        # 4 - É verificado se a resposta esta dentro do esperado pelo cálculo do Checksum:                                                              #
                                                                                                                                                                                        #
                                        except OSError as ex:                                                                                                                           #
                                            if 'No communication' in str(ex):                                                                                                           #
                                                gateway.eventosGateway(self, 7 , True)                                                                                                  #
                                                break                                                                                                                                   #
                                                                                                                                                                                        #
                                        except ValueError as ex:                                                                                                                        #
                                            if 'Checksum error' in str(ex):                                                                                                             #
                                                gateway.eventosGateway(self, 7 , True)                                                                                                  #
                                                break                                                                                                                                   #
                                                                                                                                                                                        #
                                        #                                                                                                                                               #
                                        # 5 - Se a pergunta não pode ser enviado por algum motivo, a pergunta é refeita usando outra função de leitura (3 to 4)                         #
                                            elif 'The slave is indicating an error' in str(ex):                                                                                         #
                                                try:resp = mbus.read_registers((ref - 1),((uRef - ref)+2), 4)                                                                           #
                                                                                                                                                                                        #
                                                except OSError as ex:                                                                                                                   #
                                                    if 'No communication' in str(ex):                                                                                                   #
                                                        gateway.eventosGateway(self, 7 , True)                                                                                          #
                                                        break                                                                                                                           #
                                                                                                                                                                                        #
                                                except ValueError as ex:                                                                                                                #
                                                    if 'Checksum error' in str(ex):                                                                                                     #
                                                        gateway.eventosGateway(self, 7 , True)                                                                                          #
                                                        break                                                                                                                           #
                                                except: break                                                                                                                           #
                                        #                                                                                                                                               #
                                        # 6 - Se a resposta estiver correta, o programa localizará o tipo da variável esperada e atribuirá ao valor.                                    #
                                        #     Novamente, as variaveis do tipo Real, Longa e Longa CS tem suas words invertidas e são desinvertidas pelo programa                        #
                                        #                                                                                                                                               #
                                        for evt in self.evntsGateway:                                                                                                                   #
                                            if evt.codEvntGate == 7:                                                                                                                    #
                                                if evt.sinalizadoGate:                                                                                                                  #
                                                    gateway.eventosGateway(self, 20, True)                                                                                              #
                                                else: gateway.eventosGateway(self, 20, False)                                                                                           #
                                                                                                                                                                                        #
                                        gateway.eventosGateway(self, 7 , False)                                                                                                         #
                                                                                                                                                                                        #
                                        for var in conjVar:                                                                                                                             #    
                                            if   var.tipoValor.cod == 1:      #BOOL                                                                                                     #
                                                 try:var.valor = mbus.read_bit((var.endereco - 1),2)                                                                                    #
                                                 except: break                                                                                                                          #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if     int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                  #
                                                     else:  var.valor = '?'                                                                                                             #
                                            elif var.tipoValor.cod == 2:      #INT                                                                                                      #
                                                 try:var.valor = mbus.read_register((var.endereco - 1), 0, 3, False)                                                                    #
                                                 except: break                                                                                                                          #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                      #
                                                     else:  var.valor = '?'                                                                                                             #
                                            elif var.tipoValor.cod == 6:      #INT CS                                                                                                   #
                                                 try:var.valor = mbus.read_register((var.endereco - 1), 0, 3, True)                                                                     #
                                                 except: break                                                                                                                          #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                      #
                                                     else:  var.valor = '?'                                                                                                             #
                                            elif var.tipoValor.cod == 3:      #REAL                                                                                                     #
                                                 var.valor = unpack('f',pack('HH',resp[var.endereco - ref],resp[var.endereco - ref + 1]))[0]                                            #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                      #
                                                     else:  var.valor = '?'                                                                                                             #
                                            elif var.tipoValor.cod == 4:      #LONGA                                                                                                    #
                                                 var.valor = unpack('l',pack('HH',resp[var.endereco - ref],resp[var.endereco - ref + 1]))[0]                                            #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                      #
                                                     else:  var.valor = '?'                                                                                                             #
                                            elif var.tipoValor.cod == 7:      #LONGA CS                                                                                                 #
                                                 var.valor = unpack('l',pack('HH',resp[var.endereco - ref],resp[var.endereco - ref + 1]))[0]                                            #
                                                 if var.disp_ext:                                                                                                                       #
                                                     if int(var.novoValor) == int(var.valor): var.disp_ext = False                                                                      #
                                                     else:  var.valor = '?'                                                                                                             #
                                        # --------------------------------------------------------------------------------------------------------------------------------------------- # 

                                            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PZ1~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
                                            # É a possibilidade do usuário escrever um novo valor, sem alterar o registro no dispositivo externo                 #
                                            # Esta função é executada pelo bit 4, então, independente do valor lido acima, um novo valor será atribuído          #
                                            #                                                                                                                    #
                                            # Também é possível que o usuário deseje forçar um valor, sem alterar o registro.                                    #
                                            # Esta função é executada pelo bit 4, diferente do bit 7 que ocorre apenas uma única vez, forçar um valor se mantem  #
                                            # Até o usuário reverter.                                                                                            #
                                            #                                                                                                                    #
                                            if   var.escreverNovoValor == True or var.forcar == True:                                                            #
                                                if var.forcar:                                                                                                   #
                                                    if int(var.valor) == int(var.novoValor): var.forcado = True                                                  #
                                                    else:                                    var.forcado = False                                                 #
                                                else: var.forcado = False                                                                                        #
                                                var.valor = var.novoValor                                                                                        #
                                            else: var.forcado = False                                                                                            #
                                            if   var.escreverNovoValor: var.escreverNovoValor = False                                                            #
                                            var.timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")                                                         #
                                            #                                                                                                                    #
                                            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

                                            #print('\nModbus', var.endereco ,'-', var.nome,'- Tipo:',var.tipoValor.tipo,'- Valor:', var.valor)
                                else: gateway.eventosGateway(self, 7 , True)
                # PZ2 : A quebra do looping é feita quando já foram coletadas todos os registos esperados, para que seja sinalizado ao Watchdog que a função ainda esta em funcionamento
                break

class pOnti(Thread):

    def __init__(self, usandoPonti, codMaquina, arqINI, arqOFF, IP, Port_SA, Port_SP, timeOut, timeOut_c, ttyUSB, setBit):

        Thread.__init__(self)        

        self.usandoPonti  = usandoPonti
        self.codMaq       = codMaquina
        self.arqINI       = arqINI
        self.arqOFF       = arqOFF       
        
        self.SA_pOnti     = socket(AF_INET, SOCK_STREAM)
                
        self.timeoutInatividade = False
        self.SA_emExecucao      = False
        self.SP_emExecucao      = False
        self.conectado          = False
        self.trava              = False

        self.IP           = IP
        self.setBit       = setBit
        self.Port_SA      = Port_SA
        self.Port_SP      = Port_SP       
        self.ttyUSB       = ttyUSB
        self.pOntimeOut   = int(timeOut)
        self.pOntimeOut_c = int(timeOut_c)

        self.SA_Stop()
        self.SP_Stop()        

    def SA_Start(self):

        mysql = MySQL(self.arqINI, self.arqOFF)
        
        if not self.SA_emExecucao:

            try:
                
                self.SA_pOnti = socket(AF_INET, SOCK_STREAM)
                self.SA_pOnti.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)            
                self.SA_pOnti.bind((self.IP, self.Port_SA))            
                self.SA_pOnti.listen(1)

                self.SA_emExecucao = True

##                SQL  = "UPDATE Nuvem_Gateway INNER JOIN Nuvem_Maquina ON Nuvem_Gateway.Cod_Gateway = Nuvem_Maquina.Cod_Gateway "
##                SQL += "SET Status_pOnti = 1, Timestamp_pOnti = '"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"'"
##                SQL += " WHERE Nuvem_Maquina.Cod_Maquina = '"+str(self.codMaq)+"'"
##
##                try:mysql.executaQueryBD(SQL,True)
##                except:print_exc()
                print('Servidor Auxiliar')
                print("\nAguardando Cliente\n")
                
            except: pass
            
    def SA_Stop(self):
        
        self.SA_pOnti.close()        
        self.SA_emExecucao = False
        
    def SP_Start(self):

        while True:

            if not self.SP_emExecucao and self.conectado:
                
                try:
                    getoutput('sudo killall -9 SP_pOnti')

##                    mysql = MySQL(self.arqINI, self.arqOFF)
##                    
##                    SQL  = "SELECT pOnti_Timeout_Conexao, Porta_Servidor_Ethernet, Valor_Parametro FROM "
##                    SQL += "(Nuvem_Gateway INNER JOIN Nuvem_Maquina ON Nuvem_Maquina.Cod_Gateway = Nuvem_Gateway.Cod_Gateway "
##                    SQL += "INNER JOIN Nuvem_Configuracao_Protocolo_Comunicacao_Maquina ON Nuvem_Configuracao_Protocolo_Comunicacao_Maquina.Cod_Maquina = Nuvem_Maquina.Cod_Maquina) "
##                    SQL += "WHERE Nuvem_Configuracao_Protocolo_Comunicacao_Maquina.Cod_Maquina = '"+str(self.codMaq)+"' "
##                    SQL += "AND Nuvem_Configuracao_Protocolo_Comunicacao_Maquina.Cod_Parametro = 11"
##
##                    Dados_Inicializar_SP, = mysql.pesquisarBD(SQL,True)
##
##                    self.pOntimeOut_c = Dados_Inicializar_SP['Valor_Parametro']
##                    self.pOntimeOut   = Dados_Inicializar_SP['pOnti_Timeout_Conexao']
##                    self.Port_SP      = Dados_Inicializar_SP['Porta_Servidor_Ethernet']
                    self.ttyUSB       = gateway.getUSB(self)
                    print('IP: {} | Porta SP: {} | Timeout: {} | USB: {} | '.format(self.IP,self.Port_SP,self.pOntimeOut_c,self.ttyUSB))
                    getoutput("sudo /usr/lib/"+str(gateway.getPythonVer(self))+"/./SP_pOnti "+str(self.Port_SP)+" "+str(self.pOntimeOut_c)+" "+str(self.ttyUSB)+" "+str(self.IP))
                    print('Servidor Principal')                               
                except: print_exc()
                    
                            
            sleep(0.5)
                      
    def SP_Stop(self):
                        
        try:
            PIDf = findall(r"\d{1,8}\/", getoutput('sudo netstat -lnp| grep "'+str(self.Port_SP)+'"'))[0]
            PIDf = PIDf[:PIDf.find("/")]                
            getoutput("sudo kill " + str(PIDf))
        except: pass

        self.SP_emExecucao = False
                        
    def Sniffer(self):

        while True:

            if not self.SP_emExecucao:
                if findall(r"\d{1,8}\/", getoutput('sudo netstat -lnp| grep "'+str(self.Port_SP)+'"')):
                    self.SP_emExecucao = True                    
            
            if self.SP_emExecucao:
                
                getoutput('sudo killall -9 tshark')                
                if len(getoutput('sudo tshark -c 5 -a duration:10 -f "src port ' + str(self.Port_SP)+'"')) > 500:                
                    self.trava = False           
                    sleep(5)
                
    def Timeout(self):

        while True:            
            if self.conectado and not self.timeoutInatividade:        
                
                if not self.trava:
                    temporizadorInicial = tempor()
                    self.trava = True
                    
                temporizadorAtual = tempor()                
            
                if ((temporizadorAtual - temporizadorInicial) > self.pOntimeOut+40):                    
                    self.timeoutInatividade  = True                      
                    
            else:
                temporizadorInicial = tempor()
                temporizadorAtual   = tempor()
                
                self.trava    = False
                
            sleep(5)
                    
    def run(self):

        mysql = MySQL(self.arqINI, self.arqOFF)
        
        sniffer  = Thread(target = self.Sniffer)            
        timeout  = Thread(target = self.Timeout)
        servidor = Thread(target = self.SP_Start)
        
        sniffer.start()
        timeout.start()
        servidor.start()        

        print("\n           pOnti            ")
        
        while True:                        
            
            if self.setBit.isSet():
                self.SA_Stop()                

            else:
                                        
                if not self.SA_emExecucao:
                    self.SA_Start()                                                                    
                    self.SA_pOnti.setblocking(0)
                            
            try:         
                con, cliente = self.SA_pOnti.accept()                
                con.setblocking(0)                
                
                self.conectado = True                        
                self.usandoPonti.set()
                
                print("\nCliente Conectado\n")
##                a = tempor()
##                print(a)
##                SQL  = "UPDATE Nuvem_Gateway INNER JOIN Nuvem_Maquina ON Nuvem_Gateway.Cod_Gateway = Nuvem_Maquina.Cod_Gateway "
##                SQL += "SET Status_pOnti = 3, Timestamp_pOnti = '"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"'"
##                SQL += " WHERE Nuvem_Maquina.Cod_Maquina = '"+str(self.codMaq)+"'"
##                b = tempor()
##                print(b-a,'ponti=3')
##                try:mysql.executaQueryBD(SQL,True)
##                except:print_exc()

            except: self.conectado = False
            
            while self.conectado == True:
                         
                sleep(1)
                try:    recebido = con.recv(1024)
                except: recebido = 'null'            
                
                if   recebido == b'' or self.timeoutInatividade == True or not self.SA_emExecucao:  status = 'desconectado'
                elif recebido == b'\x01': status = 'conectado'
                elif recebido == b'\x03': status = 'resetTimeout'                
                else:                     status = ''

                if status == 'conectado':
                    
                    try: con.send(b'\xC8')
                    except: pass
                    
                if status == 'desconectado':
                    
                    print("Desconectado")
                    self.usandoPonti.clear()

                    self.SP_Stop()
                    self.SA_Stop()

                    self.SP_emExecucao = False
                    self.SA_emExecucao = False
                    
                    self.timeoutInatividade = False                
                    self.conectado = False                                                                    

##                    a = tempor()
##                    print(a)
##                    SQL  = "UPDATE Nuvem_Gateway INNER JOIN Nuvem_Maquina ON Nuvem_Gateway.Cod_Gateway = Nuvem_Maquina.Cod_Gateway "
##                    SQL += "SET Status_pOnti = 1, Timestamp_pOnti = '"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"'"
##                    SQL += " WHERE Nuvem_Maquina.Cod_Maquina = '"+str(self.codMaq)+"'"
##                    b = tempor()
##                    print(b-a,'ponti=1')
##                
##                    try:mysql.executaQueryBD(SQL,True)
##                    except:print_exc()

                elif status == 'resetTimeout':

                    self.trava = False                    
                    print("Reset Timeout")
            
