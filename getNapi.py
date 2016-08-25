#!/usr/bin/env python

import sys, os, re
import urllib
import urllib2
import hashlib
import subprocess

### CONFIGURATION ###

# Path to p7zip program (http://p7zip.sourceforge.net/)
p7zip = '/usr/bin/7za'

# Movies extensions
movie_ext = ['.avi', '.mkv', '.mp4', '.wmv']


class NapiProject:
	def __init__(self, file):
		
		md5_str = self.getcache(file)
		if md5_str and len(md5_str) == 32:
			self.d = md5_str
		else:
			d = hashlib.md5()
			d.update(open(file).read(10485760))		
			self.d = d.hexdigest()
			md5_file = open(os.path.splitext(file)[0] + '.md5', 'w')
			md5_file.write(self.d)
			md5_file.close()
		
	def f(self, z):
		idx = [ 0xe, 0x3,  0x6, 0x8, 0x2 ]
		mul = [   2,   2,    5,   4,   3 ]
		add = [   0, 0xd, 0x10, 0xb, 0x5 ]

		b = []
		for i in xrange(len(idx)):
			a = add[i]
			m = mul[i]
			i = idx[i]

			t = a + int(z[i], 16)
			v = int(z[t:t+2], 16)
			b.append( ("%x" % (v*m))[-1] )

		return ''.join(b)

	def getcache(self, file):
		md5_file = os.path.splitext(file)[0] + '.md5'
		
		if os.path.isfile(md5_file) and os.path.getsize(md5_file) > 0:
			return open(md5_file).read()
		else:
			return 0

	def getnapi(self, file, lang):
		dir = os.path.dirname(file)
		str = 'http://napiprojekt.pl/unit_napisy/dl.php?l=' + lang.upper() + '&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s' % (self.d, self.f(self.d), os.name)

		open('%s/napisy.7z' % (dir), 'w').write(urllib.urlopen(str).read())

		if (not os.system('%s x -y -so -piBlm8NTigvru0Jr0 "%s/napisy.7z" 2>/dev/null > "%s"' % (p7zip, dir, file[:-3] + 'txt'))):
			os.remove('%s/napisy.7z' % (dir))
			return 1
		else:
			os.remove('%s/napisy.7z' % (dir))
			os.remove('%s' % (file[:-3] + 'txt'))
			return 0


class SubConv:
	def fromMdvd(self, lines, fps):
		"""
		Read micro-dvd subtitles.
		input: contents of a file as list
		returns: list of subtitles in form: [[time_start in secs, time_end in secs, line1, ...],....]
		"""
		re1 = re.compile('^\{(\d+)\}\{(\d*)\}\s*(.*)')
		subtitles = []
		while len(lines)>0:
		    m = re1.match(lines.pop(0), 0)
		    if m:
		        subt = [int(m.group(1)) / float(fps)]
		        if m.group(2):
		            subt.append(int(m.group(2)) / float(fps))
		        else:
		            subt.append(int(m.group(1)) / float(fps) + 3)
		        subt.extend(m.group(3).strip().split('|'))
		        subtitles.append(subt)
		return subtitles


	def fromMpl2(self, lines, fps):
		re_line = re.compile('\[(?P<start>\d+)\]\[(?P<stop>\d+)\](?P<line>.*)', re.S)
		subtitles = []

		for line in lines:
			group = re_line.match(line.strip())
			if group is None:
				continue
			else:
				group = group.groupdict()
		
			start = int(float(group['start'])*0.1*float(fps)) or 1
			stop = int(float(group['stop'])*0.1*float(fps))
			rest = group['line']
			subtitles.append('{%d}{%d}%s' % (start, stop, rest))

		return subtitles


	def toSrt(self, lines):
		"""
		Converts list of subtitles (internal format) to srt format
		"""
		outl = []
		count = 1
		for l in lines:
		    secs1 = l[0]
		    h1 = int(secs1/3600)
		    m1 = int(int(secs1%3600)/60)
		    s1 = int(secs1%60)
		    f1 = (secs1 - int(secs1))*1000
		    secs2 = l[1]
		    h2 = int(secs2/3600)
		    m2 = int(int(secs2%3600)/60)
		    s2 = int(secs2%60)
		    f2 = (secs2 - int(secs2))*1000
		    outl.append('%d\n%.2d:%.2d:%.2d,%.3d --> %.2d:%.2d:%.2d,%.3d\n%s\n\n' % (count,h1,m1,s1,f1,h2,m2,s2,f2,'\n'.join(l[2:])))
		    count = count + 1

		return outl


	def convert(self, file):
		# if os.path.splitext(file)[1] == '.avi':
		# fps = subprocess.Popen('file "%s"' % file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
	    	# fps = re.search(", ([0-9]+\.[0-9]+) fps", fps).group(1)
  		# else:
		fps = '23.976'
		txt = os.path.splitext(file)[0] + '.txt'
		isRecognized = None

		try:
			f = open(txt, 'r')
			lines = f.readlines()

			for line in lines:
				if re.match('^(\d+):(\d+):(\d+),\d+\s*-->.*', line):
					os.rename(txt, os.path.splitext(file)[0] + '.srt')
					isRecognized = True
					break
				elif re.match('^\{(\d+)\}\{(\d*)\}\s*(.*)', line):
					isRecognized = True
					srt = self.toSrt(self.fromMdvd(lines, fps))
					dst = open(os.path.splitext(file)[0] + '.srt', 'w')
					dst.writelines(srt)
					dst.close()
					os.remove(txt)
					break
				elif re.match(r'\A\[', line):
					isRecognized = True
					srt = self.toSrt(self.fromMdvd(self.fromMpl2(lines, fps), fps))
					dst = open(os.path.splitext(file)[0] + '.srt', 'w')
					dst.writelines(srt)
					dst.close()
					os.remove(txt)
					break

			f.close
			return 1 if isRecognized else 0
		except IOError:
			print('! IO ERROR ! ')
			return 0


