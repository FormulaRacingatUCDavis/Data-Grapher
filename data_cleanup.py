import os

#for line in open('test.txt', 'r') { 
#	lines = [i for i in line.split()]
#	if (int(lines[0]) == 400) {
#		file2.write(line)/

file1 = open('data.txt', 'r')
file2 = open('telemetry.txt', 'w')
file3 = open('pei.txt', 'w') 
file4 = open('bms.txt', 'w') 

lines = file1.readlines()
for line in lines:
    parts = line.split()
    if (parts[0] == '400'):
        file2.write(line)
    if (parts[0] == '387'):
        file3.write(line)
    if (parts[0] == '380'):
        file4.write(line) 

file1.close()
file2.close()
file3.close()
file4.close()

