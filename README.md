# getNapi

## What is it
It's simple python script to search and download subtitles in NapiProjekt.pl repository.
Improved version of napi2srt script (https://github.com/sternik/napi2srt).

### Main features
* Can recursively search through whole directory
* After first searching attempT md5 file checksum is stored to speed-up next attempt
* Default language is set to Polish. If Polish subs are unavailable, then it will try check for English one
* Automatically convert to .srt format
* If subtitles in .txt format is found, then will convert it to .srt



## Dependenties
You need to have installed p7zip (http://p7zip.sourceforge.net)

If you are Debian's user just do `apt-get install p7zip-full`

## Usage
* `getNapi.py /path/to/directory/` - will search for subtitles for all movie files inside specified dir

* `getNapi.py /path/to/file` - will search for subtitle for this particular movie file
