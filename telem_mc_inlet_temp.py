import matplotlib.pyplot as plt 

x = [] 
y = [] 
for line in open('telemetry.txt', 'r'): 
	lines = [i for i in line.split()] 
	y.append(int(lines[1])) 
	x.append(int(lines[9]) / 60000) 
	
plt.title("Data Analyzer - Telem Node") 
plt.ylabel('MC Inlet Temperature (C)') 
plt.xlabel('Timestamp (minutes)') 
plt.yticks(y) 
plt.plot(x, y, marker = 'o', c = 'g') 

plt.show()

