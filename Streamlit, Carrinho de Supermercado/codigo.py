import streamlit as st

st.set_page_config(
    page_title="Calculadora de Supermercado",
    page_icon="🛒",
    layout="centered"
)

st.title("Calculadora de Compras de Supermercado 🧮")
st.write("Insira os itens, informe o valor pago e calcule o troco.")

precos_itens = {
    "Arroz (5kg)": 25.90,
    "Feijão (1kg)": 8.50,
    "Leite (1L)": 4.90,
    "Café (500g)": 14.20,
    "Açúcar (1kg)": 4.30,
    "Óleo de Soja (900ml)": 6.80,
    "Pão de Forma": 7.50
}

def calcular_preco_total(itens_selecionados):
    total = sum(precos_itens[item] for item in itens_selecionados)
    return total
itens_selecionados = st.multiselect(
    label="Selecione os itens do supermercado:",
    options=list(precos_itens.keys())
)


if itens_selecionados:
    st.subheader("Itens Selecionados:")
    for item in itens_selecionados:
        st.write(f"- {item}: R$ {precos_itens[item]:.2f}")
    
    total_compra = calcular_preco_total(itens_selecionados)
    
    st.divider()
    st.metric(label="Total da Compra", value=f"R$ {total_compra:.2f}")
    st.divider()
    
    st.subheader("Pagamento e Troco")
    
    col1, col2 = st.columns(2)
    with col1:
        valor_pago = st.number_input("Dinheiro entregue (R$)", value=0.0, step=1.0)
    with col2:
        st.write("")
        st.write("")
        botao_calcular = st.button("Calcular Troco", type="primary")
        
    if botao_calcular:
        if valor_pago >= total_compra:
            troco = valor_pago - total_compra
            st.success(f"**Troco a devolver:** R$ {troco:.2f}")
        else:
            st.error("Erro: O valor pago é menor que o total da compra.")
else:
    st.info("Nenhum item selecionado. Marque os produtos acima para ver o valor total.")