# -*- coding: utf-8 -*-
import argparse
import random
import os	
import json
import datetime

import cherrypy
from cherrypy.lib import static

localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

USERS = ['john', 'bill', 'garry']
PASSWORDS = ['5f4dcc3b5aa765d61d8327deb882cf99']
CONNECTED_USERS = []

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

class ChatPlugin(WebSocketPlugin):
	def __init__(self, bus):
		WebSocketPlugin.__init__(self, bus)
		self.clients = {}

	def start(self):
		WebSocketPlugin.start(self)
		self.bus.subscribe('add-client', self.add_client)
		self.bus.subscribe('get-client', self.get_client)
		self.bus.subscribe('del-client', self.del_client)

	def stop(self):
		WebSocketPlugin.stop(self)
		self.bus.unsubscribe('add-client', self.add_client)
		self.bus.unsubscribe('get-client', self.get_client)
		self.bus.unsubscribe('del-client', self.del_client)

	def add_client(self, name, websocket):
		self.clients[name] = websocket

	def get_client(self, name):
		return self.clients[name]

	def del_client(self, name):
		del self.clients[name]

class ChatWebSocketHandler(WebSocket):
	def received_message(self, m):
		global CONNECTED_USERS
		dict = json.loads( m.data.decode(m.encoding) )
		dict['message'] = "{" + str(datetime.datetime.today().strftime("%H:%M:%S %d.%m.%y")) + " from " + str(dict['users']) + " } " + str(dict['message'])
		CONNECTED_USERS = list(set(CONNECTED_USERS + dict['users']))
		dict['users'] = [user for user in CONNECTED_USERS]
		cherrypy.log(str((dict)))
		m.data = json.dumps(dict).encode(m.encoding)
		cherrypy.engine.publish('websocket-broadcast', m)

	def connected(self, code, info, user):
		pass
		#cherrypy.engine.publish('websocket-broadcast', TextMessage("param " + user))

	def closed(self, code, reason="A client left the room without a proper explanation."):
		#global CONNECTED_USERS
		#dict = {}#json.loads( m.data.decode(m.encoding) )
		#dict['message'] = "{" + str(datetime.datetime.today().strftime("%H:%M:%S %d.%m.%y")) + " from " + str(dict['users']) + " } " + str(dict['message'])
		#CONNECTED_USERS = list(set(CONNECTED_USERS + dict['users']))
		#dict['users'] = [user for user in CONNECTED_USERS]
		#cherrypy.log(str((dict)))
		#m.data = json.dumps(dict).encode(m.encoding)
		cherrypy.engine.publish('websocket-broadcast', TextMessage("param "))

