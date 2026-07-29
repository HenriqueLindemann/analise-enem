# Migração para 4.0.0

A versão 4 mantém os formatos de retorno de nota, theta e acertos. Duas
resoluções ambíguas foram removidas porque podiam calcular silenciosamente a
prova errada:

1. `MapeadorProvas.obter_codigo()` agora é estrito. Para manter deliberadamente
   o fallback para a primeira aplicação, passe `permitir_fallback=True`.
2. `SimuladorNota.calcular()` não escolhe mais a primeira prova encontrada e
   não presume a primeira aplicação quando só recebe uma cor. Informe
   `co_prova`, ou a combinação completa `cor_prova` + `tipo_aplicacao`.

Para LC, informe também `lingua="ingles"` ou `lingua="espanhol"`. Uma língua
não oferecida pelo caderno agora causa erro explícito.

Os CSVs de itens deixaram `microdados_limpos/` e agora são dados internos do
pacote em `src/tri_enem/data/itens/`. Código que não fornece caminho continua
funcionando fora da raiz do projeto. Um caminho externo explícito ainda é
aceito por `CalculadorTRI` e `SimuladorNota`.
