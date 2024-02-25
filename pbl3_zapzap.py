import json
import socket
import threading
import uuid
import os
import time
import copy
import platform
import sys

LIMPAR_WIN = "cls"
LIMPAR_LINUX = "clear"
LIMPAR = LIMPAR_LINUX if platform.system() == "Linux" else LIMPAR_WIN

#Dicionario para testar em casa
#membros_grupo = {1 : '127.0.0.1:1234', 2 : '127.0.0.1:5678', 3 : '127.0.0.1:9000', 4 : '127.0.0.1:1111'}
#Dicionario com ips e portas para o lab
membros_grupo = {1: '172.16.103.1:1111', 2: '172.16.103.2:2222', 3: '172.16.103.3:3333', 4 : '172.16.103.4:4444', 5: '172.16.103.5:5555', 6: '172.16.103.6:6666', 7: '172.16.103.7:7777', 8: '172.16.103.8:8888', 9: '172.16.103.9:9999', 10: '172.16.103.10:9899', 11: '172.16.103.11:7888', 12: '172.16.103.12:8569', 13: '172.16.103.13:9044', 14: '172.16.103.14:8944'}
membros_online = {}  # Conjunto de clientes online
heartbeat_timestamps = {}  # Dicionário para manter o timestamp dos últimos batimentos cardíacos
msg_confirm =[]
msg_time = {}
recoverInAuto = False
save_indices = []
cont_indice_ciclos = []
recoverTemp = []
indiceTemp = []
repeatRecover = True
tempoPedido = None
pacote_recebido = False
for i in membros_grupo:
    heartbeat_timestamps[membros_grupo[i]] = 0


mensagens_all = []
#Contatos conhecidos (Dicionario com o endereço dos usuarios conectados) - host:porta

# Códigos de escape ANSI para cores de texto
CORES = [
    '\033[91m',  # Vermelho
    '\033[92m',  # Verde
    '\033[93m',  # Amarelo
    '\033[94m',  # Azul
    '\033[95m',  # Magenta
    '\033[96m',  # Ciano
    '\033[97m',  # Branco
    '\033[31m',  # Vermelho claro
    '\033[32m',  # Verde claro
    '\033[33m',  # Amarelo claro
    '\033[34m',  # Azul claro
    '\033[35m',  # Magenta claro
    '\033[36m',  # Ciano claro
    '\033[37m',  # Cinza
]

#Histórico de mensagens
historico_mensagens = []
historico_temporario = {}

lock_list = threading.Lock()
lock_online = threading.Lock()

#Classe responsável pelo relógio lógico de Lamport
class LamportClock:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def update(self, received_time):
        with self.lock:
            self.value = max(self.value, received_time) + 1
            return self.value

def env_mt(HOST, PORT, clock):
    with open("input_file.txt", 'a+', encoding='utf-8') as arquivo:
            arquivo.seek(0) # Mover o cursos para o inicio
            for linha in arquivo:
                mensagem = linha.rstrip('\n')
                        
                clock.increment()
                id = gerar_id()
                #mensagem = criptografar(mensagem)
                dict_mensagem = {'time' : clock.value, 'type' : 'msg_env', 'conteudo' : mensagem, 'user' : str(HOST) + ':' + str(PORT), 'id' : id}
                on_env = []
                for chave, valor in heartbeat_timestamps.items():
                    if valor < 3:
                        on_env.append(chave)
                dict_mensagem['enviados'] = on_env
                enviar_socket(dict_mensagem, dict_mensagem['enviados'], HOST, PORT)
                print()
                dict_mensagem['origem'] = time.time()
                dict_mensagem['confirmados'] = []

                with lock_list:
                    historico_temporario[dict_mensagem['id']] = dict_mensagem
                                

                time.sleep(0.5)
            
            print("Mensagens do arquivo enviadas.")

#Função responsável por sincronizar o relógio lógico
def sincronizar_relogio(clock, HOST ,PORT):
    sinc_mensagem = {'type': 'clockSync', 'clock': clock.value, 'host' : HOST, 'port' : PORT}
    mensagem_encode = json.dumps(sinc_mensagem)
    for i in membros_grupo:
            if membros_grupo[i] != (str(HOST) + ':' + str(PORT)):
                endereco_destino = membros_grupo[i].split(':')
                destino_ip = endereco_destino[0]
                destino_porta = int(endereco_destino[1])
                enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                enviar_socket.sendto(mensagem_encode.encode(), (destino_ip, destino_porta))
                enviar_socket.close()

