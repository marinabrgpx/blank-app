import streamlit as st
import functions as f
import pandas as pd
from algoritmo_asignacion import algoritmo
import streamlit.components.v1 as components
from pyvis.network import Network
import tempfile
import os
import json
import random
import colorsys

# 🔹 Inicializar estado global
if "modelos" not in st.session_state:
    st.session_state.modelos = {}
if "modelo_seleccionado" not in st.session_state:
    st.session_state.modelo_seleccionado = "original"
if "mostrar_tabla" not in st.session_state:
    st.session_state.mostrar_tabla = False
if "mostrar_grafo" not in st.session_state:
    st.session_state.mostrar_grafo = True
if "main_df" not in st.session_state:
    st.session_state.main_df = None
if "vista_tabla_modelo" not in st.session_state:
    st.session_state.vista_tabla_modelo = False
if "mostrar_comparacion" not in st.session_state:
    st.session_state.mostrar_comparacion = False
if "mostrar_ajustes" not in st.session_state:
    st.session_state.mostrar_ajustes = False
if "mostrar_ahorro_global" not in st.session_state:
    st.session_state.mostrar_ahorro_global = False



# 🔹 Funciones de control de vista
def resetear_vistas():
    st.session_state.mostrar_tabla = False
    st.session_state.mostrar_grafo = False
    st.session_state.vista_tabla_modelo = False
    st.session_state.mostrar_comparacion = False
    st.session_state.mostrar_ajustes = False
    st.session_state.mostrar_ahorro_global =False

def mostrar_tabla_principal():
    resetear_vistas()
    st.session_state.mostrar_tabla = True

def mostrar_tabla_modelo():
    resetear_vistas()
    st.session_state.mostrar_tabla = True
    st.session_state.vista_tabla_modelo = True

def mostrar_grafo():
    resetear_vistas()
    st.session_state.mostrar_grafo = True

def mostrar_comparacion():
    resetear_vistas()
    st.session_state.mostrar_comparacion = True

def mostrar_ajustes():
    resetear_vistas()
    st.session_state.mostrar_ajustes = True

def mostrar_ahorro_global():
    resetear_vistas()
    st.session_state.mostrar_ahorro_global = True


def renombrar_modelo(nombre_actual, nuevo_nombre):
    if nuevo_nombre in st.session_state.modelos:
        st.warning("⚠️ Ya existe un modelo con ese nombre.")
    elif nuevo_nombre.strip() == "":
        st.warning("⚠️ El nombre no puede estar vacío.")
    else:
        st.session_state.modelos[nuevo_nombre] = st.session_state.modelos.pop(nombre_actual)

        # Actualizar selección si corresponde
        if st.session_state.modelo_seleccionado == nombre_actual:
            st.session_state.modelo_seleccionado = nuevo_nombre
        st.success(f"✅ Modelo '{nombre_actual}' renombrado a '{nuevo_nombre}'")



# 🔹 Sidebar: carga de archivo y navegación
add_uploader = st.sidebar.file_uploader("Cargar archivo", type=["xlsx"])

matriz_similitud = {
    "Grande": {"Grande": 1.0, "Mediano": 0.75, "Chico": 0.25, "Macro": 0.75},
    "Mediano": {"Grande": 0.75, "Mediano": 1.0, "Chico": 0.75, "Macro": 0.5},
    "Chico": {"Grande": 0.5, "Mediano": 0.75, "Chico": 1.0, "Macro": 0.25},
    "Macro": {"Grande": 0.75, "Mediano": 0.5, "Chico": 0.25, "Macro": 1},

}

st.sidebar.markdown("---")
st.sidebar.markdown("### ➕ Crear nuevo modelo")
nuevo_modelo_uploader = st.sidebar.file_uploader("Subir archivo con hojas de modelos", type=["xlsx"], key="nuevo_modelo")


