import pandas as pd
KeyDAYS = {
    'L' : 'Lunes',
    'A' : 'Martes',
    'M' : 'Miércoles',
    'J' : 'Jueves',
    'V' : 'Viernes',
}

class Materia:
    def __init__(self, kargs) -> None:
        self.NRC      = kargs['NRC'     ]
        self.CLAVE    = kargs['Clave'   ]
        self.NOMBRE   = kargs['Materia']
        self.SECC     = kargs['Secc'    ]
        self.DIAS     = [KeyDAYS[kargs['Días']  ]]
        self.HORAS    = [kargs['Hora']  ]
        self.PROFESOR = kargs['Profesor']
        self.SALON    = kargs['Salón'   ]
        
    def show(self) -> None:
        df = pd.DataFrame([vars(self)], index=['Values'])
        print(df)

    def add_hora(self, hora) -> None:
        self.HORAS.append(hora)
    
    def add_dia(self, dia):
        self.DIAS.append(KeyDAYS[dia])