#Função responsável por selecionar qual o PC do láboratório que está sendo utilizado
def definir_pc():
    while True:
        try:
            pc = int(input("Digite o número do seu PC: "))
            if pc in membros_grupo:
                endreco = membros_grupo[pc].split(":")
                return endreco[0], int(endreco[1])
        except:
            continue

#Função responsável por criar a chave de criptografia
def gerar_chave_cripto():
    var, var2 = 0, 0
    for valor in membros_grupo.values():
        chave1 = valor.split(":")[1]
        var += int(chave1)
        chave2 = valor.split(":")[0]
        var2 += sum(int(digito) for digito in chave2 if digito.isdigit())
    return var, var2

#Função responsável por criptografar as mensagens
def criptografar(msg):
    mensagem = ""
    var, var2 = gerar_chave_cripto()
    for i in msg:
        mensagem += chr (ord(i) + (var % var2))
    return mensagem

#Função responsável por descriptografar as mensagens
def descriptografar(msg):
    mensagem = ""
    var, var2 = gerar_chave_cripto()
    for i in msg:
        mensagem += chr (ord(i) - (var % var2))
    return mensagem

def verif_online(HOST, PORT):
    
    cont = 0
    while True:

        verif_tick = {'type': 'sendTick', 'host' : HOST, 'port' : PORT}

        mensagem_encode = json.dumps(verif_tick)
        for i in membros_grupo:
            if membros_grupo[i] != (str(HOST) + ':' + str(PORT)):
                endereco_destino = membros_grupo[i].split(':')
                destino_ip = endereco_destino[0]
                destino_porta = int(endereco_destino[1])
                enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                enviar_socket.sendto(mensagem_encode.encode(), (destino_ip, destino_porta))
                enviar_socket.close()
    
        time.sleep(0.5)
        cont += 1
        
        for i in heartbeat_timestamps:
            heartbeat_timestamps[i] += 1
        if cont == 3:
            for i in heartbeat_timestamps:
                if heartbeat_timestamps[i] >= 3 and i in membros_online:
                    membros_online.pop(i)
            cont = 0
            
def return_tick(mensagem, HOST, PORT):
       
    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sinc_mensagem = {'type': 'returnTick', 'data' : "online", 'ender' : str(HOST) + ":" +  str(PORT)}
    sinc_mensagem = json.dumps(sinc_mensagem)
    enviar_socket.sendto(sinc_mensagem.encode(), (mensagem['host'], mensagem['port']))
    enviar_socket.close()

#c
def confirm_msg(msg, HOST, PORT):
    confirm = {'type': 'confirm_msg', 'id': msg['id'], 'remetente' :  str(HOST) + ":" + str(PORT)}
    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    endereco = msg['user'].split(':')

    sinc_mensagem = json.dumps(confirm)
    enviar_socket.sendto(sinc_mensagem.encode(), (endereco[0], int(endereco[1])))
    enviar_socket.close()


def atualiza_historico(historico_mensagens ,HOST, PORT):
    while True:
        autorizacao_env = []
        autorizacao_rcv = []
        lixeira = []
        autorizar_exibicao = []


        with lock_list:
            copia_historico = copy.deepcopy(historico_temporario)
            for i in copia_historico:
  
                if historico_temporario[i]['type'] == 'msg_env':

                    if set(historico_temporario[i]['enviados']) == set(historico_temporario[i]['confirmados']): 
 
                        autorizacao_env.append(historico_temporario[i])
 
                else:
                    if historico_temporario[i]['exibir'] == True:
                        autorizacao_rcv.append(historico_temporario[i])
   
            
        
        if autorizacao_env:
 
            for i in autorizacao_env:
                confirm = {'type' : 'EXIBIR', 'id' : i['id'], 'remetente' : i['user']}
                autorizar_exibicao += i['enviados']
                historico_mensagens.append(i)
                lixeira.append(i['id'])
            enviar_socket(confirm, autorizar_exibicao, HOST, PORT )
            enviar_socket(confirm, autorizar_exibicao, HOST, PORT )
            exibir_mensagens()
                    
        if autorizacao_rcv:

            for i in autorizacao_rcv:
                confirm = {'type' : 'EXIBIR', 'id' : i['id'], 'remetente' : i['user']}
                autorizar_exibicao = membros_online.keys()
                enviar_socket(confirm, autorizar_exibicao, HOST, PORT )
                enviar_socket(confirm, autorizar_exibicao, HOST, PORT )
                lixeira.append(i['id'])
                historico_mensagens.append(i)
                exibir_mensagens()


        if lixeira:
            for item in lixeira if lixeira else []:

                with lock_list:
                    historico_temporario.pop(item)

        autorizacao_env.clear() , autorizacao_rcv.clear() , lixeira.clear()
        time.sleep(0.2)
