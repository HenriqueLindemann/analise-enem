# live_input

Componente local (bi-directional component do Streamlit) que renderiza um
campo de texto que devolve o valor a cada digitação, com debounce.

## Proveniência

Adaptado do [`streamlit-keyup` 0.3.0](https://github.com/blackary/streamlit-keyup)
de Zachary Blackwood (licença MIT, preserved em `LICENSE`). O
`streamlit-component-lib.js` é o trecho mínimo de API do Streamlit divulgado
no [fórum oficial](https://discuss.streamlit.io/t/code-snippet-create-components-without-any-frontend-tooling-no-react-babel-webpack-etc/13064)
(crédito no cabeçalho do arquivo).

## Por que uma cópia local

- Remove a dependência externa do `requirements.txt` (o app é pequeno e o
  componente é minúsculo).
- Mantém o estado da resposta em `session_state[key]` (sem o prefixo
  `st_keyup_` do original), que é a chave que o resto do app e os testes
  usam.
- Não substitui o rascunho nem a seleção do usuário quando o Python devolve
  o valor (o original reescrevia o campo a cada rerun).
- Faz flush imediato em `blur` e `Enter`, além do debounce.

## Mudanças em relação ao original

`main.js` só inicializa o campo na primeira renderização; as seguintes
apenas redimensionam o iframe e reaplicam o tema. `__init__.py` é um
wrapper que espelha o valor do componente em `st.session_state[key]`.
