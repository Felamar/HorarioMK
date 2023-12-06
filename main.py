import pandas as pd
import tabula
from materia import Materia
from sys import argv
import os
import itertools

def get_df(path):
    if not os.path.exists('horarios.csv'):
        pdf = tabula.read_pdf(path, pages="all", lattice=True, multiple_tables=True)
        df  = pd.concat(pdf)
        df['Materia' ] = df['Materia' ].replace('\r', ' ', regex=True)
        df['Profesor'] = df['Profesor'].replace('\r', ' ', regex=True)
        df.to_csv("horarios.csv", index=False)
    else:
        df = pd.read_csv('horarios.csv')
    return df

def get_materias(df):
    Imparte = []
    NRCs = {}

    for _, row in df.iterrows():
        if row['NRC'] in NRCs:
            NRCs[row['NRC']].add_hora(row['Hora'])
            NRCs[row['NRC']].add_dia(row['Días'])
        else:
            NRCs[row['NRC']] = Materia(row.to_dict())

        if (row['NRC'], row['Profesor']) not in Imparte:
            Imparte.append((row['NRC'], row['Profesor']))

    return NRCs, Imparte

def get_horarios(NRCs, a_cursar):
    available = []
    for _, materia in NRCs.items():
        if materia.NOMBRE in a_cursar:
            available.append(materia)
        
    return available

def by_name(available_classes):
    horarios = {}
    for clas in available_classes:
        if clas.NOMBRE not in horarios:
            horarios[clas.NOMBRE] = [clas.NRC]
        else:
            horarios[clas.NOMBRE].append(clas.NRC)
    return horarios

def main():
    to_apply_to = []
    path = 'horarios.pdf'
    classes_quantity = int(argv[1])
    df = get_df(path)

    for i in range(classes_quantity):
        to_apply_to.append(input(f'Nombre de la materia {i+1}: '))

    NRCs, Imparte = get_materias(df)
    available_classes = get_horarios(NRCs, to_apply_to)

    # conflicts = {}
    # for course in available_classes:
    #     schedule = f'{course.DIAS}, {course.HORAS}'
    #     if schedule in conflicts:
    #         conflicts[schedule].append(course.NRC)
    #     else:
    #         conflicts[schedule] = [course.NRC]

    classes = by_name(available_classes)

    horarios = itertools.product(*classes.values())


    with open('output.txt', 'w') as file:
        for h in (horarios):
            conflicts = {}
            conflict = False
            for nrc in h:
                key = f'{NRCs[nrc].DIAS, NRCs[nrc].HORAS}'
                conflicts[key] = conflicts.get(key, 0) + 1
                if conflicts[key] > 1: conflict = True; break
            if not conflict: 
                file.write(f'{h}\n')

if __name__ == '__main__':
    main()
