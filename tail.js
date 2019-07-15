const filename = process.argv[2];
//const childs = require('child_process');
const app = require('express')();
const http = require('http').createServer(app);

if (!filename)
	return console.log("Usage: node watcher.js filename");
/*
// Look at http://nodejs.org/api.html#_child_processes for detail.
var tail = childs.spawn("tail", ["-f", filename]);
console.log("start tailing");

tail.stdout.setEncoding('utf8');
tail.stdout.on('data', function(data) {
	console.log(data.toString());
});
*/

app.get('/', function(req, res){
	res.sendFile(__dirname + '/logs/log.txt');
});

http.listen(8000, function(){
	console.log('listening on *:8000');
});

/*
// From nodejs.org/jsconf.pdf slide 56
http.createServer(function (req, res) {
	res.writeHead(200, {"Content-Type": "text/plain"});
	tail.stdout.on('data', function(data) {
		res.write(data.toString(), function(err) { netSocket.end(); });
	});
}).listen(8000);
 */