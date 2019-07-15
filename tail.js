const filename = process.argv[0];
const childs = require('child_process');
const http = require("http");

if (!filename)
	return console.log("Usage: node watcher.js filename");

// Look at http://nodejs.org/api.html#_child_processes for detail.
var tail = childs.spawn("tail", ["-f", filename]);
console.log("start tailing");

tail.stdout.on('data', function(data) {
	console.log(data.toString());
});

// From nodejs.org/jsconf.pdf slide 56
http.createServer(function (req, res) {
	res.writeHead(200, {"Content-Type": "text/plain"});
	tail.stdout.on('data', function(data) {
		res.write(data);
	});

	res.end();
}).listen(8000);
