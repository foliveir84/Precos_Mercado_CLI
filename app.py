import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from ui_style import apply_custom_style

# Configuração da Página
st.set_page_config(
    page_title="PharmaMarketPrice",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar Estilo Visual
apply_custom_style()

@st.cache_data
def load_and_process_data(file_val, file_uni, n_pharmacies):
    try:
        df_val = pd.read_excel(file_val)
        df_uni = pd.read_excel(file_uni)
    except Exception as e:
        return None, f"Erro ao ler ficheiros: {e}", None

    # --- LÓGICA DE COLUNAS (Índices Fixos: 3 e 8) ---
    try:
        col_cod = df_val.columns[0]
        col_prod = df_val.columns[1]
        col_farm_val = df_val.columns[3]
        col_reg_val = df_val.columns[8]
        
        col_farm_uni = df_uni.columns[3]
        col_reg_uni = df_uni.columns[8]
    except IndexError:
        return None, "Estrutura do ficheiro inválida. Verifique os índices das colunas.", None

    cols_info = {"Farmácia": col_farm_val, "Região": col_reg_val}

    # Limpeza e Merge
    df_val_clean = df_val[[col_cod, col_prod, col_farm_val, col_reg_val]].copy()
    df_val_clean.columns = ['Cód', 'Produto', 'Farm_Val', 'Reg_Val']
    
    df_uni_clean = df_uni[[col_cod, col_farm_uni, col_reg_uni]].copy()
    df_uni_clean.columns = ['Cód', 'Farm_Qtd', 'Reg_Qtd']

    df_merged = pd.merge(df_val_clean, df_uni_clean, on='Cód')
    
    # Remover Totais e Converter Numéricos
    df_merged = df_merged[~df_merged['Cód'].astype(str).str.contains('Totais', case=False, na=False)]
    
    cols_num = ['Farm_Val', 'Reg_Val', 'Farm_Qtd', 'Reg_Qtd']
    for col in cols_num:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)

    # --- CÁLCULOS DE ENGENHARIA REVERSA ---
    
    # 1. Totais da Região (Extrapolação)
    total_val_region = df_merged['Reg_Val'] * n_pharmacies
    total_qty_region = df_merged['Reg_Qtd'] * n_pharmacies
    
    # 2. Isolar "Outras Farmácias"
    others_val = total_val_region - df_merged['Farm_Val']
    others_qty = total_qty_region - df_merged['Farm_Qtd']
    
    # Média de unidades vendidas POR FARMÁCIA CONCORRENTE
    n_others = max(1, n_pharmacies - 1)
    df_merged['Avg_Unit_Others'] = (others_qty / n_others).round(0).clip(lower=0)

    # 3. Quota de Mercado (Market Share)
    df_merged['Market_Share_Qty'] = np.where(
        total_qty_region > 0.001,
        (df_merged['Farm_Qtd'] / total_qty_region) * 100,
        0
    )

    # 4. PVPs
    df_merged['My_PVP'] = np.where(df_merged['Farm_Qtd'] > 0, df_merged['Farm_Val'] / df_merged['Farm_Qtd'], 0)
    
    others_qty_safe = others_qty.apply(lambda x: x if x > 0.1 else 0)
    df_merged['Others_PVP'] = np.where(others_qty_safe > 0, others_val / others_qty_safe, 0)
    
    # 5. Diferencial
    df_merged['Diff_Percent'] = np.where(
        (df_merged['Others_PVP'] > 0) & (df_merged['My_PVP'] > 0),
        ((df_merged['My_PVP'] - df_merged['Others_PVP']) / df_merged['Others_PVP']) * 100,
        0
    )

    # 6. Matriz de Poder (Position)
    conditions = [
        (df_merged['Market_Share_Qty'] >= 40), 
        (df_merged['Market_Share_Qty'] >= 15) & (df_merged['Market_Share_Qty'] < 40),
        (df_merged['Market_Share_Qty'] < 15)
    ]
    choices = ['Dominante 👑', 'Competitivo ⚔️', 'Seguidor 🏃']
    df_merged['Position'] = np.select(conditions, choices, default='Seguidor 🏃')

    # Preço Sugerido (Estratégia: Alinhar com o Mercado)
    df_merged['Suggested_Price'] = df_merged['Others_PVP']

    # 7. Oportunidade Financeira (Dinheiro na Mesa)
    # Quanto perco por estar abaixo do preço de mercado
    df_merged['Opportunity_Eur'] = np.where(
        df_merged['My_PVP'] < df_merged['Others_PVP'],
        (df_merged['Others_PVP'] - df_merged['My_PVP']) * df_merged['Farm_Qtd'],
        0
    )

    return df_merged, None, cols_info