envios_recover = []
def recuperar_mensagens(HOST, PORT):
    pedido = {'type' : 'recoverMSG', 'remetente' : str(HOST) + ':' + str(PORT)}
    enviar_socket(pedido, None, HOST, PORT)     



#Função responsável por receber todas as mensagens e solicitações via socket
def receber_mensagens(recv_socket):
    while True:
        try:
            data, endereco = recv_socket.recvfrom(1024)
            mensagem = json.loads(data.decode())
            mensagens_all.append(mensagem)
            
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
#Função responsável por enviar todas as mensagens e solicitações via socket
def enviar_socket(data, onlineagora, HOST, PORT):
    mensagem_encode = json.dumps(data)
    with lock_online:
        on_teste = []
        for chave, valor in heartbeat_timestamps.items():
            if valor != 3:
                if  chave != (str(HOST) + ':' + str(PORT)):
                    endereco_destino = chave.split(':')
                    destino_ip = endereco_destino[0]
                    destino_porta = int(endereco_destino[1])
                    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    enviar_socket.sendto(mensagem_encode.encode(), (destino_ip, destino_porta))
                    enviar_socket.close()
#Função responsável por padronizar as mensagens para que possam ser enviadas via socket e adicionadas ao histórico de mensagens
def enviar_mensagem(clock, HOST, PORT):
        mensagem = input("Digite a mensagem: ")
        if mensagem == 'batata00':
            env_mt(HOST, PORT, clock)
        if mensagem == 'update00':
            exibir_mensagens()
        if mensagem == 'recuperar00':
            
            recuperar_mensagens(HOST, PORT)
        clock.increment()
        id = gerar_id()
        #mensagem = criptografar(mensagem)
        dict_mensagem = {'time' : clock.value, 'type' : 'msg_env', 'conteudo' : mensagem, 'user' : str(HOST) + ':' + str(PORT), 'id' : id}
        on_env = []
        for chave, valor in heartbeat_timestamps.items():
            if valor < 3:
                on_env.append(chave)

        
        dict_mensagem['enviados'] = on_env
        enviar_socket(dict_mensagem, dict_mensagem['enviados'], HOST, PORT)
        print()
        dict_mensagem['origem'] = time.time()
        dict_mensagem['confirmados'] = []

        with lock_list:
            historico_temporario[dict_mensagem['id']] = dict_mensagem
   
