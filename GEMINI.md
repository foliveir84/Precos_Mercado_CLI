# Market Price Intelligence - Dashboard de Competitividade

Este projeto é uma ferramenta avançada de análise de mercado para o setor farmacêutico. O seu objetivo é permitir que uma farmácia identifique oportunidades de margem e ajuste de preços através da comparação direta com a média da sua região, utilizando técnicas de engenharia reversa de dados.

## 🚀 Funcionalidades Principais

*   **Engenharia Reversa de Preços:** Isola matematicamente os dados da própria farmácia da média regional para descobrir o PVP real praticado pela concorrência.
*   **KPIs Dinâmicos:**
    *   **Oportunidade Real:** Cálculo do ganho financeiro imediato ao igualar o preço de mercado em produtos onde a farmácia é mais barata.
    *   **Simulador de Impacto:** Permite prever o lucro extra ao aplicar aumentos fixos na seleção de produtos atual.
*   **Visualizações Estratégicas:**
    *   **Gráfico Preço vs. Mercado:** Identificação visual de produtos "Baratos" (Oportunidade) vs "Caros" (Risco).
    *   **Matriz de Poder (Quota vs. Preço):** Classifica produtos como Dominantes, Competitivos ou Seguidores.
*   **Filtros Inteligentes:** Seleção múltipla de produtos com atualização instantânea de todas as métricas e gráficos.

## 🧪 Lógica Matemática (O "Cérebro")

A ferramenta baseia-se na desconstrução da média aritmética da região para encontrar o comportamento dos vizinhos.

Seja **N** o número de farmácias na amostra da região:
1.  **Total Região:** `Média_Região * N`
2.  **Total Concorrência:** `Total_Região - Valor_Minha_Farmácia`
3.  **PVP Concorrência:** `Faturação_Concorrência / Unidades_Concorrência`

### Classificações de Poder:
*   **Dominante 👑:** Quota de Mercado > 40%. A farmácia tem poder para definir o preço.
*   **Competitivo ⚔️:** Quota entre 15% e 40%. O preço deve estar alinhado com o mercado.
*   **Seguidor 🏃:** Quota < 15%. A farmácia tem pouco impacto; deve seguir o preço de mercado para não perder vendas.

## 🛠️ Tecnologias Utilizadas

*   **Python 3.x**
*   **Streamlit:** Interface de utilizador (Dashboard).
*   **Pandas:** Processamento e limpeza de dados.
*   **Plotly:** Gráficos interativos.
*   **Openpyxl:** Leitura de ficheiros Excel.

## 📁 Estrutura do Projeto

*   `app.py`: Aplicação principal Streamlit.
*   `ValorVendido.xlsx`: Dados de faturação (Entrada).
*   `UnidadesVendidas.xlsx`: Dados de quantidades (Entrada).
*   `requirements.txt`: Dependências do sistema.
*   `calculate_pvp.py`: Script utilitário para validação rápida via CLI.

## 📖 Como Utilizar

1.  Instale as dependências: `pip install -r requirements.txt`
2.  Execute o dashboard: `streamlit run app.py`
3.  Na barra lateral:
    *   Ajuste o número de farmácias da região (ex: 6).
    *   Faça upload dos dois ficheiros Excel.
4.  No ecrã principal, utilize o filtro de produtos para focar a análise no seu "Top de Vendas".

---
*Desenvolvido como uma ferramenta de apoio à decisão estratégica farmacêutica.*
