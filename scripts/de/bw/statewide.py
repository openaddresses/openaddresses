"""
Filter out addresses with cadastral psuedonumbers (col 3 == 'C'). These are ids/pseudo-numbers and not house numbers.

https://www.lgl-bw.de/Produkte/Liegenschaftskataster/Hauskoordinaten/
Das Datenelement 3 kennzeichnet die Qualität der Gebäudekoordinate wie folgt:
A = Amtliche Hausnummer, deren Koordinate sicher innerhalb der erfassten Gebäudegeometrie liegt.
B = Amtliche Hausnummer, deren Koordinate sicher innerhalb der Flurstücksfläche liegt, ein Gebäude ist nicht sicher in der Örtlichkeit vorhanden.
C = Katasterinterne Hausnummer (Pseudonummer), deren Koordinate sicher innerhalb der erfassten Gebäudegeometrie liegt.
"""
import csv
import logging


logging.basicConfig(level=logging.INFO)


def main():
    with open('adressen_bw.txt', 'r') as input_csv, open('adressen_bw-filtered.txt', 'w') as output_csv:
        reader = csv.reader(input_csv, delimiter=';')
        writer = csv.writer(output_csv, delimiter=';')
        for line in reader:
            if line[2] != 'C':  # Filter out cadastral psuedonumbers
                writer.writerow(line)

if __name__ == "__main__":
    logging.info("Processing Baden-Württemberg statewide addresses to remove cadastral psuedonumbers")
    main()
    logging.info("Finished processing Baden-Württemberg statewide addresses")