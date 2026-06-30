#!/usr/bin/env python3
"""
exportar_resultados_cache.py

Lê os arquivos .txt gerados pelo simulador de cache e consolida os parâmetros
e resultados em um arquivo CSV compatível com Excel.

Uso:
    py exportar_resultados_cache.py resultados
ou:
    python exportar_resultados_cache.py resultados

O diretório "resultados" deve conter arquivos como:
    cache_16.txt
    cache_32.txt
    bloco_64.txt
    associatividade_4.txt
etc.

O arquivo produzido será:
    resultados_cache.csv

O CSV usa ponto e vírgula e UTF-8 com BOM, para abrir corretamente no Excel
em configuração regional brasileira.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any


# Cada chave corresponde a uma linha que o simulador imprime.
PADROES: list[tuple[str, str, type]] = [
    ("arquivo_entrada", r"^Arquivo de entrada:\s*(.+)$", str),
    ("politica_escrita", r"^Politica de escrita:\s*(\d+)\s*\(([^)]+)\)", str),
    ("tamanho_bloco_bytes", r"^Tamanho da linha/bloco:\s*(\d+)\s*bytes$", int),
    ("numero_linhas_cache", r"^Numero de linhas da cache:\s*(\d+)$", int),
    ("associatividade", r"^Associatividade:\s*(\d+)\s*linha", int),
    ("numero_conjuntos", r"^Numero de conjuntos:\s*(\d+)$", int),
    ("hit_time_ns", r"^Hit time:\s*(\d+)\s*ns$", int),
    ("politica_substituicao", r"^Politica de substituicao:\s*(.+)$", str),
    ("tempo_leitura_mp_ns", r"^Tempo de leitura da memoria principal:\s*(\d+)\s*ns$", int),
    ("tempo_escrita_mp_ns", r"^Tempo de escrita da memoria principal:\s*(\d+)\s*ns$", int),
    ("total_acessos", r"^Total de enderecos no arquivo de entrada:\s*(\d+)$", int),
    ("total_leituras_arquivo", r"^Total de leituras no arquivo:\s*(\d+)$", int),
    ("total_escritas_arquivo", r"^Total de escritas no arquivo:\s*(\d+)$", int),
    ("leituras_mp", r"^Total de leituras da memoria principal:\s*(\d+)$", int),
    ("escritas_mp", r"^Total de escritas da memoria principal:\s*(\d+)$", int),
    ("acessos_mp", r"^Total de acessos a memoria principal:\s*(\d+)$", int),
    ("taxa_acerto_leitura", r"^\s*-\s*Leitura:\s*([0-9.]+)", float),
    ("taxa_acerto_escrita", r"^\s*-\s*Escrita:\s*([0-9.]+)", float),
    ("taxa_acerto_global", r"^\s*-\s*Global:\s*([0-9.]+)", float),
    ("tempo_medio_acesso_ns", r"^Tempo medio de acesso da cache:\s*([0-9.]+)\s*ns$", float),
]

COLUNAS = [
    "arquivo_saida",
    "arquivo_entrada",
    "politica_escrita",
    "tamanho_bloco_bytes",
    "numero_linhas_cache",
    "associatividade",
    "numero_conjuntos",
    "hit_time_ns",
    "politica_substituicao",
    "tempo_leitura_mp_ns",
    "tempo_escrita_mp_ns",
    "total_acessos",
    "total_leituras_arquivo",
    "total_escritas_arquivo",
    "leituras_mp",
    "escritas_mp",
    "acessos_mp",
    "taxa_acerto_leitura",
    "taxa_acerto_escrita",
    "taxa_acerto_global",
    "tempo_medio_acesso_ns",
]


def converter(valor: str, tipo: type) -> Any:
    """Converte o campo preservando o formato numérico do simulador."""
    if tipo is int:
        return int(valor)
    if tipo is float:
        return float(valor)
    return valor.strip()


def ler_resultado(caminho: Path) -> dict[str, Any]:
    """Extrai parâmetros e métricas de um único arquivo de saída."""
    try:
        conteudo = caminho.read_text(encoding="utf-8", errors="replace")
    except OSError as erro:
        raise RuntimeError(f"Não foi possível ler '{caminho.name}': {erro}") from erro

    dados: dict[str, Any] = {"arquivo_saida": caminho.name}

    for chave, padrao, tipo in PADROES:
        resultado = re.search(padrao, conteudo, flags=re.MULTILINE)
        if not resultado:
            continue

        if chave == "politica_escrita":
            # Junta código e nome, por exemplo: "0 (write-through)".
            dados[chave] = f"{resultado.group(1)} ({resultado.group(2).strip()})"
        else:
            dados[chave] = converter(resultado.group(1), tipo)

    # Garante que o arquivo é realmente uma saída do simulador.
    if "total_acessos" not in dados or "tamanho_bloco_bytes" not in dados:
        raise ValueError(
            f"'{caminho.name}' não parece conter a saída completa do simulador."
        )

    return dados


def ordenar_chave(dados: dict[str, Any]) -> tuple:
    """Ordena por experimento/configuração, e por nome como desempate."""
    return (
        str(dados.get("politica_escrita", "")),
        int(dados.get("tamanho_bloco_bytes", 0)),
        int(dados.get("numero_linhas_cache", 0)),
        int(dados.get("associatividade", 0)),
        str(dados.get("politica_substituicao", "")),
        str(dados.get("arquivo_saida", "")),
    )


def escrever_csv(destino: Path, linhas: list[dict[str, Any]]) -> None:
    """Escreve CSV compatível com Excel em português do Brasil."""
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=COLUNAS,
            delimiter=";",
            extrasaction="ignore",
        )
        escritor.writeheader()

        for linha in linhas:
            # O simulador já informa a taxa em formato decimal, por exemplo:
            # 0.5341. No Excel, basta aplicar o formato "Porcentagem" à coluna
            # para visualizar 53,41%.
            escritor.writerow(linha)


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: py exportar_resultados_cache.py <pasta_com_txts>")
        return 1

    pasta = Path(sys.argv[1]).expanduser().resolve()

    if not pasta.is_dir():
        print(f"Erro: a pasta não existe: {pasta}")
        return 1

    # "saida_simulacao.txt" é o arquivo automático que o programa sobrescreve
    # a cada execução. Ele é ignorado para evitar duplicar o último teste,
    # pois os resultados relevantes devem estar nos TXT nomeados pelo usuário.
    nomes_ignorados = {"resultados_cache.txt", "saida_simulacao.txt"}

    arquivos = sorted(
        caminho
        for caminho in pasta.glob("*.txt")
        if caminho.name.lower() not in nomes_ignorados
    )

    if not arquivos:
        print(f"Erro: nenhum arquivo .txt foi encontrado em: {pasta}")
        return 1

    resultados: list[dict[str, Any]] = []
    ignorados: list[str] = []

    for arquivo in arquivos:
        try:
            resultados.append(ler_resultado(arquivo))
        except (RuntimeError, ValueError) as erro:
            ignorados.append(str(erro))

    if not resultados:
        print("Erro: nenhum arquivo de saída válido do simulador foi encontrado.")
        for mensagem in ignorados:
            print(f" - {mensagem}")
        return 1

    resultados.sort(key=ordenar_chave)
    destino = pasta / "resultados_cache.csv"
    escrever_csv(destino, resultados)

    print(f"OK: {len(resultados)} arquivo(s) consolidado(s).")
    print(f"Planilha criada: {destino}")

    if ignorados:
        print("\nArquivos ignorados:")
        for mensagem in ignorados:
            print(f" - {mensagem}")

    print(
        "\nObservação: no Excel, formate as colunas de taxa de acerto como "
        "Porcentagem. Os valores já estão no formato decimal, por exemplo 0,5341."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
