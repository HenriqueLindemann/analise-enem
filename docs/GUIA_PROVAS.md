# Guia de Provas do ENEM - Codigos por Cor e Aplicacao

## AVISO IMPORTANTE

Este mapeamento foi gerado por **inferencia estatistica** baseada no
numero de participantes por prova. **NAO foi validado manualmente**.

**Limitacoes:**
- A classificacao de cores pode estar incorreta
- 'Outras aplicacoes' mistura 2a chamada, PPL e provas adaptadas
- Anos antigos (pre-2016) tem menos metadados disponiveis

**Confiabilidade:**
- **1a Aplicacao**: ALTA (top 4 provas por participantes)
- **Outras**: BAIXA (requer validacao futura)

---

## Como usar o calculador

O calculador TRI **precisa do codigo correto da prova** para maxima precisao.
Se voce nao informar, ele usa a primeira prova disponivel, que pode nao ser a sua.

```python
from tri_enem import SimuladorNota

sim = SimuladorNota()

# COM codigo (recomendado se souber)
resultado = sim.calcular('MT', 2023, respostas, co_prova=1211)  # Azul

# SEM codigo (usa primeira prova - pode nao ser a sua)
resultado = sim.calcular('MT', 2023, respostas)
```

---

## ENEM 2024

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | VERDE | 1409 | 756,397 |
| MT | AMARELA | 1408 | 747,639 |
| MT | CINZA | 1410 | 747,330 |
| MT | AZUL | 1407 | 746,854 |
| CN | VERDE | 1421 | 756,397 |
| CN | AMARELA | 1420 | 747,639 |
| CN | CINZA | 1422 | 747,330 |
| CN | AZUL | 1419 | 746,854 |
| CH | VERDE | 1386 | 797,364 |
| CH | AZUL | 1383 | 788,173 |
| CH | BRANCA | 1385 | 787,903 |
| CH | AMARELA | 1384 | 787,563 |
| LC | VERDE | 1397 | 797,364 |
| LC | AZUL | 1395 | 788,173 |
| LC | BRANCA | 1398 | 787,903 |
| LC | AMARELA | 1396 | 787,563 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | VERDE | 1411 | 3,282 |
| MT | LARANJA | 1414 | 1,319 |
| MT | ROXA | 1415 | 1,225 |
| MT | VERDE | 1412 | 701 |
| MT | CINZA | 1366 | 64 |
| MT | AMARELA | 1364 | 59 |
| MT | AZUL | 1363 | 58 |
| MT | VERDE | 1365 | 53 |
| CN | VERDE | 1423 | 3,282 |
| CN | LARANJA | 1426 | 1,319 |
| CN | ROXA | 1427 | 1,225 |
| CN | VERDE | 1424 | 701 |
| CN | CINZA | 1375 | 64 |
| CN | AMARELA | 1374 | 59 |
| CN | AZUL | 1373 | 58 |
| CN | VERDE | 1376 | 53 |
| CH | VERDE | 1387 | 3,505 |
| CH | LARANJA | 1390 | 1,413 |
| CH | ROXA | 1391 | 1,289 |
| CH | VERDE | 1388 | 745 |
| LC | VERDE | 1399 | 3,505 |
| LC | LARANJA | 1402 | 1,413 |
| LC | ROXA | 1403 | 1,289 |
| LC | VERDE | 1400 | 745 |

</details>

---

