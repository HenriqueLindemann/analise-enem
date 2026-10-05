#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Investiga associações dos parâmetros publicados usando notas de calibração.

O ajuste contínuo serve apenas para identificar curvas candidatas. A solução
final procura parâmetros já existentes no arquivo oficial, inclusive um item
sem contribuição à verossimilhança. Nenhuma nota de holdout entra no ajuste.
SciPy é necessário somente nesta ferramenta, nunca no motor distribuído.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares, linear_sum_assignment
from scipy.special import expit


ESCALAS = {
    "MT": (129.63, 500.0), "CN": (113.13, 501.16),
    "CH": (112.32, 501.47), "LC": (108.08, 500.0),
}


def quadratura_grade():
    pontos = np.linspace(-4.0, 4.0, 41)
    return pontos, np.exp(-pontos ** 2 / 2)


def probabilidades(parametros, pontos):
    a, b, c = np.asarray(parametros, dtype=float).T
    return np.clip(c + (1 - c) * expit((pontos[:, None] - b) * a),
                   1e-15, 1 - 1e-15)


def theta_parametros(respostas, parametros, pontos=None, pesos=None):
    if pontos is None:
        pontos, pesos = quadratura_grade()
    p = probabilidades(parametros, pontos)
    log_l = respostas @ np.log(p).T + (1 - respostas) @ np.log1p(-p).T
    log_l -= log_l.max(axis=1, keepdims=True)
    posterior = np.exp(log_l) * pesos
    return posterior @ pontos / posterior.sum(axis=1)


def ajustar_curvas(respostas, notas, parametros, area, max_nfev=800):
    """Derivada analítica de EAP: covariância posterior com d(log L)/dp."""
    u, y = np.asarray(respostas), np.asarray(notas)
    parametros = np.asarray(parametros).copy()
    n = len(parametros)
    # Linhas sem parâmetros recebem só uma inicialização para a investigação.
    parametros[parametros[:, 0] <= 0] = [0.5, 4.0, 0.2]
    a, b, c = parametros.T
    c = np.clip(c, 1e-6, 1 - 1e-6)
    inicial = np.r_[np.log(a), b, np.log(c / (1 - c))]
    pontos, pesos = quadratura_grade()
    slope, intercept = ESCALAS[area]
    cache = {}

    def avaliar(v):
        if "v" in cache and np.array_equal(cache["v"], v):
            return cache
        aa, bb, cc = np.exp(v[:n]), v[n:2*n], expit(v[2*n:])
        z = expit((pontos[:, None] - bb) * aa)
        p = np.clip(cc + (1 - cc) * z, 1e-14, 1 - 1e-14)
        log_l = u @ np.log(p).T + (1 - u) @ np.log1p(-p).T
        log_l -= log_l.max(axis=1, keepdims=True)
        posterior = np.exp(log_l) * pesos
        posterior /= posterior.sum(axis=1, keepdims=True)
        theta = posterior @ pontos
        cov = posterior * (pontos[None, :] - theta[:, None])
        derivadas_p = (
            (1 - cc) * z * (1 - z) * (pontos[:, None] - bb) * aa,
            -(1 - cc) * z * (1 - z) * aa,
            (1 - z) * cc * (1 - cc),
        )
        jac = []
        for dp in derivadas_p:
            sim, nao = dp / p, -dp / (1 - p)
            jac.append(slope * ((cov @ (sim - nao)) * u + cov @ nao))
        cache.update(v=v.copy(), pred=slope * theta + intercept,
                     jac=np.column_stack(jac))
        return cache

    limites = (
        np.r_[np.full(n, -5), np.full(n, -15), np.full(n, -10)],
        np.r_[np.full(n, 3), np.full(n, 40), np.full(n, 1)],
    )
    inicial = np.clip(inicial, limites[0], limites[1])
    fit = least_squares(lambda v: avaliar(v)["pred"] - y, inicial,
                        jac=lambda v: avaliar(v)["jac"], bounds=limites,
                        max_nfev=max_nfev, ftol=1e-10, xtol=1e-10)
    curvas = np.column_stack((np.exp(fit.x[:n]), fit.x[n:2*n],
                              expit(fit.x[2*n:])))
    return curvas, {"nfev": fit.nfev, "custo": float(fit.cost),
                    "convergiu": bool(fit.success)}