def main():
    # --- Logo na Sidebar ---
    if os.path.exists("Logo.png"):
        st.sidebar.image("Logo.png", width='stretch')

    # --- Header Principal ---
    st.title("PharmaMarketPrice")
    st.markdown("#### Intelligence in Pricing")
    
    # --- ONBOARDING / GUIA ---
    with st.expander("📘 Guia Rápido: Como ler este Dashboard", expanded=True):
        st.markdown("""
        <div class="glass-card">
            <h3>👋 Bem-vindo ao Painel de Preços</h3>
            <p style="color: #bbb; line-height: 1.6;">
                Esta ferramenta utiliza engenharia reversa para calcular o PVP real da concorrência com base nos seus dados e na média da região.
            </p>
            <div style="margin-top: 20px; display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; min-width: 200px;">
                    <span style="font-size: 1.2rem;">🔵</span> <b>Oportunidade</b><br>
                    <span style="font-size: 0.8rem; color: #888;">Bolas Azuis: Mais barato que o mercado.</span>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; min-width: 200px;">
                    <span style="font-size: 1.2rem;">🔴</span> <b>Risco</b><br>
                    <span style="font-size: 0.8rem; color: #888;">Bolas Vermelhas: Mais caro que o mercado.</span>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; min-width: 200px;">
                    <span style="font-size: 1.2rem;">👑</span> <b>Matriz de Poder</b><br>
                    <span style="font-size: 0.8rem; color: #888;">Domínio (>40%) vs Seguidores (<15%).</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Configuração")
        n_pharmacies = st.slider("Nº Farmácias na Região", 2, 20, 6)
        
        st.divider()
        st.subheader("📂 Carregar Dados")
        file_val = st.file_uploader("Ficheiro Valor (€)", type=['xlsx'])
        file_uni = st.file_uploader("Ficheiro Unidades (Qtd)", type=['xlsx'])

        st.divider()
        st.subheader("💡 Simulador de Aumento")
        st.markdown("Se aumentar X€ nos produtos visualizados, quanto ganho?")
        sim_increase = st.number_input("Aumento Unitário (€)", value=0.15, step=0.05, format="%.2f")

    if file_val and file_uni:
        df, error, cols_info = load_and_process_data(file_val, file_uni, n_pharmacies)
        
        if error:
            st.error(error)
            return
        
        # Filtro Base: Remover produtos sem vendas
        df = df[df['Farm_Qtd'] > 0].copy()

        st.divider()
        
        # --- ÁREA DE FILTROS ---
        st.markdown("##### 🔎 Filtrar Produtos")
        prod_options = df.sort_values(by='Farm_Qtd', ascending=False)['Produto'].unique()
        selected_prods = st.multiselect(
            "Escolha produtos para simular ou deixe vazio para ver todos:",
            options=prod_options,
            default=[]
        )
        
        # Aplicação do Filtro
        if selected_prods:
            df_filtered = df[df['Produto'].isin(selected_prods)].copy()
            filter_label = "Seleção"
        else:
            df_filtered = df.copy()
            filter_label = "Total"

        # --- CÁLCULO DE KPIS (SEMPRE SOBRE O FILTRO ATUAL) ---
        if not df_filtered.empty:
            avg_my_pvp = df_filtered[df_filtered['My_PVP'] > 0]['My_PVP'].mean()
            avg_mkt_pvp = df_filtered[df_filtered['Others_PVP'] > 0]['Others_PVP'].mean()
            
            # KPI 1: Dinheiro na Mesa (Gap para o Mercado)
            total_opp = df_filtered['Opportunity_Eur'].sum()
            
            # KPI 2: Simulação Manual (Impacto Direto na Seleção)
            # Soma das vendas dos produtos filtrados * aumento unitário
            total_sales_selection = df_filtered['Farm_Qtd'].sum()
            sim_gain = total_sales_selection * sim_increase
            
            delta_pvp = avg_my_pvp - avg_mkt_pvp
        else:
            avg_my_pvp, avg_mkt_pvp, total_opp, sim_gain, delta_pvp = 0, 0, 0, 0, 0
            
        # Tratar NaNs
        avg_my_pvp = 0 if np.isnan(avg_my_pvp) else avg_my_pvp
        avg_mkt_pvp = 0 if np.isnan(avg_mkt_pvp) else avg_mkt_pvp

        # --- EXIBIÇÃO DE KPIS EM CARDS ---
        st.markdown(f"""
        <div class="glass-card" style="padding: 20px;">
            <h4 style="margin-bottom: 20px;">📊 Indicadores Chave ({filter_label})</h4>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
                <div style="text-align: center;">
                    <span style="font-size: 0.9rem; color: #aaa;">Meu PVP Médio</span><br>
                    <span style="font-size: 1.5rem; font-weight: bold; color: white;">{avg_my_pvp:.2f}€</span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 0.9rem; color: #aaa;">PVP Mercado</span><br>
                    <span style="font-size: 1.5rem; font-weight: bold; color: { '#ff4b4b' if delta_pvp > 0 else '#00cc96' };">
                        {avg_mkt_pvp:.2f}€
                    </span>
                    <br><span style="font-size: 0.8rem;">Delta: {delta_pvp:+.2f}€</span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 0.9rem; color: #aaa;">Oportunidade Real</span><br>
                    <span style="font-size: 1.5rem; font-weight: bold; color: #00e5ff;">{total_opp:.2f}€</span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 0.9rem; color: #aaa;">Simulação (+{sim_increase:.2f}€)</span><br>
                    <span style="font-size: 1.5rem; font-weight: bold; color: #d900ff;">+{sim_gain:.2f}€</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # --- VISUALIZAÇÕES ---
        tab1, tab2, tab3 = st.tabs(["💰 Preço vs Oportunidade", "👑 Matriz de Poder", "📋 Dados Detalhados"])

        with tab1:
            if not df_filtered.empty:
                st.markdown("#### Onde estou barato (Azul) ou caro (Vermelho)?")
                fig = px.scatter(
                    df_filtered, x="Others_PVP", y="My_PVP", size="Farm_Qtd", color="Diff_Percent",
                    color_continuous_scale="RdBu_r", range_color=[-30, 30],
                    labels={
                        "Others_PVP": "Preço Mercado (€)", 
                        "My_PVP": "Meu Preço (€)", 
                        "Diff_Percent": "Diferença (%)", 
                        "Farm_Qtd": "Vendas (Qtd)",
                        "Opportunity_Eur": "Oportunidade (€)"
                    },
                    hover_name="Produto", hover_data={'Opportunity_Eur':':.2f', 'Diff_Percent':':.1f%'}
                )
                # Linha de Igualdade
                max_val = max(df_filtered['My_PVP'].max(), df_filtered['Others_PVP'].max())
                fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="Gray", dash="dash"))
                
                # Ajuste para tema escuro
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#f0f2f6"),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Sem dados para exibir.")

        with tab2:
            if not df_filtered.empty:
                st.markdown("#### Cruzamento: Minha Força vs Meu Preço")
                st.caption("Quadrante Ideal: **Verde (Dominante)** mas abaixo da linha zero (Barato) -> **SUBIR PREÇO**")
                
                fig_mat = px.scatter(
                    df_filtered, x="Market_Share_Qty", y="Diff_Percent", size="Farm_Qtd", color="Position",
                    color_discrete_map={'Dominante 👑': '#00CC96', 'Competitivo ⚔️': '#636EFA', 'Seguidor 🏃': '#EF553B'},
                    labels={
                        "Market_Share_Qty": "Minha Quota (%)", 
                        "Diff_Percent": "Diferença Preço (%)",
                        "My_PVP": "Meu Preço (€)",
                        "Others_PVP": "Preço Mercado (€)",
                        "Farm_Qtd": "Vendas (Qtd)",
                        "Position": "Posição"
                    },
                    hover_name="Produto", hover_data={'My_PVP':':.2f', 'Others_PVP':':.2f'}
                )
                fig_mat.add_hline(y=0, line_dash="solid", line_color="gray")
                fig_mat.add_vline(x=100/n_pharmacies, line_dash="dot", line_color="gray", annotation_text="Quota Média")
                
                # Ajuste para tema escuro
                fig_mat.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#f0f2f6"),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                )
                st.plotly_chart(fig_mat, use_container_width=True)
            else:
                st.warning("Sem dados para exibir.")

        with tab3:
            if not df_filtered.empty:
                st.markdown("#### Tabela Detalhada")
                
                col_map = {
                    'Produto': 'Produto',
                    'Farm_Qtd': 'Vendas (Qtd)',
                    'Avg_Unit_Others': 'Venda Média/Rival',
                    'Market_Share_Qty': 'Quota (%)',
                    'My_PVP': 'Meu PVP',
                    'Others_PVP': 'PVP Mercado',
                    'Diff_Percent': 'Dif Preço (%)',
                    'Position': 'Posição',
                    'Suggested_Price': 'Preço Sugerido',
                    'Opportunity_Eur': 'Oportunidade (€)'
                }
                
                # Filtrar colunas existentes e renomear
                cols_final = [c for c in col_map.keys() if c in df_filtered.columns]
                df_show = df_filtered[cols_final].rename(columns=col_map).sort_values(by='Vendas (Qtd)', ascending=False)

                st.dataframe(
                    df_show.style.format({
                        'Vendas (Qtd)': '{:.0f}',
                        'Venda Média/Rival': '{:.0f}',
                        'Quota (%)': '{:.1f}%',
                        'Meu PVP': '{:.2f}€',
                        'PVP Mercado': '{:.2f}€',
                        'Dif Preço (%)': '{:.1f}%',
                        'Preço Sugerido': '{:.2f}€',
                        'Oportunidade (€)': '{:.2f}€'
                    }).background_gradient(subset=['Dif Preço (%)'], cmap='RdBu_r', vmin=-30, vmax=30),
                    use_container_width=True
                )
            else:
                st.warning("Sem dados para exibir.")

    else:
        # Estado Inicial (Sem ficheiros)
        st.markdown("""
        <div class="glass-card" style="text-align: center; margin-top: 50px;">
            <h3>📂 Aguardando Dados</h3>
            <p>Comece por carregar os ficheiros <b>Valor (€)</b> e <b>Unidades (Qtd)</b> na barra lateral.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