if nuevo_modelo_uploader is not None:
    excel_obj = pd.ExcelFile(nuevo_modelo_uploader)
    hojas_disponibles = excel_obj.sheet_names

    hoja_seleccionada = st.sidebar.selectbox("Seleccionar hoja del modelo", hojas_disponibles, key="hoja_nuevo_modelo")
    
    if st.sidebar.button("📦 Crear modelo desde hoja seleccionada"):
        df_nuevo = excel_obj.parse(hoja_seleccionada)

        columnas_requeridas = ["Área", "Tarea", "Tipo de empleado", "Carga (h) dia tarea", "Divisible", "Cadena"]

        if all(col in df_nuevo.columns for col in columnas_requeridas):
            nombre_modelo = f"modelo_{len(st.session_state.modelos)}"

            posibles_areas = df_nuevo["Área"].unique().tolist()
            tareas, areas, trabajadores, unique_types, turnos_tareas, ids_tareas, task_seq, divisible = f.get_data(df_nuevo)
            resultado_modelo = algoritmo(tareas, areas, trabajadores, unique_types, 8, turnos_tareas, ids_tareas, task_seq, divisible)

            st.session_state.modelos[nombre_modelo] = {
                "df": df_nuevo,
                "resultado": resultado_modelo,
                "areas_posibles": posibles_areas
            }

            st.success(f"✅ Modelo '{nombre_modelo}' creado con éxito desde hoja '{hoja_seleccionada}'")
        else:
            st.error("❌ El archivo no tiene la estructura esperada. Revisa las columnas.")


st.sidebar.button("Ver grafo", on_click=mostrar_grafo)
st.sidebar.button("Ver tabla principal", on_click=mostrar_tabla_principal)
st.sidebar.button("Ver tabla del modelo actual", on_click=mostrar_tabla_modelo)
st.sidebar.button("Comparar modelos", on_click=mostrar_comparacion)
st.sidebar.button("⚙️ Ajustar modelos", on_click=mostrar_ajustes)
st.sidebar.button("💰 Estimar ahorro global", on_click=lambda: mostrar_ahorro_global())



