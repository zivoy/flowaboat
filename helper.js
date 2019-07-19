const LocalStorage = require('node-localstorage').LocalStorage;
localStorage = new LocalStorage('./scratch');

const moment = require('moment');
const fs = require('fs-extra');
const path = require('path');
const { execFileSync } = require('child_process');
const axios = require('axios');

const config = require('./config.json');

const sep = ' ✦ ';
const cmd_escape = "```";

let commands;

function dateFolders (startDir, date){
	if (date === undefined) {
		date = moment();
	}
	let year, month, day;
	year = startDir + "/" + date.format("YYYY");
	month = year + "/" + date.format("MM");
	day = month + "/" + date.format("DD");

	if (!fs.existsSync(year)){
		fs.mkdirSync(year);
	}
	if (!fs.existsSync(month)) {
		fs.mkdirSync(month);
	}
	if (!fs.existsSync(day)) {
		fs.mkdirSync(day);
	}
	return day;
}

function logFiles (startDir, path){
	if (path === undefined){
		path = todaysPath
	}
	let todaysFolder = dateFolders(startDir);
	if (todaysFolder === path){
	} else {
		logStream.end();
		errStream.end();
		logStream = fs.createWriteStream(todaysFolder + "/log.log", {flags:'a'});
		errStream = fs.createWriteStream(todaysFolder + "/err.log", {flags:'a'});
		todaysPath = todaysFolder;
	}

}

let todaysPath = dateFolders(__dirname + "/logs");
let logStream = fs.createWriteStream(todaysPath + "/log.log", {flags:'a'});
let errStream = fs.createWriteStream(todaysPath + "/err.log", {flags:'a'});


