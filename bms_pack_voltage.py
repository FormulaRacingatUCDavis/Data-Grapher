import matplotlib.pyplot as plt 

from can_util import pack_16bit

x = [] 
y = [] 
for line in open('bms.txt', 'r'): 
	lines = [i for i in line.split()] 
	y.append(pack_16bit(int(lines[4]), int(lines[5])))
	x.append(int(lines[9]) / 60000) 
	
plt.title("Data Analyzer - BMS Main") 
plt.ylabel('Pack Voltage') 
plt.xlabel('Timestamp (minutes)') 
plt.yticks(y) 
plt.plot(x, y, marker = 'o', c = 'g') 

plt.show()