## ENEM 2023

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | ROSA | 1213 | 674,819 |
| MT | CINZA | 1214 | 669,321 |
| MT | AMARELA | 1212 | 668,909 |
| MT | AZUL | 1211 | 668,204 |
| CN | ROSA | 1223 | 674,819 |
| CN | CINZA | 1224 | 669,321 |
| CN | AMARELA | 1222 | 668,909 |
| CN | AZUL | 1221 | 668,204 |
| CH | ROSA | 1194 | 707,167 |
| CH | BRANCA | 1193 | 701,519 |
| CH | AMARELA | 1192 | 701,475 |
| CH | AZUL | 1191 | 701,099 |
| LC | ROSA | 1203 | 707,168 |
| LC | BRANCA | 1204 | 701,518 |
| LC | AMARELA | 1202 | 701,475 |
| LC | AZUL | 1201 | 701,099 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | ROSA | 1215 | 3,319 |
| MT | CINZA | 1294 | 1,313 |
| MT | ROSA | 1293 | 1,301 |
| MT | AZUL | 1291 | 1,297 |
| MT | AMARELA | 1292 | 1,293 |
| MT | VERDE | 1219 | 1,212 |
| MT | LARANJA | 1218 | 673 |
| MT | ROSA | 1216 | 646 |
| MT | LARANJA | 1217 | 120 |
| CN | ROSA | 1225 | 3,319 |
| CN | CINZA | 1303 | 1,313 |
| CN | ROSA | 1304 | 1,301 |
| CN | AZUL | 1301 | 1,297 |
| CN | AMARELA | 1302 | 1,293 |
| CN | VERDE | 1229 | 1,212 |
| CN | LARANJA | 1228 | 673 |
| CN | ROSA | 1226 | 646 |
| CN | LARANJA | 1227 | 120 |
| CH | ROSA | 1195 | 3,471 |
| CH | BRANCA | 1273 | 1,295 |
| CH | AMARELA | 1272 | 1,290 |
| CH | AZUL | 1271 | 1,274 |
| CH | VERDE | 1199 | 1,273 |
| CH | ROSA | 1274 | 1,272 |
| CH | LARANJA | 1198 | 704 |
| CH | ROSA | 1196 | 679 |
| CH | LARANJA | 1197 | 125 |
| LC | ROSA | 1205 | 3,471 |
| LC | BRANCA | 1284 | 1,295 |
| LC | AMARELA | 1282 | 1,290 |
| LC | AZUL | 1281 | 1,274 |
| LC | VERDE | 1209 | 1,273 |
| LC | ROSA | 1283 | 1,272 |
| LC | LARANJA | 1208 | 704 |
| LC | ROSA | 1206 | 679 |
| LC | LARANJA | 1207 | 125 |

</details>

---

## ENEM 2022

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | CINZA | 1078 | 586,191 |
| MT | AZUL | 1075 | 578,780 |
| MT | ROSA | 1077 | 578,711 |
| MT | AMARELA | 1076 | 578,696 |
| CN | CINZA | 1087 | 586,191 |
| CN | AZUL | 1085 | 578,780 |
| CN | ROSA | 1088 | 578,711 |
| CN | AMARELA | 1086 | 578,696 |
| CH | BRANCA | 1057 | 621,146 |
| CH | AZUL | 1055 | 613,221 |
| CH | ROSA | 1058 | 612,395 |
| CH | AMARELA | 1056 | 612,198 |
| LC | BRANCA | 1068 | 621,146 |
| LC | AZUL | 1065 | 613,221 |
| LC | ROSA | 1067 | 612,395 |
| LC | AMARELA | 1066 | 612,198 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | ROSA | 1185 | 7,502 |
| MT | AZUL | 1183 | 7,425 |
| MT | CINZA | 1186 | 7,367 |
| MT | AMARELA | 1184 | 7,348 |
| MT | VERDE | 1083 | 949 |
| MT | CINZA | 1158 | 540 |
| MT | AMARELA | 1156 | 533 |
| MT | AZUL | 1155 | 513 |
| MT | ROSA | 1157 | 501 |
| MT | LARANJA | 1082 | 339 |
| CN | ROSA | 1189 | 7,502 |
| CN | AZUL | 1187 | 7,425 |
| CN | CINZA | 1190 | 7,367 |
| CN | AMARELA | 1188 | 7,348 |
| CN | VERDE | 1093 | 949 |
| CN | CINZA | 1167 | 540 |
| CN | AMARELA | 1166 | 533 |
| CN | AZUL | 1165 | 513 |
| CN | ROSA | 1168 | 501 |
| CN | LARANJA | 1092 | 339 |
| CH | ROSA | 1178 | 8,123 |
| CH | AMARELA | 1176 | 8,037 |
| CH | BRANCA | 1177 | 8,034 |
| CH | AZUL | 1175 | 8,000 |
| CH | VERDE | 1063 | 1,002 |
| CH | LARANJA | 1062 | 349 |
| CH | AMARELA | 1136 | 244 |
| CH | AZUL | 1135 | 243 |
| CH | BRANCA | 1137 | 237 |
| CH | ROSA | 1138 | 213 |
| LC | ROSA | 1182 | 8,123 |
| LC | AMARELA | 1180 | 8,037 |
| LC | BRANCA | 1181 | 8,034 |
| LC | AZUL | 1179 | 8,000 |
| LC | VERDE | 1073 | 1,002 |
| LC | LARANJA | 1072 | 349 |
| LC | AMARELA | 1146 | 244 |
| LC | AZUL | 1145 | 243 |
| LC | BRANCA | 1148 | 237 |
| LC | ROSA | 1147 | 213 |

