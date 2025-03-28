from ortools.linear_solver import pywraplp
import math

def algoritmo(tasks, areas, valid_types, worker_types, H, task_turnos, ids, task_sequences, divisible, alpha=1.0, beta=0.1, gamma=0.5):
    final_result = {}
    unique_areas = list(set(areas))

    for area in unique_areas:
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            print("No se pudo crear el solver.")
            continue

        indices = [i for i, a in enumerate(areas) if a == area]
        area_tasks = [tasks[i] for i in indices]
        area_valid_types = [valid_types[i] for i in indices]
        area_task_turnos = [task_turnos[i] for i in indices]
        area_divisible = [divisible[i] for i in indices]

        n = len(area_tasks)
        K = len(worker_types)

        M = []
        for k in range(K):
            carga_k = sum(area_tasks[j] for j in range(n) if k in area_valid_types[j])
            num_turnos = len(set([t for idx, t in enumerate(area_task_turnos) if k in area_valid_types[idx]]))
            M.append(max(3, math.ceil(carga_k / H), num_turnos))  # al menos 3 por si hay 3 turnos


        w, x, z = [], [], []

        for k in range(K):
            w_k, x_k, z_k = [], [], []
            for i in range(M[k]):
                w_var = solver.IntVar(0, 1, f'w_{k}_{i}')
                w_k.append(w_var)
                x_i, z_i = [], []
                for j in range(n):
                    if k in area_valid_types[j]:
                        x_var = solver.NumVar(0, solver.infinity(), f'x_{k}_{i}_{j}')
                        z_var = solver.IntVar(0, 1, f'z_{k}_{i}_{j}')
                        solver.Add(x_var <= H * z_var)
                        solver.Add(x_var >= 0.001 * z_var)
                        solver.Add(x_var <= H * w_var)
                        x_i.append(x_var)
                        z_i.append(z_var)
                    else:
                        x_i.append(None)
                        z_i.append(None)
                x_k.append(x_i)
                z_k.append(z_i)
            w.append(w_k)
            x.append(x_k)
            z.append(z_k)

        # Cobertura total de la carga de cada tarea
        for j in range(n):
            sum_x = []
            z_list = []
            for k in range(K):
                for i in range(M[k]):
                    if x[k][i][j] is not None:
                        sum_x.append(x[k][i][j])
                        z_list.append(z[k][i][j])
            solver.Add(solver.Sum(sum_x) == area_tasks[j])

            # Restricción adicional: tarea no divisible
            if area_divisible[j] == "no":
                solver.Add(solver.Sum(z_list) <= 1)
                # Warning opcional
                if area_tasks[j] > H:
                    print(f"⚠️ Atención: La tarea {ids[indices[j]]} no es divisible y su carga ({area_tasks[j]}) excede H ({H}).")

        # Capacidad trabajador
        for k in range(K):
            for i in range(M[k]):
                sum_x = []
                for j in range(n):
                    if x[k][i][j] is not None:
                        sum_x.append(x[k][i][j])
                solver.Add(solver.Sum(sum_x) <= H * w[k][i])

        # ✅ Restricción: un trabajador solo puede estar en un único turno (Mañana, Tarde, Noche, Flexible)
        TURNOS_VALIDOS = ["Mañana", "Tarde", "Noche", "Flexible"]

        # Estandariza los turnos (evita None)
        area_task_turnos = [
            turno if turno is not None else "Flexible"
            for turno in area_task_turnos
        ]

        # Crear variables de turno activo por trabajador
        turno_vars = {}  # clave: (k, i, turno) → variable binaria

        for k in range(K):
            for i in range(M[k]):
                turno_flags = []
                for turno in TURNOS_VALIDOS:
                    var = solver.IntVar(0, 1, f"turno_activo_{k}_{i}_{turno}")
                    turno_vars[(k, i, turno)] = var
                    turno_flags.append(var)

                # ✅ Solo puede tener un turno activo
                solver.Add(solver.Sum(turno_flags) <= 1)

        # Forzar que las tareas asignadas coincidan con el turno activo del trabajador
        for k in range(K):
            for i in range(M[k]):
                for j in range(n):
                    if x[k][i][j] is not None:
                        turno_j = area_task_turnos[j]
                        turno_var = turno_vars[(k, i, turno_j)]
                        solver.Add(z[k][i][j] <= turno_var)


        # SOFT SECUENCIAS POR TURNO
        penalizaciones_slacks = []
        for turno_actual in ["Mañana", "Tarde", "Noche", "Flexible"]:
            ids_turno = [ids[indices[j]] for j in range(n) if task_turnos[indices[j]] == turno_actual]

            for idx_seq, seq in enumerate(task_sequences.get(area, [])):
                seq_ids = [id_ for id_ in ids_turno if id_ in seq]

                if len(seq_ids) >= 2:
                    for k in range(K):
                        for i in range(M[k]):
                            z_seq = []
                            for id_local in seq_ids:
                                if id_local in ids:
                                    j_idx = [idx for idx, j in enumerate(indices) if ids[indices[idx]] == id_local]
                                    if j_idx:
                                        j = j_idx[0]
                                        z_seq.append(z[k][i][j])
                            if len(z_seq) >= 2:
                                for idx in range(len(z_seq) - 1):
                                    slack = solver.NumVar(0, solver.infinity(), f'slack_{turno_actual}_{k}_{i}_{idx}')
                                    solver.Add(z_seq[idx] >= z_seq[idx + 1] - slack)
                                    penalizaciones_slacks.append(slack)

        # OBJETIVO
        total_personas_en_tareas = []
        for j in range(n):
            n_personas = solver.Sum(z[k][i][j] for k in range(K) for i in range(M[k]) if z[k][i][j] is not None)
            total_personas_en_tareas.append(n_personas)

        total_workers = solver.Sum(w[k][i] for k in range(K) for i in range(M[k]))
        total_task_people = solver.Sum(total_personas_en_tareas)
        total_penalizaciones = solver.Sum(penalizaciones_slacks)

        solver.Minimize(alpha * total_workers + beta * total_task_people + gamma * total_penalizaciones)

        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            result_dict = {}
            type_counters = {k: 1 for k in range(K)}
            for k in range(K):
                for i in range(M[k]):
                    if w[k][i].solution_value() > 0.5:
                        worker_label = f"{worker_types[k]} {type_counters[k]}"
                        type_counters[k] += 1
                        tareas_asignadas = []
                        for j in range(n):
                            if x[k][i][j] is not None:
                                val = x[k][i][j].solution_value()
                                if val > 1e-6:
                                    tareas_asignadas.append((
                                        ids[indices[j]],
                                        round(val, 2)
                                    ))
                        result_dict[worker_label] = tareas_asignadas
            final_result[area] = result_dict
        else:
            print(f"No se encontró solución óptima para área: {area}")

    return final_result