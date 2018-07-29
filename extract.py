import sys
import csv

with open('data/waypoints/Austria.cup', 'r') as f:
    reader = csv.reader(f)
    writer = csv.writer(sys.stdout)
    for row in reader:
        if row[6] != '5':
            writer.writerow(row)