#Função responsável por realizar a triagem de todas as mensagens e solicitações recebidas
def triagem_mensagens(clock, HOST, PORT, recoverInAuto, historico_mensagens, save_indices):
    tempoPedido = None
    while True:
        if mensagens_all:
            mensagem = mensagens_all.pop()

            if mensagem['type'] == 'msg_env':
          
                mensagem['origem'] = time.time()
                mensagem['type'] = 'msg_rcv'
                mensagem['exibir'] = False
                clock.update(mensagem['time'])
                with lock_list:
                    historico_temporario[mensagem['id']] = mensagem
            
                exibir_mensagens()
                confirm_msg(mensagem, HOST, PORT)


            elif mensagem['type'] == 'clockSync':
                clock.update(mensagem['clock'])
                sinc_mensagem = {'type': 'updateClock', 'clock': clock.value}
                sinc_mensagem = json.dumps(sinc_mensagem)
                enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                enviar_socket.sendto(sinc_mensagem.encode(), (mensagem['host'], mensagem['port']))
                enviar_socket.close()
            elif mensagem['type'] == 'updateClock':
                clock.update(mensagem['clock']) 

            elif mensagem['type'] == 'sendTick':
                return_tick(mensagem, HOST, PORT)
            elif mensagem['type'] == 'returnTick':
                if mensagem['ender'] not in membros_online:
                    membros_online[mensagem['ender']] = 0
                else:
                    membros_online[mensagem['ender']] = 0
            elif mensagem['type'] == 'confirm_msg':
                with lock_list:
                    try:
                        historico_temporario[mensagem['id']]['confirmados'].append(mensagem['remetente'])
                    except:
                        pass
            elif mensagem['type'] == 'EXIBIR':
                if mensagem['id'] in historico_temporario:
                    with lock_list:
                        historico_temporario[mensagem['id']]['exibir'] = True
            elif mensagem['type'] == 'recoverMSG':
                ender = mensagem['remetente'].split(':')
                print(mensagem['remetente'])
                returnPedido = {'type' : 'returnPedido','host' : HOST, 'port' : PORT}

                mensagem_encode = json.dumps(returnPedido)
                enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                enviar_socket.sendto(mensagem_encode.encode(), (ender[0], int(ender[1])))
                enviar_socket.close()
            elif mensagem['type'] == 'returnPedido':
                if recoverInAuto == False:
                    pedido_iindices = {'type' : 'pedido_indices','host' : HOST, 'port' : PORT}
                    recoverInAuto = True
                    mensagem_encode = json.dumps(pedido_iindices)
                    
                    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    enviar_socket.sendto(mensagem_encode.encode(), (mensagem['host'], int(mensagem['port'])))
                    enviar_socket.close()
            elif mensagem['type'] == 'pedido_indices':
                lista_indices = []
                indices_divididos = []
                for i in historico_mensagens.copy():
                    lista_indices.append(i['id'])
                
                for i in range(0, len(lista_indices), 20):
                    indices_divididos.append(lista_indices[i:i+20])
                
                for i in range(len(indices_divididos)):
                    update_idices = {'type' : 'update_idices', 'indices': indices_divididos[i], 'indice_atual': i + 1, 'total_indices' : len(indices_divididos), 'host' : HOST, 'port' : PORT}
                    mensagem_encode = json.dumps(update_idices)
                    
                    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    enviar_socket.sendto(mensagem_encode.encode(), (mensagem['host'], int(mensagem['port'])))
                    enviar_socket.close()
            elif mensagem['type'] == 'update_idices':
                try:
                    save_indices += mensagem['indices']
                    cont_indice_ciclos.append(mensagem['indice_atual'])
                    if mensagem['indice_atual'] == 1:
                        tempoPedido = time.time()
                    elif tempoPedido != None:
                        #print('\n-=-=-  AQUIIII...-=-=-\n')
                        #time.sleep(3)
                        if tempoPedido - time.time() > 10:
                            #finalizar programa
                            print('\n-=-=-RECUPERANDO MENSAGENS, POR FAVOR AGUARDE...-=-=-\n')
                            #time.sleep(3)
                            #sys.exit()
                            recoverInAuto = False
                            tempoPedido = None
                            save_indices.clear()
                            cont_indice_ciclos.clear()
                            recoverTemp.clear()
                            indiceTemp.clear()
                            recuperar_mensagens(HOST, PORT)
                except Exception as e:
                    print(e)
                    print("ERROOOOOOO!!!")
                    time.sleep(10)
                
                if cont_indice_ciclos[-1] == mensagem['total_indices']:
                    if len(cont_indice_ciclos) == mensagem['total_indices']:
                        #pedir mensagens agora
                        pedido_msg = {'type' : 'pedido_msg','host' : HOST, 'port' : PORT}
                        mensagem_encode = json.dumps(pedido_msg)
                    
                        enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        enviar_socket.sendto(mensagem_encode.encode(), (mensagem['host'], int(mensagem['port'])))
                        enviar_socket.close()
                        
            elif mensagem['type'] == 'pedido_msg':
                indiceFinal = historico_mensagens.copy()[-1]['id']
                
                for i in historico_mensagens.copy():
                    envio_recoverMSG = {'type' : 'envio_recoverMSG', 'msg' : i, 'indice_final' : indiceFinal}
                    mensagem_encode = json.dumps(envio_recoverMSG)
                    
                    enviar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    enviar_socket.sendto(mensagem_encode.encode(), (mensagem['host'], mensagem['port']))
                    enviar_socket.close()
                    time.sleep(0.1)
            elif mensagem['type'] == 'envio_recoverMSG':
                recoverTemp.append(mensagem['msg'])
                indiceTemp.append(mensagem['msg']['id'])

                if recoverTemp.copy()[-1]['id'] == mensagem['indice_final']:
                    if set(indiceTemp) == set(save_indices): 
                        for i in recoverTemp:
                            if i not in historico_mensagens:
                                historico_mensagens.append(i)
                       
                    else:
                        print('\n-=-=-RECUPERANDO MENSAGENS, POR FAVOR AGUARDE...-=-=-\n')
                        #time.sleep(3)
                        #sys.exit()
                        recoverInAuto = False
                        save_indices.clear()
                        cont_indice_ciclos.clear()
                        recoverTemp.clear()
                        indiceTemp.clear()
                        recuperar_mensagens(HOST, PORT)
                    exibir_mensagens()
                        

            
