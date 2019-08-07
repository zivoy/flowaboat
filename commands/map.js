const osu = require('../osu.js');
const helper = require('../helper.js');

module.exports = {
	command: ['map', 'mp', 'mapinfo', 'info'],
	description: "Show information on map.",
	startsWith: true,
	usage: '[beatmap url] [+mods]',
	example: [
		{
			run: "map",
			result: "Returns map info for the last beatmap."
		},
		{
			run: "map +HR",
			result: "Returns map info with HR applied for the last beatmap."
		},
		{
			run: "map https://osu.ppy.sh/b/75",
			result: "Returns map info for this beatmap."
		}
	],
	configRequired: ['debug'],
	call: obj => {
		return new Promise((resolve, reject) => {
			let { argv, msg, last_beatmap } = obj;

			let beatmap_id, beatmap_url, beatmap_promise, download_promise, mods = "", custom_url = false, type;

			argv.map(arg => arg.toLowerCase());

			argv.slice(1).forEach(arg => {
				if(arg.startsWith('+')){
					mods = arg.toUpperCase().substr(1);
				}else{
					beatmap_url = arg;
					beatmap_promise = osu.parse_beatmap_url(beatmap_url);
					beatmap_promise.then(response => {
						beatmap_id = response;
						if(!beatmap_id) custom_url = true;
					});
				}
			});

			Promise.resolve(beatmap_promise).finally(() => {
				if(!(msg.channel.id in last_beatmap)){
					reject(helper.commandHelp('map'))
					return false;
				}else if(!beatmap_id && !custom_url){
					beatmap_id = last_beatmap[msg.channel.id].beatmap_id;
					download_promise = helper.downloadBeatmap(beatmap_id);

					mods = last_beatmap[msg.channel.id].mods.join('');
				}

				let download_path = path.resolve(config.osu_cache_path, `${beatmap_id}.osu`);

				if(!beatmap_id || custom_url){
					let download_url = URL.parse(beatmap_url);
					download_path = path.resolve(os.tmpdir(), `${Math.floor(Math.random() * 1000000) + 1}.osu`);

					download_promise = helper.downloadFile(download_path, download_url);

					download_promise.catch(reject);
				}

				Promise.resolve(download_promise).then(() => {
					osu.get_strains_graph(download_path, mods, cs, ar, type, (err, buf) => {
						if(err){
							reject(err);
							return false;
						}

						if(beatmap_id){
							helper.updateLastBeatmap({
								beatmap_id,
								mods,
								fail_percent: 1,
								acc: 1
							}, msg.channel.id, last_beatmap);
						}

						resolve({file: buf, name: 'strains.png'});
					});
				});
			});
		});
	}
};
