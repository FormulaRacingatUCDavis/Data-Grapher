import csv

datafile = open('016.csv', 'r')
telem = open('telemetry.txt', 'w')
pei = open('pei.txt', 'w') 
bms = open('bms.txt', 'w') 

reader = csv.reader(datafile)
for row in reader:
    if (len(row) < 10):
        print(f'Warning: Unknown row "{row}"')
        continue
    
    if (row[0] == '400'):
        telem.write(' '.join(row))
        telem.write('\n')
    if (row[0] == '387'):
        pei.write(' '.join(row))
        pei.write('\n')
    if (row[0] == '380'):
        bms.write(' '.join(row))
        bms.write('\n')

datafile.close()
telem.close()
pei.close()
bms.close()

