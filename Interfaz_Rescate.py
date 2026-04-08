# -*- coding: utf-8 -*-
"""
CENTRO DE MONITOREO - OPERACIONES DE RESCATE
Autor: Sistema de Monitoreo LoRaWAN
"""

import sys
import math
import webbrowser
import pandas as pd
import os
import chardet
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 🔥 NUEVAS IMPORTACIONES PARA PDF PROFESIONAL
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4


class SistemaRescate(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CENTRO DE MONITOREO - RESCATE LoRaWAN")
        self.setGeometry(100, 100, 1500, 820)

        self.df = None
        self.df_filtrado = None
        self.tracker_seleccionado = None
        self.punto_seleccionado = None

        self.initUI()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def initUI(self):
        self.setStyleSheet("""
        QMainWindow { background-color: #0F111A; }

        QPushButton {
            background-color: #151A25;
            color: #00F5FF;
            font-size: 14px;
            padding: 12px;
            border-radius: 12px;
            border: 2px solid #00F5FF;
        }

        QPushButton:hover {
            background-color: #00F5FF;
            color: black;
        }

        QLabel {
            color: #E0E0E0;
            font-size: 15px;
        }

        QTableWidget {
            background-color: #141821;
            color: white;
            gridline-color: #00F5FF;
        }
        """)
        
        main_layout = QHBoxLayout()
        panel_botones = QVBoxLayout()

        self.btn_cargar = QPushButton("1️⃣ Cargar Documento")
        self.btn_cargar.clicked.connect(self.cargar_documento)

        self.btn_selector = QPushButton("2️⃣ Seleccionar Tracker / Punto")
        self.btn_selector.clicked.connect(self.modulo_filtrado)

        self.btn_metricas = QPushButton("3️⃣ Ver Métricas")
        self.btn_metricas.clicked.connect(self.ver_metricas)

        self.btn_graficas = QPushButton("4️⃣ Generar Gráficas")
        self.btn_graficas.clicked.connect(self.generar_graficas)

        self.btn_informe = QPushButton("5️⃣ Generar Informe Técnico")
        self.btn_informe.clicked.connect(self.generar_informe_pdf)  # 🔥 CONEXIÓN AGREGADA

        self.btn_salir = QPushButton("Cerrar Sistema")
        self.btn_salir.clicked.connect(self.close)

        panel_botones.addWidget(self.btn_cargar)
        panel_botones.addWidget(self.btn_selector)
        panel_botones.addWidget(self.btn_metricas)
        panel_botones.addWidget(self.btn_graficas)
        panel_botones.addWidget(self.btn_informe)
        panel_botones.addStretch()
        panel_botones.addWidget(self.btn_salir)

        panel_visual = QVBoxLayout()
        self.label_estado = QLabel("Sistema listo para cargar documento")
        self.label_estado.setAlignment(Qt.AlignCenter)

        self.tabla = QTableWidget()
        self.tabla.itemSelectionChanged.connect(self.capturar_punto)

        panel_visual.addWidget(self.label_estado)
        panel_visual.addWidget(self.tabla)

        container = QWidget()
        main_layout.addLayout(panel_botones, 1)
        main_layout.addLayout(panel_visual, 4)

        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # ======================================================
    # CARGAR DOCUMENTO MULTIFORMATO PROFESIONAL
    # ======================================================

    def cargar_documento(self):

        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar documento",
            "",
            "Archivos de datos (*.csv *.xlsx *.xls *.ods *.txt);;Todos (*.*)"
        )

        if not archivo:
            return

        try:
            extension = os.path.splitext(archivo)[1].lower()

            # =========================
            # LECTURA SEGÚN EXTENSIÓN
            # =========================

            if extension == ".csv":
                try:
                    self.df = pd.read_csv(archivo, sep=None, engine="python", encoding="utf-8")
                except:
                    self.df = pd.read_csv(archivo, sep=None, engine="python", encoding="latin1")

            elif extension in [".xlsx", ".xls"]:
                self.df = pd.read_excel(archivo)

            elif extension == ".ods":
                self.df = pd.read_excel(archivo, engine="odf")

            elif extension == ".txt":

                with open(archivo, "rb") as f:
                    resultado = chardet.detect(f.read())
                    encoding_detectado = resultado["encoding"]

                try:
                    self.df = pd.read_csv(
                        archivo,
                        sep=None,
                        engine="python",
                        encoding=encoding_detectado
                    )
                except:
                    self.df = pd.read_csv(
                        archivo,
                        sep=";",
                        encoding=encoding_detectado
                    )

            else:
                QMessageBox.warning(self, "Formato no soportado", "Tipo de archivo no compatible.")
                return

            # =========================
            # LIMPIEZA Y NORMALIZACIÓN
            # =========================

            self.df.columns = self.df.columns.str.strip()

            columnas_requeridas = ["ID Tracker", "Usuario Asignado", "Fecha", "Hora", "Latitud", "Longitud"]

            for col in columnas_requeridas:
                if col not in self.df.columns:
                    QMessageBox.warning(self, "Error", f"Falta la columna requerida: {col}")
                    return

            # Convertir lat/long (corrige comas decimales)
            self.df["Latitud"] = self.df["Latitud"].astype(str).str.replace(",", ".").astype(float)
            self.df["Longitud"] = self.df["Longitud"].astype(str).str.replace(",", ".").astype(float)

            self.mostrar_tabla(self.df)
            self.label_estado.setText(f"Documento cargado correctamente: {os.path.basename(archivo)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{str(e)}")
    # ======================================================
    # MOSTRAR TABLA
    # ======================================================

    def mostrar_tabla(self, df):
        self.tabla.clear()
        self.tabla.setRowCount(len(df))
        self.tabla.setColumnCount(len(df.columns))
        self.tabla.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j in range(len(df.columns)):
                self.tabla.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.tabla.resizeColumnsToContents()

    # ======================================================
    # CAPTURAR PUNTO
    # ======================================================

    def capturar_punto(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return

        df_base = self.df_filtrado if self.df_filtrado is not None else self.df
        if df_base is None:
            return

        self.punto_seleccionado = df_base.iloc[fila]

    # ======================================================
    # FILTRADO
    # ======================================================

    def modulo_filtrado(self):
        if self.df is None:
            QMessageBox.warning(self, "Atención", "Primero cargue un documento.")
            return

        col_tracker = next((c for c in self.df.columns
                            if "tracker" in c.lower() or "id" in c.lower()), None)

        if not col_tracker:
            QMessageBox.warning(self, "Error", "No se encontró columna Tracker.")
            return

        trackers = self.df[col_tracker].dropna().unique()

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Seleccione Tracker")
        dialogo.setStyleSheet("background-color:#141821; color:white;")

        layout = QVBoxLayout()
        combo_tracker = QComboBox()
        combo_tracker.addItems([str(t) for t in trackers])
        btn_filtrar = QPushButton("Mostrar Datos")

        def aplicar_filtro():
            tracker_sel = combo_tracker.currentText()
            df_filtrado = self.df[self.df[col_tracker].astype(str) == tracker_sel]

            if df_filtrado.empty:
                QMessageBox.warning(dialogo, "Sin datos", "No hay datos para ese tracker.")
                return

            self.df_filtrado = df_filtrado
            self.tracker_seleccionado = tracker_sel
            self.mostrar_tabla(self.df_filtrado)
            dialogo.accept()

        btn_filtrar.clicked.connect(aplicar_filtro)

        layout.addWidget(QLabel("Seleccione Tracker:"))
        layout.addWidget(combo_tracker)
        layout.addWidget(btn_filtrar)
        dialogo.setLayout(layout)
        dialogo.exec_()

    # ======================================================
    # MÉTRICAS
    # ======================================================

    def ver_metricas(self):
        if self.punto_seleccionado is None:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un punto en la tabla.")
            return

        try:

            punto = self.punto_seleccionado
            tracker_id = punto["ID Tracker"]

            df_tracker = self.df[self.df["ID Tracker"] == tracker_id].copy()

            df_tracker["FechaHora"] = pd.to_datetime(
                df_tracker["Fecha"].astype(str) + " " + df_tracker["Hora"].astype(str),
                errors="coerce"
            )

            df_tracker = df_tracker.sort_values("FechaHora").reset_index(drop=True)

            coincidencias = df_tracker[
                (df_tracker["Fecha"] == punto["Fecha"]) &
                (df_tracker["Hora"] == punto["Hora"]) &
                (df_tracker["Latitud"] == punto["Latitud"]) &
                (df_tracker["Longitud"] == punto["Longitud"])
            ]

            if coincidencias.empty:
                QMessageBox.warning(self, "Error", "No se pudo localizar el punto.")
                return

            indice = coincidencias.index[0]

            def haversine(lat1, lon1, lat2, lon2):
                R = 6371000
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            distancia_anterior = 0
            tiempo_anterior = 0
            velocidad_instantanea = 0
            distancia_acumulada = 0

            for i in range(1, indice + 1):
                dist = haversine(
                    df_tracker.loc[i-1, "Latitud"],
                    df_tracker.loc[i-1, "Longitud"],
                    df_tracker.loc[i, "Latitud"],
                    df_tracker.loc[i, "Longitud"]
                )
                distancia_acumulada += dist

                if i == indice:
                    distancia_anterior = dist
                    t1 = df_tracker.loc[i-1, "FechaHora"]
                    t2 = df_tracker.loc[i, "FechaHora"]
                    tiempo_anterior = (t2 - t1).total_seconds()
                    if tiempo_anterior > 0:
                        velocidad_instantanea = distancia_anterior / tiempo_anterior

            lat_inicio = df_tracker.loc[0, "Latitud"]
            lon_inicio = df_tracker.loc[0, "Longitud"]

            distancia_origen = haversine(
                lat_inicio, lon_inicio,
                punto["Latitud"], punto["Longitud"]
            )

            tiempo_total = (
                df_tracker.loc[indice, "FechaHora"] -
                df_tracker.loc[0, "FechaHora"]
            ).total_seconds()

            velocidad_media = distancia_acumulada / tiempo_total if tiempo_total > 0 else 0

            estado = "Movimiento normal"
            riesgo = "Bajo"

            if velocidad_instantanea < 0.3:
                estado = "Inmovilidad crítica"
                riesgo = "Alto"
            elif velocidad_instantanea < 1.2:
                estado = "Movimiento lento"
                riesgo = "Medio"

            mensaje = "=== MÉTRICAS DEL PUNTO ===\n\n"

            for col in punto.index:
                mensaje += f"{col}: {punto[col]}\n"

            mensaje += "\n--- MÉTRICAS CALCULADAS ---\n\n"
            mensaje += f"Distancia anterior: {distancia_anterior:.2f} m\n"
            mensaje += f"Tiempo anterior: {tiempo_anterior:.2f} s\n"
            mensaje += f"Velocidad instantánea: {velocidad_instantanea:.2f} m/s ({velocidad_instantanea*3.6:.2f} km/h)\n"
            mensaje += f"Distancia acumulada: {distancia_acumulada:.2f} m\n"
            mensaje += f"Distancia desde origen: {distancia_origen:.2f} m\n"
            mensaje += f"Velocidad media: {velocidad_media:.2f} m/s ({velocidad_media*3.6:.2f} km/h)\n"
            mensaje += f"Estado: {estado}\n"
            mensaje += f"Nivel de riesgo: {riesgo}\n"

            dialogo = QDialog(self)
            dialogo.setWindowTitle("Métricas del Punto")
            dialogo.resize(600, 500)

            layout = QVBoxLayout()
            texto = QTextEdit()
            texto.setReadOnly(True)
            texto.setText(mensaje)

            layout.addWidget(texto)
            dialogo.setLayout(layout)
            dialogo.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", str(e))
    # ======================================================
    # GRÁFICAS PROFESIONALES + MAPA
    # ======================================================

    def generar_graficas(self):
        if self.punto_seleccionado is None:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un punto en la tabla.")
            return

        try:
            punto = self.punto_seleccionado
            tracker_id = punto["ID Tracker"]

            df_tracker = self.df[self.df["ID Tracker"] == tracker_id].copy()
            df_tracker["FechaHora"] = pd.to_datetime(
                df_tracker["Fecha"].astype(str) + " " + df_tracker["Hora"].astype(str),
                errors="coerce"
            )
            df_tracker = df_tracker.sort_values("FechaHora").reset_index(drop=True)

            velocidades = [0]
            dist_acum = [0]

            def haversine(lat1, lon1, lat2, lon2):
                R = 6371000
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            for i in range(1, len(df_tracker)):
                dist = haversine(
                    df_tracker.loc[i-1, "Latitud"],
                    df_tracker.loc[i-1, "Longitud"],
                    df_tracker.loc[i, "Latitud"],
                    df_tracker.loc[i, "Longitud"]
                )
                tiempo = (df_tracker.loc[i, "FechaHora"] - df_tracker.loc[i-1, "FechaHora"]).total_seconds()
                vel = dist / tiempo if tiempo > 0 else 0
                velocidades.append(vel)
                dist_acum.append(dist_acum[-1] + dist)

            df_tracker["Velocidad"] = pd.Series(velocidades).clip(lower=0, upper=20)
            df_tracker["DistanciaAcum"] = dist_acum

            coincidencias = df_tracker[
                (df_tracker["Fecha"] == punto["Fecha"]) &
                (df_tracker["Hora"] == punto["Hora"]) &
                (df_tracker["Latitud"] == punto["Latitud"]) &
                (df_tracker["Longitud"] == punto["Longitud"])
            ]
            if coincidencias.empty:
                QMessageBox.warning(self, "Error", "No se pudo localizar el punto.")
                return

            indice = coincidencias.index[0]

            dialogo = QDialog(self)
            dialogo.setWindowTitle("Análisis Gráfico del Tracker")
            dialogo.resize(1000, 700)
            layout = QVBoxLayout()
            tabs = QTabWidget()

            # ---------------- Trayectoria ----------------
            fig1 = Figure()
            canvas1 = FigureCanvas(fig1)
            ax1 = fig1.add_subplot(111)
            ax1.plot(df_tracker["Longitud"], df_tracker["Latitud"])
            ax1.scatter(df_tracker["Longitud"], df_tracker["Latitud"], s=10)
            ax1.scatter(df_tracker.loc[indice, "Longitud"], df_tracker.loc[indice, "Latitud"], s=120)
            ax1.set_title("Trayectoria")
            ax1.grid(True)
            tabs.addTab(canvas1, "📍 Trayectoria")

            # ---------------- Velocidad ----------------
            fig2 = Figure()
            canvas2 = FigureCanvas(fig2)
            ax2 = fig2.add_subplot(111)
            ax2.plot(df_tracker["FechaHora"], df_tracker["Velocidad"])
            ax2.scatter(df_tracker.loc[indice, "FechaHora"], df_tracker.loc[indice, "Velocidad"], s=120)
            ax2.set_ylim(0, 20)
            ax2.set_title("Velocidad vs Tiempo")
            ax2.grid(True)
            tabs.addTab(canvas2, "📈 Velocidad")

            # ---------------- Distancia ----------------
            fig3 = Figure()
            canvas3 = FigureCanvas(fig3)
            ax3 = fig3.add_subplot(111)
            ax3.plot(df_tracker["FechaHora"], df_tracker["DistanciaAcum"])
            ax3.scatter(df_tracker.loc[indice, "FechaHora"], df_tracker.loc[indice, "DistanciaAcum"], s=120)
            ax3.set_title("Distancia acumulada")
            ax3.grid(True)
            tabs.addTab(canvas3, "📊 Distancia")

            # ---------------- Riesgo ----------------
            riesgo_numerico = [3 if v < 0.3 else 2 if v < 1.2 else 1 for v in df_tracker["Velocidad"]]
            fig4 = Figure()
            canvas4 = FigureCanvas(fig4)
            ax4 = fig4.add_subplot(111)
            ax4.plot(df_tracker["FechaHora"], riesgo_numerico)
            ax4.scatter(df_tracker.loc[indice, "FechaHora"], riesgo_numerico[indice], s=120)
            ax4.set_yticks([1, 2, 3])
            ax4.set_title("Nivel de Riesgo")
            ax4.grid(True)
            tabs.addTab(canvas4, "📉 Riesgo")

            # ---------------- Mapa OpenStreetMap ----------------
            widget_mapa = QWidget()
            layout_mapa = QVBoxLayout()
            btn_mapa = QPushButton("🌍 Abrir trayectoria en OpenStreetMap")

            def abrir_mapa():
                try:
                    latitudes = df_tracker["Latitud"].astype(float).tolist()
                    longitudes = df_tracker["Longitud"].astype(float).tolist()
                    lat_sel = float(df_tracker.loc[indice, "Latitud"])
                    lon_sel = float(df_tracker.loc[indice, "Longitud"])
                    vel_sel = float(df_tracker.loc[indice, "Velocidad"])
                    dist_sel = float(df_tracker.loc[indice, "DistanciaAcum"])
                    fecha_sel = str(df_tracker.loc[indice, "Fecha"])
                    hora_sel = str(df_tracker.loc[indice, "Hora"])

                    coords_js = ",\n".join([f"[{latitudes[i]}, {longitudes[i]}]" for i in range(len(latitudes))])

                    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Trayectoria Tracker</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <style>
        #map {{ height: 100vh; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Crear mapa
        var map = L.map('map');

        // Tiles de OpenStreetMap con calles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);

        // Trayectoria
        var trayectoria = [
            {coords_js}
        ];
        var polyline = L.polyline(trayectoria, {{color: 'blue'}}).addTo(map);

        // Marcador del punto seleccionado
        var marker = L.marker([{lat_sel}, {lon_sel}], {{
            icon: L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }})
        }}).addTo(map);

        marker.bindPopup(
            "<b>Punto Seleccionado</b><br>" +
            "Fecha: {fecha_sel}<br>" +
            "Hora: {hora_sel}<br>" +
            "Velocidad: {vel_sel:.2f} m/s<br>" +
            "Distancia acumulada: {dist_sel:.2f} m"
        ).openPopup();

        // Ajustar vista al área de la trayectoria
        map.fitBounds(polyline.getBounds());
    </script>