module.exports = {
    init: _commands => {
        commands = _commands;
    },

    sep: sep,

    cmd_escape: cmd_escape,

	dateFolders: (...params) => dateFolders(...params),

    log: (...params) => {
		logFiles(__dirname + "/logs");
        console.log(`[${moment().toISOString()}]`, ...params);
		logStream.write(`[${moment().toISOString()}] ` + params.join(' '));
    },

    error: (...params) => {
		logFiles(__dirname + "/logs");
		console.error(`[${moment().toISOString()}]`, ...params);
		errStream.write(`[${moment().toISOString()}] ` + params.join(' '));
	},

    setItem: (item, data) => {
        localStorage.setItem(item, data);
    },

    getItem: item => {
        return localStorage.getItem(item);
    },

    commandHelp: command_name => {
        if(Array.isArray(command_name))
            command_name = command_name[0];

        for(let i = 0; i < commands.length; i++){
            let command = commands[i];

            if(!Array.isArray(command.command))
                command.command = [command.command];

            if(command.command.includes(command_name)){
                let embed = {
                    fields: []
                };

                let commands_value = "";
                let commands_name = "Command";

                if(command.command.length > 1)
                    commands_name += "s";

                command.command.forEach((_command, index) => {
                    if(index > 0)
                        commands_value += ", ";

                    commands_value += `\`${config.prefix}${_command}\``;
                });

                embed.fields.push({
                    name: commands_name,
                    value: commands_value + "\n"
                });

                if(!Array.isArray(command.description))
                    command.description = [command.description];

                if(command.description){
                    embed.fields.push({
                        name: "Description",
                        value: command.description.join("\n") + "\n"
                    })
                }

                if(command.usage){
                    embed.fields.push({
                        name: "Usage",
                        value: `${cmd_escape}${config.prefix}${command.command[0]} ${command.usage}${cmd_escape}\n`
                    });
                }

                if(command.example){
                    let examples = command.example;
                    let examples_value = "";
                    let examples_name = "Example";

                    if(!Array.isArray(examples))
                        examples = [examples];

                    if(examples.length > 1)
                        examples_name += "s";

                    examples.forEach((example, index) => {
                        if(index > 0)
                            examples_value += "\n\n";

                        if(typeof example === 'object'){
                            examples_value += `${cmd_escape}${config.prefix}${example.run}${cmd_escape}`;
                            examples_value += example.result;
                        }else{
                            examples_value += `${cmd_escape}${config.prefix}${example}${cmd_escape}`;
                        }
                    });

                    embed.fields.push({
                        name: examples_name,
                        value: examples_value + "\n"
                    })
                }

                return {embed: embed};
            }
        }

        return "Couldn't find command.";
    },

    validateBeatmap: beatmap_path => {
        let file = fs.readFileSync(beatmap_path, 'utf8');
        let lines = file.split("\n");

        if(lines.length > 0 && !lines[0].includes('osu file format'))
            return false;

        return true;
    },

    downloadFile: (file_path, url) => {
        return new Promise((resolve, reject) => {
            fs.ensureDirSync(path.dirname(file_path));

            axios.get(url, {responseType: 'stream'}).then(response => {
                let stream = response.data.pipe(fs.createWriteStream(file_path));

                stream.on('finish', () => {
                    if(!module.exports.validateBeatmap(file_path)){
                        fs.remove(file_path);
                        reject("Couldn't download file");
                    }

                    resolve();
                });

                stream.on('error', () => {
                    reject("Couldn't download file");
                });
            }).catch(() => {
                reject("Couldn't download file");
            });
        });
    },

    downloadBeatmap: beatmap_id => {
        return new Promise((resolve, reject) => {
            let beatmap_path = path.resolve(config.osu_cache_path, `${beatmap_id}.osu`);

            fs.ensureDirSync(path.dirname(beatmap_path));

            if(!fs.existsSync(beatmap_path)
            || (fs.existsSync(beatmap_path) && !module.exports.validateBeatmap(beatmap_path))){
                module.exports.downloadFile(beatmap_path, `https://osu.ppy.sh/osu/${beatmap_id}`).then(() => {
                    resolve();
                }).catch(reject);
            }else{
                resolve();
            }
        });
    },

    emote: (emoteName, guild, client) => {
        let emote;

        if(guild)
            emote = guild.emojis.find(emoji => emoji.name.toLowerCase() === emoteName.toLowerCase());

        if(!emote)
            emote = client.emojis.find(emoji => emoji.name.toLowerCase() === emoteName.toLowerCase());

        return emote;
    },

    replaceAll: (target, search, replacement) => {
        return target.split(search).join(replacement);
    },

    splitWithTail: (string, delimiter, count) => {
        let parts = string.split(delimiter);
        let tail = parts.slice(count).join(delimiter);
        let result = parts.slice(0,count);
        result.push(tail);

        return result;
    },

    getRandomArbitrary: (min, max) => {
        return Math.random() * (max - min) + min;
    },

    getRandomInt: (min, max) => {
        min = Math.ceil(min);
        max = Math.floor(max);
        return Math.floor(Math.random() * (max - min)) + min;
    },

    simplifyUsername: username => {
        return username.replace(/[^a-zA-Z0-9]/g, '').toLowerCase().trim();
    },

    validUsername: username => {
        return !(/[^a-zA-Z0-9\_\[\]\ \-]/g.test(username));
    },

    getUsername: (args, message, user_ign) => {
        let return_username;

        args = args.slice(1);

        args.forEach(function(arg){
            if(module.exports.validUsername(arg))
                return_username = arg;
            else if(module.exports.validUsername(arg.substr(1)) && arg.startsWith('*'))
                return_username = arg;
        });

         if(message.guild && user_ign){
             let members = message.guild.members.array();

            args.forEach(function(arg){
                let matching_members = [];

                members.forEach(member => {
                    if(module.exports.simplifyUsername(member.user.username) == module.exports.simplifyUsername(arg))
                        matching_members.push(member.id);
                });

                matching_members.forEach(member => {
                    if(member in user_ign)
                        return_username = user_ign[member];
                });
            });
         }

        args.forEach(function(arg){
           if(arg.startsWith("<@")){
                let user_id = arg.substr(2).split(">")[0].replace('!', '');

                if(user_ign && user_id in user_ign)
                    return_username = user_ign[user_id];
           }
        });

        if(!return_username){
            if(message.author.id in user_ign)
                return_username = user_ign[message.author.id];
        }

        if(config.debug)
            module.exports.log('returning data for username', return_username);

        return return_username;
    },

    updateLastBeatmap: (recent, channel_id, last_beatmap) => {
        last_beatmap[channel_id] = {
            beatmap_id: recent.beatmap_id,
            mods: recent.mods,
            acc: recent.acc,
            fail_percent: recent.fail_percent
        };

        if(recent.score_id)
            last_beatmap[channel_id].score_id = recent.score_id;

        module.exports.setItem('last_beatmap', JSON.stringify(last_beatmap));
    }
}