</details>

---

## ENEM 2021

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELA | 900 | 540,520 |
| MT | CINZA | 902 | 534,778 |
| MT | ROSA | 901 | 534,535 |
| MT | AZUL | 899 | 533,925 |
| CN | AMARELA | 910 | 540,520 |
| CN | CINZA | 911 | 534,778 |
| CN | ROSA | 912 | 534,535 |
| CN | AZUL | 909 | 533,925 |
| CH | AMARELA | 880 | 571,150 |
| CH | BRANCA | 881 | 563,999 |
| CH | ROSA | 882 | 563,957 |
| CH | AZUL | 879 | 563,554 |
| LC | AMARELA | 890 | 571,150 |
| LC | BRANCA | 892 | 563,999 |
| LC | ROSA | 891 | 563,957 |
| LC | AZUL | 889 | 563,554 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | AMARELA | 1036 | 16,489 |
| MT | CINZA | 1038 | 16,228 |
| MT | ROSA | 1037 | 16,174 |
| MT | AZUL | 1035 | 16,083 |
| MT | CINZA | 1010 | 8,623 |
| MT | AZUL | 1007 | 8,585 |
| MT | AMARELA | 1008 | 8,514 |
| MT | ROSA | 1009 | 8,474 |
| MT | VERDE | 907 | 874 |
| MT | AMARELA | 980 | 449 |
| CN | AMARELA | 1046 | 16,489 |
| CN | CINZA | 1047 | 16,228 |
| CN | ROSA | 1048 | 16,174 |
| CN | AZUL | 1045 | 16,083 |
| CN | CINZA | 1014 | 8,623 |
| CN | AZUL | 1011 | 8,585 |
| CN | AMARELA | 1012 | 8,514 |
| CN | ROSA | 1013 | 8,474 |
| CN | VERDE | 917 | 874 |
| CN | AMARELA | 990 | 449 |
| CH | AMARELA | 1016 | 19,114 |
| CH | BRANCA | 1017 | 18,778 |
| CH | AZUL | 1015 | 18,725 |
| CH | ROSA | 1018 | 18,693 |
| CH | AMARELA | 1000 | 9,337 |
| CH | BRANCA | 1001 | 9,250 |
| CH | AZUL | 999 | 9,216 |
| CH | ROSA | 1002 | 9,180 |
| CH | VERDE | 887 | 916 |
| CH | AMARELA | 960 | 560 |
| LC | AMARELA | 1026 | 19,114 |
| LC | BRANCA | 1028 | 18,778 |
| LC | AZUL | 1025 | 18,725 |
| LC | ROSA | 1027 | 18,693 |
| LC | AMARELA | 1004 | 9,337 |
| LC | BRANCA | 1005 | 9,250 |
| LC | AZUL | 1003 | 9,216 |
| LC | ROSA | 1006 | 9,180 |
| LC | VERDE | 897 | 916 |
| LC | AMARELA | 970 | 560 |

