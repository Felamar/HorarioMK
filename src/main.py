import pandas as pd
import tabula
from materia import Materia
from sys import argv
import os
import itertools

def get_df(DF_PATH_OUTPUT: str) -> pd.DataFrame:
    PDF_PATH       = input('| PDF Path'.ljust(20) + ' | ')
    print(' '+'-'*20)
    if not os.path.exists('data'): os.mkdir('data')
    if not os.path.exists(DF_PATH_OUTPUT):
        pdf_table = tabula.read_pdf(
            PDF_PATH, 
            pages="all", 
            lattice=True, 
            multiple_tables=True
        )
        df  = pd.concat(pdf_table)
        df['Materia' ] = df['Materia' ].replace('\r', ' ', regex=True)
        df['Profesor'] = df['Profesor'].replace('\r', ' ', regex=True)
        df.to_csv(DF_PATH_OUTPUT, index=False)
    else:
        df = pd.read_csv(DF_PATH_OUTPUT)
    return df

def range_to_intervals(hours: tuple) -> list[str]:
    hour_it     = hours[0]
    hour_ranges = []
    while True:
        start    = str(hour_it   ).zfill(4)
        finish   = str(hour_it+59).zfill(4)
        hour_it += 100
        hour_ranges.append(f'{start}-{finish}')
        if hour_it-41 == hours[1]: break
    return hour_ranges

def get_NRCs(df: pd.DataFrame, classes_to_take: list[str]) -> tuple[dict[str, Materia], list[tuple[str, str]]]:
    NRCs    = {}
    Imparte = []

    for _, row in df.iterrows():
        if row['Materia'] not in classes_to_take: continue
        start, finish = row['Hora'].split('-')
        hours = range_to_intervals((int(start), int(finish)))
        if row['NRC'] in NRCs:
            NRCs[row['NRC']].add_hora(hours)
            NRCs[row['NRC']].add_dia(row['Días'])
        else:
            row_dict         = row.to_dict()
            row_dict['Hora'] = hours
            NRCs[row['NRC']] = Materia(row_dict)
        if (row['NRC'], row['Profesor']) not in Imparte:
            Imparte.append((row['NRC'], row['Profesor']))

    return NRCs, Imparte

def group_by_name(NRCs : dict[str, Materia]) -> dict[str, list[str]]:
    classes_by_name = {}
    for _, class_ in NRCs.items():
        if class_.NOMBRE not in classes_by_name:
            classes_by_name[class_.NOMBRE] = [class_.NRC]
        else:
            classes_by_name[class_.NOMBRE].append(class_.NRC)
    return classes_by_name

def get_schedules(NRCs: dict[str, Materia], classes_by_name: dict[str, list[str]], prof_blacklist: list[str], hour_ranges: list[str]) -> list[tuple[str]]:
    OUTPUT_PATH        = 'schedules/combinations.txt'
    if not os.path.exists('schedules'): os.mkdir('schedules')
    schedules          = []
    possible_schedules = itertools.product(*classes_by_name.values())

    with open(OUTPUT_PATH, 'w') as file:
        for schedule in possible_schedules:
            time_conflicts  = {}
            conflict_exists = False
            for nrc in schedule:
                # Check if there is a professor conflict
                if NRCs[nrc].PROFESOR in prof_blacklist: conflict_exists = True; break
                # Check if there is a hour conflict
                all_hours_in_range = all(hour_range in hour_ranges for hour_range in NRCs[nrc].HORAS)
                if not all_hours_in_range: conflict_exists = True; break
                # Check if there is a schedule conflict
                time_slot = f'{NRCs[nrc].DIAS, NRCs[nrc].HORAS}'
                time_conflicts[time_slot] = time_conflicts.get(time_slot, 0) + 1
                if time_conflicts[time_slot] > 1: conflict_exists = True; break
            if not conflict_exists: 
                file.write(f'{schedule}\n')
                schedules.append(schedule)
    return schedules

