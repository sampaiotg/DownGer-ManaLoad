#!/usr/bin/python
from socket import socket , AF_INET as IP ,SOCK_STREAM as TCP, gethostbyname_ex
import signal , threading as t, re, sys, os
import base64
from time import sleep, time
import thread

proxy = False
sleepvar = 0.1
bufferLocal = []
buffGlobal = []
lim = 200
numCon = 15
pause = False
partes = numCon #controla quando o download acaba
npktbaixado = 0
tempototalseg = 0
pcent = 0

def handler():
    global pause
    if pause:
        pause = False
    else:
        pause = True


#url =  'http://jovemnerd.com.br/podpress_trac/web/92979/3/nerdcast_404_nerdtour_londres.zip'
#url = 'http://nerdcast.jovemnerd.com.br/nerdcast_404_nerdtour_londres.zip'
#url = 'http://jovemnerd.com.br/podpress_trac/web/92649/0/nerdcast_403_robocop_vs_robocop.mp3'
url = 'http://1hdwallpapers.com/wallpapers/happy_day_for_you.jpg'
#url = 'http://srv66.vidtomp3.com/download/4pmYb2xkoWRpr6yq3JmZtGpjoWdnY3JqnJTfjqKU3KGho2w=/'
#url = 'http://srv63.vidtomp3.com/download/4piXcW5im2SwpquunJbfaWxpnWRtZXBul9+5oZ2k15+kZg==/'
url = 'http://www.imgfans.com.br/i777/dream/th_Samsung-Galaxy-Note-3.png'
url = 'http://www.jscape.com/Portals/26878/images/ad_hoc_file-transfer-with-clients.png'
#url = 'http://srv70.vidtomp3.com/download/4pSacG1inmZlr6yq3JqTtGpjoWdnaW5wmpvfjqKU3KGho2w=/'
#url = 'http://ubuntu.ufes.br/ubuntu-releases//saucy/ubuntu-13.10-desktop-amd64.iso'
#url = 'http://nerdcast.jovemnerd.com.br/nerdcast_403_robocop_vs_robocop.mp3'
#url = 'http://127.0.0.1/Colbie.mp3'


url = raw_input('Url do Arquivo: ')
lim = int(raw_input('Taxa de Transferencia Maxima: '))
numCon = int(raw_input('Numero de Conexoes: '))

HOST =  url.strip('http://').split('/')[0]
PORT = 80
for x in range(0,numCon):
   f = open('download.part{0}'.format(x),'w')
   f.close()

def conecta(dic):
    global npktbaixado
    global bufferLocal
    global pause
    global partes
    try:
       conexao = socket(dic['IP'],dic['TCP'])
       if proxy:
         conexao.connect(('10.0.16.1',3128))
       else:
         conexao.connect((dic['HOST'],dic['PORT']))
       conexao.send(dic['header'])
       pkt = conexao.recv(1024)
       vaiLer = True
       while len(pkt) != 0:
            if pause:
                while pause:
                    continue
            if 'HTTP/1.1' in pkt:
                #head = pkt.split('\r\n\r\n')[0]
                pkt = pkt.split('\r\n\r\n')[1]
            sem[dic['part']].acquire()
            if bufferLocal[dic['part']][1] == 0:
                vaiLer = False
            else:
                bufferLocal[dic['part']][0] += pkt
                bufferLocal[dic['part']][1] -= 1
                vaiLer = True
            sem[dic['part']].release()
            if vaiLer:
                pkt = conexao.recv(1024)  
                sem[dic['part']].acquire()
                bufferLocal[dic['part']][2] += 1
                sem[dic['part']].release()
       conexao.close()
       print 'Parte '+str(dic['part'])+' Finalizada!'
       dic['file'].close()
    except Exception:
       print 'Caiu a conexao',sys.exc_info()[0]
    
