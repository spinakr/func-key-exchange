import sys, socket, select, json, time
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.schemes.abenc import abenc_waters09
from charm.core.engine.util import objectToBytes,bytesToObject

 
#Function to broadcast chat messages to all connected clients
def broadcast (sock, message):
    #Do not send the message to master socket and the client who has send us the message
    for socket in userdata.keys():
        if socket != server_socket and socket != sock :
            try :
                time.sleep(0.1)
                socket.send(message)
            except :
                # broken socket connection may be, chat client pressed ctrl+c for example
                socket.close()
                if socket in userdata:
                    removeUser(sock)
                      
def handleNewConnection():
    sockfd, addr = server_socket.accept()
    userdata[sockfd] = 'Anonymous {}'.format(len(userdata))
    #send the room policy
    sockfd.send(roomPolicy)                                                     
    #send pk and group
    sockfd.send(objectToBytes(pk,groupObj))                                    
    #send key using a attr set
    sockfd.send(objectToBytes(cpabe.keygen(pk, msk, attr_dict[i]),groupObj))    
    #receive the encapsulation
    encap = bytesToObject(sockfd.recv(RECV_BUFFER), groupObj)                   
    #save it
    encapsulations.append(encap)                                                         
    entities.append(addr)
    broadcastEncapList(sockfd, addr) 
    broadcast(sockfd, "[server] {} entered room\n".format(userdata[sockfd]))
    print 'Users in the room: {}\n\n'.format(str(userdata.values()))

def broadcastEncapList(sockfd, addr):
    broadcast(sock, "1000001"+str(len(encapsulations)))                         
    time.sleep(1)
    print "Client {}, on {} connected".format(userdata[sockfd], addr)           
    for j in xrange(0,len(encapsulations)):
        time.sleep(0.1)
        broadcast(sock, objectToBytes(encapsulations[j], groupObj)) 
        print('Send encapsulation number {} of {}'.format(j+1,len(encapsulations)))

def removeUser(sock):
    broadcast(sock, "[server] Client {} is offline\n".format(str(userdata[sock])))
    print "Client {} left the room.".format(userdata[sock])
    del userdata[sock]
    broadcast(sock, "[server] Clients in the room:  {}\n".format(str(userdata.values())))
    print "Clients in the room: {}\n\n".format(str(userdata.values()))
        

def processData():
    try:
        # receiving data from the socket.
        data = sock.recv(RECV_BUFFER)
        if data:
            # there is something in the socket
            broadcast(sock, "\r" + '[' + userdata[sock] + '] ' + data)  
            return True
        else:
            # remove the socket that's broken    
            if sock in userdata.keys():
                removeUser(sock)
            return True
    except:
        return False

def disconnected():
    print "Unexpected error:", sys.exc_info()[0]
    print 'Users in the room: {}'.format(str(userdata.values()))
    broadcast(sock, "[server] Client {} is offline\n".format(userdata[sock]))

if __name__ == '__main__':
    attr_dict = [
                ['THREE', 'ONE', 'TWO'],
                ['THREE', 'TWO', 'FOUR'], 
                ['ONE', 'THREE', 'FOUR'], 
                ['ONE', 'TWO', 'FIVE']]
    i=0
    groupObj = PairingGroup('SS512') 
    #Init the abe class
    cpabe = abenc_waters09.CPabe09(groupObj)            
    (msk, pk) = cpabe.setup()                            
    #Run setup method
    roomPolicy = '((ONE or THREE) and (TWO or FOUR))'

    userdata = {} #list of sockets and chat names.
    encapsulations = []
    entities = []
    RECV_BUFFER = 4096 
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    # Add server socket to the list of readable connections
    userdata[server_socket] = ''
 
    print "Chat server started on port " + str(PORT)
    print "Current room policy: {}\n\n".format(roomPolicy)

    #Start the server main loop 
    while 1:
        read_sockets,write_sockets,error_sockets = select.select(userdata,[],[])
        for sock in read_sockets: 
            if sock == server_socket: #New connection
                handleNewConnection()
                i+=1
            else:   #Incoming message from a client
                processData() or disconnected()
    server_socket.close()
