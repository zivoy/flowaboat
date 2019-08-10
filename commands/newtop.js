const osu = require('../osu.js');
const helper = require('../helper.js');
const config = require('../config.json');

module.exports = {
	command: ['top', 'rnb', 'recentnewbest', 'onb', 'oldnewbest'],
	description: "Show a specific top play.",
	startsWith: true,
	usage: '[username]',
	example: [
		{
			run: "newtop",
			result: "Returns your #1 top play. with new pp"
		},
		{
			run: "newtop5 vaxei",
			result: "Returns Vaxei's #5 top play."
		},
		{
			run: "rnb",
			result: "Returns your most recent top play."
		},
		{
			run: "onb",
			result: "Returns your oldest top play (from your top 100)."
		}
	],
	configRequired: ['credentials.osu_api_key'],
	call: obj => {
		return new Promise((resolve, reject) => {
			let { argv, msg, user_ign, last_beatmap } = obj;

			let top_user = helper.getUsername(argv, msg, user_ign);

			let command = argv[0].toLowerCase().replace(/[0-9]/g, '');

			if(!module.exports.command.includes(command))
				return false;

			let rb = argv[0].toLowerCase().startsWith('rnb') || argv[0].toLowerCase().startsWith('recentnewbest');
			let ob = argv[0].toLowerCase().startsWith('onb') || argv[0].toLowerCase().startsWith('oldnewbest');

			let index = 1;
			let match = argv[0].match(/\d+/);
			let _index = match > 0 ? match[0] : 1;

			if(_index >= 1 && _index <= 100)
				index = _index;

			if(!top_user){
				if(user_ign[msg.author.id] == undefined){
					reject(helper.commandHelp('ign-set'));
				}else{
					reject(helper.commandHelp('newtop'));
				}

				return false;
			}else{
				osu.get_new_top({user: top_user, index: index, rb: rb, ob: ob}, (err, recent, strains_bar, ur_promise) => {
					if(err){
						helper.error(err);
						reject(err);
						return false;
					}else{
						let embed = osu.format_embed(recent);
						helper.updateLastBeatmap(recent, msg.channel.id, last_beatmap);

						if(ur_promise){
							resolve({
								embed: embed,
								files: [{attachment: strains_bar, name: 'strains_bar.png'}],
								edit_promise: new Promise((resolve, reject) => {
									ur_promise.then(recent => {
										embed = osu.format_embed(recent);
										resolve({embed});
									});
								})});
						}else{
							resolve({
								embed: embed,
								files: [{attachment: strains_bar, name: 'strains_bar.png'}]
							});
						}
					}
				});
			}
		});
	}
};