#Função responsável por selecionar uma respectiva cor para casa usuário no sistema
def select_cor(var):
    for i in membros_grupo:
        if membros_grupo[i] == var:
            return CORES[i - 1]
#Função responsável por exibir as mensagens na na tela
def exibir_mensagens():
    os.system(LIMPAR) #windowns
    #os.system('clear') #linux
    print('''
    -=-=-=-=-=-=--=--=-=-
            ZAPZAP
    -=-=-=-=-=-=--=--=-=-
''')
    hisorico_ordenado = sorted(historico_mensagens, key=lambda x: (x['time'], x['id']))
    for i in hisorico_ordenado:
        #mensagem = descriptografar(i['conteudo'])
        cor = select_cor(i['user'])
        try:
            print(i['time'],cor + i['user'], ' - ', i['conteudo'] + '\033[97m')
        except:
            print(i['user'], ' - ', i['conteudo'])


def exibir_membros_online():
    os.system(LIMPAR) #windowns
    #os.system('clear') #linux
    print('''
    -=-=-=-=-=-=--=--=-=-
            ZAPZAP
    -=-=-=-=-=-=--=--=-=-
''')
    for i in membros_online:

        try:
            print(i + '\033[97m')
        except:
            print(i)



#Função responsável por gerar um ID único para idenificação das mensagens
def gerar_id(): 
    return str(uuid.uuid4())
#Função main responável por instanciar o objeto do relógio de Lamport, as threads, iniciar o envio das mensagens e selecionar qual PC do laboratório está sendo usado
def main():
    while True:
        try:
            HOST , PORT = definir_pc()
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_socket.bind((HOST, PORT))
            break
        except:
            
            continue
    clock = LamportClock() #Criando o objeto do relógio
    #Thread para receber as mensagens a todo momento
    thread_receber = threading.Thread(target=receber_mensagens, args=(recv_socket,))
    thread_receber.daemon = True
    thread_receber.start()
    #Thread para realizar a triagem das mensagens recebidas
    thread_triagem = threading.Thread(target=triagem_mensagens, args=(clock,HOST, PORT, recoverInAuto, historico_mensagens, save_indices,))
    thread_triagem.daemon = True
    thread_triagem.start()


    #Thread para verificar membros que estão online
    thread_online = threading.Thread(target=verif_online, args=(HOST, PORT, ))
    thread_online.daemon = True
    thread_online.start()

    
    recuperar_mensagens(HOST, PORT)
    thread_atualizaHistorico = threading.Thread(target=atualiza_historico, args=(historico_mensagens, HOST, PORT,))
    thread_atualizaHistorico.daemon = True
    thread_atualizaHistorico.start()


    sincronizar_relogio(clock, HOST, PORT) #Chamada da função de sincronização do relógio

    while True:
        enviar_mensagem(clock, HOST, PORT) #Chamada do envio das mensagens




if __name__ == "__main__":
    main()