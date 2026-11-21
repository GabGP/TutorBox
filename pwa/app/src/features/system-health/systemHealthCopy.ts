/** Spanish explanations on each card: what the reading is, its normal range, and what to do when it is high. */
export const HEALTH_COPY = {
  cpu: 'Uso de los seis núcleos del procesador. Sube al preparar preguntas, y eso es normal. Si se queda por encima de 85 % mucho rato, la voz y el servidor van lentos: cierra otras aplicaciones.',
  gpu: 'Trabajo de la GPU, donde corre el modelo de preguntas. Es normal que esté alta mientras se genera una pregunta; no hay alerta para esto.',
  memory:
    'RAM compartida por la CPU y la GPU. Lo libre es lo que pueden usar los modelos y la voz. Con menos de 1,5 GB, cierra otras aplicaciones o sal del modo Tutor: el modelo de preguntas necesita unos 2,4 GB para caber entero en la GPU.',
  temperatures:
    'Temperatura de cada zona del chip. Por encima de 80 °C revisa el ventilador y que la caja tenga aire; cerca de 95 °C el Jetson baja su velocidad para protegerse.',
  power:
    'Potencia que consume la placa ahora. VDD_IN es todo lo que entra por la fuente; los demás son sus partes.',
  disk: 'Espacio libre donde está la base de datos. Por debajo de 10 % conviene borrar copias o archivos viejos; por debajo de 5 % es urgente.',
  models:
    'Modelos de lenguaje que Ollama tiene cargados. 100 % de GPU quiere decir que caben enteros en la GPU; menos significa que parte corre en la CPU y va mucho más lento.',
  voices:
    'Motores de voz con sus pesos en memoria. Se cargan solos cuando hace falta hablar, así que liberarlos no pierde nada.',
  release:
    'Descarga los modelos y voces que no se usan ahora y vuelve a cargar solo lo que pide el modo actual.',
} as const;