</details>

---

## ENEM 2020

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | ROSA | 589 | 632,575 |
| MT | AMARELA | 588 | 625,032 |
| MT | CINZA | 590 | 624,878 |
| MT | AZUL | 587 | 624,708 |
| CN | ROSA | 600 | 632,575 |
| CN | AMARELA | 598 | 625,032 |
| CN | CINZA | 599 | 624,878 |
| CN | AZUL | 597 | 624,708 |
| CH | ROSA | 570 | 670,868 |
| CH | AMARELA | 568 | 663,819 |
| CH | AZUL | 567 | 663,654 |
| CH | BRANCA | 569 | 663,616 |
| LC | ROSA | 579 | 670,868 |
| LC | AMARELA | 578 | 663,819 |
| LC | AZUL | 577 | 663,654 |
| LC | BRANCA | 580 | 663,616 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | AZUL | 667 | 15,643 |
| MT | ROSA | 669 | 15,582 |
| MT | CINZA | 670 | 15,575 |
| MT | AMARELA | 668 | 15,506 |
| MT | CINZA | 698 | 6,655 |
| MT | AZUL | 695 | 6,645 |
| MT | ROSA | 697 | 6,583 |
| MT | AMARELA | 696 | 6,538 |
| MT | VERDE | 595 | 1,160 |
| MT | LARANJA | 594 | 360 |
| CN | AZUL | 677 | 15,643 |
| CN | ROSA | 680 | 15,582 |
| CN | CINZA | 679 | 15,575 |
| CN | AMARELA | 678 | 15,506 |
| CN | CINZA | 702 | 6,655 |
| CN | AZUL | 699 | 6,645 |
| CN | ROSA | 701 | 6,583 |
| CN | AMARELA | 700 | 6,538 |
| CN | VERDE | 605 | 1,160 |
| CN | LARANJA | 604 | 360 |
| CH | ROSA | 650 | 15,506 |
| CH | AMARELA | 648 | 15,499 |
| CH | BRANCA | 649 | 15,472 |
| CH | AZUL | 647 | 15,316 |
| CH | BRANCA | 689 | 7,249 |
| CH | AZUL | 687 | 7,237 |
| CH | ROSA | 690 | 7,197 |
| CH | AMARELA | 688 | 7,122 |
| CH | VERDE | 575 | 1,205 |
| CH | LARANJA | 574 | 380 |
| LC | ROSA | 659 | 15,506 |
| LC | AMARELA | 658 | 15,499 |
| LC | BRANCA | 660 | 15,472 |
| LC | AZUL | 657 | 15,316 |
| LC | BRANCA | 693 | 7,249 |
| LC | AZUL | 691 | 7,237 |
| LC | ROSA | 694 | 7,197 |
| LC | AMARELA | 692 | 7,122 |
| LC | VERDE | 585 | 1,205 |
| LC | LARANJA | 584 | 380 |

</details>

---

## ENEM 2019

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | CINZA | 518 | 933,535 |
| MT | AMARELA | 516 | 925,530 |
| MT | AZUL | 515 | 924,465 |
| MT | ROSA | 517 | 924,211 |
| CN | CINZA | 505 | 933,535 |
| CN | AMARELA | 504 | 925,530 |
| CN | AZUL | 503 | 924,465 |
| CN | ROSA | 506 | 924,211 |
| CH | AMARELA | 508 | 986,473 |
| CH | BRANCA | 509 | 978,235 |
| CH | AZUL | 507 | 978,165 |
| CH | ROSA | 510 | 977,435 |
| LC | AMARELA | 512 | 986,473 |
| LC | BRANCA | 514 | 978,235 |
| LC | AZUL | 511 | 978,165 |
| LC | ROSA | 513 | 977,435 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | VERDE | 526 | 2,089 |
| MT | LARANJA | 522 | 505 |
| CN | VERDE | 523 | 2,089 |
| CN | LARANJA | 519 | 505 |
| CH | VERDE | 524 | 2,206 |
| CH | LARANJA | 520 | 532 |
| LC | VERDE | 525 | 2,206 |
| LC | LARANJA | 521 | 532 |

