# Table Of Contents
### Commands
- [o!ar](#oar)
- [o!bpm](#obpm)
- [o!cs](#ocs)
- [o!flowaboat](#oflowaboat)
- [o!hello](#ohello)
- [o!help](#ohelp)
- [o!hp](#ohp)
- [o!ign-set](#oign-set)
- [o!od](#ood)
- [o!osu](#oosu)
- [o!recent](#orecent)
- [o!schedule](#oschedule)
- [o!set-muda](#oset-muda)
- [o!statme](#ostatme)
- [o!top](#otop)
### Administrative functions
- [badmuda](#badmuda)
- [bruh](#bruh)
- [when pinged](#when pinged)
---
## o!ar
Calculate Approach Rate values and milliseconds with mods applied.

**Required variables**: `1`

**Usage**: `o!ar <ar> [+mods]`

### Examples:

```
o!ar 8 +DT
```
Returns AR of AR8 with DT applied.



```
o!ar 6.4 +EZ
```
Returns AR of AR6.4 with EZ applied.


## o!bpm
Plot a graph of the bpm over the course of the song

**Required variables**: `0`

**Usage**: `o!bpm [map link] [+mods]`

### Examples:

```
o!bpm +DT
```
Returns BPM graph for the last beatmap with Double time.



```
o!bpm https://osu.ppy.sh/beatmapsets/545156#osu/1262906
```
Returns a BPM chart for Loose Change [Rohit's Insane].


## o!cs
Calculate Circle Size value with mods applied.

**Required variables**: `1`

**Usage**: `o!cs <cs> [+mods]`

### Examples:

```
o!cs 6 +HR
```
Returns CS of AR8 with HR applied.



```
o!cs 8.3 +EZ
```
Returns CS of AR8.3 with EZ applied.


## o!flowaboat
Show information about this bot.

**Required variables**: `0`

**Usage**: `o!flowaboat `

### Example:

```
o!flowaboat
```
Tells you about flowaboat.


## o!hello
say hello back

**Required variables**: `0`

**Usage**: `o!hello `

#### Synonyms:

`o!hi`

### Example:

```
o!hello
```
hello <@user>


## o!help
Get help for a command. 

 **List of all commands**: 
 https://github.com/zivoy/flowaboat/blob/pythonized/COMMANDS.md

**Required variables**: `1`

**Usage**: `o!help <command>`

#### Synonyms:

`o!h`

### Example:

```
o!help pp
```
Returns help on how to use the `o!pp` command.


## o!hp
Calculate Health value with mods applied.

**Required variables**: `1`

**Usage**: `o!hp <hp> [+mods]`

### Examples:

```
o!hp 4 +HR
```
Returns HP of AR8 with HR applied.



```
o!hp 7 +EZ
```
Returns HP of AR6.4 with EZ applied.


## o!ign-set
Sets your username for platform.

**Required variables**: `2`

**Usage**: `o!ign-set [osu|steam] <username>`

#### Synonyms:

`o!set-ign`, `o!set `, `o!ign `

### Examples:

```
o!set-ign osu nathan on osu
```
Sets your osu! username to nathan on osu.



```
o!set steam flyingpigoftheapocalypse
```
Sets your steam username to flyingpigoftheapocalypse.


## o!od
Calculate Overall Difficulty values and milliseconds with mods applied.

**Required variables**: `1`

**Usage**: `o!od <od> [+mods]`

### Examples:

```
o!od 7 +HT
```
Returns OD of AR8 with HT applied.



```
o!od 3.5 +HR
```
Returns OD of AR6.4 with HR applied.


## o!osu
Show osu! stats.

**Required variables**: `0`

**Usage**: `o!osu [username]`

### Examples:

```
o!osu
```
Returns your osu! stats.



```
o!osu nathan_on_osu
```
Returns nathan on osu's osu! stats.


## o!recent
Show recent score or pass.

**Required variables**: `0`

**Usage**: `o!recent [username]`

#### Synonyms:

`o!recent\d+`, `o!rs`, `o!recentpass`, `o!rp`

### Examples:

```
o!recent nathan_on_osu
```
Returns nathan on osu's most recent score.



```
o!recent3 respektive
```
Returns respektive's most recent score.



```
o!recentpass
```
Returns your most recent pass.


## o!schedule
Schedule events.

**Required variables**: `1`

**Usage**: `o!schedule <command>`

#### Synonyms:

`o!sched`, `o!event`

### Examples:

```
o!sched init
```
Sets the current channel as ping channel.



```
o!event new
```
Walks you through setting up a new event


## o!set-muda
set safe place for muda

**Required variables**: `0`

**Usage**: `o!set-muda `

#### Synonyms:

`o!setmuda`, `o!mudainit`, `o!muda-init`

### Example:

```
o!set-muda
```
set as muda dump


## o!statme
Show data on your user

**Required variables**: `0`

**Usage**: `o!statme [username]`

#### Synonyms:

`o!me`, `o!info`, `o!stat`

### Examples:

```
o!me
```
Returns your information and stats.



```
o!info tmanti
```
Returns tmanti's stats.


## o!top
Show a specific top play.

**Required variables**: `0`

**Usage**: `o!top [username]`

#### Synonyms:

`o!top\d+`, `o!rb`, `o!recentbest`, `o!ob`, `o!oldbest`

### Examples:

```
o!top
```
Returns your #1 top play.



```
o!top5 vaxei
```
Returns Vaxei's #5 top play.

---

## badmuda
Warns users if they use the Muda bot in the wrong channel.

### Trigger:
if a user posts anything starting with a `$` they will be put on a watchlist and if muda (627115852944375808) responds it will trigger admin function

### Action:
once triggered the message by muda will be deleted and replaced with a warning

### Example:

```
$w
```
will result in
```
**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**
<@!userID> this is a warning. you are in the wrong channel go to <#mudaHomeChannelID>
**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**
```


## bruh
Reacts with the Bruh emoji when user types /bruh

### Trigger:
if a user says /bruh it will trigger the function

### Action:
once triggered the bot will react with Bruh emoji

### Example:

```
/bruh
```
will result in
```
reacts with bruh
```


## when pinged
bot gives information on itself when its pinged

### Trigger:
taging the bot in message

### Action:
will return information on the bot

### Example:

```
@bot_name
```
will result in
```
returns flowaboat page
```

