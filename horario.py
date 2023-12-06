class Horario:
    def __init__(self) -> None:
        self.materias = []
    
    def add_materia(self, materia):
        self.materias.append(materia)
    
    def get_names(self):
        return [materia.NOMBRE for materia in self.materias]