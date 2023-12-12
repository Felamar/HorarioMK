import pandas as pd

class Materia:
    def __init__(self, kargs) -> None:
        self.NRC      = kargs['NRC'     ]
        self.CLAVE    = kargs['Clave'   ]
        self.NOMBRE   = kargs['Materia' ]
        self.SECC     = kargs['Secc'    ]
        self.DIAS     = [kargs['Días'   ]]
        self.HORAS    = kargs['Hora'    ]
        self.PROFESOR = kargs['Profesor'].lower()
        self.SALON    = kargs['Salón'   ]
        
    def add_hora(self, hora) -> None:
        self.HORAS.extend(hora)
        self.HORAS = set(self.HORAS)
        self.HORAS = sorted(list(self.HORAS))
    
    def add_dia(self, dia):
        self.DIAS.append(dia)