# 🔹 Lógica principal
if add_uploader is not None:
    main = pd.read_excel(add_uploader, sheet_name="actual_model")
    st.session_state.main_df = main  # Guardar tabla original
    # Obtener tamaño de instalación por área (del archivo original)
    df_tamanios = st.session_state.main_df[["Área", "Tamaño instalacion"]].drop_duplicates()
    dict_area_tamanio = dict(zip(df_tamanios["Área"], df_tamanios["Tamaño instalacion"]))

    # Guardar modelo original si no existe
    if "original" not in st.session_state.modelos:
        posibles_areas = main["Área"].unique().tolist()
        tareas, areas, trabajadores, unique_types, turnos_tareas, ids_tareas, task_seq, divisible = f.get_data(main)
        resultado_modelo = algoritmo(tareas, areas, trabajadores, unique_types, 8, turnos_tareas, ids_tareas, task_seq, divisible)

        st.session_state.modelos["original"] = {
            "df": main,
            "resultado": resultado_modelo,
            "areas_posibles": posibles_areas
        }

    # Selector de modelo
    st.session_state.modelo_seleccionado = st.selectbox(
        "Seleccionar modelo a visualizar",
        list(st.session_state.modelos.keys()),
        index=list(st.session_state.modelos.keys()).index(st.session_state.modelo_seleccionado)
    )

    modelo = st.session_state.modelo_seleccionado
    modelo_data = st.session_state.modelos[modelo]

    # Filtro por áreas del modelo (solo si es relevante mostrarlo)
    key_filtro = f"filtro_areas_{modelo.replace(' ', '_')}"
    if key_filtro not in st.session_state:
        st.session_state[key_filtro] = modelo_data["areas_posibles"]

    if st.session_state.mostrar_grafo or st.session_state.vista_tabla_modelo:
        areas_seleccionadas = st.multiselect(
            f"Filtrar áreas para modelo '{modelo}'",
            modelo_data["areas_posibles"],
            default=st.session_state[key_filtro],
            key=key_filtro
        )
    else:
        areas_seleccionadas = st.session_state[key_filtro]

    # Aplicar filtro a datos del modelo
    df_filtrado = modelo_data["df"]
    df_filtrado = df_filtrado[df_filtrado["Área"].isin(areas_seleccionadas)]

    # Recalcular modelo con filtro aplicado
    tareas, areas, trabajadores, unique_types, turnos_tareas, ids_tareas, task_seq, divisible = f.get_data(df_filtrado)
    resultado_modelo = algoritmo(tareas, areas, trabajadores, unique_types, 8, turnos_tareas, ids_tareas, task_seq, divisible)

    # Mostrar contenido según vista
    if st.session_state.mostrar_tabla:
        if st.session_state.vista_tabla_modelo:
            st.subheader(f"Tabla del modelo '{modelo}' filtrado")
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            df_original = st.session_state.main_df
            key_filtro_original = f"filtro_areas_original_view"

            if key_filtro_original not in st.session_state:
                st.session_state[key_filtro_original] = df_original["Área"].unique().tolist()

            areas_original = st.multiselect(
                "Filtrar áreas para tabla original",
                df_original["Área"].unique().tolist(),
                default=st.session_state[key_filtro_original],
                key=key_filtro_original
            )

            df_original_filtrado = df_original[df_original["Área"].isin(areas_original)]
            st.subheader("Tabla original filtrada")
            st.dataframe(df_original_filtrado, use_container_width=True)

    if st.session_state.mostrar_grafo:
        f.plot_assignment_graph_streamlit(resultado_modelo)

        # Mostrar tabla resumen debajo del grafo
        st.markdown("### 📊 Resumen por tipo de empleado y área")
        tabla_resumen = f.generar_tabla_resumen(resultado_modelo)
        st.dataframe(tabla_resumen, use_container_width=True)

    # 🔹 Vista de comparación de modelos
    if st.session_state.mostrar_comparacion:
        st.header("📊 Comparación de modelos (por área y tipo de empleado)")

        modelos_disponibles = list(st.session_state.modelos.keys())
        modelos_a_comparar = st.multiselect("Selecciona modelos para comparar", modelos_disponibles)

        comparacion_df = None

        if modelos_a_comparar:
            data_pivot = []

            for modelo in modelos_a_comparar:
                resultado = st.session_state.modelos[modelo]["resultado"]
                df_resumen = f.generar_tabla_resumen(resultado)
                df_resumen["Modelo"] = modelo
                data_pivot.append(df_resumen)

            # Unir todo y pivotear
            df_total = pd.concat(data_pivot)
            df_pivot = df_total.pivot_table(
                index=["Área", "Tipo de empleado"],
                columns="Modelo",
                values="Nº empleados",
                fill_value=0
            ).reset_index()

            comparacion_df = df_pivot
            st.dataframe(comparacion_df, use_container_width=True)

            # Botón de descarga
            csv = comparacion_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar resumen como CSV", data=csv, file_name="comparacion_modelos.csv", mime="text/csv")
            # Gráfico comparativo por tipo de empleado
            st.markdown("### 📊 Comparación visual por tipo de empleado")
            fig = f.plot_comparacion_tipos_modelos(st.session_state.modelos, modelos_a_comparar)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecciona al menos un modelo para comparar.")
    # 🔧 Vista de ajustes de modelos
    if st.session_state.mostrar_ajustes:
        st.header("⚙️ Ajustar modelos")

        modelos_existentes = list(st.session_state.modelos.keys())
        modelo_actual = st.selectbox("Selecciona un modelo", modelos_existentes, key="ajustar_modelo")

        nuevo_nombre = st.text_input("✏️ Nuevo nombre", value=modelo_actual, key="nuevo_nombre_modelo")
        descripcion_actual = st.session_state.modelos[modelo_actual].get("descripcion", "")
        nueva_descripcion = st.text_area("📝 Descripción del modelo", value=descripcion_actual, key="descripcion_modelo")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Guardar cambios"):
                # Renombrar si cambió el nombre
                if nuevo_nombre != modelo_actual:
                    if nuevo_nombre in st.session_state.modelos:
                        st.warning("❗ Ya existe un modelo con ese nombre.")
                    elif nuevo_nombre.strip() == "":
                        st.warning("❗ El nombre no puede estar vacío.")
                    else:
                        st.session_state.modelos[nuevo_nombre] = st.session_state.modelos.pop(modelo_actual)
                        st.session_state.modelos[nuevo_nombre]["descripcion"] = nueva_descripcion

                        if st.session_state.modelo_seleccionado == modelo_actual:
                            st.session_state.modelo_seleccionado = nuevo_nombre

                        st.success(f"✅ Modelo renombrado a '{nuevo_nombre}'")
                else:
                    # Solo actualiza la descripción
                    st.session_state.modelos[modelo_actual]["descripcion"] = nueva_descripcion
                    st.success("✅ Descripción actualizada")

        with col2:
            if st.button("🗑️ Eliminar modelo"):
                if modelo_actual == "original":
                    st.warning("❗ No puedes eliminar el modelo original.")
                else:
                    del st.session_state.modelos[modelo_actual]
                    st.success(f"🗑️ Modelo '{modelo_actual}' eliminado")
                    if st.session_state.modelo_seleccionado == modelo_actual:
                        st.session_state.modelo_seleccionado = "original"

        st.markdown("---")
        if st.button("📄 Duplicar modelo"):
            nombre_base = f"{modelo_actual}_copy"
            i = 1
            nuevo_nombre = nombre_base
            while nuevo_nombre in st.session_state.modelos:
                i += 1
                nuevo_nombre = f"{nombre_base}_{i}"

            import copy
            st.session_state.modelos[nuevo_nombre] = copy.deepcopy(st.session_state.modelos[modelo_actual])
            st.success(f"✅ Modelo duplicado como '{nuevo_nombre}'")
    # 💰 Vista de estimación de ahorro global
    if st.session_state.mostrar_ahorro_global:
        st.header("💰 Estimación de ahorro global")

        # Cargar archivo de costos desde archivo local
        ruta_costos = "costes_empleados_completos.xlsx"

        try:
            df_costos = pd.read_excel(ruta_costos)
            st.success("✅ Archivo de costos cargado correctamente")

            if "Nivel GPX" not in df_costos.columns or "Coste empresa anual (MXN)" not in df_costos.columns:
                st.warning("⚠️ La tabla debe tener las columnas 'Nivel GPX' y 'Coste empresa anual (MXN)'")
            else:
                st.markdown("### 🔍 Seleccionar modelos para comparar con el original")

                modelos_disponibles = [m for m in st.session_state.modelos.keys() if m != "original"]
                modelos_seleccionados = st.multiselect("Selecciona modelos a comparar", modelos_disponibles)

                if modelos_seleccionados:
                    st.markdown("### 📉 Reducción de empleados por área y tipo (vs. modelo original)")

                    # 1. Totales originales por área y tipo
                    original_resultado = st.session_state.modelos["original"]["resultado"]
                    resumen_original = f.generar_tabla_resumen(original_resultado)
                    resumen_original["Modelo"] = "original"

                    resumen_reduccion = []

                    # Convertimos el resumen original a un diccionario indexado por (Área, Tipo)
                    original_dict = resumen_original.set_index(["Área", "Tipo de empleado"])["Nº empleados"].to_dict()

                    for modelo in modelos_seleccionados:
                        resultado_modelo = st.session_state.modelos[modelo]["resultado"]
                        df_modelo = f.generar_tabla_resumen(resultado_modelo)
                        df_modelo["Modelo"] = modelo

                        modelo_dict = df_modelo.set_index(["Área", "Tipo de empleado"])["Nº empleados"].to_dict()

                        # Comparar cada combinación presente en el original
                        for (area, tipo), empleados_orig in original_dict.items():
                            empleados_mod = modelo_dict.get((area, tipo), 0)

                            if empleados_orig > 0:
                                reduccion_pct = (empleados_orig - empleados_mod) / empleados_orig
                            else:
                                reduccion_pct = 0.0

                            resumen_reduccion.append({
                                "Modelo": modelo,
                                "Área": area,
                                "Tipo de empleado": tipo,
                                "Original": empleados_orig,
                                "Modelo actual": empleados_mod,
                                "% Reducción estimada": round(reduccion_pct * 100, 2)
                            })

                    df_reduccion = pd.DataFrame(resumen_reduccion)
                    st.dataframe(df_reduccion, use_container_width=True)




        except Exception as e:
            st.error(f"❌ Error al cargar archivo de costos: {e}")



else:
    st.text("Aún no hay datos cargados")