def associar_curvas(curvas, candidatos):
    """Compara log-odds sem constantes que se cancelam no posterior.

    Um candidato nulo é acrescentado por posição: a ferramenta pode detectar
    ausência de contribuição mesmo quando IN_ITEM_ABAN está incorreto.
    """
    candidatos = np.asarray(candidatos)
    # Uma grade abrangente identifica tanto discriminação quanto transição
    # do patamar de acerto casual. Curvas constantes não informam theta.
    pontos = np.linspace(-3, 4, 141)

    def forma(p):
        a, b, c = p.T
        delta = b + np.log(np.maximum(c, 1e-15)) / np.maximum(a, 1e-15)
        f = np.logaddexp(0, a[:, None] * (pontos - delta[:, None]))
        return f - f.mean(axis=1, keepdims=True)

    f, g = forma(curvas), forma(candidatos)
    custo = np.mean((f[:, None] - g[None]) ** 2, axis=2)
    custo_nulo = np.mean(f ** 2, axis=1)
    custo = np.column_stack([custo, np.repeat(custo_nulo[:, None], len(f), axis=1)])
    linhas, colunas = linear_sum_assignment(custo)
    escolhidos = np.zeros((len(f), 3))
    escolhidos[:, 2] = 0.2
    indices = np.full(len(f), -1, dtype=int)
    for i, j in zip(linhas, colunas):
        if j < len(candidatos):
            escolhidos[i] = candidatos[j]
            indices[i] = j
    return escolhidos, indices


def refinar_associacao(respostas, notas, parametros, candidatos, max_passes=10):
    """Busca discreta por posição; publica somente parâmetros da fonte.

    Cada substituição é avaliada com reajuste afim analítico. O custo usa
    apenas calibração, e candidatos nulos continuam elegíveis.
    """
    u, y = np.asarray(respostas), np.asarray(notas)
    pontos, pesos = quadratura_grade()
    candidatos = np.vstack([candidatos, [0, 0, 0.2]])
    p_cand = probabilidades(candidatos, pontos).T
    log_sim, log_nao = np.log(p_cand), np.log1p(-p_cand)
    parametros = np.asarray(parametros).copy()
    yc = y - y.mean()

    def custo(log_l):
        log_l = log_l - log_l.max(axis=-1, keepdims=True)
        post = np.exp(log_l) * pesos
        t = post @ pontos / post.sum(axis=-1)
        tc = t - t.mean(axis=-1, keepdims=True)
        s = (tc @ yc) / np.maximum((tc * tc).sum(axis=-1), 1e-15)
        residuos = tc * s[..., None] - yc
        return (residuos * residuos).mean(axis=-1)

    p = probabilidades(parametros, pontos)
    ll = u @ np.log(p).T + (1 - u) @ np.log1p(-p).T
    atual = float(custo(ll))
    for _ in range(max_passes):
        mudou = False
        for j in range(len(parametros)):
            old = u[:, j, None] * np.log(p[:, j]) + (1 - u[:, j, None]) * np.log1p(-p[:, j])
            new = (u[None, :, j, None] * log_sim[:, None, :]
                   + (1 - u[None, :, j, None]) * log_nao[:, None, :])
            alternativas = ll[None, :, :] - old + new
            custos = custo(alternativas)
            melhor = int(np.argmin(custos))
            if custos[melhor] < atual - 1e-8:
                parametros[j] = candidatos[melhor]
                p[:, j] = p_cand[melhor]
                ll = alternativas[melhor]
                atual = float(custos[melhor])
                mudou = True
        if not mudou:
            break
    return parametros, atual


