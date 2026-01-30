# sperm_ai - Web UI para análise de espermatozoides (local)

Instruções rápidas para rodar localmente:

1. Clone/baixe a pasta com os arquivos fornecidos aqui em `sperm_ai/`.

2. Crie um ambiente virtual e ative:
   - Linux/macOS:
     python -m venv venv
     source venv/bin/activate
   - Windows:
     python -m venv venv
     venv\Scripts\activate

3. Instale dependências:
   pip install -r requirements.txt

4. Coloque seus pesos YOLOv8 em `models/yolo/` (ex: `models/yolo/yolov8n.pt`).
   - Se ainda não treinou, pode baixar `yolov8n.pt` do repositório Ultralytics (ou usar um peso inicial).
   - Ajuste o caminho em `app.py` (parâmetro "weights") se necessário.

5. Execute o servidor Flask:
   python app.py

6. Abra no navegador:
   http://127.0.0.1:5000

7. Suba um vídeo ou imagem, ajuste parâmetros (µm/pixel, fps, volume da gota) e clique em "Analisar".

Observações:
- Para resultados corretos em µm/s, configure `microns_per_pixel` medido com micro-régua.
- `drop_volume_ul` é a estimativa do volume (µL) do campo analisado; alta precisão não é necessária no início.
- O processamento é bloqueante no endpoint `/analyze`. Para uso intensivo, recomendamos adaptar para job queue (celery / rq).
- Ajuste thresholds (velocidade, linearidade) no código se quiser calibrar para sua espécie/condições.
- Talvez seja necessário ajustar parâmetros do DeepSORT dependendo do comportamento das detecções.

Se quiser, eu adapto:
- Rodar processamento assíncrono com barra de progresso real.
- Fazer inferência em frames ao vivo (webcam/microscópio adaptado).
- Exportar relatório em PDF.