</details>

---

## ENEM 2018

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELA | 460 | 981,496 |
| MT | CINZA | 462 | 974,252 |
| MT | AZUL | 459 | 973,429 |
| MT | ROSA | 461 | 973,310 |
| CN | AMARELA | 448 | 981,496 |
| CN | CINZA | 449 | 974,252 |
| CN | AZUL | 447 | 973,429 |
| CN | ROSA | 450 | 973,310 |
| CH | AZUL | 451 | 1,041,549 |
| CH | BRANCA | 453 | 1,034,562 |
| CH | AMARELA | 452 | 1,034,414 |
| CH | ROSA | 454 | 1,033,871 |
| LC | AZUL | 455 | 1,041,549 |
| LC | BRANCA | 458 | 1,034,562 |
| LC | AMARELA | 456 | 1,034,414 |
| LC | ROSA | 457 | 1,033,871 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | VERDE | 470 | 2,052 |
| MT | LARANJA | 466 | 546 |
| CN | VERDE | 467 | 2,052 |
| CN | LARANJA | 463 | 546 |
| CH | VERDE | 468 | 2,165 |
| CH | LARANJA | 464 | 566 |
| CH | AMARELA | 492 | 299 |
| CH | ROSA | 494 | 289 |
| CH | AZUL | 491 | 282 |
| CH | BRANCA | 493 | 253 |
| LC | VERDE | 469 | 2,165 |
| LC | LARANJA | 465 | 566 |
| LC | AMARELA | 496 | 299 |
| LC | ROSA | 498 | 289 |
| LC | AZUL | 495 | 282 |
| LC | BRANCA | 497 | 253 |

</details>

---

## ENEM 2017

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELA | 404 | 1,113,123 |
| MT | CINZA | 406 | 1,107,238 |
| MT | AZUL | 403 | 1,107,111 |
| MT | ROSA | 405 | 1,107,045 |
| CN | AMARELA | 392 | 1,113,123 |
| CN | CINZA | 393 | 1,107,238 |
| CN | AZUL | 391 | 1,107,111 |
| CN | ROSA | 394 | 1,107,045 |
| CH | AZUL | 395 | 1,179,817 |
| CH | BRANCA | 397 | 1,172,978 |
| CH | AMARELA | 396 | 1,172,847 |
| CH | ROSA | 398 | 1,171,611 |
| LC | AZUL | 399 | 1,179,817 |
| LC | BRANCA | 402 | 1,172,978 |
| LC | AMARELA | 400 | 1,172,847 |
| LC | ROSA | 401 | 1,171,611 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | VERDE | 414 | 2,416 |
| MT | LARANJA | 410 | 564 |
| CN | VERDE | 411 | 2,416 |
| CN | LARANJA | 407 | 564 |
| CH | VERDE | 412 | 2,493 |
| CH | LARANJA | 408 | 587 |
| CH | AZUL | 435 | 275 |
| CH | ROSA | 438 | 267 |
| CH | AMARELA | 436 | 248 |
| CH | BRANCA | 437 | 242 |
| LC | VERDE | 413 | 2,493 |
| LC | LARANJA | 409 | 587 |
| LC | AZUL | 439 | 275 |
| LC | ROSA | 442 | 267 |
| LC | AMARELA | 440 | 248 |
| LC | BRANCA | 441 | 242 |

</details>

---

