import os
import tabula
import itertools
import pandas as pd
from random import randint
from materia import Materia
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

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
        if class_.MATERIA not in classes_by_name:
            classes_by_name[class_.MATERIA] = [class_.NRC]
        else:
            classes_by_name[class_.MATERIA].append(class_.NRC)
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

def format_xlsx(PATH: str, color_map: dict[str, str]) -> None:
    book = load_workbook(f'{PATH}/schedules.xlsx')
    sheet = book.active

    for column in sheet.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[column[0].column_letter].width = adjusted_width

    for nrc, color in color_map.items():
        pattern = PatternFill(start_color=color, end_color=color, fill_type='solid')
        for row in sheet.iter_rows(min_row=2, max_col=sheet.max_column, max_row=sheet.max_row):
            for cell in row:
                if cell.value == str(nrc):
                    cell.fill = pattern

    book.save(f'{PATH}/schedules.xlsx')

def save_schedules(SCHEDULES_PATH: str, schedules: list[tuple[str]], NRCs: dict[str, Materia]) -> None:
    if os.path.exists(SCHEDULES_PATH):
        for file in os.listdir(SCHEDULES_PATH):
            os.remove(f'{SCHEDULES_PATH}/{file}') if file.endswith('.csv') else None
    else:
        os.mkdir(SCHEDULES_PATH)

    color_map  = {}
    colors = [
        'ffa6cee3',
        'fffdbf6f',
        'ffb2df8a',
        'fffb9a99',
        'ffd0d1e6',
        'ffd8b365',
        'fff4cae4',
        'ffbababa',
        'ffffff99',
        'ff9ecae1',
        'ffb3de69',
        'ffffad80',
        'ff80cdc1',
        'ffffb3b3',
        'ffb3daff',
        'ffffe699',
        'ffc2f0c2',
        'ffcc6666',
        'ff666699',
        'ffe0e0f2'
    ]
    i = 0
    
    with pd.ExcelWriter(f'{SCHEDULES_PATH}/schedules.xlsx') as writer:
        row_count = 0
        for schedule in schedules:
            shcedule_df     = pd.DataFrame(columns=['HORAS', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'])
            classes_df_keys = ['NRC', 'MATERIA', 'PROFESOR']
            classes_df      = pd.DataFrame(columns=classes_df_keys)
            for nrc in schedule:

                shcedule_df = pd.concat([shcedule_df, pd.DataFrame({
                    'HORAS'    : [NRCs[nrc].HORAS[0]], 
                    'Lunes'    : nrc if 'L' in NRCs[nrc].DIAS and 'M' in NRCs[nrc].DIAS else None,
                    'Martes'   : nrc if 'A' in NRCs[nrc].DIAS else None,
                    'Miércoles': nrc if 'M' in NRCs[nrc].DIAS else None,
                    'Jueves'   : nrc if 'J' in NRCs[nrc].DIAS else None,
                    'Viernes'  : nrc if 'V' in NRCs[nrc].DIAS else None
                })])
                shcedule_df = pd.concat([shcedule_df, pd.DataFrame({
                    'HORAS'    : [NRCs[nrc].HORAS[1]], 
                    'Lunes'    : nrc if 'L' in NRCs[nrc].DIAS and 'A' in NRCs[nrc].DIAS else None,
                    'Martes'   : nrc if 'A' in NRCs[nrc].DIAS else None,
                    'Miércoles': nrc if 'M' in NRCs[nrc].DIAS else None,
                    'Jueves'   : nrc if 'J' in NRCs[nrc].DIAS else None,
                    'Viernes'  : nrc if 'V' in NRCs[nrc].DIAS else None
                })])

                class_temp = pd.DataFrame({key: NRCs[nrc].__dict__[key] for key in classes_df_keys}, index=['NRC'])
                classes_df = pd.concat([classes_df, class_temp])

                if nrc not in color_map: color_map[nrc] = colors[i%len(colors)]; i+=1

            grouped_df  = shcedule_df.groupby(['HORAS']).agg(custom_agg)
            grouped_df = grouped_df.astype(str)
            grouped_df.to_excel(
                writer, 
                sheet_name='Sheet1', 
                startrow=row_count
            )
            classes_df = classes_df.astype(str)
            classes_df['PROFESOR'] = classes_df['PROFESOR'].str.title()
            classes_df.to_excel(
                writer, 
                sheet_name='Sheet1', 
                startrow=row_count, 
                startcol=len(grouped_df.columns) + 2, 
                index=False
            )
            row_count += len(grouped_df) + 4

    format_xlsx(SCHEDULES_PATH, color_map)

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
