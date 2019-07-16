const dirName = process.argv[2];
const childs = require('child_process');
const app = require('express')();
const http = require('http').createServer(app);
const io = require('socket.io')(http);
const fs = require("fs");

if (!dirName)
	return console.log("Usage: node tail.js log folder");

var tail = childs.spawn("tail", ["-f", dirName + '/log.log']);
console.log("start tailing");

tail.stdout.setEncoding('utf8');

tail.stdout.on('data', function(data) {
	console.log(data.toString());
});


app.get('/', function(req, res){
	res.sendFile(__dirname + '/logRender.html');
});

app.get('/log', function(req, res){
	res.sendFile(dirName + '/log.log', {root: __dirname});
});

app.get('/out', function(req, res){
	res.sendFile(dirName + '/out.log', {root: __dirname});
});

app.get('/err', function(req, res){
	res.sendFile(dirName + '/err.log', {root: __dirname});
});

io.on('connect', function(socket) {
	fs.readFile("log.log", function(error, data) {
		if (error) { throw error; }
		data.toString().split("\n").forEach(function(line) {
			io.to(`${socket["id"]}`).emit('log output', data.toString());
		});
	});
});

io.on('connection', function(socket){
	tail.stdout.on('data', function(data) {
		io.to(`${socket["id"]}`).emit('log output', data.toString());
	});
});

http.listen(80, function(socket){
	console.log('listening on *:80');
});