def refinar_trocas(respostas, notas, parametros, max_passes=20):
    """Troca pares preservando o conjunto de curvas e sua soma de log(1-P).

    A busca por uma posição isolada pode ficar presa: corrigir apenas uma das
    duas associações cria uma curva duplicada e perde outra. As trocas evitam
    esse obstáculo sem ajustar qualquer parâmetro publicado.
    """
    u, y = np.asarray(respostas), np.asarray(notas)
    parametros = np.asarray(parametros).copy()
    pontos, pesos = quadratura_grade()
    yc = y - y.mean()

    def custo(ll):
        ll = ll - ll.max(axis=-1, keepdims=True)
        posterior = np.exp(ll) * pesos
        t = posterior @ pontos / posterior.sum(axis=-1)
        tc = t - t.mean(axis=-1, keepdims=True)
        slope = (tc @ yc) / np.maximum((tc * tc).sum(axis=-1), 1e-15)
        return ((tc * slope[..., None] - yc) ** 2).mean(axis=-1)

    pares = [(a, b) for a in range(len(parametros)) for b in range(a + 1, len(parametros))]
    for _ in range(max_passes):
        p = probabilidades(parametros, pontos)
        odds = (np.log(p) - np.log1p(-p)).T
        ll = u @ np.log(p).T + (1 - u) @ np.log1p(-p).T
        atual = float(custo(ll))
        melhor, troca = atual, None
        for inicio in range(0, len(pares), 32):
            bloco = pares[inicio:inicio + 32]
            a, b = np.asarray(bloco).T
            delta = (u[:, a] - u[:, b]).T[:, :, None] * (odds[b] - odds[a])[:, None, :]
            custos = custo(ll + delta)
            indice = int(np.argmin(custos))
            if custos[indice] < melhor - 1e-8:
                melhor, troca = float(custos[indice]), bloco[indice]
        if troca is None:
            break
        a, b = troca
        parametros[[a, b]] = parametros[[b, a]]
    return parametros, melhor


def refinar_gabaritos(respostas_texto, notas, parametros, gabaritos, candidatos,
                     max_passes=4):
    """Busca letras e curvas publicadas conjuntamente, só com casos de treino.

    Necessário quando uma letra X exclui indevidamente um item que ainda foi
    usado no cálculo oficial. Cada alternativa continua sujeita à seleção
    independente; uma redução de custo em treino não autoriza publicação.
    """
    raw, y = np.asarray(respostas_texto), np.asarray(notas)
    parametros, gabaritos = np.asarray(parametros).copy(), np.asarray(gabaritos).copy()
    candidatos = np.vstack([candidatos, [0, 0, .2]])
    pontos, pesos = quadratura_grade()
    p_cand = probabilidades(candidatos, pontos).T
    log_sim, log_nao = np.log(p_cand), np.log1p(-p_cand)
    yc = y - y.mean()
    u = (raw == gabaritos).astype(float)

    def custo(ll):
        ll = ll - ll.max(axis=-1, keepdims=True)
        post = np.exp(ll) * pesos
        theta = post @ pontos / post.sum(axis=-1)
        tc = theta - theta.mean(axis=-1, keepdims=True)
        slope = (tc @ yc) / np.maximum((tc * tc).sum(axis=-1), 1e-15)
        return ((tc * slope[..., None] - yc) ** 2).mean(axis=-1)

    for _ in range(max_passes):
        p = probabilidades(parametros, pontos)
        ll = u @ np.log(p).T + (1 - u) @ np.log1p(-p).T
        atual = float(custo(ll))
        for j in range(len(parametros)):
            old = u[:, j, None] * np.log(p[:, j]) + (1 - u[:, j, None]) * np.log1p(-p[:, j])
            melhor = (atual, None, None, None)
            for letra in "ABCDE":
                if letra == gabaritos[j]:
                    continue
                bits = (raw[:, j] == letra).astype(float)
                alternativas = (ll - old + bits[None, :, None] * log_sim[:, None, :]
                                + (1 - bits[None, :, None]) * log_nao[:, None, :])
                custos = custo(alternativas)
                indice = int(np.argmin(custos))
                if custos[indice] < melhor[0] - 1e-7:
                    melhor = (float(custos[indice]), letra, indice, alternativas[indice])
            novo_custo, letra, indice, novo_ll = melhor
            if letra is not None:
                gabaritos[j] = letra
                parametros[j] = candidatos[indice]
                p[:, j] = p_cand[indice]
                u[:, j] = raw[:, j] == letra
                ll, atual = novo_ll, novo_custo
        parametros, atual = refinar_associacao(u, y, parametros, candidatos, 10)
        if atual < .002:
            break
    return parametros, gabaritos, atual