def userInterface(conexoes):
    global npktbaixado
    global tamanho
    global bufferLocal
    global sem
    global pause
    global pcent
    tamanhoParcial = 0
    tamanhoAnterior = 0
    vetVel = []
    while tamanhoParcial < tamanho/1024:
        if pause:
            while pause:
                print '\n'*100,'|'*int((pcent*100)*0.6),' '+str(round(pcent*100,2))+'%'
                print 'Download Pausado '+str(round(pcent*100,2))+'%'
                sleep(1)
        tamanhoParcial = 0
        for x in range(0,numCon):
            sem[x].acquire()
            tamanhoParcial += bufferLocal[x][2]
            sem[x].release()
        pcent = float(tamanhoParcial * 1024)/tamanho
        veloc = (tamanhoParcial-tamanhoAnterior)*1024
        vetVel += [veloc/1024]
        if len(vetVel) > 10:
            vetVel = vetVel[len(vetVel)-10:]
        veloc = (sum(vetVel)/len(vetVel))*1024
        try:
            print '\n'*100,'|'*int((pcent*100)*0.6)
            #print '|'*int((pcent*100)*0.6)
            if pcent*100 > 100:
               pcent = 1.00
            print str(veloc/1024)+'KBps '+str(round(pcent*100,2))+'% ETD: '+str(int(((tamanho-tamanhoParcial)/veloc)/3600))+':'+str(int((((tamanho-tamanhoParcial)/veloc)%3600)/60))+':'+str(int((((tamanho-tamanhoParcial)/veloc)%3600)%60))
        except:
            print '\n'*100,'|'*int((pcent*100)*0.6)
            print str(veloc/1024)+'KBps '+str(round(pcent*100,2))+'% ETD: 00:00:00'
        tamanhoAnterior = tamanhoParcial
        sleep(1)
    
def controlBuffer(dic): #consumidor
    global npktbaixado
    global buffGlobal
    global bufferLocal
    global tempototalseg
    while npktbaixado*1024 < tamanho:
        sem[dic['part']].acquire()
        try:
            if bufferLocal[dic['part']][1] < lim/numCon :
                #buffGlobal[dic['part']] += bufferLocal[dic['part']][0]
                dic['file'].write(bufferLocal[dic['part']][0])
                bufferLocal[dic['part']][1] = lim/numCon
                bufferLocal[dic['part']][0] = ''                
        except:
            print 'Bugo a porra toda!'
        sem[dic['part']].release()
        tempototalseg += 1
        sleep(1)
        
                
class uiThread(t.Thread):
    def __init__(self, c):
        t.Thread.__init__(self)
        self.daemon = True
        self.con = c
    def run(self):
            userInterface(self.con)

class controlThread(t.Thread):
    def __init__(self, c):
        t.Thread.__init__(self)
        self.daemon = True
        self.con = c
    def run(self):
            controlBuffer(self.con)
            
class MyThread(t.Thread):
    def __init__(self, dic):
        t.Thread.__init__(self)
        self.daemon = True
        self.dict = dic
    def run(self):
            conecta(self.dict)
 
if proxy: 
   print 'Proxy Ativado!'
   os.environ['http_proxy'] = 'http://'+usuario+':'+senha+'@10.0.16.1:3128'
   header = 'HEAD '+ url  +' HTTP/1.1\r\nProxy-Authorization: Basic MjAxMDExNzIyMDM1OlRoaWFnbzA2\r\nCredentials: 201011722035:Thiago06  \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n' # Proxy
else:
   header = 'HEAD '+url+' HTTP/1.1\r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
   
print header
conexao = socket(IP,TCP) #Cria um conexao do tipo TCP usando o Protocolo de rede IP
if proxy:
   conexao.connect(('10.0.16.1',3128))     #Proxy
else:
   conexao.connect((HOST,PORT))
