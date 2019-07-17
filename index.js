if(require('semver').lt(process.version, '10.0.0'))
	throw "flowabot only runs on Node.js 10 or higher";

const Discord = require('discord.js');
const fs = require('fs-extra');
const path = require('path');
const objectPath = require("object-path");
const chalk = require('chalk');

const osu = require('./osu.js');
const helper = require('./helper.js');

const childs = require('child_process');
const app = require('express')();
const http = require('http').createServer(app);
const io = require('socket.io')(http);
const sha1 = require('js-sha1');

var auth = {};
const key = "e31ecac48f92a2c23373214d13f54135d31105eb";
const dirName = "./logs";

const client = new Discord.Client({autoReconnect:true});

const tail = childs.spawn("tail", ["-f", dirName + '/log.log']);
console.log("");
helper.log("start tailing");

tail.stdout.setEncoding('utf8');

client.on('error', helper.error);

const config = require('./config.json');

let user_ign = {};

if(helper.getItem('user_ign')){
	user_ign = JSON.parse(helper.getItem('user_ign'));
}else{
	helper.setItem("user_ign", JSON.stringify(user_ign));
}

let last_beatmap = {};

if(helper.getItem('last_beatmap')){
	last_beatmap = JSON.parse(helper.getItem('last_beatmap'));
}else{
	helper.setItem('last_beatmap', JSON.stringify(last_beatmap));
}

let last_message = {}

if(helper.getItem('last_message')){
	last_message = JSON.parse(helper.getItem('last_message'));
}else{
	helper.setItem('last_message', JSON.stringify(last_message));
}

if(config.credentials.osu_api_key && config.credentials.osu_api_key.length > 0)
    osu.init(client, config.credentials.osu_api_key, last_beatmap);

function getClintAddr(soc){
	let address;
	try {
		address = soc.request.connection.remoteAddress;
		//var port = soc.request.connection.remotePort;
	} catch (TypeError) {
		address = soc.ip;
		//var port = soc.request.connection.remotePort;
	}
	const port = "0000";
	return address +":"+ port
}

function checkCommand(msg, command){
    if(!msg.content.startsWith(config.prefix))
        return false;

	if(msg.author.bot)
		return false;

    let argv = msg.content.split(' ');

    let command_match = false;

    let msg_check = msg.content.toLowerCase().substr(config.prefix.length).trim();

    let commands = command.command;

    let startswith = false;

    if(command.startsWith)
        startswith = true;

    if(!Array.isArray(commands))
        commands = [commands];

    for(let i = 0; i < commands.length; i++){
        let command_check = commands[i].toLowerCase().trim();
        if(startswith){
            if(msg_check.startsWith(command_check))
                command_match = true;
        }else{
            if(msg_check.startsWith(command_check + ' ')
            || msg_check == command_check)
                command_match = true;
        }
    }

    if(command_match){
        let hasPermission = true;

        if(command.permsRequired)
            hasPermission = command.permsRequired.length == 0 || command.permsRequired.some(perm => msg.member.hasPermission(perm));

        if(!hasPermission)
            return 'Insufficient permissions for running this command.';

        if(command.argsRequired !== undefined && argv.length <= command.argsRequired)
            return helper.commandHelp(command.command);

        return true;
    }

    return false;
}

let commands = [];
let commands_path = path.resolve(__dirname, 'commands');

fs.readdir(commands_path, (err, items) => {
    if(err)
        throw "Unable to read commands folder";

    items.forEach(item => {
        if(path.extname(item) == '.js'){
            let command = require(path.resolve(commands_path, item));

            command.filename = path.resolve(commands_path, item);

            let available = true;
            let unavailability_reason = [];

            if(command.folderRequired !== undefined && command.folderRequired.length > 0){
                let { folderRequired } = command;

                if(!Array.isArray(command.folderRequired))
                    folderRequired = [folderRequired];

                folderRequired.forEach(folder => {
                    if(!fs.existsSync(path.resolve(__dirname, folder)))
                        available = false;
                        unavailability_reason.push(`required folder ${folder} does not exist`);
                });
            }

            if(command.configRequired !== undefined && command.configRequired.length > 0){
                let { configRequired } = command;

                if(!Array.isArray(command.configRequired))
                    configRequired = [configRequired];

                configRequired.forEach(config_path => {
                    if(!objectPath.has(config, config_path)){
                        available = false;
                        unavailability_reason.push(`required config option ${config_path} not set`);
                    }else if(objectPath.get(config, config_path).length == 0){
                        available = false;
                        unavailability_reason.push(`required config option ${config_path} is empty`);
                    }
                });
            }

            if(command.emoteRequired !== undefined && command.emoteRequired.length > 0){
                let { emoteRequired } = command;

                if(!Array.isArray(command.emoteRequired))
                    emoteRequired = [emoteRequired];

                emoteRequired.forEach(emote_name => {
                    let emote = helper.emote(emote_name, null, client);
                    if(!emote){
                        available = false;
                        unavailability_reason.push(`required emote ${emote_name} is missing`);
                    }
                });
            }

            if(available){
                commands.push(command);
			}else{
				if(!Array.isArray(command.command))
					command.command = [command.command];

				console.log('');
				console.log(chalk.yellow(`${config.prefix}${command.command[0]} was not enabled:`));
				unavailability_reason.forEach(reason => {
					console.log(chalk.yellow(reason));
				});
			}
        }
    });

    helper.init(commands);
});

