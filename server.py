import socket, select, json, time
from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
from charm.schemes.abenc import abenc_waters09
from charm.core.engine.util import objectToBytes,bytesToObject

 
#Function to broadcast chat messages to all connected clients
def broadcast (sock, message):
    #Do not send the message to master socket and the client who has send us the message
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock :
        #if socket != server_socket:
            try :
                socket.send(message)
            except :
                # broken socket connection may be, chat client pressed ctrl+c for example
                socket.close()
                if socket in CONNECTION_LIST:
                    CONNECTION_LIST.remove(socket)


def removeUser(sock):
    broadcast_data(sock, "Client (%s, %s) is offline" % addr)
    print "Client (%s, %s) is offline" % addr
    sock.close()
    CONNECTION_LIST.remove(sock)


     
if __name__ == '__main__':
    attr_dict = [['THREE', 'ONE', 'TWO'], ['THREE', 'TWO', 'FOUR'], ['ONE', 'THREE', 'FOUR'], ['ONE', 'TWO', 'FIVE']]
    i=0
    groupObj = PairingGroup('SS512')

    cpabe = abenc_waters09.CPabe09(groupObj)
    (msk, pk) = cpabe.setup()
    roomPolicy = '((ONE or THREE) and (TWO or FOUR))'

    # List to keep track of socket descriptors
    CONNECTION_LIST = []
    #list of current encapsulations for the room
    encapsulations = []
    RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
    PORT = 5000

    #Setup key exchange socket and message socket     
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)
 
    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)
 
    print "Chat server started on port " + str(PORT)
 
    while 1:
        # Get the list sockets which are ready to be read through select
        read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
        
        for sock in read_sockets:
            #New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()
                CONNECTION_LIST.append(sockfd)
                sockfd.send(roomPolicy) #send the room policy
                sockfd.send(objectToBytes(pk,groupObj))
                sockfd.send(objectToBytes(cpabe.keygen(pk, msk, attr_dict[i]),groupObj))
                print('USED ATTR SET # {}'.format(i))
                i+=1
                encap = bytesToObject(sockfd.recv(RECV_BUFFER), groupObj) #receive the encapsulation
                #print 'Received one encapsulation: {}'.format(encap)
                encapsulations.append(encap) #add the encapsulation to current list
                broadcast(sock, "1000001"+str(len(encapsulations)))
                for j in xrange(0,len(encapsulations)):
                    time.sleep(0.1)
                    broadcast(sock, objectToBytes(encapsulations[j], groupObj)) #send all the current encapsulations
                    print('Send encapsulation number {} of {}'.format(j+1,len(encapsulations)))
                print "Client {} connected".format(addr)
                 
                #broadcast(sockfd, "{} entered room\n".format(addr))
                print 'Users in the room: {}'.format(str(CONNECTION_LIST))

            #Some incoming message from a client
            else:
                # process data recieved from client, 
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        # there is something in the socket
                        broadcast(sock, "\r" + '[' + str(sock.getpeername()) + '] ' + data)  
                    else:
                        # remove the socket that's broken    
                        if sock in CONNECTION_LIST:
                            CONNECTION_LIST.remove(sock)

                        # at this stage, no data means probably the connection has been broken
                        broadcast(sock, "Client (%s, %s) is offline\n" % addr) 
                        broadcast(sock, "CLients in the room:  {}".format(str(CONNECTION_LIST)))


                # exception 
                except:
                    broadcast(sock, "Client (%s, %s) is offline\n" % addr)
                    continue

     
    server_socket.close()
