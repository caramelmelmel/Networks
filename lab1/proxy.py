# 50.012 network lab 1

from socket import *
import sys, os
import _thread as thread

proxy_port=8079
cache_directory = "./cache/"
#print(cache_directory)

def client_thread(clientFacingSocket):

	clientFacingSocket.settimeout(5.0)

	try:
		message = clientFacingSocket.recv(4096).decode()
		msgElements = message.split()
		#print(msgElements)
		#supported request message
		#print('type of request is ')
		#print(msgElements[0].upper())
		if len(msgElements) < 5 or msgElements[0].upper() != 'GET' or 'Range:' in msgElements:
			#print("non-supported request: " , msgElements)
			print('socket receiving from client is closing')
			clientFacingSocket.close()
			return

		# Extract the following info from the received message
		#   webServer: the web server's host name
		#   resource: the web resource requested
		#   file_to_use: a valid file name to cache the requested resource
		#   Assume the HTTP reques is in the format of:
		#      GET http://www.mit.edu/ HTTP/1.1\r\n
		#      Host: www.mit.edu\r\n
		#      User-Agent: .....
		#      Accept:  ......

		
		resource = msgElements[1].replace("http://","", 1)
	
		hostHeaderIndex = msgElements.index('Host:')
		webServer = msgElements[hostHeaderIndex+1]

		port = 80

		print("webServer:", webServer)
		print("resource:", resource)

		message=message.replace("Connection: keep-alive","Connection: close")
		
		website_directory = cache_directory + webServer.replace("/",".") + "/"

		if not os.path.exists(website_directory):
			os.makedirs(website_directory)
		
		
		file_to_use = website_directory + resource.replace("/",".")


	except:
		print(str(sys.exc_info()[0]))                                                
		clientFacingSocket.close()
		return
		
	# Check wether the file exists in the cache
	try:
		with open(file_to_use, "rb") as f:
			# ProxyServer finds a cache hit and generates a response message
			print("served from the cache")
			while True:
				#reads the file stream
				buff = f.read(4096)
				if buff:
					#Fill in start
					clientFacingSocket.send(buff)
					# Fill in end
				else:
					break
	#not found in the cache
	except FileNotFoundError as e:            
		try:
			print("the cache doesnt contain the website")        
			# Create a socket on the proxyserver
			serverFacingSocket = socket(AF_INET,SOCK_STREAM) 
			print('listening from server')    # Fill in start              # Fill in end
			# Connect to the socket to port 80
			# Fill in start
			serverFacingSocket.bind((webServer,port))
			serverFacingSocket.listen(1)
			print('prepared to listen from server')

			# Fill in end
			#get from the server to the proxy server the file
			with open(file_to_use, "wb") as cacheFile:
				while True:
					#need to get into the buffer
					buff =  serverFacingSocket.recv(4096)# Fill in start             # Fill in end
					cacheFile.write(buff)
					if buff:
						
						# Fill in start  
						clientFacingSocket.send(buff)
						           # Fill in end
					else:
						break
		except:
			print(str(sys.exc_info()[0]))                                                
		finally:
			serverFacingSocket.close()
			# Fill in start             # Fill in end
	except:
		print(str(sys.exc_info()[0]))

	finally:
		clientFacingSocket.close()
		# Fill in start             # Fill in end


if len(sys.argv) > 2:
	print('Usage : "python proxy.py port_number"\n')
	sys.exit(2)
if len(sys.argv) == 2:
	proxy_port = int(sys.argv[1])

if not os.path.exists(cache_directory):
	os.makedirs(cache_directory)
	
# Create a server socket, bind it to a port and start listening
welcomeSocket = socket(AF_INET, SOCK_STREAM)# Fill in start             # Fill in end

# Fill in start
welcomeSocket.bind(("localhost",proxy_port))
welcomeSocket.listen(1)
# Fill in end


print('Proxy ready to serve at port', proxy_port)

try: 
	while True:
		# Start receiving data from the client
		clientFacingSocket, addr = welcomeSocket.accept()#Fill in start             # Fill in end
		print('Received a connection from:', addr)
		print(clientFacingSocket)
		# the following function starts a new thread, taking the function name as the first argument, and a tuple of arguments to the function as its second argument
		thread.start_new_thread(client_thread, (clientFacingSocket, ))

except KeyboardInterrupt:
	print('bye...')

finally:
	welcomeSocket.close()
	# Fill in start             # Fill in end

