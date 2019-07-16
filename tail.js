const dirName = process.argv[2];
const childs = require('child_process');
const app = require('express')();
const http = require('http').createServer(app);
const io = require('socket.io')(http);
const fs = require("fs");
const sha1 = require('js-sha1');
var auth = {};
var key = "e31ecac48f92a2c23373214d13f54135d31105eb";

if (!dirName)
	return console.log("Usage: node tail.js log folder");

var tail = childs.spawn("tail", ["-f", dirName + '/log.log']);
console.log("start tailing");

tail.stdout.setEncoding('utf8');

/*tail.stdout.on('data', function(data) {
	console.log(data.toString());
});*/

function getClintAddr(soc){
	try {
		var address = soc.request.connection.remoteAddress;
		//var port = soc.request.connection.remotePort;
	} catch (TypeError) {
		var address = soc.ip;
		//var port = soc.request.connection.remotePort;
	}
	var port = "0000";
	return address +":"+ port
}

app.get("/",function (req, res) {
	//console.log(req);
	res.sendFile(__dirname + "/pass.html")
});

app.get('/liveLog', function(req, res){
	var address = getClintAddr(req);
	if (auth[address]) {
		res.sendFile(__dirname + '/logRender.html');
	} else {
		res.redirect("/")
	}
});
/*
app.get('/log', function(req, res){
	res.sendFile(dirName + '/log.log', {root: __dirname});
});

app.get('/out', function(req, res){
	res.sendFile(dirName + '/out.log', {root: __dirname});
});

app.get('/err', function(req, res){
	res.sendFile(dirName + '/err.log', {root: __dirname});
});
*/


io.on('connect', function(passph){
	var address = getClintAddr(passph);
	auth[address] = false;
});

io.on('connection', function(passph){
	passph.on('chat message', function(msg){
		var address = getClintAddr(passph);
		console.log(address + " sent " + sha1(msg));
		if (sha1(msg) === key){
			passph.emit('redirect', "./liveLog");
			auth[address] = true
		}
	});
});

io.on('connect', function(socket) {
	var address = getClintAddr(socket);
	fs.readFile(dirName + '/log.log', function(error, data) {
		if (error) { throw error; }
		data.toString().split("\n").forEach(function(line) {
			io.to(`${socket["id"]}`).emit('log output', line);
		});
	});
	auth[address] = false;
});

io.on('connection', function(socket){
	tail.stdout.on('data', function(data) {
		io.to(`${socket["id"]}`).emit('log output', data.toString());
	});
});

http.listen(80, function(socket){
	console.log('listening on *:80');
});