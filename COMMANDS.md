# Commands
### Table Of Contents
- [o!hello](#ohello)
- [o!od](#ood)
- [o!osu](#oosu)
- [o!flowaboat](#oflowaboat)
- [o!bpm](#obpm)
- [o!top](#otop)
- [o!ign-set](#oign-set)
- [o!cs](#ocs)
- [o!hp](#ohp)
- [o!ar](#oar)
- [o!help](#ohelp)
---
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


## o!flowaboat
Show information about this bot.

**Required variables**: `0`

**Usage**: `o!flowaboat `

#### Synonyms:

`o!info`

### Example:

```
o!flowaboat
```
Tells you about flowaboat.


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


## o!top
Show a specific top play.

**Required variables**: `0`

**Usage**: `o!top [username]`

#### Synonyms:

`o!top\d+`

### Examples:

```
o!top
```
Returns your #1 top play.



```
o!top5 vaxei
```
Returns Vaxei's #5 top play.


## o!ign-set
Sets your username for platform.

**Required variables**: `2`

**Usage**: `o!ign-set [osu|steam] <username>`

#### Synonyms:

`o!set-ign`, `o!set`

### Examples:

```
o!set-ign osu nathan on osu
```
Sets your osu! username to nathan on osu.



```
o!set steam flyingpigoftheapocalypse
```
Sets your steam username to flyingpigoftheapocalypse.


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