</body>
</html>
"""

                    file_path = "mapa_tracker.html"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    webbrowser.open_new_tab(file_path)

                except Exception as e:
                    QMessageBox.critical(self, "Error inesperado", str(e))

            btn_mapa.clicked.connect(abrir_mapa)
            layout_mapa.addWidget(btn_mapa)
            widget_mapa.setLayout(layout_mapa)
            tabs.addTab(widget_mapa, "🗺 Mapa")

            # ---------------- Mostrar todas las pestañas ----------------
            layout.addWidget(tabs)
            dialogo.setLayout(layout)
            dialogo.exec_() 
        except Exception as e: 
            QMessageBox.critical(self, "Error inesperado", str(e))
    # ======================================================
    # GENERAR INFORME PDF PROFESIONAL AVANZADO
    # ======================================================

    def generar_informe_pdf(self):

        if self.punto_seleccionado is None:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un punto.")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Informe",
            "Informe_Tecnico_GPS.pdf",
            "PDF Files (*.pdf)"
        )

        if not archivo:
            return

        try:

            punto = self.punto_seleccionado
            tracker_id = punto["ID Tracker"]
            usuario = punto["Usuario Asignado"]

            df_tracker = self.df[self.df["ID Tracker"] == tracker_id].copy()

            df_tracker["FechaHora"] = pd.to_datetime(
                df_tracker["Fecha"].astype(str) + " " + df_tracker["Hora"].astype(str),
                errors="coerce"
            )

            df_tracker = df_tracker.sort_values("FechaHora").reset_index(drop=True)

            import math
            import folium
            import os
            from datetime import datetime

            # ------------------------------------------------
            # FUNCIÓN HAVERSINE
            # ------------------------------------------------

            def haversine(lat1, lon1, lat2, lon2):
                R = 6371000
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            # ------------------------------------------------
            # CÁLCULO DE MÉTRICAS
            # ------------------------------------------------

            distancia_total = 0
            velocidades = []
            aceleraciones = []
            dist_acum = [0]

            for i in range(1, len(df_tracker)):
                dist = haversine(
                    df_tracker.loc[i-1, "Latitud"],
                    df_tracker.loc[i-1, "Longitud"],
                    df_tracker.loc[i, "Latitud"],
                    df_tracker.loc[i, "Longitud"]
                )

                tiempo = (df_tracker.loc[i, "FechaHora"] -
                          df_tracker.loc[i-1, "FechaHora"]).total_seconds()

                vel = dist / tiempo if tiempo > 0 else 0
                velocidades.append(vel)
                distancia_total += dist
                dist_acum.append(distancia_total)

                if i > 1:
                    acc = (velocidades[-1] - velocidades[-2]) / tiempo if tiempo > 0 else 0
                    aceleraciones.append(abs(acc))

            tiempo_total = (df_tracker["FechaHora"].iloc[-1] -
                            df_tracker["FechaHora"].iloc[0]).total_seconds()

            velocidad_promedio = distancia_total / tiempo_total if tiempo_total > 0 else 0
            velocidad_maxima = max(velocidades) if velocidades else 0
            aceleracion_maxima = max(aceleraciones) if aceleraciones else 0

            desplazamiento_neto = haversine(
                df_tracker.iloc[0]["Latitud"],
                df_tracker.iloc[0]["Longitud"],
                df_tracker.iloc[-1]["Latitud"],
                df_tracker.iloc[-1]["Longitud"]
            )

            radio_max = max(dist_acum)

            intervalos = df_tracker["FechaHora"].diff().dt.total_seconds().dropna()
            intervalo_promedio = intervalos.mean() if not intervalos.empty else 0

            detenciones = sum(1 for v in velocidades if v < 0.3)

            velocidad_anomala = velocidad_maxima > 3.5
            detencion_prolongada = detenciones > 5

            # ------------------------------------------------
            # GENERAR MAPA OPENSTREETMAP PROFESIONAL
            # ------------------------------------------------

            mapa = folium.Map(
                location=[df_tracker["Latitud"].mean(),
                          df_tracker["Longitud"].mean()],
                zoom_start=16
            )

            coordenadas = list(zip(df_tracker["Latitud"], df_tracker["Longitud"]))

            # Trayectoria
            folium.PolyLine(
                coordenadas,
                color="blue",
                weight=4
            ).add_to(mapa)

            # Punto inicial (verde)
            folium.Marker(
                location=coordenadas[0],
                popup="Inicio del recorrido",
                icon=folium.Icon(color="green")
            ).add_to(mapa)

            # Punto final (negro)
            folium.Marker(
                location=coordenadas[-1],
                popup="Fin del recorrido",
                icon=folium.Icon(color="black")
            ).add_to(mapa)

            # Punto seleccionado (rojo)
            folium.Marker(
                location=[punto["Latitud"], punto["Longitud"]],
                popup=f"Tracker {tracker_id} - Punto seleccionado",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(mapa)

            # Ajuste automático de zoom
            mapa.fit_bounds(coordenadas)

            nombre_mapa = f"Mapa_Tracker_{tracker_id}.html"
            mapa.save(nombre_mapa)

            ruta_mapa = os.path.abspath(nombre_mapa)
            ruta_mapa_pdf = ruta_mapa.replace("\\", "/")

            # ------------------------------------------------
            # RESUMEN
            # ------------------------------------------------

            resumen = f"""
