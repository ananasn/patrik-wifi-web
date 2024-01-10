import netifaces as ni
ip = ni.ifaddresses('wlp0s20f3')[ni.AF_INET][0]['addr']
print(ip)