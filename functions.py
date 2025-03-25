import streamlit as st
import pandas as pd
import utils as u
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components
import os
import plotly.express as px

def show_main(df):
    st.session_state.mostrar_tabla = True
    st.session_state.mostrar_grafo = False
    st.dataframe(df, use_container_width=True)

def get_data(data):
    tareas_expanded = u.expandir_tareas(data)
    tareas = tareas_expanded['Carga (h) dia tarea'].tolist()
    nombres_tareas = tareas_expanded['Tarea'].tolist()
    trabajadores_exp  = tareas_expanded['Tipo de empleado'].tolist()
    areas = tareas_expanded['Área'].tolist()
    unique_types = data['Tipo de empleado'].unique().tolist()
    type_to_index = {t: i for i, t in enumerate(unique_types)}
    trabajadores = [[type_to_index[trab]] for trab in trabajadores_exp]
    ids_tareas = tareas_expanded["ID"].tolist()
    divisible = tareas_expanded['Divisible'].tolist()
    unique_types = data['Tipo de empleado'].unique().tolist()
    turnos_tareas = tareas_expanded["Turno_final"].tolist()
    task_seq = u.task_sequencing(tareas_expanded)

    return tareas, areas, trabajadores, unique_types, turnos_tareas, ids_tareas,task_seq,divisible


def plot_assignment_graph_streamlit(final_result, graph_title="assignment_graph"):
    net = Network(height="500px", width="100%", directed=True, notebook=False, cdn_resources="in_line")
    net.toggle_physics(True)

    area_base_colors = [
        ("#4A90E2", "#A3C8F0"),  # Azul
        ("#50C878", "#A6E6C2"),  # Verde
        ("#DA70D6", "#E9B8E8"),  # Violeta
        ("#FFA500", "#FFD580"),  # Naranja
        ("#FF6347", "#FFB6A9"),  # Rojo
    ]

    area_idx = 0
    area_offset = 500

    for area, workers_dict in final_result.items():
        color_workers, color_tasks = area_base_colors[area_idx % len(area_base_colors)]
        offset_x = area_idx * area_offset
        area_idx += 1


        # Nodo de área
        net.add_node(
            f"AREA_{area}", label=area, color="gray", shape="ellipse",
            x=offset_x, y=-300, physics=False
        )

        added_tasks = {}

        for worker, tareas in workers_dict.items():
            total_horas_worker = sum(h for _, h in tareas)
            worker_node_id = f"{area}__{worker}"

            # Color dinámico según horas asignadas
            color_actual = "#FF0000" if total_horas_worker < 8 else color_workers

            net.add_node(
                worker_node_id, label=f"{worker}\n{total_horas_worker}h", color=color_actual,
                borderWidth=2, borderWidthSelected=4, x=offset_x + 200, y=0
            )

            for tarea, horas in tareas:
                if horas > 0.5:
                    tarea_node_id = f"{area}__{tarea}"
                    if tarea_node_id not in added_tasks:
                        net.add_node(
                            tarea_node_id, label=tarea, color=color_tasks, shape="box",
                            x=offset_x + 100, y=-50
                        )
                        net.add_edge(f"AREA_{area}", tarea_node_id, width=1, color="gray", dashes=True)
                        added_tasks[tarea_node_id] = True

                    net.add_edge(worker_node_id, tarea_node_id, label=f"{horas}h", width=1 + horas / 2)

    html_content = net.generate_html()

    # 2️⃣ Inyectar estilo para evitar espacio blanco a la derecha
    html_content = html_content.replace(
        "<head>",
        "<head><style>body { margin: 0; overflow-x: hidden; }</style>"
    )

    # 3️⃣ Guardar HTML corregido
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(html_content)
        html_path = tmp_file.name


    components.html(open(html_path, 'r', encoding='utf-8').read(), height=550, scrolling=False)

    os.remove(html_path)

def generar_tabla_resumen(resultado_modelo):
    resumen = []

    for area, trabajadores in resultado_modelo.items():
        conteo_por_tipo = {}

        for trabajador in trabajadores:
            tipo = trabajador.split()[0]
            conteo_por_tipo[tipo] = conteo_por_tipo.get(tipo, 0) + 1

        for tipo, cantidad in conteo_por_tipo.items():
            resumen.append({
                "Área": area,
                "Tipo de empleado": tipo,
                "Nº empleados": cantidad
            })

    return pd.DataFrame(resumen)

def plot_comparacion_tipos_modelos(modelos_dict, modelos_seleccionados):
    data = []

    for modelo in modelos_seleccionados:
        resumen_tipo = {}

        resultado = modelos_dict[modelo]["resultado"]
        for area, trabajadores in resultado.items():
            for trabajador in trabajadores:
                tipo = trabajador.split()[0]
                resumen_tipo[tipo] = resumen_tipo.get(tipo, 0) + 1

        for tipo, cantidad in resumen_tipo.items():
            data.append({
                "Tipo de empleado": tipo,
                "Modelo": modelo,
                "Cantidad": cantidad
            })

    df = pd.DataFrame(data)

    # Agrupado por tipo en X, una barra por modelo en cada grupo
    fig = px.bar(
        df,
        x="Tipo de empleado",
        y="Cantidad",
        color="Modelo",
        barmode="group",
        title="Comparación de cantidad por tipo de empleado (por modelo)"
    )

    return fig


