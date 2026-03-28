# 🎯 JobRadar AI

¡Bienvenido a **JobRadar AI**! Un asistente de búsqueda de empleo Open Source diseñado para automatizar, analizar y gestionar tus postulaciones utilizando Inteligencia Artificial.

En lugar de leer cientos de ofertas de trabajo manualmente, JobRadar AI obtiene las ofertas de una base de datos, cruza los requisitos con tu CV, y te dice exactamente qué porcentaje de compatibilidad (*Match Score*) tienes con la vacante, explicándote el porqué.

---

## 🚀 ¿Cómo funciona el sistema?

El proyecto está dividido en un flujo de 3 pasos:

1. **Recolección de Datos (PostgreSQL):** Las ofertas de trabajo se almacenan en una base de datos relacional.
2. **Análisis con Inteligencia Artificial (Backend Python/FastAPI):** Cuando solicitas analizar una oferta, el Backend toma tu perfil/CV, toma la descripción del puesto y le pide a la IA que evalúe qué tan buen candidato eres, devolviendo un puntaje (0-100%) y una justificación.
3. **Gestión Visual (Frontend React):** Todo se muestra en un tablero Kanban interactivo. Las ofertas se mueven automáticamente de "Nuevas" a "Analizadas por IA" o "Postuladas".

---

## 🛠️ Tecnologías Utilizadas

### Frontend
* **React & Next.js** (o Vite)
* **TypeScript** para un código seguro.
* **Tailwind CSS** para un diseño moderno, responsivo y modo oscuro.
* **Lucide React** para la iconografía.

### Backend & Base de Datos
* **Python** con **FastAPI** para una API ultrarrápida.
* **PostgreSQL** como base de datos principal.
* **Uvicorn** como servidor ASGI.
* **Integración de IA** para el procesamiento del lenguaje natural.

---

---
## ⚙️ Configurar la Base de Datos (PostgreSQL)
Asegúrate de tener PostgreSQL instalado y ejecutándose. Deberás crear una base de datos y tener tus credenciales a la mano (usuario, contraseña, host, puerto).

## ⚙️ Levantar el Backend (API de Python)
Abre una terminal y navega a la carpeta del backend:
cd backend
Instala las dependencias necesarias usando el archivo requirements.txt
pip install -r requirements.txt
Crea un archivo .env en la carpeta backend con tus credenciales:
## ⚙️ Arranca el servidor backend:
uvicorn main:app --reload
http://localhost:8000/docs 


## ⚙️ Arranca el servidor frontend:
npm run dev
http://localhost:3000/

## ⚙️ Cómo instalar y arrancar el proyecto paso a paso
Si quieres correr este proyecto en tu máquina local, sigue estos pasos:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/UNPROGRAMADORMAS-6b/JobRadar_AI.git](https://github.com/UNPROGRAMADORMAS-6b/JobRadar_AI.git)
cd JobRadar_AI```