def ajustar_um_item(respostas, notas, parametros, max_nfev=120):
    """Diagnóstico de parâmetros ausentes/incorretos após a associação discreta.

    Ajusta somente três parâmetros de um item de cada vez, com escala afim
    como nuisance. Retorna a maior redução de MSE exclusivamente no treino;
    a aceitação deve ser feita em seleção independente.
    """
    u, y = np.asarray(respostas), np.asarray(notas)
    parametros = np.asarray(parametros).copy()
    pontos, pesos = quadratura_grade()
    p = probabilidades(parametros, pontos)
    ll = u @ np.log(p).T + (1 - u) @ np.log1p(-p).T
    theta = theta_parametros(u, parametros)
    slope, intercept = np.polyfit(theta, y, 1)
    melhor = float(np.mean((slope * theta + intercept - y) ** 2))
    resultado, item_escolhido = parametros.copy(), None
    for j in range(len(parametros)):
        old = u[:, j, None] * np.log(p[:, j]) + (1 - u[:, j, None]) * np.log1p(-p[:, j])
        base = ll - old
        a, b, c = parametros[j] if parametros[j, 0] > 0 else (0.5, 4, 0.2)
        c = np.clip(c, 1e-6, 1 - 1e-6)
        inicial = np.clip(
            [np.log(a), b, np.log(c / (1 - c)), slope, intercept],
            [-5, -15, -10, 50, 300], [3, 40, 1, 200, 700],
        )
        cache = {}

        def avaliar(v):
            if "v" in cache and np.array_equal(cache["v"], v):
                return cache
            aa, bb, cc, ss, ii = np.exp(v[0]), v[1], expit(v[2]), v[3], v[4]
            z = expit(aa * (pontos - bb))
            pr = np.clip(cc + (1 - cc) * z, 1e-14, 1 - 1e-14)
            log_l = base + u[:, j, None] * np.log(pr) + (1 - u[:, j, None]) * np.log1p(-pr)
            log_l -= log_l.max(axis=1, keepdims=True)
            post = np.exp(log_l) * pesos
            post /= post.sum(axis=1, keepdims=True)
            t = post @ pontos
            cov = post * (pontos - t[:, None])
            jac = []
            for dp in ((1 - cc) * z * (1 - z) * aa * (pontos - bb),
                       -(1 - cc) * z * (1 - z) * aa,
                       (1 - z) * cc * (1 - cc)):
                dl = u[:, j, None] * dp / pr - (1 - u[:, j, None]) * dp / (1 - pr)
                jac.append(ss * np.sum(cov * dl, axis=1))
            cache.update(v=v.copy(), pred=ss * t + ii,
                         jac=np.column_stack([*jac, t, np.ones(len(t))]))
            return cache

        fit = least_squares(lambda v: avaliar(v)["pred"] - y, inicial,
                            jac=lambda v: avaliar(v)["jac"],
                            bounds=([-5, -15, -10, 50, 300], [3, 40, 1, 200, 700]),
                            max_nfev=max_nfev, ftol=1e-9, xtol=1e-9)
        custo = 2 * float(fit.cost) / len(y)
        if custo < melhor - 1e-8:
            melhor, item_escolhido = custo, j
            resultado = parametros.copy()
            resultado[j] = [np.exp(fit.x[0]), fit.x[1], expit(fit.x[2])]
    return resultado, melhor, item_escolhido
