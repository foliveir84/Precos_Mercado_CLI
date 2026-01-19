import pandas as pd
import numpy as np

def calculate_market_pvp(n_pharmacies=6):
    print(f"--- Iniciar Análise de PVP de Mercado (N={n_pharmacies}) ---")
    
    # 1. Carregar Dados
    # Usar dtype object para preservar códigos com zeros à esquerda se necessário, mas aqui parece numérico
    df_val = pd.read_excel('ValorVendido.xlsx')
    df_uni = pd.read_excel('UnidadesVendidas.xlsx')

    # 2. Limpeza e Validação Preliminar
    # Garantir que estamos a comparar os mesmos produtos. Vamos fazer merge pelo 'Cód'.
    # Sufixos: _val (faturação), _uni (quantidade)
    df_merged = pd.merge(
        df_val[['Cód', 'Produto', 'Farmácia Nov/2025', 'Região Nov/2025']],
        df_uni[['Cód', 'Farmácia Nov/2025', 'Região Nov/2025']],
        on='Cód',
        suffixes=('_val', '_uni')
    )

    print(f"Total de produtos analisados: {len(df_merged)}")

    # 3. Implementação da Lógica Matemática
    
    # A. Extrair Variáveis
    my_val = df_merged['Farmácia Nov/2025_val']    # A minha Faturação
    avg_val_region = df_merged['Região Nov/2025_val'] # Média de Faturação da Região
    
    my_qty = df_merged['Farmácia Nov/2025_uni']    # As minhas Unidades
    avg_qty_region = df_merged['Região Nov/2025_uni'] # Média de Unidades da Região

    # B. Calcular Totais da Região (Extrapolação Inversa)
    # Total Região = Média * N
    total_val_region = avg_val_region * n_pharmacies
    total_qty_region = avg_qty_region * n_pharmacies

    # C. Isolar o "Resto do Mercado" (Outras Farmácias)
    # Outros = Total Região - Eu
    others_val = total_val_region - my_val
    others_qty = total_qty_region - my_qty

    # D. Calcular PVPs (Preço Médio Unitário)
    # PVP = Faturação / Quantidade
    
    # O meu PVP (Validar)
    # Usamos np.where para evitar divisão por zero
    df_merged['My_PVP'] = np.where(my_qty > 0, my_val / my_qty, 0)
    
    # O PVP do Mercado (Excluindo-me)
    # Nota: others_qty pode ser 0 ou muito próximo de 0 devido a arredondamentos dos ficheiros originais
    # Vamos arredondar others_qty para evitar float artifacts perto de zero
    others_qty = others_qty.round(4)
    df_merged['Others_PVP'] = np.where(others_qty > 0, others_val / others_qty, 0)

    # 4. Enriquecer Análise
    # Diferença Percentual: (Meu PVP - PVP Mercado) / PVP Mercado
    df_merged['Price_Diff_%'] = np.where(
        df_merged['Others_PVP'] > 0,
        ((df_merged['My_PVP'] - df_merged['Others_PVP']) / df_merged['Others_PVP']) * 100,
        0
    )

    # Colunas de Controlo (Debug da Lógica)
    df_merged['Others_Qty_Est'] = others_qty
    df_merged['Others_Val_Est'] = others_val

    # 5. Formatar e Apresentar Resultados
    # Reordenar colunas para leitura fácil
    cols = [
        'Cód', 'Produto', 
        'My_PVP', 'Others_PVP', 'Price_Diff_%',
        'Farmácia Nov/2025_uni', 'Others_Qty_Est'
    ]
    
    final_df = df_merged[cols].copy()
    
    # Arredondamentos para display
    final_df['My_PVP'] = final_df['My_PVP'].round(2)
    final_df['Others_PVP'] = final_df['Others_PVP'].round(2)
    final_df['Price_Diff_%'] = final_df['Price_Diff_%'].round(1)
    final_df['Others_Qty_Est'] = final_df['Others_Qty_Est'].round(1)

    print("\n--- Resultados (Top 10 Produtos por Faturação da Farmácia) ---")
    # Ordenar pelos que mais vendemos para ver onde temos impacto
    print(final_df.sort_values(by='Farmácia Nov/2025_uni', ascending=False).head(10).to_string(index=False))

    print("\n--- Análise Crítica de Discrepâncias ---")
    # Verificar casos onde vendemos muito mas o mercado tem preço muito diferente
    discrepancies = final_df[
        (final_df['Farmácia Nov/2025_uni'] > 5) & 
        (abs(final_df['Price_Diff_%']) > 10)
    ]
    if not discrepancies.empty:
        print("Produtos com >5 unidades vendidas e diferença de preço > 10%:")
        print(discrepancies.to_string(index=False))
    else:
        print("Nenhuma discrepância significativa encontrada em produtos de alto volume.")

    # Guardar Excel para o user validar
    output_file = 'Analise_PVP_Mercado.xlsx'
    final_df.to_excel(output_file, index=False)
    print(f"\nAnálise completa guardada em: {output_file}")

if __name__ == "__main__":
    calculate_market_pvp(n_pharmacies=6)
