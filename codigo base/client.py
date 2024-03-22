#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
import time
import numpy as np
import random
from funcoes import int_to_bytes
from crc import Calculator, Crc8
calculator = Calculator(Crc8.CCITT)

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM3"                  # Windows(variacao de)


def main():
    try:
        print("Iniciou o main")

        #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
        #para declarar esse objeto é o nome da porta.
        com1 = enlace(serialName)
        
    
        # Ativa comunicacao. Inicia os threads e a comunicação seiral 
        com1.enable()
        time.sleep(.2)
        com1.sendData(b'00')
        time.sleep(1)

        com1.rx.clearBuffer()
        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print("Abriu a comunicação")
        

        #Carrega Primeira Imagem
        print("Carregando imagem")
        print("-------------------------")
        imager = './1.jpg'
        imager2 = './2.jpg'
        img = [imager, imager2]

        #Monta o E.O.P
        eop = b'\xAA\xBB\xCC\xDD'

        #Monta o Head
        head = b''
        mensagens = [
                b'\x01',  # Comando 1 
                b'\x00',  # Comando 2
                b'\x00',  # Comando 3
                b'\x00',  # Comando 4
                b'\x00',  # Comando 5
                b'\x00',  # Comando 6
                b'\x00',  # Comando 7
                b'\x00',  # Comando 8
                b'\x00',  # Comando 9
                b'\x00',  # Comando 10
            ]
        
        # n_payloadsb = n_payloads.to_bytes(1, byteorder='big')
        # mensagens[2] = n_payloadsb
        

        for b in mensagens:
            head += b
            
        #Monta o payload
        payload = b''
            
        #Monta mensagem inicial
        txBuffer = head+payload+eop
        print(txBuffer)
        com1.sendData(txBuffer)


        handshaked = False
        encerra = False
        grove = 1
        for imageR in img:
            if grove == 1:
                arquido = open('erros.txt', 'w')
            else:
                arquido = open('erros2.txt', 'w')

            if handshaked == False:
                print("Confirma Handhake")
                while com1.rx.getIsEmpty():
                    pass
                head_rx = com1.rx.getBuffer(10)
                payload_rx = com1.rx.getBuffer(head_rx[1])
                eop_rx = com1.rx.getBuffer(4)
                tipo_msg = head_rx[0]
                print(f'Tipo da mensagem recebida: {head_rx[0]}')
                if tipo_msg != 2:
                    print("Erro ao receber mensagem de confirmação")
                    arquido.write('Erro no recebimento do handshake\n')
                    encerra = True
                    break
                else:
                    print("Mensagem de confirmação recebida")
                    handshaked = True

            
            imagemR_b = open(imageR, 'rb').read()
            print("Meu array de bytes tem tamanho {}" .format(len(imagemR_b)))
            n_payloads = len(imagemR_b) // 140
            n_payloads += 1
            print("Número de payloads: {}".format(n_payloads))

            byte_imagem = grove.to_bytes(1, byteorder='big')
            # print(f'Byte da imagem: {byte_imagem}')
            
            
            #Envia Imagem
            mensagens = [
                b'\x03',  # Comando 1 
                b'\x00',  # Comando 2
                b'\x00',  # Comando 3
                b'\x00',  # Comando 4
                b'\x00',  # Comando 5
                byte_imagem,  # Comando 6
                b'\x00',  # Comando 7
                b'\x00',  # Comando 8
                b'\x00',  # Comando 9
                b'\x00',  # Comando 10
            ]
        
            n_payloadsb = n_payloads.to_bytes(1, byteorder='big')
            mensagens[2] = n_payloadsb

            c = 0
            com1.rx.clearBuffer()
            while c < n_payloads:
                print(f'Payloads enviados: {c}/{n_payloads}')
                head = b''
                payload = b''
                eop = b'\xAA\xBB\xCC\xDD'
                if c == n_payloads - 1:
                    payload = imagemR_b[c*140:]
                    bytes_payload = len(imagemR_b[c*140:])
                else:
                    payload = imagemR_b[c*140:(c+1)*140]
                    bytes_payload = (c+1)*140 - c*140

                #Faz o negocio do projeto 4
                crc = calculator.checksum(payload)
                print(f'CRC: {crc}')
                print(f'Tipo do crc: {type(crc)}')
                byte = crc.to_bytes(1, byteorder='big')
                print(f'Byte do CRC: {byte}')
                mensagens[6] = byte
                
                # Atualiza o tamanho do payload
                mensagens[1] = bytes_payload.to_bytes((bytes_payload.bit_length() + 7) // 8, 'big')
                print(f'Numero de bytes no payload: {mensagens[1]}')

                # Atualiza o número de payloads total
                n_payloadsb = n_payloads.to_bytes(1, byteorder='big')
                mensagens[2] = n_payloadsb

                # Atualiza o número do pacote atual
                num_pacote_atual = (c + 1).to_bytes(1, byteorder='big')
                mensagens[4] = num_pacote_atual  # Adiciona o número do pacote atual ao cabeçalho

                for b in mensagens:
                    head += b
                print(f'Tipo da mensagem enviada: {head[0]}')
                print(f'Head da mensagem enviada: {head}')
                # print(f'Eop: {eop_rx}')
                txBuffer = head+payload+eop
                # print(f'Datagrama: {txBuffer}')
                # time.sleep(10)
                com1.sendData(txBuffer)

                while com1.rx.getIsEmpty():
                    pass

                head_rx = com1.rx.getBuffer(10)
                payload_rx = com1.rx.getBuffer(head_rx[1])
                eop_rx = com1.rx.getBuffer(4)
                tipo_msg = head_rx[0]
                print(f'Tipo da mensagem recebida: {head_rx[0]}')
                # print(f'Head da mensagem recebida: {head_rx}')
                print(f'Eop: {eop_rx}')
                if tipo_msg == 4:
                    print("Pode seguir com a próxima mensagem")
                    c += 1
                elif tipo_msg == 7:
                    print("Timeout")
                    arquido.write('Erro de timout\n')
                    encerra = True
                    break
                else:
                    print("Erro ao receber mensagem, enviar de novo")
                    arquido.write('Erro de recebimento de datagrama\n')
            print(f'Payloads enviados: {c}/{n_payloads}')
            print('Acabou o loop')

            if encerra:
                break

            grove += 1

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