let handlers = [];
let handlers_path = path.resolve(__dirname, 'handlers');

fs.readdir(handlers_path, (err, items) => {
    if(err)
        throw "Unable to read handlers folder";

    items.forEach(item => {
        if(path.extname(item) == '.js'){
            let handler = require(path.resolve(handlers_path, item));
            handlers.push(handler);
        }
    });
});

function onMessage(msg){
    let argv = msg.content.split(' ');

    argv[0] = argv[0].substr(config.prefix.length);

    if(config.debug)
        helper.log(msg.author.username + "@" + msg.channel.name + ':', msg.content);

    commands.forEach(command => {
        let check_command = checkCommand(msg, command);

        if(check_command === true){
            if(command.call && typeof command.call === 'function'){
                let promise = command.call({
                    msg,
                    argv,
                    client,
                    user_ign,
                    last_beatmap,
                    last_message
                });

                Promise.resolve(promise).then(response => {
                    if(response){
                        let message_promise, edit_promise, replace_promise, remove_path, content;

                        if(typeof response === 'object' && 'edit_promise' in response){
                            ({edit_promise} = response);
                            delete response.edit_promise;
                        }

						if(typeof response === 'object' && 'replace_promise' in response){
                            ({replace_promise} = response);
                            delete response.replace_promise;
                        }

                        if(typeof response === 'object' && 'remove_path' in response){
							({remove_path} = response);
                            delete response.remove_path;
                        }

						if(typeof response === 'object' && 'content' in response){
							({content} = response);
                            delete response.content;
						}

						if(content)
	                        message_promise = msg.channel.send(content, response);
						else
							message_promise = msg.channel.send(response);

						message_promise.catch(err => {
							msg.channel.send(`Couldn't run command: \`${err}\``);
						});


                        Promise.all([message_promise, edit_promise, replace_promise]).then(responses => {
                            let message = responses[0];
                            let edit_promise = responses[1];
							let replace_promise = responses[2];

                            if(edit_promise)
                                message.edit(edit_promise).catch(helper.error);

							if(replace_promise){
								msg.channel.send(replace_promise)
								.catch(err => {
									msg.channel.send(`Couldn't run command: \`${err}\``);
								}).finally(() => {
									message.delete();

									if(typeof replace_promise === 'object' && 'remove_path' in replace_promise){
										({remove_path} = replace_promise);
			                            delete replace_promise.remove_path;
			                        }

									if(remove_path)
										fs.remove(remove_path, err => { if(err) helper.error });
								});
							}

                            if(remove_path)
                                fs.remove(remove_path, err => { if(err) helper.error });
                        }).catch(err => {
							msg.channel.send(`Couldn't run command: \`${err}\``);
						});
                    }
                }).catch(err => {
                    if(typeof err === 'object')
                        msg.channel.send(err);
                    else
                        msg.channel.send(`Couldn't run command: \`${err}\``);

                    helper.error(err);
                });
            }
        }else if(check_command !== false){
            msg.channel.send(check_command);
        }
    });

    handlers.forEach(handler => {
        if(handler.message && typeof handler.message === 'function'){
            handler.message({
                msg,
                argv,
                client,
                user_ign,
                last_beatmap,
                last_message
            });
        }
    });
}

client.on('message', onMessage);

client.on('ready', () => {
	helper.log('flowabot is ready');
/*	if(config.credentials.discord_client_id)
		helper.log(
			`Invite bot to server: ${chalk.blueBright('https://discordapp.com/api/oauth2/authorize?client_id='
			+ config.credentials.discord_client_id + '&permissions=8&scope=bot')}`);*/
});

client.login(config.credentials.bot_token).catch(err => {
	console.error('');
	console.error(chalk.redBright("Couldn't log into Discord. Wrong bot token?"));
	console.error('');
	console.error(err);
	process.exit();
});

app.get("/",function (req, res) {
	res.sendFile(__dirname + "/pass.html");
});

app.get('/liveLog', function(req, res){
	const address = getClintAddr(req);
	if (auth[address]) {
		res.sendFile(__dirname + '/logRender.html');
	} else {
		res.redirect("/");
	}
});

io.on('connect', function(passph){
	const address = getClintAddr(passph);
	auth[address] = false;
});

io.on('connection', function(passph){
	passph.on('chat message', function(msg){
		const address = getClintAddr(passph);
		helper.log(address + " sent " + sha1(msg));
		if (sha1(msg) === key){
			passph.emit('redirect', "./liveLog");
			auth[address] = true;
		}
	});
	passph.on("disconnect", function() {
		const address = getClintAddr(passph);
		auth[address] = null;
	});
});

io.on('connect', function(socket) {
	const address = getClintAddr(socket);
	fs.readFile(dirName + '/log.log', function(error, data) {
		if (error) { throw error; }
		data.toString().split("\n").forEach(function(line) {
			io.to(`${socket["id"]}`).emit('log output', line);
		});
	});
	auth[address] = null;
});

io.on('connection', function(socket){
	tail.stdout.on('data', function(data) {
		io.to(`${socket["id"]}`).emit('log output', data.toString());
	});
});

http.listen(80, function(req){
	helper.log('listening on', req.get('host'));
});