## ENEM 2016

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELA | 304 | 1,496,488 |
| MT | AZUL | 303 | 1,447,465 |
| MT | CINZA | 306 | 1,403,296 |
| MT | ROSA | 305 | 1,341,448 |
| CN | AZUL | 291 | 1,535,085 |
| CN | BRANCA | 293 | 1,483,706 |
| CN | AMARELA | 292 | 1,433,420 |
| CN | ROSA | 294 | 1,385,828 |
| CH | AZUL | 295 | 1,535,085 |
| CH | BRANCA | 297 | 1,483,706 |
| CH | AMARELA | 296 | 1,433,420 |
| CH | ROSA | 298 | 1,385,828 |
| LC | AMARELA | 300 | 1,496,488 |
| LC | AZUL | 299 | 1,447,465 |
| LC | CINZA | 302 | 1,403,296 |
| LC | ROSA | 301 | 1,341,448 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | AMARELA | 367 | 41,184 |
| MT | AZUL | 366 | 39,858 |
| MT | CINZA | 369 | 38,084 |
| MT | ROSA | 368 | 36,221 |
| MT | CINZA | 310 | 745 |
| CN | AZUL | 351 | 42,353 |
| CN | BRANCA | 353 | 41,216 |
| CN | AMARELA | 352 | 38,593 |
| CN | ROSA | 354 | 37,317 |
| CN | BRANCA | 307 | 1,065 |
| CN | AZUL | 331 | 129 |
| CN | AMARELA | 332 | 118 |
| CN | BRANCA | 333 | 108 |
| CH | AZUL | 356 | 42,353 |
| CH | BRANCA | 358 | 41,216 |
| CH | AMARELA | 357 | 38,593 |
| CH | ROSA | 359 | 37,317 |
| CH | BRANCA | 308 | 1,065 |
| CH | AZUL | 336 | 129 |
| CH | AMARELA | 337 | 118 |
| CH | BRANCA | 338 | 108 |
| LC | AMARELA | 362 | 41,184 |
| LC | AZUL | 361 | 39,858 |
| LC | CINZA | 364 | 38,084 |
| LC | ROSA | 363 | 36,221 |
| LC | CINZA | 309 | 745 |

</details>

---

## ENEM 2015

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 243 | 1,470,298 |
| MT | AZUL | 245 | 1,428,885 |
| MT | CINZA | 244 | 1,386,745 |
| MT | ROSA | 246 | 1,332,697 |
| CN | AZUL | 235 | 1,500,556 |
| CN | BRANCO | 237 | 1,460,681 |
| CN | AMARELO | 236 | 1,414,064 |
| CN | ROSA | 238 | 1,373,197 |
| CH | AZUL | 231 | 1,500,556 |
| CH | BRANCO | 233 | 1,460,681 |
| CH | AMARELO | 232 | 1,414,064 |
| CH | ROSA | 234 | 1,373,197 |
| LC | AMARELO | 239 | 1,470,298 |
| LC | AZUL | 241 | 1,428,885 |
| LC | CINZA | 240 | 1,386,745 |
| LC | ROSA | 242 | 1,332,697 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | CINZA | 254 | 3,019 |
| MT | AMARELO | 283 | 1,040 |
| MT | AZUL | 285 | 978 |
| MT | CINZA | 284 | 966 |
| MT | ROSA | 286 | 912 |
| CN | BRANCO | 252 | 3,111 |
| CN | AZUL | 275 | 932 |
| CN | BRANCO | 277 | 867 |
| CN | AMARELO | 276 | 859 |
| CN | ROSA | 278 | 824 |
| CH | BRANCO | 251 | 3,111 |
| CH | AZUL | 271 | 932 |
| CH | BRANCO | 273 | 867 |
| CH | AMARELO | 272 | 859 |
| CH | ROSA | 274 | 824 |
| LC | CINZA | 253 | 3,019 |
| LC | AMARELO | 279 | 1,040 |
| LC | AZUL | 281 | 978 |
| LC | CINZA | 280 | 966 |
| LC | ROSA | 282 | 912 |

</details>

---

