# Reto2-BI
Autor: Carlos Santiago Perdomo Gutiérrez
Correo institucional: csperdomog@eafit.edu.co
Programa académico: Administración de Negocios
Fecha de entrega: 22/10/2025
Repositorio: https://github.com/santiagoperguti/Reto2-BI.git

🧾 Descripción
Este proyecto desarrolla un tablero interactivo en Streamlit para analizar información contable almacenada en una base de datos SQLite. El tablero incluye consultas SQL (Q1 – Q4) y una consulta opcional (Q5), cada una acompañada de sus visualizaciones y conclusiones. El objetivo es presentar informes contables claros, visuales y fáciles de interpretar para la toma de decisiones.

🧱 Estructura del proyecto

Reto2-Streamlit-Contable/
├─ app.py
├─ data/
│ └─ contabilidad.sqlite
├─ sql/
│ ├─ Q1.sql
│ ├─ Q2.sql
│ ├─ Q3.sql
│ ├─ Q4.sql
│ └─ Q5.sql
├─ imgs/
│ ├─ tablero_home.png
│ ├─ q1_chart.png
│ ├─ q2_chart.png
│ └─ q3_chart.png
├─ requirements.txt
└─ README.md

⚙️ Instalación y ejecución

1️⃣ Clonar el repositorio

git clone https://github.com/<usuario>/<nombre_del_repo>.git
cd Reto2-Streamlit-Contable

2️⃣ Crear y activar entorno virtual (opcional)

conda create -n reto2 python=3.11 -y
conda activate reto2

3️⃣ Instalar dependencias

pip install -r requirements.txt

4️⃣ Ejecutar el tablero

streamlit run app.py

Luego abre tu navegador en http://localhost:8501

📊 Consultas SQL y conclusiones
Consulta	Archivo	Descripción	Conclusión
Q1	sql/Q1.sql	Análisis mensual de ingresos	
Q2	sql/Q2.sql	Gastos principales por categoría	
Q3	sql/Q3.sql	Comparativo de ingresos por socio
Q4	sql/Q4.sql	Tendencia del balance general	
Q5 (opcional)	sql/Q5.sql	Métrica personalizada	

📦 Dependencias principales
streamlit
pandas
numpy
plotly
sqlite3-binary ; platform_system=="Windows"
altair

👨‍💻 Autor

Proyecto desarrollado por Carlos Santiago Perdomo Gutiérrez para el Introducción a BI – Universidad EAFIT.