class Root(object):
	def __init__(self, host, port, ssl=False):
		self.host = host
		self.port = port
		self.scheme = 'wss' if ssl else 'ws'
		
	@cherrypy.expose
	def index(self):
		return """<html>
		<head>
			<meta name="viewport" content="width=device-width, initial-scale=1">
			<link href="/css/style.css" rel="stylesheet">
		</head>
		<body>
		<p><a href="/files">update download files</a></p>
		<form id='ctr' action='/chat_room' id='chatform' method='post'>
			<center>
			<strong><input class="centery" type='text' name='username' value='ЛОГИН'  /><br />
			<input class="centery" type='password' name='password' value='password'  /><br />
			<p><input class="centery" id='send' type='submit' value='ВОЙТИ' /></p>
			</strong></center>
		</form>
		<p class="bottom"><strong>Чат ОАО "Планар" 2019</strong></p>
		</body>
		</html>
		"""
	@cherrypy.expose
	def files(self):
		out = """
		<html><body>
			<h2>Upload a file</h2>
			<form method="post" action="/upload" enctype="multipart/form-data">
			<input type="file" name="ufile" />
			<input type="submit" />
			</form>
			<h2>Download a file</h2>"""
		files_html = ''
		names = os.listdir(os.getcwd() + '\\files')
		for name in names:
			files_html = files_html + "<p><a href=\"/download?file=" + name + '\">' + name + '</a></p>\n'
		#herrypy.log(len(files_html))
		#cherrypy.log(files_html)
		return out + files_html + '</body></html>'

	@cherrypy.expose
	def upload(self, ufile):
		# Either save the file to the directory where server.py is
		# or save the file to a given path:
		# upload_path = '/path/to/project/data/'
		upload_path = os.getcwd() + '\\files'

		# Save the file to a predefined filename
		# or use the filename sent by the client:
		# upload_filename = ufile.filename
		upload_filename = ufile.filename

		upload_file = os.path.normpath(
			os.path.join(upload_path, upload_filename))
		size = 0
		with open(upload_file, 'wb') as out:
			while True:
				data = ufile.file.read(8192)
				if not data:
					break
				out.write(data)
				size += len(data)
		out = '''
			File received.
			Filename: {}
			Length: {}
			Mime-type: {}
			<form method="post" action="/files" enctype="multipart/form-data">
			<input type="submit" value="Refresh and return" />
			</form>
			''' .format(ufile.filename, size, ufile.content_type, data)
		return out



	@cherrypy.expose
	def download(self, file):
		download_path = os.getcwd() + '\\files'
		path = os.path.join(download_path, file)
		#return (path)
		return static.serve_file(path, 'application/x-download',
								 'attachment', os.path.basename(path))

	@cherrypy.expose
	def chat_room(self, username, password):
		if username not in USERS:
			return """<html>
		<head>
		</head>
		<body>
		Вы не авторизованный пользователь.
		</body>
		</html>"""
		else:
			#if password not in PASSWORDS:
			"""	return <html>
			#<head>
			</head>
			<body>
			Вы не авторизованный пользователь. Вот.
			</body>
			</html>"""
			#else:
			return """<html>
			<head>
			<link href="/css/style.css" rel="stylesheet">
			<style>
			div.poswrap {
			float:right;
			opacity:0.6;
			}
			div.wrapper {
			width:777px;
			}
			div.right_block {
			float:right;
			}
			div.left_block {
			float:left;
			}
			div.footer {
			float:left;
			}
			

			</style>
			</style>
			</head>
			<body>
			<div class="poswrap">
			<div class="wrapper">				
			<div class="left_block">
			<textarea id='chat' cols='70' rows='20'></textarea>
			</div>
			<div class="right_block">
			<textarea id='users' cols='35' rows='20'></textarea>
			</div>
			<div class="footer">
			<label for='message'>%(username)s: </label><input id='message' />
			<button type="button" id='send' >Send</button>
			</div>
			</div>
			</div>
					 <script type='application/javascript'>
						 websocket = '%(scheme)s://%(host)s:%(port)s/ws';				 
						 if (window.WebSocket) {
							ws = new WebSocket(websocket);
						 }
						 else if (window.MozWebSocket) {
						 ws = MozWebSocket(websocket);
						 }
						 else {
						 console.log('WebSocket Not Supported');
						 }
						 var c = document.getElementById('chat');
						 var u = document.getElementById('users');
						 window.onbeforeunload = function(e) {
						 c.value=c.value + 'Bye bye...\\n';
						 ws.close(1000, '%(username)s left the room');
						 if(!e) e = window.event;
						 e.stopPropagation();
						 e.preventDefault();
						 };
						 ws.onmessage = function (evt) {
							var data = JSON.parse(evt.data);
							c.value=data.message + '\\n' + c.value;
							u.value=data.users.join("\\n");
						 };
						 ws.onopen = function() {
							var mes = {
								users: Array("%(username)s"),
								message: "%(username)s successfuly connected!"
							}
							ws.send(JSON.stringify(mes));
						 };
						 ws.onclose = function(evt) {
							var mes = {
								users: Array("%(username)s"),
								message: "%(username)s disconnected from chat!"
							}
							ws.send(JSON.stringify(mes));
						 };
						document.getElementById('send').onclick = function() {
							console.log(document.getElementById('message').value);
							var mes = {
								users: Array("%(username)s"),
								message: document.getElementById('message').value
							}
							ws.send(JSON.stringify(mes));
							//ws.send("%(username)s: " +document.getElementById('message').value);
							 document.getElementById('message').value ="";
							return false;
						 };
					 </script>
			</body>
			</html>
			""" % {'username': username, 'host': self.host, 'port': self.port, 'scheme': self.scheme}

	@cherrypy.expose
	def ws(self):
		cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

if __name__ == '__main__':
	import logging
	from ws4py import configure_logger
	configure_logger(level=logging.DEBUG)

	current_dir = os.getcwd() + '\\static'
	
	parser = argparse.ArgumentParser(description='Echo CherryPy Server')
	parser.add_argument('--host', default='127.0.0.1')
	parser.add_argument('-p', '--port', default=8080, type=int)
	parser.add_argument('--ssl', action='store_true')
	args = parser.parse_args()
	#cherrypy.log('Hosting on ' + args.host)
	#cherrypy.log(os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')))
	cherrypy.config.update({'server.socket_host': args.host,
							'server.socket_port': args.port,
							'tools.staticdir.root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))})

	if args.ssl:
		cherrypy.config.update({
		'server.ssl_module':'builtin',
		'server.ssl_certificate': 'server.crt',
		'server.ssl_private_key': 'server.key'})

	WebSocketPlugin(cherrypy.engine).subscribe()
	#ChatPlugin(cherrypy.engine).subscribe()
	cherrypy.tools.websocket = WebSocketTool()

	cherrypy.quickstart(Root(args.host, args.port, args.ssl), '/', config={
		'/': {
			'tools.staticdir.root' : current_dir
			},
		'/ws': {
			'tools.websocket.on': True,
			'tools.websocket.handler_cls': ChatWebSocketHandler
			},
		'/js': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': 'js'
			},
		'/css': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': 'css'
			}
		}
	)