## ENEM 2014

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 207 | 4,298,204 |
| MT | AZUL | 209 | 1,514,920 |
| MT | CINZA | 208 | 1,481,040 |
| MT | ROSA | 210 | 1,426,037 |
| CN | AZUL | 199 | 4,165,100 |
| CN | BRANCO | 201 | 1,560,652 |
| CN | AMARELO | 200 | 1,520,508 |
| CN | ROSA | 202 | 1,474,870 |
| CH | AZUL | 195 | 4,165,100 |
| CH | BRANCO | 197 | 1,560,652 |
| CH | AMARELO | 196 | 1,520,508 |
| CH | ROSA | 198 | 1,474,870 |
| LC | AMARELO | 203 | 4,298,204 |
| LC | AZUL | 205 | 1,514,920 |
| LC | CINZA | 204 | 1,481,040 |
| LC | ROSA | 206 | 1,426,037 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | CINZA-LEDOR | 218 | 1,091 |
| MT | CINZA | 214 | 956 |
| CN | BRANCO-LEDOR | 216 | 1,118 |
| CH | BRANCO-LEDOR | 215 | 1,118 |
| LC | CINZA-LEDOR | 217 | 1,091 |
| LC | CINZA | 213 | 956 |

</details>

---

## ENEM 2013

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 179 | 3,456,013 |
| MT | AZUL | 181 | 1,275,826 |
| MT | CINZA | 180 | 1,243,798 |
| MT | ROSA | 182 | 1,196,970 |
| CN | AZUL | 171 | 3,327,907 |
| CN | BRANCO | 173 | 1,321,266 |
| CN | AMARELO | 172 | 1,279,025 |
| CN | ROSA | 174 | 1,244,399 |
| CH | AZUL | 167 | 3,327,907 |
| CH | BRANCO | 169 | 1,321,266 |
| CH | AMARELO | 168 | 1,279,025 |
| CH | ROSA | 170 | 1,244,399 |
| LC | AMARELO | 175 | 3,456,013 |
| LC | AZUL | 177 | 1,275,826 |
| LC | CINZA | 176 | 1,243,798 |
| LC | ROSA | 178 | 1,196,970 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | CINZA | 190 | 956 |
| CN | BRANCO | 188 | 966 |
| CH | BRANCO | 187 | 966 |
| LC | CINZA | 189 | 956 |

</details>

---

## ENEM 2012

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELA | 149 | 1,067,089 |
| MT | AZUL | 151 | 1,037,858 |
| MT | CINZA | 150 | 1,013,485 |
| MT | ROSA | 152 | 975,027 |
| CN | AZUL | 141 | 1,101,221 |
| CN | BRANCA | 143 | 1,070,411 |
| CN | AMARELA | 142 | 1,037,685 |
| CN | ROSA | 144 | 1,009,248 |
| CH | AZUL | 137 | 1,101,221 |
| CH | BRANCA | 139 | 1,070,411 |
| CH | AMARELA | 138 | 1,037,685 |
| CH | ROSA | 140 | 1,009,248 |
| LC | AMARELA | 145 | 1,067,089 |
| LC | AZUL | 147 | 1,037,858 |
| LC | CINZA | 146 | 1,013,485 |
| LC | ROSA | 148 | 975,027 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | CINZA | 156 | 425 |
| CN | BRANCA | 153 | 233 |
| CH | BRANCA | 154 | 233 |
| LC | CINZA | 155 | 425 |

</details>

---

## ENEM 2011

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 129 | 2,504,003 |
| MT | AZUL | 131 | 978,571 |
| MT | CINZA | 130 | 958,723 |
| MT | ROSA | 132 | 925,634 |
| CN | AZUL | 121 | 2,422,466 |
| CN | BRANCO | 123 | 1,007,247 |
| CN | AMARELO | 122 | 983,318 |
| CN | ROSA | 124 | 953,900 |
| CH | AZUL | 117 | 2,422,466 |
| CH | BRANCO | 119 | 1,007,247 |
| CH | AMARELO | 118 | 983,318 |
| CH | ROSA | 120 | 953,900 |
| LC | AMARELO | 125 | 2,504,003 |
| LC | AZUL | 127 | 978,571 |
| LC | CINZA | 126 | 958,723 |
| LC | ROSA | 128 | 925,634 |

---

