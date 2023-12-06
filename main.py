import pandas as pd
import tabula
from materia import Materia
from sys import argv
import os
import itertools

KeyDAYS = {
    'L' : 'Lunes',
    'A' : 'Martes',
    'M' : 'Miércoles',
    'J' : 'Jueves',
    'V' : 'Viernes',
}

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

def NRC_dict(df):
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

def get_materias(NRCs, a_cursar):
    available = []
    for _, materia in NRCs.items():
        if materia.NOMBRE in a_cursar:
            available.append(materia)
    return available

def materias_by_name(available_classes):
    horarios = {}
    for clas in available_classes:
        if clas.NOMBRE not in horarios:
            horarios[clas.NOMBRE] = [clas.NRC]
        else:
            horarios[clas.NOMBRE].append(clas.NRC)
    return horarios

def get_horarios(NRCs, classes, prof_restr, hour_restr):
    horarios = itertools.product(*classes.values())
    valid_horarios = []
    with open('output.txt', 'w') as file:
        for horario in horarios:
            conflicts = {}
            isThereConflict = False
            for nrc in horario:
                # Check if there is a professor conflict
                if NRCs[nrc].PROFESOR in prof_restr: isThereConflict = True; break
                # Check if there is a hour conflict
                if NRCs[nrc].HORAS[-1] not in hour_restr: isThereConflict = True; break
                # Check if there is a schedule conflict
                key = f'{NRCs[nrc].DIAS, NRCs[nrc].HORAS}'
                conflicts[key] = conflicts.get(key, 0) + 1
                if conflicts[key] > 1: isThereConflict = True; break

            if not isThereConflict: 
                file.write(f'{horario}\n')
                valid_horarios.append(horario)
                
    return valid_horarios
def custom_agg(x):
    st = set(x.dropna())
    st_str = ', '.join(str(e) for e in st)
    return st_str if st_str else ''

def main():
    to_apply_to = []
    path = 'horarios.pdf'
    classes_quantity = int(argv[1])
    df = get_df(path)

    for i in range(classes_quantity):
        to_apply_to.append(input(f'Nombre de la materia {i+1}:'))

    NRCs, Imparte = NRC_dict(df)
    available_classes = get_materias(NRCs, to_apply_to)

    classes = materias_by_name(available_classes)
    prof_restr = input('Profesores a evitar: ').lower().split(', ')
    hours = (int(input('Desde:'.ljust(10)))*100, int(input('Hasta:'.ljust(10)))*100-41)
    hour_restr = []
    hour = hours[0] 

    while True:
        start  = str(hour).zfill(4)
        finish = str(hour + 159).zfill(4)
        hour_restr.append(f'{start}-{finish}')
        hour  += 200
        if hour-41 == hours[1]: break

    horarios_t = get_horarios(NRCs, classes, prof_restr, hour_restr)

    if os.path.exists('horarios'):
        for file in os.listdir('horarios'):
            os.remove(f'horarios/{file}')
    else:
        os.mkdir('horarios')

    for i, horario in enumerate(horarios_t):
        df = pd.DataFrame(columns=['HORAS', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'])
        for nrc in horario:
            df = pd.concat([df, pd.DataFrame({
                'HORAS'    : NRCs[nrc].HORAS[1:], 
                'Lunes'    : None,
                'Martes'   : nrc if 'A' in NRCs[nrc].DIAS else None,
                'Miércoles': nrc if 'M' in NRCs[nrc].DIAS else None,
                'Jueves'   : nrc if 'J' in NRCs[nrc].DIAS else None,
                'Viernes'  : nrc if 'V' in NRCs[nrc].DIAS else None
            })])
            df = pd.concat([df, pd.DataFrame({
                'HORAS'    : [NRCs[nrc].HORAS[0]], 
                'Lunes'    : nrc if 'L' in NRCs[nrc].DIAS else None,
                'Martes'   : None,
                'Miércoles': None,
                'Jueves'   : None,
                'Viernes'  : None
            })])
        grouped_df = df.groupby(['HORAS']).agg(custom_agg)
        grouped_df.to_csv(f'horarios/horario{i+1}.csv')
        
if __name__ == '__main__':
    main()
