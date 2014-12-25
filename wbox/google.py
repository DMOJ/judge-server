import urllib2

file = urllib2.urlopen('http://www.google.com/')
try:
    print file.read()
finally:
    file.close()
