PAINEL IBGE — NÚMEROS QUE FALAM

1. Abra o terminal na pasta painel (a que contém painel.py).
2. Instale as bibliotecas:
   py -m pip install -r requirements.txt
3. Execute:
   py -m streamlit run painel.py

Se seu computador usar o comando python em vez de py:
   python -m pip install -r requirements.txt
   python -m streamlit run painel.py

O painel.py abre o menu com cinco páginas, na pasta paginas/:
- desocupacao.py
- estrutura_etaria.py
- alfabetizacao.py
- dashboard_individual.py
- dashboard_rendimento_boxplot.py

As páginas não devem ser executadas separadamente. Alguns dados precisam de conexão
com a internet. A página de alfabetização usa dados ilustrativos.