def deleteSRT(file):
	srt = os.path.splitext(file)[0] + '.srt'
	if os.path.isfile(srt):
		os.remove(srt)

	return 1


def processing(files):
	for file in files:
		napiProject = NapiProject(file)
		subConv = SubConv()

		print '\nSearching subtitles for:\n%s\n' % os.path.basename(file)

		# if txt exist only converting
		if os.path.isfile(os.path.splitext(file)[0] + '.txt') and os.path.getsize(os.path.splitext(file)[0] + '.txt') > 0:
			print 'TXT file already exists:               YES'
			print 'Converting to SRT format:             ',
			print 'DONE' if subConv.convert(file) else 'FAILED (UNKNOWN FORMAT)\n\n'
		# downloading and converting subtitles
		else:
			print 'TXT file already exists:               NO\n'
			print 'Checking NapiProjekt database ...\n'
			print 'Downloaded subtitle language          ',
			if (napiProject.getnapi(file, 'PL')):
				print 'POLISH'
				deleteSRT(file)
				print 'Converting to SRT format:             ',
				print 'DONE' if subConv.convert(file) else 'FAILED (UNKNOWN FORMAT)'
			elif (napiProject.getnapi(file, 'ENG')):
				print 'ENGLISH'
				deleteSRT(file)
                                print 'Converting to SRT format:             ',
				print 'DONE' if subConv.convert(file) else 'FAILED (UNKNOWN FORMAT)'
			else:
				print 'NOT FOUND'

		print '\n--------------------------------\n'
	return 1


def main():
    # checking if p7zip exist in path configured in p7zip
    popen = subprocess.Popen(p7zip, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if (not popen.stdout.read()):
        print 'You must install p7zip to use this program.'
        return 0

    if len(sys.argv) == 2:
        fd = sys.argv[1]
    else:
        print 'usage: %s movie_file or path_with_movies' % os.path.basename(sys.argv[0])
        return 0

    # checking if file or path exist
    if not os.path.isdir(fd) and not os.path.isfile(fd):
        print 'File or path doesn\'t exist'
        return 0

    # if file
    elif not os.path.isdir(fd) and os.path.isfile(fd):
        filelist = [fd]
        processing(filelist)

    # if path
    elif os.path.isdir(fd):
        filelist = []
        for root, subFolders, files in os.walk(fd):
            for file in files:
                # adding movie to file list if exist in movie_ext
                if os.path.splitext(file)[1] in movie_ext:
                	filelist.append(os.path.join(root, file))

        processing(filelist)

	return 1

# START:
if __name__ == '__main__':
    sys.exit(main())
