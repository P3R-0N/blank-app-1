import streamlit as st
import pandas as pd
import altair as alt


# Função para carregar e limpar os dados
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            # Lê o arquivo CSV
            data = pd.read_csv(uploaded_file)

            # Normaliza os nomes das colunas (remove espaços, ajusta capitalização)
            data.columns = [col.strip().replace(" ", "_").capitalize() for col in data.columns]

            # Colunas necessárias
            required_columns = ['Data/hora', 'Consumo_kwh', 'Custo_total']

            # Verifica se as colunas estão presentes
            if not set(required_columns).issubset(data.columns):
                st.error(f"O arquivo não contém todas as colunas necessárias: {', '.join(required_columns)}.")
                return None

            # Filtra apenas as colunas necessárias
            data = data[required_columns]

            # Converte 'Data/hora' para datetime
            data['Data/hora'] = pd.to_datetime(data['Data/hora'], errors='coerce')

            # Converte 'Consumo_kwh' e 'Custo_total' para numérico
            data['Consumo_kwh'] = pd.to_numeric(data['Consumo_kwh'], errors='coerce')
            data['Custo_total'] = pd.to_numeric(data['Custo_total'], errors='coerce')

            # Remove linhas com valores ausentes nas colunas críticas
            data = data.dropna(subset=['Data/hora', 'Consumo_kwh', 'Custo_total'])

            return data
        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar carregar os dados: {e}")
            return None
    return None


# Função para exibir dados filtrados
def display_filtered_data(data, start_date, end_date):
    filtered_data = data[
        (data['Data/hora'] >= pd.to_datetime(start_date)) & (data['Data/hora'] <= pd.to_datetime(end_date))]
    return filtered_data


# Função para mostrar o gráfico de consumo total por dia
def plot_consumo_por_dia(data):
    data['Dia'] = data['Data/hora'].dt.date
    consumo_diario = data.groupby('Dia')['Consumo_kwh'].sum()
    dia_maior_consumo = consumo_diario.idxmax()

    chart = alt.Chart(consumo_diario.reset_index()).mark_bar().encode(
        x='Dia:T',
        y='Consumo_kwh:Q'
    ).properties(width=800, height=400)

    st.altair_chart(chart, use_container_width=True)
    st.markdown(f"**Dia com maior consumo**: {dia_maior_consumo}")


# Função para mostrar o gráfico de consumo médio por hora
def plot_consumo_horario_medio(data):
    data['Hora'] = data['Data/hora'].dt.hour
    consumo_horario = data.groupby('Hora')['Consumo_kwh'].mean()

    chart = alt.Chart(consumo_horario.reset_index()).mark_line().encode(
        x='Hora:O',
        y='Consumo_kwh:Q'
    ).properties(width=800, height=400)

    st.altair_chart(chart, use_container_width=True)


# Função para mostrar a distribuição de consumo
def plot_distribuicao_consumo(data):
    data['Hora'] = data['Data/hora'].dt.hour
    pico_consumo = data[data['Hora'].between(18, 23)]['Consumo_kwh'].sum()
    noturno_consumo = data[data['Hora'].between(0, 5)]['Consumo_kwh'].sum()
    outros_consumo = data[~data['Hora'].between(0, 5)].loc[~data['Hora'].between(18, 23), 'Consumo_kwh'].sum()

    categorias = ['Pico (18h-23h)', 'Noturno (0h-5h)', 'Outros']
    valores = [pico_consumo, noturno_consumo, outros_consumo]

    chart = alt.Chart(pd.DataFrame({'Categoria': categorias, 'Consumo (kWh)': valores})).mark_bar().encode(
        x='Categoria:O',
        y='Consumo (kWh):Q'
    ).properties(width=800, height=400)

    st.altair_chart(chart, use_container_width=True)


# Função principal
def main():
    st.set_page_config(page_title="Analisador de Consumo de Energia", page_icon="🔌", layout="wide")

    st.title("Analisador de Consumo de Energia Residencial")

    # Upload do arquivo CSV
    uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type=["csv"])

    if uploaded_file is not None:
        data = load_data(uploaded_file)

        if data is not None:
            # Abas para navegação
            tab1, tab2, tab3 = st.tabs(["Visão Geral", "Gráficos", "Análise de Consumo"])

            with tab1:
                st.header("Resumo dos Dados")
                st.write("Aqui estão as primeiras linhas dos dados carregados:")
                st.dataframe(data.head())

                # Filtro por data
                start_date = st.date_input("Selecione a data de início", data['Data/hora'].min().date())
                end_date = st.date_input("Selecione a data de fim", data['Data/hora'].max().date())

                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)

                # Filtra os dados
                filtered_data = display_filtered_data(data, start_date, end_date)

                # Consumo total e Custo total
                total_consumo = filtered_data['Consumo_kwh'].sum()
                total_custo = filtered_data['Custo_total'].sum()

                st.write(f"Consumo total no período selecionado: {total_consumo:.2f} kWh")
                st.write(f"Custo total no período selecionado: R${total_custo:.2f}")

            with tab2:
                st.header("Gráficos de Consumo")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Consumo Total por Dia")
                    plot_consumo_por_dia(data)

                with col2:
                    st.subheader("Consumo Médio por Hora")
                    plot_consumo_horario_medio(data)

            with tab3:
                st.header("Análise de Consumo")

                # Comparação entre consumo diário médio e o consumo do período
                st.subheader("Distribuição do Consumo de Energia")
                plot_distribuicao_consumo(data)


if __name__ == "__main__":
    main()