## ENEM 2010

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 97 | 2,205,034 |
| MT | AZUL | 99 | 819,013 |
| MT | CINZA | 98 | 809,296 |
| MT | ROSA | 100 | 778,269 |
| CN | AZUL | 89 | 2,121,088 |
| CN | BRANCO | 91 | 852,571 |
| CN | AMARELO | 90 | 818,158 |
| CN | ROSA | 92 | 815,108 |
| CH | AZUL | 85 | 2,121,088 |
| CH | BRANCO | 87 | 852,571 |
| CH | AMARELO | 86 | 818,158 |
| CH | ROSA | 88 | 815,108 |
| LC | AMARELO | 93 | 2,205,034 |
| LC | AZUL | 95 | 819,013 |
| LC | CINZA | 94 | 809,296 |
| LC | ROSA | 96 | 778,269 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| CN | AZUL | 105 | 1,329 |
| CN | BRANCO | 107 | 1,151 |
| CN | AMARELO | 106 | 1,127 |
| CN | ROSA | 108 | 1,080 |
| CH | AZUL | 101 | 1,329 |
| CH | BRANCO | 103 | 1,151 |
| CH | AMARELO | 102 | 1,127 |
| CH | ROSA | 104 | 1,080 |

</details>

---

## ENEM 2009

### 1a Aplicacao (Regular)

| Area | Cor | Codigo | Participantes |
|------|-----|--------|---------------|
| MT | AMARELO | 61 | 632,832 |
| MT | CINZA | 62 | 614,684 |
| MT | AZUL | 63 | 605,604 |
| MT | ROSA | 64 | 582,468 |
| CN | AZUL | 49 | 672,170 |
| CN | AMARELO | 50 | 638,427 |
| CN | BRANCO | 51 | 632,001 |
| CN | ROSA | 52 | 612,995 |
| CH | AZUL | 53 | 672,170 |
| CH | AMARELO | 54 | 638,427 |
| CH | BRANCO | 55 | 632,001 |
| CH | ROSA | 56 | 612,995 |
| LC | AMARELO | 57 | 632,832 |
| LC | CINZA | 58 | 614,684 |
| LC | AZUL | 59 | 605,604 |
| LC | ROSA | 60 | 582,468 |

### Outras Aplicacoes (2a chamada, PPL, adaptadas)

<details>
<summary>Clique para expandir</summary>

| Area | Cor/Tipo | Codigo | Participantes |
|------|----------|--------|---------------|
| MT | AMARELO | 77 | 1,556 |
| MT | CINZA | 78 | 1,439 |
| MT | AZUL | 79 | 1,438 |
| MT | ROSA | 80 | 1,371 |
| MT | COR_DESCONHECIDA | 84 | 103 |
| CN | AZUL | 65 | 1,673 |
| CN | AMARELO | 66 | 1,564 |
| CN | BRANCO | 67 | 1,492 |
| CN | ROSA | 68 | 1,443 |
| CN | COR_DESCONHECIDA | 81 | 131 |
| CH | AZUL | 69 | 1,673 |
| CH | AMARELO | 70 | 1,564 |
| CH | BRANCO | 71 | 1,492 |
| CH | ROSA | 72 | 1,443 |
| CH | COR_DESCONHECIDA | 82 | 131 |
| LC | AMARELO | 73 | 1,556 |
| LC | CINZA | 74 | 1,439 |
| LC | AZUL | 75 | 1,438 |
| LC | ROSA | 76 | 1,371 |
| LC | COR_DESCONHECIDA | 83 | 103 |

</details>

---

## Trabalhos Futuros

- [ ] Validar cores com cadernos de prova reais
- [ ] Identificar padrao de codigos para cada tipo de aplicacao
- [ ] Separar corretamente 2a aplicacao de PPL
- [ ] Adicionar provas digitais (2020+)
- [ ] Integrar com dados oficiais do INEP

---

*Gerado automaticamente. Para regenerar: `python tools/gerar_mapeamento_aplicacoes.py`*