def custom_agg(x: pd.Series) -> str:
    st = set(x.dropna())
    st_str = ', '.join(str(e) for e in st)
    return st_str if st_str else ''

def get_params() -> tuple[list[str], list[str], tuple[int]]:
    classes_to_take = []
    print(' '+'-'*20)
    classes_quantity = int(input('| No. Clases'.ljust(20) + ' | '))
    print(' '+'-'*20)
    for i in range(classes_quantity):
        classes_to_take.append(input(f'| Clase {i+1}'.ljust(20) + ' | '))
        print(' '+'-'*20)
        # classes_to_take.append(input(f'Nombre de la materia {i+1}: '.ljust(25)))
    prof_blacklist = input('| Profes a Evitar'.ljust(20) + ' | ').lower().split(', ')
    print(' '+'-'*20)
    start_hour = int(input('| Desde: '.ljust(20) + ' | '))
    print(' '+'-'*20)
    end_hour   = int(input('| Hasta: '.ljust(20) + ' | '))
    print(' '+'-'*20)
    hour_range = (start_hour*100, end_hour*100-41)
    return classes_to_take, prof_blacklist, hour_range

def save_schedules(SCHEDULES_PATH: str, schedules: list[tuple[str]], NRCs: dict[str, Materia]) -> None:
    if os.path.exists(SCHEDULES_PATH):
        for file in os.listdir(SCHEDULES_PATH):
            os.remove(f'{SCHEDULES_PATH}/{file}') if file.endswith('.csv') else None
    else:
        os.mkdir(SCHEDULES_PATH)

    for i, schedule in enumerate(schedules):
        df = pd.DataFrame(columns=['HORAS', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'])
        for nrc in schedule:
            df = pd.concat([df, pd.DataFrame({
                'HORAS'    : [NRCs[nrc].HORAS[0]], 
                'Lunes'    : nrc if 'L' in NRCs[nrc].DIAS and 'M' in NRCs[nrc].DIAS else None,
                'Martes'   : nrc if 'A' in NRCs[nrc].DIAS else None,
                'Miércoles': nrc if 'M' in NRCs[nrc].DIAS else None,
                'Jueves'   : nrc if 'J' in NRCs[nrc].DIAS else None,
                'Viernes'  : nrc if 'V' in NRCs[nrc].DIAS else None
            })])
            df = pd.concat([df, pd.DataFrame({
                'HORAS'    : [NRCs[nrc].HORAS[1]], 
                'Lunes'    : nrc if 'L' in NRCs[nrc].DIAS and 'A' in NRCs[nrc].DIAS else None,
                'Martes'   : nrc if 'A' in NRCs[nrc].DIAS else None,
                'Miércoles': nrc if 'M' in NRCs[nrc].DIAS else None,
                'Jueves'   : nrc if 'J' in NRCs[nrc].DIAS else None,
                'Viernes'  : nrc if 'V' in NRCs[nrc].DIAS else None
            })])

        grouped_df  = df.groupby(['HORAS']).agg(custom_agg)
        empty_count = grouped_df.map(lambda x: x == '' or x == ' ').sum().sum()
        grouped_df.to_csv(f'{SCHEDULES_PATH}/{empty_count}_schedule_{i+1}.csv')

def main():
    SCHEDULES_PATH = 'schedules'
    DF_PATH_OUTPUT = 'data/classes.csv'

    classes_to_take, prof_blacklist, hour_range = get_params()
    df              = get_df(DF_PATH_OUTPUT)
    NRCs, Imparte   = get_NRCs(df, classes_to_take)
    classes_by_name = group_by_name(NRCs)
    hour_intervals  = range_to_intervals(hour_range)
    schedules       = get_schedules(NRCs, classes_by_name, prof_blacklist, hour_intervals)
    save_schedules(SCHEDULES_PATH, schedules, NRCs)
    
if __name__ == '__main__':
    main()