conexao.send(header)
header = conexao.recv(1024)
print header
if 'Accept-Ranges' in header:
    if 'HTTP/1.1 302' in header.split('\n\r')[0]:
        endereco = header.split()
        for x in range(0,len(endereco)):
            if 'Location' in endereco[x]:
                endereco = endereco[x+1]
        url = endereco
        print 'Arquivo movido Temporariamente para' , endereco
        if proxy:
            header = 'HEAD '+ endereco  +' HTTP/1.1\r\nProxy-Authorization: Basic MjAxMDExNzIyMDM1OlRoaWFnbzA2\r\nCredentials: 201011722035:Thiago06  \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
        else:
            header = 'HEAD '+url+' HTTP/1.1\r\nHost: '+ url.strip('http://').split('/')[0].strip() +'\r\n\r\n'
        print header
        conexao.close()
        conexao = socket(IP,TCP) #Cria um conexao do tipo TCP usando o Protocolo de rede IP
        if proxy:
            conexao.connect(('10.0.16.1',3128))
        else:
            conexao.connect((HOST,PORT))
        
        conexao.send(header)
        header = conexao.recv(1024)
        print header
    tamanho = header.split('Content-Length: ')[1]
    tamanho = int(tamanho.split('\n')[0])
    tamPartes = tamanho/numCon
    listaCon = []
    listaTreads = []
    listaTreadsCons = []
    arquBuff = {}
    bufferLocal = [['',lim/numCon,0]] 
    buffGlobal = ['']
    sem = []
    ini = time()
    semaforo = thread.allocate_lock()
    print str(numCon) + ' Partes de '+str(tamPartes)+'Kb',header
    for x in range(0,numCon):
        #header = 'GET '+ url  +' HTTP/1.1\r\nProxy-Authorization: Basic MjAxMDExNzIyMDM1OlRoaWFnbzA2\r\nCredentials: 201011722035:Thiago06  \r\nRange: bytes='+ str(x*tamPartes)+'-'+str((x*tamPartes)+(tamPartes)-1) +' \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
        if x != numCon:
            if proxy:
               header = 'GET '+ url  +' HTTP/1.1\r\nProxy-Authorization: Basic MjAxMDExNzIyMDM1OlRoaWFnbzA2\r\nCredentials: 201011722035:Thiago06  \r\nRange: bytes='+ str(x*tamPartes)+'-'+str((x*tamPartes)+(tamPartes)-1) +' \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
            else:
               header = 'GET '+ url  +' HTTP/1.1\r\nRange: bytes='+ str(x*tamPartes)+'-'+str((x*tamPartes)+(tamPartes)-1) +' \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
        else:
            if proxy:
               header = 'GET '+ url  +' HTTP/1.1\r\nProxy-Authorization: Basic MjAxMDExNzIyMDM1OlRoaWFnbzA2\r\nCredentials: 201011722035:Thiago06  \r\nRange: bytes='+ str(x*tamPartes)+'-'+str((x*tamPartes)+(tamPartes)) +' \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
            else:
               header = 'GET '+ url  +' HTTP/1.1\r\nRange: bytes='+ str(x*tamPartes)+'-'+str((x*tamPartes)+(tamPartes)) +' \r\nHost: '+ url.strip('http://').split('/')[0] +'\r\n\r\n'
        file = open('download.part'+str(x),'ab')
        dicionario = {'tamanho':tamPartes, 'header':header, 'part':x,'IP':IP,'TCP':TCP,'HOST':HOST,'PORT':PORT,'file':file}
        listaTreads += [MyThread(dicionario)]
        listaTreads[x].start()
        sem += [thread.allocate_lock()]
        listaTreadsCons += [controlThread(dicionario)]
        listaTreadsCons[x].start()
        bufferLocal += [['',lim/numCon,0]]
        buffGlobal += ['']
        
    interface = uiThread(0)    
    interface.start()
    while int(pcent*100) < 100 :        
        try:
            sleep(1)    
        except KeyboardInterrupt:
            handler()
    
    print 'Juntando Partes'
    fim = time()
    nomearq = url.split('/')[-1]
    if nomearq == '':
        nomearq = 'saida.txt'
    elif len(nomearq) > 30:
        nomearq = raw_input('Nome de Arquivo Invalido, qual o nome para salvar? ')
    arq = open(nomearq,'wb')
    #for x in buffGlobal:
        #arq.write(x)
    #Junta download.parts em somente um
    for x in range(0,numCon):
        f = open('download.part'+str(x),'rb')
        arq.write(f.read())
        f.close()
    arq.close()
    print 'Download Concluido em: '+ str(fim - ini)