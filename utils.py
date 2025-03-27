import pandas as pd

def expandir_tareas(df):
    TURNOS_MAP = {'M': 'Mañana', 'T': 'Tarde', 'N': 'Noche'}
    expanded_rows = []

    for idx, row in df.iterrows():
        nombre_tarea = str(row["Tarea"]).strip()
        turnos = row.get("Turnos", "")

        if pd.isna(turnos) or turnos.strip() == "":
            new_row = row.copy()
            new_row["Turno_final"] = "Flexible"
            new_row["ID"] = nombre_tarea
            expanded_rows.append(new_row)
        else:
            turnos_split = [t.strip() for t in str(turnos).split(",")]
            carga_original = row["Carga (h) dia tarea"]
            carga_por_turno = carga_original / len(turnos_split)

            for t in turnos_split:
                new_row = row.copy()
                turno_label = TURNOS_MAP.get(t, f"Turno {t}")
                new_row["Turno_final"] = turno_label
                new_row["Carga (h) dia tarea"] = round(carga_por_turno, 2)
                new_row["ID"] = f"{nombre_tarea} - {turno_label}"
                expanded_rows.append(new_row)

    return pd.DataFrame(expanded_rows)



def task_sequencing(df):
    task_sequences = {}
    for area in df['Área'].unique():
        sub_df = df[df['Área'] == area]
        cadenas = {}

        for idx, row in sub_df.iterrows():
            cadena_str = row['Cadena']
            if pd.notnull(cadena_str):
                grupo, orden = cadena_str.split('-')
                orden = int(orden)
                if grupo not in cadenas:
                    cadenas[grupo] = []
                cadenas[grupo].append((orden, idx))

        # Agrupar secuencias ordenadas
        task_sequences[area] = []
        for grupo in cadenas.values():
            grupo_ordenado = [idx for orden, idx in sorted(grupo)]
            task_sequences[area].append(grupo_ordenado)
    return task_sequences