El tracker ID {tracker_id} presentó un recorrido total de {distancia_total/1000:.2f} km
durante {tiempo_total/60:.2f} minutos, con velocidad promedio de
{velocidad_promedio*3.6:.2f} km/h y velocidad máxima de
{velocidad_maxima*3.6:.2f} km/h.
"""

            if detencion_prolongada:
                resumen += "Se detectaron periodos de posible detención prolongada. "
            if velocidad_anomala:
                resumen += "Se identificaron velocidades superiores al rango esperado. "
            if not detencion_prolongada and not velocidad_anomala:
                resumen += "No se detectaron patrones operativos anómalos."

            if detencion_prolongada:
                evaluacion = "Posible situación de inmovilidad crítica detectada."
            elif velocidad_anomala:
                evaluacion = "Comportamiento cinemático fuera del rango esperado."
            else:
                evaluacion = "Desplazamiento consistente con movilidad peatonal normal."

            # ------------------------------------------------
            # GRÁFICAS
            # ------------------------------------------------

            import matplotlib.pyplot as plt

            plt.figure()
            plt.plot(velocidades)
            plt.title("Velocidad vs Tiempo")
            plt.grid(True)
            plt.savefig("velocidad.png", dpi=300)
            plt.close()

            plt.figure()
            plt.plot(dist_acum)
            plt.title("Distancia Acumulada")
            plt.grid(True)
            plt.savefig("distancia.png", dpi=300)
            plt.close()

            plt.figure()
            plt.plot(df_tracker["Longitud"], df_tracker["Latitud"])
            plt.title("Trayectoria XY")
            plt.grid(True)
            plt.savefig("trayectoria.png", dpi=300)
            plt.close()

            # ------------------------------------------------
            # CREAR PDF
            # ------------------------------------------------

            doc = SimpleDocTemplate(archivo, pagesize=A4)
            elementos = []
            estilos = getSampleStyleSheet()

            elementos.append(Paragraph("UNIVERSIDAD TÉCNICA DEL NORTE", estilos["Heading1"]))
            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("FICA", estilos["Normal"]))
            elementos.append(Paragraph("Sistema de Monitoreo GPS basado en LoRaWAN", estilos["Normal"]))
            elementos.append(Paragraph(f"Fecha de generación: {datetime.now()}", estilos["Normal"]))
            elementos.append(Paragraph(f"Tracker Analizado: {tracker_id}", estilos["Normal"]))
            elementos.append(Paragraph(f"Usuario Asignado: {usuario}", estilos["Normal"]))
            elementos.append(Spacer(1, 20))

            elementos.append(Paragraph("Resumen Operativo", estilos["Heading2"]))
            elementos.append(Spacer(1, 10))
            elementos.append(Paragraph(resumen, estilos["Normal"]))
            elementos.append(Spacer(1, 20))
            
            data_tabla = [
                ["Métrica", "Valor"],
                ["Distancia Total (m)", f"{distancia_total:.2f}"],
                ["Desplazamiento Neto (m)", f"{desplazamiento_neto:.2f}"],
                ["Tiempo Total (s)", f"{tiempo_total:.2f}"],
                ["Velocidad Promedio (m/s)", f"{velocidad_promedio:.2f}"],
                ["Velocidad Máxima (m/s)", f"{velocidad_maxima:.2f}"],
                ["Aceleración Máxima (m/s²)", f"{aceleracion_maxima:.2f}"],
                ["Intervalo Promedio (s)", f"{intervalo_promedio:.2f}"],
                ["Radio Máximo (m)", f"{radio_max:.2f}"],
            ]

            tabla = Table(data_tabla)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
            ]))

            elementos.append(tabla)
            elementos.append(Spacer(1, 20))

            elementos.append(Paragraph("Mapa interactivo OpenStreetMap:", estilos["Heading2"]))
            elementos.append(Spacer(1, 10))
            link_mapa = f'<a href="file:///{ruta_mapa_pdf}">Abrir mapa interactivo en navegador</a>'
            elementos.append(Paragraph(link_mapa, estilos["Normal"]))
            elementos.append(Spacer(15, 20))

            elementos.append(Image("velocidad.png", width=400, height=200))
            elementos.append(Spacer(1, 15))
            elementos.append(Image("distancia.png", width=400, height=200))
            elementos.append(Spacer(1, 15))
            elementos.append(Image("trayectoria.png", width=400, height=200))
            elementos.append(Spacer(1, 20))

            elementos.append(Paragraph("Evaluación Automática", estilos["Heading2"]))
            elementos.append(Spacer(1, 10))
            elementos.append(Paragraph(evaluacion, estilos["Normal"]))

            doc.build(elementos)

            QMessageBox.information(self, "Éxito", "Informe profesional generado correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = SistemaRescate()
    ventana.show()
    sys.exit(app.exec_())